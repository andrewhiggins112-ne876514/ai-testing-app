"""First-hour home checklist widget (KAN-215 / F7 / FR-UI-6 + FR-UI-1)."""
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
from plans.home_checklist import home_checklist_summary  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    start_suite_run,
)
from settings.store import write_settings  # noqa: E402


class HomeChecklistTests(unittest.TestCase):
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

    def test_empty_lab_steps_incomplete(self):
        payload = home_checklist_summary()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["home_only"])
        self.assertFalse(payload["blocks_app"])
        self.assertFalse(payload["forced_wizard"])
        self.assertTrue(payload["auto_hide_when_done"])
        self.assertFalse(payload["all_done"])
        ids = [s["id"] for s in payload["steps"]]
        self.assertEqual(ids, ["connection", "first_plan", "first_run"])
        self.assertFalse(payload["steps"][0]["done"])
        self.assertFalse(payload["steps"][1]["done"])
        self.assertFalse(payload["steps"][2]["done"])

    def test_connection_first_plan_first_run_progress(self):
        write_settings(
            {
                "security_level": "OFFICIAL",
                "jira_url": "https://jira.example.com",
                "target_url": "https://app.example.com",
            }
        )
        mid = home_checklist_summary()
        self.assertTrue(mid["steps"][0]["done"])
        self.assertFalse(mid["steps"][1]["done"])
        self.assertFalse(mid["all_done"])

        created = create_plan(
            name="F7 plan",
            intent="first hour",
            sources={"jira_keys": ["KAN-215"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        after_plan = home_checklist_summary()
        self.assertTrue(after_plan["steps"][1]["done"])
        self.assertFalse(after_plan["steps"][2]["done"])
        self.assertFalse(after_plan["all_done"])

        cid = add_case(pid, name="smoke", tags=["smoke"])["case"]["id"]
        sr = start_suite_run(pid, mode="suite")
        self.assertEqual(sr["status"], "ok")
        sid = sr["suite_run"]["id"]
        rid = add_run(pid, cid, result="pass", duration_ms=50, suite_run_id=sid)[
            "run"
        ]["id"]
        finished = finish_suite_run(
            pid, sid, case_runs=[{"case_id": cid, "run_id": rid}]
        )
        self.assertEqual(finished["status"], "ok")

        done = home_checklist_summary()
        self.assertTrue(done["all_done"])
        self.assertTrue(done["steps"][2]["done"])
        self.assertEqual(done["done_count"], 3)

    def test_api_and_desktop_ui_desk84(self):
        client = TestClient(main.app)
        res = client.get("/api/plans/home-checklist")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["home_only"])
        self.assertFalse(body["forced_wizard"])
        self.assertFalse(body["blocks_app"])
        self.assertTrue(body["auto_hide_when_done"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk84", html)
        self.assertIn("desk84", desk)
        self.assertIn('id="hud-checklist"', html)
        self.assertIn("hud-checklist-toggle", html)
        self.assertIn("hud-checklist-steps", html)
        self.assertIn("First-hour checklist", html)
        self.assertIn("/api/plans/home-checklist", js)
        self.assertIn("loadHomeChecklistHud", js)
        self.assertIn("checklistAllDone", js)


if __name__ == "__main__":
    unittest.main()
