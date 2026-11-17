"""Project-wide draft in batches (KAN-161 / C3 / FR-PLAN-3)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.draft import (  # noqa: E402
    MAX_PROJECT_BATCH,
    clamp_project_batch,
    draft_plan_from_project,
)
from settings.store import write_settings  # noqa: E402


class ProjectDraftTests(unittest.IsolatedAsyncioTestCase):
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

    def test_clamp_batch_size_visible_cap(self):
        self.assertEqual(clamp_project_batch(5), 5)
        self.assertEqual(clamp_project_batch(0), 1)
        self.assertEqual(clamp_project_batch(999), MAX_PROJECT_BATCH)
        self.assertEqual(clamp_project_batch("nope"), 5)

    async def test_project_draft_uses_settings_project_and_batch_cap(self):
        listed = {
            "status": "ok",
            "stories": [
                {"key": "KAN-101", "summary": "First story", "type": "Story"},
                {"key": "KAN-102", "summary": "Second story", "type": "Story"},
                {"key": "KAN-103", "summary": "Third (beyond batch)", "type": "Story"},
            ],
            "note": "showing 3 of 40",
        }

        async def fake_read(key: str):
            return {
                "status": "ok",
                "key": key,
                "summary": f"Summary {key}",
                "description": "Acceptance criteria\n1. Check login\n2. Check logout",
                "acceptance_criteria": "1. Check login\n2. Check logout",
                "has_acceptance_criteria": True,
            }

        with (
            patch(
                "plugins.jira_plugin.list_stories",
                new=AsyncMock(return_value=listed),
            ) as list_mock,
            patch(
                "plugins.jira_plugin.read_issue",
                new=AsyncMock(side_effect=fake_read),
            ) as read_mock,
        ):
            result = await draft_plan_from_project(batch_size=2)

        self.assertEqual(result["status"], "ok", result)
        self.assertFalse(result.get("jira_write"))
        self.assertTrue(result.get("review_required"))
        self.assertFalse(result.get("auto_run"))
        self.assertEqual(result["project"], "KAN")
        self.assertEqual(result["batch_size"], 2)
        self.assertEqual(result["issue_count"], 2)
        self.assertEqual(len(result["issues_drafted"]), 2)
        self.assertGreaterEqual(result["case_count"], 4)

        list_mock.assert_awaited()
        # First call drafts the batch; later call (C4) lists a wider project window.
        first_list = list_mock.await_args_list[0]
        self.assertEqual(first_list.args[0], "KAN")
        self.assertEqual(first_list.kwargs.get("max"), 2)
        self.assertGreaterEqual(list_mock.await_count, 2)
        self.assertEqual(read_mock.await_count, 2)
        self.assertIn("coverage_gaps", result)
        self.assertFalse(result.get("cases_created_for_gaps"))

        plan = result["plan"]
        self.assertEqual(set(plan["sources"]["jira_keys"]), {"KAN-101", "KAN-102"})
        for case in plan["suite"]["cases"]:
            self.assertEqual(case["source"]["kind"], "jira")
            self.assertIn(case["jira_key"], ("KAN-101", "KAN-102"))

    async def test_project_draft_missing_jira_project(self):
        write_settings(
            {
                "security_level": "OFFICIAL",
                "orb_style": "mystic",
                "jira_project": "",
            }
        )
        result = await draft_plan_from_project(batch_size=5)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "project_required")
        self.assertFalse(result.get("jira_write"))

    async def test_project_draft_no_jira_writes_on_list_failure(self):
        with patch(
            "plugins.jira_plugin.list_stories",
            new=AsyncMock(
                return_value={"status": "rate_limited", "message": "Slow down"}
            ),
        ):
            result = await draft_plan_from_project(batch_size=3)
        self.assertEqual(result["status"], "error")
        self.assertFalse(result.get("jira_write"))
        self.assertEqual(result["batch_size"], 3)


if __name__ == "__main__":
    unittest.main()
