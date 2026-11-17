"""Single-case Playwright run + degraded + source view + evidence + failure class + pause + rerun (KAN-137…151)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.defect_packet import defect_packet_preview
from plans.evidence_bundle import write_failure_bundle
from plans.pause_session import clear_sessions
from plans.rerun_failed import rerun_failed_cases, select_rerun_candidates
from plans.run_case import case_detail, run_single_case
from plans.store import (
    add_case,
    add_run,
    create_plan,
    get_plan,
    set_known_issue_link,
    set_run_failure_class,
)
from settings.degraded import degraded_status, ollama_chat_blocked


class PlanRunCaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()
        clear_sessions()

    def tearDown(self):
        clear_sessions()
        self._tmp.cleanup()

    def test_disabled_case_refused(self):
        created = create_plan("P", intent="t")
        pid = created["plan"]["id"]
        added = add_case(pid, "Off", enabled=False)
        cid = added["case"]["id"]
        import asyncio

        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("error"), "case_disabled")

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_records_pass(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "screenshot": r"C:\tmp\ok.png",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("P2")
        pid = created["plan"]["id"]
        added = add_case(pid, "Go", note="open app", source_ref="goto home")
        cid = added["case"]["id"]
        import asyncio

        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertEqual(out.get("only_case_id"), cid)
        mock_pw.assert_called_once()
        self.assertFalse(mock_pw.call_args.kwargs.get("headless"))

    @patch("plans.run_case._check_target")
    def test_target_down_is_environment_not_pass(self, mock_tgt):
        mock_tgt.return_value = {"up": False, "message": "Target timed out."}
        created = create_plan("P3")
        pid = created["plan"]["id"]
        added = add_case(pid, "T")
        cid = added["case"]["id"]
        import asyncio

        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("run", {}).get("result"), "error")
        self.assertEqual(out.get("run", {}).get("failure_class"), "environment")

    def test_case_detail_source_and_last_run(self):
        created = create_plan("Src")
        pid = created["plan"]["id"]
        added = add_case(
            pid,
            "AC one",
            jira_key="KAN-1",
            source_kind="jira",
            source_ref="bullet 1",
        )
        cid = added["case"]["id"]
        add_run(pid, cid, result="fail", duration_ms=42, note="nope")
        from plans.store import get_plan

        plan = get_plan(pid)["plan"]
        loaded = case_detail(plan, cid)
        self.assertEqual(loaded.get("jira_key"), "KAN-1")
        self.assertFalse(loaded.get("manual_draft"))
        self.assertIn("fail", loaded.get("last_run_summary") or "")

    def test_evidence_bundle_paths(self):
        bundle = write_failure_bundle(
            run_id="r-test",
            plan_id="p1",
            case_id="c1",
            playwright={
                "status": "fail",
                "screenshot": r"C:\x\shot.png",
                "steps": [{"action": "click", "error": "timeout"}],
                "error": "timeout",
            },
        )
        self.assertTrue(bundle.get("bundle_path"))
        self.assertGreaterEqual(len(bundle.get("paths") or []), 2)

    def test_failure_class_and_defect_preview(self):
        created = create_plan("Pkt")
        pid = created["plan"]["id"]
        added = add_case(pid, "Broken", jira_key="KAN-9", source_ref="see AC")
        cid = added["case"]["id"]
        ran = add_run(pid, cid, result="fail", note="Expected ok", evidence=["C:\\ev.png"])
        rid = ran["run"]["id"]
        cls = set_run_failure_class(pid, cid, rid, "test_defect")
        self.assertEqual(cls.get("failure_class"), "test_defect")
        self.assertFalse(cls.get("create_bug_allowed"))
        preview = defect_packet_preview(pid, cid, run_id=rid)
        self.assertEqual(preview.get("status"), "ok")
        self.assertIn("symptom", preview.get("packet") or {})

    def test_degraded_and_chat_block(self):
        snap = degraded_status()
        self.assertIn("ollama_up", snap)
        with patch("settings.degraded.connection_health") as mock_h:
            mock_h.return_value = {
                "security_level": "OFFICIAL",
                "checks": [
                    {"id": "ollama", "up": False, "message": "down"},
                    {"id": "jira", "up": True},
                    {"id": "target", "up": True},
                ],
            }
            blocked = ollama_chat_blocked()
            self.assertIsNotNone(blocked)
            self.assertFalse(blocked.get("ok"))

    def test_api_run_endpoint_disabled(self):
        client = TestClient(main.app)
        created = create_plan("API")
        pid = created["plan"]["id"]
        added = add_case(pid, "x", enabled=False)
        cid = added["case"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/{cid}/run")
        body = res.json()
        self.assertEqual(body.get("error"), "case_disabled")

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_pause_off_by_default(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "fail",
            "playwright_mode": "headed",
            "error": "boom",
            "steps": [{"action": "click", "status": "fail", "error": "boom"}],
            "screenshot": r"C:\tmp\fail.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("PauseOff")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Fail")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("run", {}).get("result"), "fail")
        self.assertFalse(mock_pw.call_args.kwargs.get("pause_on_fail"))
        self.assertIsNone(mock_pw.call_args.kwargs.get("pause_decision"))

    @patch("plans.run_case._check_target")
    def test_pause_on_fail_stop_records_failed_run(self, mock_tgt):
        mock_tgt.return_value = {"up": True, "message": "ok"}

        async def fake_pw(**kwargs):
            self.assertTrue(kwargs.get("pause_on_fail"))
            decision = kwargs.get("pause_decision")
            self.assertIsNotNone(decision)
            partial = {
                "status": "paused",
                "error": "selector missing",
                "steps": [
                    {"action": "click", "status": "fail", "error": "selector missing"}
                ],
                "screenshot": r"C:\tmp\paused.png",
            }
            choice = await decision(partial)
            self.assertEqual(choice, "stop")
            return {
                "status": "fail",
                "playwright_mode": "headed",
                "error": "selector missing",
                "pause_decision": "stop",
                "steps": partial["steps"],
                "screenshot": r"C:\tmp\paused.png",
            }

        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("PauseStop")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Broken")["case"]["id"]

        async def scenario():
            task = asyncio.create_task(
                run_single_case(pid, cid, pause_on_fail=True)
            )
            first = await task
            self.assertEqual(first.get("status"), "paused")
            pause_id = first.get("pause_id")
            self.assertTrue(pause_id)
            from plans.pause_session import signal_decision

            stopped = await signal_decision(pause_id, "stop")
            self.assertEqual(stopped.get("run", {}).get("result"), "fail")
            self.assertEqual(stopped.get("pause_decision"), "stop")
            return stopped

        with patch("plugins.playwright_runner.run_playwright", new=fake_pw):
            final = asyncio.run(scenario())
        self.assertEqual(final.get("run", {}).get("result"), "fail")

    def test_api_pause_endpoints_not_found(self):
        client = TestClient(main.app)
        res = client.get("/api/plans/pause/missing")
        self.assertEqual(res.json().get("error"), "pause_not_found")
        res = client.post("/api/plans/pause/missing/stop")
        self.assertEqual(res.json().get("error"), "pause_not_found")

    def test_rerun_failed_skips_disabled_and_quarantined(self):
        created = create_plan("RerunSkip")
        pid = created["plan"]["id"]
        c_fail = add_case(pid, "FailOn")["case"]["id"]
        c_off = add_case(pid, "FailOff", enabled=False)["case"]["id"]
        c_q = add_case(pid, "FailQ")["case"]["id"]
        c_pass = add_case(pid, "Pass")["case"]["id"]
        add_run(pid, c_fail, result="fail", note="red")
        add_run(pid, c_off, result="fail", note="red")
        add_run(pid, c_q, result="error", note="red")
        add_run(pid, c_pass, result="pass")
        plan = get_plan(pid)["plan"]
        for case in plan["suite"]["cases"]:
            if case["id"] == c_q:
                case["quarantined"] = True
                case["quarantine"] = {"reason": "flake", "active": True}
        from plans.store import _write_plan

        _write_plan(plan, level=plan["security_level"])
        plan = get_plan(pid)["plan"]
        sel = select_rerun_candidates(plan)
        self.assertEqual(sel.get("status"), "ok")
        self.assertIn(c_fail, sel.get("to_run") or [])
        reasons = {s["case_id"]: s["reason"] for s in sel.get("skipped") or []}
        self.assertEqual(reasons.get(c_off), "disabled")
        self.assertEqual(reasons.get(c_q), "quarantined")
        self.assertNotIn(c_pass, sel.get("failed_case_ids") or [])

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_rerun_failed_new_suite_run_linked(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\rerun.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("RerunOk")
        pid = created["plan"]["id"]
        c1 = add_case(pid, "A")["case"]["id"]
        c2 = add_case(pid, "B")["case"]["id"]
        add_run(pid, c1, result="fail")
        add_run(pid, c2, result="fail")
        out = asyncio.run(rerun_failed_cases(pid))
        self.assertEqual(out.get("status"), "ok")
        suite_run_id = out.get("suite_run_id")
        self.assertTrue(suite_run_id)
        self.assertTrue(out.get("sequential"))
        self.assertEqual(len(out.get("case_results") or []), 2)
        plan = get_plan(pid)["plan"]
        self.assertTrue(any(r.get("id") == suite_run_id for r in plan.get("suite_runs") or []))
        linked = 0
        for case in plan["suite"]["cases"]:
            for run in case.get("runs") or []:
                if run.get("suite_run_id") == suite_run_id:
                    linked += 1
        self.assertEqual(linked, 2)
        self.assertEqual(mock_pw.await_count, 2)

    def test_api_rerun_failed_no_failures(self):
        client = TestClient(main.app)
        created = create_plan("RerunEmpty")
        pid = created["plan"]["id"]
        add_case(pid, "Only")
        res = client.post(f"/api/plans/{pid}/rerun-failed", json={})
        body = res.json()
        self.assertEqual(body.get("error"), "no_failed_cases")

    def test_known_issue_link_keeps_red_and_labels_known(self):
        created = create_plan("Known")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Flaky login")["case"]["id"]
        rid = add_run(pid, cid, result="fail", note="still broken")["run"]["id"]
        out = set_known_issue_link(
            pid,
            cid,
            note="Known flash on login",
            jira_key="KAN-200",
            run_id=rid,
        )
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("label"), "known")
        self.assertEqual(out.get("result"), "fail")
        self.assertTrue(out.get("result_unchanged"))
        self.assertFalse(out.get("jira_transitioned"))
        self.assertFalse(out.get("create_bug_allowed"))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "fail")
        self.assertEqual(run.get("failure_class"), "known_issue")
        self.assertEqual((run.get("known_issue") or {}).get("jira_key"), "KAN-200")
        plan = get_plan(pid)["plan"]
        detail = case_detail(plan, cid)
        self.assertEqual(detail.get("known_label"), "known")
        self.assertIn("known", detail.get("last_run_summary") or "")
        self.assertIn("fail", detail.get("last_run_summary") or "")

    def test_api_known_issue_and_report_toggle(self):
        client = TestClient(main.app)
        created = create_plan("KnownAPI")
        pid = created["plan"]["id"]
        cid = add_case(pid, "X")["case"]["id"]
        rid = add_run(pid, cid, result="error")["run"]["id"]
        res = client.post(
            f"/api/plans/{pid}/cases/{cid}/known-issue",
            json={"note": "tracked", "jira_key": "KAN-9", "run_id": rid},
        )
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("result"), "error")
        self.assertEqual(body.get("label"), "known")
        secs = client.get("/api/report-sections").json()
        self.assertIn("known_issues", secs)
        saved = client.post(
            "/api/report-sections",
            json={
                "summary": True,
                "stories": True,
                "bugs": True,
                "evidence": True,
                "known_issues": False,
            },
        ).json()
        self.assertFalse(saved.get("known_issues"))

    def test_plan_notes_case_and_run_level_scoped(self):
        from plans.store import set_plan_notes

        created = create_plan("Notes")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Explore")["case"]["id"]
        rid = add_run(pid, cid, result="fail", note="system error")["run"]["id"]
        out = set_plan_notes(
            pid,
            cid,
            case_note="Saw flicker on load",
            run_note="Retried twice; still red",
            run_id=rid,
        )
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("case_note"), "Saw flicker on load")
        self.assertEqual(out.get("tester_note"), "Retried twice; still red")
        run = out.get("run") or {}
        self.assertEqual(run.get("note"), "system error")
        self.assertEqual(run.get("tester_note"), "Retried twice; still red")
        plan = get_plan(pid)["plan"]
        detail = case_detail(plan, cid)
        self.assertEqual(detail.get("note"), "Saw flicker on load")
        self.assertEqual(detail.get("tester_note"), "Retried twice; still red")

    def test_api_plan_notes(self):
        client = TestClient(main.app)
        created = create_plan("NotesAPI")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Y")["case"]["id"]
        rid = add_run(pid, cid, result="pass")["run"]["id"]
        res = client.post(
            f"/api/plans/{pid}/cases/{cid}/notes",
            json={
                "case_note": "case ok",
                "run_note": "run ok",
                "run_id": rid,
            },
        )
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("case_note"), "case ok")
        self.assertEqual(body.get("tester_note"), "run ok")

    def test_desktop_cache_bust_desk81(self):
        root = os.path.dirname(os.path.dirname(__file__))
        html = open(os.path.join(root, "ui", "desktop", "index.html"), encoding="utf-8").read()
        desk = open(os.path.join(root, "desktop_app.py"), encoding="utf-8").read()
        self.assertIn("desk81", desk)
        self.assertIn("plan-notes-save", html)
        self.assertIn("plan-run-note", html)
        self.assertIn("plan-known-save", html)
        self.assertIn("rpt-known-issues", html)
        self.assertIn("rpt-export-run", html)
        self.assertIn("heal-run-filter", html)


if __name__ == "__main__":
    unittest.main()