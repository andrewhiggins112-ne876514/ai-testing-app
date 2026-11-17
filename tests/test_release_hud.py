"""Release HUD widget pack on orb home (KAN-207 / F3 / FR-UI-6 + FR-REP-2)."""
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
from plans.release_hud import release_hud_summary as build_release_hud  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    start_suite_run,
)
from settings.environments import upsert_environment  # noqa: E402
from settings.store import write_settings  # noqa: E402


class ReleaseHudTests(unittest.TestCase):
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
        env = upsert_environment(
            name="Staging",
            target_url="https://staging.example.test",
            activate=True,
        )
        self.assertEqual(env["status"], "ok")

        created = create_plan(
            name="Release HUD plan",
            intent="F3 widgets",
            sources={"jira_keys": ["KAN-207", "KAN-888"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        cid_ok = add_case(
            pid, name="passes", tags=["smoke"], jira_key="KAN-207"
        )["case"]["id"]
        cid_bug = add_case(
            pid, name="product break", tags=["smoke"], jira_key="KAN-207"
        )["case"]["id"]
        # KAN-888 stays with no case → uncovered.

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
        finished = finish_suite_run(
            pid,
            sid,
            case_runs=[
                {"case_id": cid_ok, "run_id": rid_ok},
                {"case_id": cid_bug, "run_id": rid_bug},
            ],
        )
        self.assertEqual(finished["status"], "ok")
        return pid, cid_ok, cid_bug

    def test_summary_env_last_uncovered_bugs(self):
        pid, _cid_ok, cid_bug = self._seed()
        payload = build_release_hud()

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["home_only"])
        self.assertFalse(payload["separate_release_home"])
        self.assertTrue(payload["readiness_ticks_on_reports"])

        env = payload["environment"]
        self.assertEqual(env["name"], "Staging")
        self.assertTrue(env["target_url_set"])
        self.assertEqual(env["readiness_links_to"], "reports")

        last = payload["last_run"]
        self.assertEqual(last["plan_id"], pid)
        self.assertEqual(last["pass"], 1)
        self.assertEqual(last["fail"], 1)
        self.assertEqual(last["readiness_links_to"], "reports")

        self.assertGreaterEqual(payload["uncovered_stories_count"], 1)
        gap_keys = {r["story_key"] for r in payload["uncovered_stories"]}
        self.assertIn("KAN-888", gap_keys)

        self.assertGreaterEqual(payload["open_product_bugs_count"], 1)
        bug_ids = {r["case_id"] for r in payload["open_product_bugs"]}
        self.assertIn(cid_bug, bug_ids)
        for row in payload["open_product_bugs"]:
            self.assertEqual(row["readiness_links_to"], "reports")

    def test_api_release_hud_and_desktop_ui_desk76(self):
        self._seed()
        client = TestClient(main.app)
        res = client.get("/api/plans/release-hud")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["separate_release_home"])
        self.assertTrue(body["home_only"])
        self.assertTrue(body["readiness_ticks_on_reports"])
        self.assertEqual(body["environment"]["name"], "Staging")

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk76", html)
        self.assertIn("desk76", desk)
        self.assertIn('id="hud-rel-env"', html)
        self.assertIn('id="hud-rel-last"', html)
        self.assertIn('id="hud-rel-uncovered"', html)
        self.assertIn('id="hud-rel-bugs"', html)
        self.assertIn("hud-rel-env-toggle", html)
        self.assertIn("hud-rel-last-toggle", html)
        self.assertIn("hud-rel-uncovered-toggle", html)
        self.assertIn("hud-rel-bugs-toggle", html)
        self.assertIn("Release HUD pack", html)
        self.assertIn("/api/plans/release-hud", js)
        self.assertIn("loadReleaseHud", js)
        self.assertIn("openReleaseReadiness", js)


if __name__ == "__main__":
    unittest.main()
