"""Coverage gaps after project draft (KAN-163 / C4 / FR-PLAN-3 / FR-REP-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.coverage import (  # noqa: E402
    classify_story_cases,
    coverage_from_plan,
    plan_coverage_gaps,
)
from plans.draft import draft_plan_from_project  # noqa: E402
from plans.store import add_case, create_plan, update_case  # noqa: E402
from settings.store import write_settings  # noqa: E402


class CoverageGapsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings(
            {
                "security_level": "OFFICIAL",
                "orb_style": "mystic",
                "jira_project": "KAN",
            }
        )

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_classify_story_cases(self):
        self.assertEqual(classify_story_cases([]), "no_case")
        self.assertEqual(
            classify_story_cases([{"enabled": False}, {"enabled": False}]),
            "all_disabled",
        )
        self.assertEqual(
            classify_story_cases([{"enabled": False}, {"enabled": True}]),
            "covered",
        )

    def test_coverage_from_plan_lists_gaps_separately_and_filterable(self):
        plan = {
            "id": "p1",
            "sources": {"jira_keys": ["KAN-1", "KAN-2", "KAN-3"], "documents": []},
            "suite": {
                "cases": [
                    {"jira_key": "KAN-1", "name": "A", "enabled": True, "archived": False},
                    {"jira_key": "KAN-2", "name": "B", "enabled": False, "archived": False},
                    {"jira_key": "KAN-2", "name": "C", "enabled": False, "archived": False},
                ]
            },
        }
        project_stories = [
            {"key": "KAN-1", "summary": "Login"},
            {"key": "KAN-2", "summary": "Logout"},
            {"key": "KAN-3", "summary": "Profile"},
            {"key": "KAN-4", "summary": "Settings page"},
        ]
        out = coverage_from_plan(plan, project_stories=project_stories)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["cases_created"])
        no_keys = {r["key"] for r in out["no_case"]}
        disabled_keys = {r["key"] for r in out["all_disabled"]}
        covered_keys = {r["key"] for r in out["covered"]}
        self.assertEqual(no_keys, {"KAN-3", "KAN-4"})
        self.assertEqual(disabled_keys, {"KAN-2"})
        self.assertEqual(covered_keys, {"KAN-1"})

        filtered = coverage_from_plan(
            plan, project_stories=project_stories, filter_text="settings"
        )
        self.assertEqual([r["key"] for r in filtered["no_case"]], ["KAN-4"])
        self.assertEqual(filtered["all_disabled"], [])
        self.assertEqual(filtered["covered"], [])

    async def test_plan_coverage_gaps_does_not_create_cases(self):
        created = create_plan(
            name="Gap plan",
            intent="test",
            sources={"jira_keys": ["KAN-10"], "documents": []},
        )
        plan_id = created["plan"]["id"]
        before = created["plan"]["suite"]["cases"]
        self.assertEqual(before, [])

        listed = {
            "status": "ok",
            "stories": [
                {"key": "KAN-10", "summary": "Open story"},
                {"key": "KAN-11", "summary": "Missing coverage"},
            ],
        }
        with patch(
            "plugins.jira_plugin.list_stories",
            new=AsyncMock(return_value=listed),
        ):
            out = await plan_coverage_gaps(plan_id, filter_text="")

        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["cases_created"])
        self.assertEqual({r["key"] for r in out["no_case"]}, {"KAN-10", "KAN-11"})

        # Disabling all cases for a drafted story moves it to all_disabled.
        added = add_case(plan_id, "Case for 10", jira_key="KAN-10", enabled=True)
        case_id = added["case"]["id"]
        update_case(plan_id, case_id, enabled=False)
        with patch(
            "plugins.jira_plugin.list_stories",
            new=AsyncMock(return_value=listed),
        ):
            out2 = await plan_coverage_gaps(plan_id)

        self.assertEqual({r["key"] for r in out2["no_case"]}, {"KAN-11"})
        self.assertEqual({r["key"] for r in out2["all_disabled"]}, {"KAN-10"})
        self.assertFalse(out2["cases_created"])

    async def test_project_draft_includes_coverage_gaps(self):
        listed = {
            "status": "ok",
            "stories": [
                {"key": "KAN-201", "summary": "First", "type": "Story"},
                {"key": "KAN-202", "summary": "Second", "type": "Story"},
                {"key": "KAN-203", "summary": "Third undrafted", "type": "Story"},
            ],
        }

        async def fake_read(key: str):
            return {
                "status": "ok",
                "key": key,
                "summary": f"Summary {key}",
                "description": "",
                "acceptance_criteria": "1. Check one thing",
                "has_acceptance_criteria": True,
            }

        list_mock = AsyncMock(return_value=listed)
        with (
            patch("plugins.jira_plugin.list_stories", new=list_mock),
            patch(
                "plugins.jira_plugin.read_issue",
                new=AsyncMock(side_effect=fake_read),
            ),
        ):
            result = await draft_plan_from_project(batch_size=2)

        self.assertEqual(result["status"], "ok")
        self.assertFalse(result.get("cases_created_for_gaps"))
        gaps = result.get("coverage_gaps") or {}
        self.assertEqual(gaps.get("status"), "ok")
        no_keys = {r["key"] for r in gaps.get("no_case") or []}
        self.assertIn("KAN-203", no_keys)
        self.assertNotIn("KAN-201", no_keys)


class CoverageGapsUiTests(unittest.TestCase):
    def test_desktop_plans_has_coverage_gap_controls(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("plan-coverage-filter", html)
        self.assertIn("plan-coverage-btn", html)
        self.assertIn("plan-coverage-no-case", html)
        self.assertIn("plan-coverage-disabled", html)
        self.assertIn("coverage-gaps", js)
        self.assertIn("refreshCoverageGaps", js)
        self.assertIn("desk71", html)
        self.assertIn("desk71", app)


if __name__ == "__main__":
    unittest.main()
