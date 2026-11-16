"""Draft plan from one story + optional document (KAN-131 / FR-PLAN-3)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.draft import add_document_draft_cases, draft_plan_from_issue  # noqa: E402
from plans.store import get_plan  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanDraftTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_draft_from_issue_builds_cases_with_source_refs(self):
        fake_issue = {
            "status": "ok",
            "key": "KAN-131",
            "summary": "Draft a plan from one story",
            "description": "Intro\nAcceptance criteria\n1. First AC bullet\n2. Second AC bullet\nOut of scope\n- Batch",
            "acceptance_criteria": "1. First AC bullet\n2. Second AC bullet",
            "has_acceptance_criteria": True,
        }
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value=fake_issue),
        ):
            result = await draft_plan_from_issue("KAN-131")
        self.assertEqual(result["status"], "ok", result)
        self.assertFalse(result.get("jira_write"))
        plan = result["plan"]
        self.assertIn("KAN-131", plan["sources"]["jira_keys"])
        self.assertIn("First AC bullet", plan["intent"])
        cases = plan["suite"]["cases"]
        self.assertGreaterEqual(len(cases), 2)
        for case in cases:
            self.assertEqual(case["jira_key"], "KAN-131")
            self.assertEqual(case["source"]["kind"], "jira")
            self.assertTrue(case["source"]["ref"])

    async def test_draft_with_document_adds_doc_cases(self):
        fake_issue = {
            "status": "ok",
            "key": "KAN-131",
            "summary": "Story",
            "description": "Acceptance criteria\n1. Only AC",
            "acceptance_criteria": "1. Only AC",
            "has_acceptance_criteria": True,
        }
        doc = (
            "Given a logged-in user\nWhen they open Plans\nThen the draft appears\n"
            "The system must reject empty issue keys."
        )
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value=fake_issue),
        ):
            result = await draft_plan_from_issue(
                "KAN-131",
                document_text=doc,
                document_name="alpha-spec.md",
            )
        self.assertEqual(result["status"], "ok", result)
        plan = result["plan"]
        self.assertIn("alpha-spec.md", plan["sources"]["documents"])
        doc_cases = [
            c for c in plan["suite"]["cases"] if c["source"]["kind"] == "document"
        ]
        self.assertGreaterEqual(len(doc_cases), 1)
        for case in doc_cases:
            self.assertEqual(case["jira_key"], "KAN-131")
            self.assertTrue(case["source"]["ref"])

    async def test_document_only_adds_cases_no_jira_write(self):
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(
                return_value={
                    "status": "ok",
                    "key": "KAN-10",
                    "summary": "S",
                    "description": "Acceptance criteria\n1. Base",
                    "acceptance_criteria": "1. Base",
                    "has_acceptance_criteria": True,
                }
            ),
        ):
            created = await draft_plan_from_issue("KAN-10")
        plan_id = created["plan"]["id"]
        added = add_document_draft_cases(
            plan_id,
            document_text="Must verify logout clears the session cookie.",
            document_name="extra.md",
            jira_key="KAN-10",
        )
        self.assertEqual(added["status"], "ok", added)
        self.assertFalse(added.get("jira_write"))
        refreshed = get_plan(plan_id)
        self.assertIn("extra.md", refreshed["plan"]["sources"]["documents"])


if __name__ == "__main__":
    unittest.main()
