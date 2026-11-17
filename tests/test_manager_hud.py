"""Manager HUD widget pack on orb home (KAN-205 / F2 / FR-UI-6 + FR-REP-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from plans.manager_hud import manager_hud_summary as build_manager_hud  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    set_known_issue_link,
    start_suite_run,
)
from settings.store import write_settings  # noqa: E402


class ManagerHudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def _seed(self):
        created = create_plan(
            name="Manager HUD plan",
            intent="F2 widgets",
            sources={"jira_keys": ["KAN-205", "KAN-999"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        cid_ok = add_case(
            pid, name="passes", tags=["smoke"], jira_key="KAN-205"
        )["case"]["id"]
        cid_bug = add_case(
            pid, name="product break", tags=["smoke"], jira_key="KAN-205"
        )["case"]["id"]
        cid_known = add_case(
            pid, name="known fail", tags=["regression"], jira_key="KAN-205"
        )["case"]["id"]
        # KAN-999 stays with no case → coverage gap.

        sr = start_suite_run(pid, mode="suite")
        self.assertEqual(sr["status"], "ok")
        sid = sr["suite_run"]["id"]
        rid_ok = add_run(
            pid, cid_ok, result="pass", duration_ms=100, suite_run_id=sid
        )["run"]["id"]
        rid_bug = add_run(
            pid,
            cid_bug,
            result="fail",
            duration_ms=200,
            failure_class="product_bug",
            suite_run_id=sid,
        )["run"]["id"]
        rid_known = add_run(
            pid,
            cid_known,
            result="fail",
            duration_ms=150,
            failure_class="known_issue",
            suite_run_id=sid,
        )["run"]["id"]
        finished = finish_suite_run(
            pid,
            sid,
            case_runs=[
                {"case_id": cid_ok, "run_id": rid_ok},
                {"case_id": cid_bug, "run_id": rid_bug},
                {"case_id": cid_known, "run_id": rid_known},
            ],
        )
        self.assertEqual(finished["status"], "ok")

        ki = set_known_issue_link(
            pid,
            cid_known,
            note="tracked elsewhere",
            jira_key="KAN-50",
            run_id=rid_known,
        )
        self.assertEqual(ki["status"], "ok")
        return pid, cid_ok, cid_bug, cid_known

    def test_summary_pass_rate_known_gaps_bugs(self):
        pid, _cid_ok, cid_bug, cid_known = self._seed()
        payload = build_manager_hud()

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["home_only"])
        self.assertFalse(payload["separate_manager_home"])
        self.assertTrue(payload["known_not_shown_as_pass"])

        rate = payload["pass_rate"]
        self.assertEqual(rate["plan_id"], pid)
        self.assertEqual(rate["pass"], 1)
        self.assertEqual(rate["fail"], 2)
        self.assertTrue(rate["known_not_counted_as_pass"])
        # 1 pass / 3 outcomes = 33.3%; known stays in fail bucket.
        self.assertEqual(rate["pass_rate_percent"], 33.3)
        self.assertGreaterEqual(rate["known_issues"], 1)

        self.assertGreaterEqual(payload["known_issue_count"], 1)
        known_ids = {r["case_id"] for r in payload["known_issues"]}
        self.assertIn(cid_known, known_ids)
        for row in payload["known_issues"]:
            self.assertFalse(row.get("shown_as_pass"))
            self.assertNotEqual(row.get("result"), "pass")

        self.assertGreaterEqual(payload["stories_no_case_count"], 1)
        gap_keys = {r["story_key"] for r in payload["stories_no_case"]}
        self.assertIn("KAN-999", gap_keys)

        self.assertGreaterEqual(payload["bugs_count"], 1)
        bug_ids = {r["case_id"] for r in payload["bugs"]}
        self.assertIn(cid_bug, bug_ids)
        self.assertNotIn(cid_known, bug_ids)

    def test_api_manager_hud_and_desktop_ui_desk79(self):
        self._seed()
        client = TestClient(main.app)
        res = client.get("/api/plans/manager-hud")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["separate_manager_home"])
        self.assertTrue(body["home_only"])
        self.assertTrue(body["known_not_shown_as_pass"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk79", html)
        self.assertIn("desk79", desk)
        self.assertIn('id="hud-mgr-pass"', html)
        self.assertIn('id="hud-mgr-known"', html)
        self.assertIn('id="hud-mgr-gaps"', html)
        self.assertIn('id="hud-mgr-bugs"', html)
        self.assertIn("hud-mgr-pass-toggle", html)
        self.assertIn("hud-mgr-known-toggle", html)
        self.assertIn("hud-mgr-gaps-toggle", html)
        self.assertIn("hud-mgr-bugs-toggle", html)
        self.assertIn("Manager HUD pack", html)
        self.assertIn("/api/plans/manager-hud", js)
        self.assertIn("loadManagerHud", js)
        self.assertIn('openArea("reports")', js)


if __name__ == "__main__":
    unittest.main()
