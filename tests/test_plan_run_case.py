"""Single-case Playwright run + degraded + source view + evidence + failure class (KAN-137…147)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.defect_packet import defect_packet_preview
from plans.evidence_bundle import write_failure_bundle
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, add_run, create_plan, set_run_failure_class
from settings.degraded import degraded_status, ollama_chat_blocked


class PlanRunCaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
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


if __name__ == "__main__":
    unittest.main()