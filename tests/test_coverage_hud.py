"""Coverage HUD widget pack on orb home (KAN-209 / F4 / FR-UI-6 + FR-PLAN-4)."""
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
from plans.coverage_hud import coverage_hud_summary as build_coverage_hud  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    upsert_jira_snapshot,
)
from settings.store import write_settings  # noqa: E402


class CoverageHudTests(unittest.TestCase):
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
            name="Coverage HUD plan",
            intent="F4 widgets",
            sources={"jira_keys": ["KAN-209"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        upsert_jira_snapshot(
            pid,
            "KAN-209",
            summary="Coverage HUD widget pack",
            acceptance_criteria=(
                "- Optional widget for open story AC lines\n"
                "- Choosing a line opens Plan on linked case\n"
                "- Widget does not edit Jira\n"
            ),
        )
        cid_pass = add_case(
            pid,
            name="Optional widget for open story AC lines",
            jira_key="KAN-209",
            source_kind="jira",
            source_ref="Optional widget for open story AC lines",
        )["case"]["id"]
        cid_fail = add_case(
            pid,
            name="Choosing a line opens Plan on linked case",
            jira_key="KAN-209",
            source_kind="jira",
            source_ref="Choosing a line opens Plan on linked case",
        )["case"]["id"]
        # Third AC line stays without a case → missing.
        add_run(pid, cid_pass, result="pass", duration_ms=50)
        add_run(pid, cid_fail, result="fail", duration_ms=80)
        return pid, cid_pass, cid_fail

    def test_summary_covered_partial_missing(self):
        pid, cid_pass, cid_fail = self._seed()
        payload = build_coverage_hud()

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["home_only"])
        self.assertFalse(payload["separate_coverage_home"])
        self.assertFalse(payload["separate_po_home"])
        self.assertFalse(payload["jira_write"])

        story = payload["open_story"]
        self.assertEqual(story["story_key"], "KAN-209")
        self.assertEqual(story["plan_id"], pid)
        self.assertEqual(story["covered_count"], 1)
        self.assertEqual(story["partial_count"], 1)
        self.assertEqual(story["missing_count"], 1)
        self.assertFalse(story["jira_write"])

        covered_ids = {r["case_id"] for r in payload["covered"]}
        partial_ids = {r["case_id"] for r in payload["partial"]}
        self.assertIn(cid_pass, covered_ids)
        self.assertIn(cid_fail, partial_ids)
        self.assertEqual(payload["missing_count"], 1)
        for row in payload["missing"]:
            self.assertIsNone(row["case_id"])
            self.assertEqual(row["status"], "missing")
            self.assertFalse(row["jira_write"])
            self.assertTrue(row["opens_plans"])

    def test_api_coverage_hud_and_desktop_ui_desk78(self):
        self._seed()
        client = TestClient(main.app)
        res = client.get("/api/plans/coverage-hud")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["separate_po_home"])
        self.assertTrue(body["home_only"])
        self.assertFalse(body["jira_write"])
        self.assertEqual(body["open_story"]["story_key"], "KAN-209")

        keyed = client.get("/api/plans/coverage-hud", params={"story_key": "KAN-209"})
        self.assertEqual(keyed.status_code, 200)
        self.assertEqual(keyed.json()["open_story"]["story_key"], "KAN-209")

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk78", html)
        self.assertIn("desk78", desk)
        self.assertIn('id="hud-cov-story"', html)
        self.assertIn('id="hud-cov-covered"', html)
        self.assertIn('id="hud-cov-partial"', html)
        self.assertIn('id="hud-cov-missing"', html)
        self.assertIn("hud-cov-story-toggle", html)
        self.assertIn("hud-cov-covered-toggle", html)
        self.assertIn("hud-cov-partial-toggle", html)
        self.assertIn("hud-cov-missing-toggle", html)
        self.assertIn("Coverage HUD pack", html)
        self.assertIn("/api/plans/coverage-hud", js)
        self.assertIn("loadCoverageHud", js)
        self.assertIn("openCoverageLine", js)


if __name__ == "__main__":
    unittest.main()
