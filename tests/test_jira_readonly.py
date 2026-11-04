"""Stdlib checks for the read-only Jira gate. No network."""
import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["AI_TESTING_SETTINGS"] = str(Path(tempfile.gettempdir()) / "ai_testing_app_test_missing.json")

from plugins.jira_plugin import jira_action  # noqa: E402


class JiraReadOnlyTests(unittest.TestCase):
    def test_missing_settings(self):
        result = asyncio.run(jira_action("list_stories", project="PROJ"))
        self.assertEqual(result["error"], "jira_not_configured")

    def test_writes_blocked(self):
        result = asyncio.run(jira_action("create_bug", project="PROJ"))
        self.assertEqual(result["status"], "confirmation_required")

    def test_bad_project_key(self):
        result = asyncio.run(jira_action("list_stories", project="bad key"))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
