"""Document ingestion → settings proposals (KAN-45 / FR-LEARN-5 / FR-SET-2)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import doc_ingest  # noqa: E402
from plugins.doc_ingest import (  # noqa: E402
    apply_proposal,
    decline_proposal,
    extract_settings_proposals,
    extract_test_ideas,
    ingest_document,
    resolve_doc_ingest,
)
from settings.store import load_settings  # noqa: E402

SAMPLE = """
# Login flow

Target application: https://app.example.com/login
Jira project: KAN
Jira URL: https://ai-testing-lab.atlassian.net
Jira email: qa@example.com
api_token: super-secret-token

Given a valid user, When they submit the form, Then they see the dashboard.
- The system must reject empty passwords.
"""


class DocIngestTests(unittest.TestCase):
    def setUp(self):
        doc_ingest.clear_pending()
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        self.settings.write_text(json.dumps({"jira_url": ""}), encoding="utf-8")

    def tearDown(self):
        doc_ingest.clear_pending()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_extract_settings_and_ideas(self):
        proposed = extract_settings_proposals(SAMPLE)
        self.assertEqual(proposed["target_url"], "https://app.example.com/login")
        self.assertEqual(proposed["jira_project"], "KAN")
        self.assertEqual(proposed["jira_url"], "https://ai-testing-lab.atlassian.net")
        self.assertEqual(proposed["jira_email"], "qa@example.com")
        self.assertEqual(proposed["jira_api_token"], "super-secret-token")
        ideas = extract_test_ideas(SAMPLE)
        self.assertTrue(any("Given" in i for i in ideas))
        self.assertTrue(any("must reject" in i.lower() for i in ideas))

    def test_proposal_does_not_write(self):
        before = self.settings.read_text(encoding="utf-8")
        result = ingest_document(text=SAMPLE, filename="spec.md", session_id="s1")
        self.assertEqual(result["status"], "proposal")
        self.assertIn("jira_url", result["settings_diff"])
        self.assertEqual(result["settings_diff"]["jira_api_token"]["to"], "(hidden)")
        self.assertEqual(self.settings.read_text(encoding="utf-8"), before)
        self.assertNotIn("super-secret-token", json.dumps(result))

    def test_decline_leaves_settings_unchanged(self):
        result = ingest_document(text=SAMPLE, session_id="s2")
        pid = result["proposal_id"]
        declined = decline_proposal(pid)
        self.assertEqual(declined["status"], "declined")
        data = load_settings()
        self.assertEqual(data.get("jira_url") or "", "")
        self.assertEqual(data.get("jira_api_token") or "", "")

    def test_confirm_writes_only_approved_keys(self):
        result = ingest_document(text=SAMPLE, session_id="s3")
        pid = result["proposal_id"]
        applied = apply_proposal(pid, keys=["jira_url", "jira_project"], confirm=True)
        self.assertEqual(applied["status"], "applied")
        data = load_settings()
        self.assertEqual(data["jira_url"], "https://ai-testing-lab.atlassian.net")
        self.assertEqual(data["jira_project"], "KAN")
        self.assertEqual(data.get("jira_api_token") or "", "")
        self.assertEqual(data.get("target_url") or "", "")

    def test_confirm_without_flag_does_not_write(self):
        result = ingest_document(text=SAMPLE, session_id="s4")
        pid = result["proposal_id"]
        preview = apply_proposal(pid, confirm=False)
        self.assertEqual(preview["status"], "confirmation_required")
        self.assertEqual(load_settings().get("jira_url") or "", "")

    def test_chat_yes_applies_pending(self):
        ingest_document(text=SAMPLE, session_id="chat")
        outcome = resolve_doc_ingest("chat", "yes")
        self.assertEqual(outcome["status"], "applied")
        self.assertTrue(load_settings().get("target_url"))

    def test_chat_decline(self):
        ingest_document(text=SAMPLE, session_id="chat2")
        outcome = resolve_doc_ingest("chat2", "decline")
        self.assertEqual(outcome["status"], "declined")
        self.assertEqual(load_settings().get("jira_url") or "", "")

    def test_markdown_file_path(self):
        path = Path(self.tmp.name) / "feature.md"
        path.write_text(
            "Target: https://docs.example.com\nProject key: ABC\n",
            encoding="utf-8",
        )
        result = ingest_document(path=str(path), session_id="file")
        self.assertEqual(result["status"], "proposal")
        self.assertEqual(result["settings_diff"]["target_url"]["to"], "https://docs.example.com")
        self.assertEqual(result["settings_diff"]["jira_project"]["to"], "ABC")


if __name__ == "__main__":
    unittest.main()
