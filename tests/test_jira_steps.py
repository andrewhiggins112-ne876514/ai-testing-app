"""Generate Playwright steps from Jira AC (KAN-85 / FR-TEST-1)."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import Agent  # noqa: E402
from plugins.jira_plugin import (  # noqa: E402
    adf_to_text,
    extract_acceptance_criteria,
    read_issue,
)
from plugins.playwright_steps import generate_steps_from_jira  # noqa: E402


ADF = {
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Acceptance criteria"}],
        },
        {
            "type": "paragraph",
            "content": [{
                "type": "text",
                "text": (
                    "Given https://example.com When user clicks Login "
                    "and fills Email with a@b.com Then expect text Welcome"
                ),
            }],
        },
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Out of scope"}],
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Silent Jira writes."}],
        },
    ],
}


class _Resp:
    def __init__(self, status_code: int, data=None):
        self.status_code = status_code
        self._data = data if data is not None else {}

    def json(self):
        return self._data


class _Client:
    def __init__(self, response, *args, **kwargs):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        return self._response


class JiraAdfTests(unittest.TestCase):
    def test_adf_and_ac_extraction(self):
        text = adf_to_text(ADF)
        self.assertIn("Acceptance criteria", text)
        ac = extract_acceptance_criteria(text)
        self.assertIn("Welcome", ac)
        self.assertNotIn("Silent Jira writes", ac)


class JiraReadIssueTests(unittest.TestCase):
    def test_bad_key(self):
        result = asyncio.run(read_issue("not a key"))
        self.assertEqual(result["status"], "error")
        self.assertIn("KEY-123", result["message"])

    def test_fetch_ok(self):
        payload = {
            "key": "KAN-85",
            "fields": {
                "summary": "Generate from AC",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Story"},
                "description": ADF,
            },
        }
        with patch("plugins.jira_plugin._list_creds", return_value={
            "url": "https://example.atlassian.net",
            "email": "u@example.com",
            "token": "tok",
        }), patch("plugins.jira_plugin.httpx.AsyncClient", lambda *a, **k: _Client(_Resp(200, payload))):
            result = asyncio.run(read_issue("KAN-85"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["key"], "KAN-85")
        self.assertTrue(result["has_acceptance_criteria"])
        self.assertIn("Welcome", result["acceptance_criteria"])

    def test_fetch_404(self):
        with patch("plugins.jira_plugin._list_creds", return_value={
            "url": "https://example.atlassian.net",
            "email": "u@example.com",
            "token": "tok",
        }), patch("plugins.jira_plugin.httpx.AsyncClient", lambda *a, **k: _Client(_Resp(404))):
            result = asyncio.run(read_issue("KAN-9999"))
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])


class GenerateFromJiraTests(unittest.TestCase):
    def test_happy_path_proposes_expect(self):
        fetched = {
            "status": "ok",
            "key": "KAN-85",
            "summary": "Login flow",
            "description": adf_to_text(ADF),
            "acceptance_criteria": extract_acceptance_criteria(adf_to_text(ADF)),
            "has_acceptance_criteria": True,
        }
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value=fetched),
        ):
            pack = asyncio.run(generate_steps_from_jira("KAN-85"))
        self.assertEqual(pack["status"], "ok")
        self.assertFalse(pack.get("invented_ac"))
        actions = [s["action"] for s in pack["steps"]]
        self.assertTrue(
            any(a in {"expect_text", "expect_url"} for a in actions),
            actions,
        )
        self.assertEqual(pack["issue_key"], "KAN-85")
        self.assertEqual(pack["source"], "acceptance_criteria")

    def test_fetch_failure_no_invented_ac(self):
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value={
                "status": "error",
                "message": "issue KAN-9999 not found",
            }),
        ):
            pack = asyncio.run(generate_steps_from_jira("KAN-9999"))
        self.assertEqual(pack["status"], "error")
        self.assertFalse(pack.get("invented_ac", True))
        self.assertEqual(pack["steps"], [])
        self.assertEqual(pack["happy_path"], [])
        self.assertIn("not found", pack["message"])

    def test_empty_description_refuses_invent(self):
        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value={
                "status": "ok",
                "key": "KAN-1",
                "summary": "Empty",
                "description": "",
                "acceptance_criteria": "",
                "has_acceptance_criteria": False,
            }),
        ):
            pack = asyncio.run(generate_steps_from_jira("KAN-1"))
        self.assertEqual(pack["status"], "error")
        self.assertFalse(pack["invented_ac"])
        self.assertEqual(pack["steps"], [])
        self.assertIn("invent", pack["message"].lower())

    def test_agent_dispatches_issue_key(self):
        agent = Agent()
        fake = {
            "status": "ok",
            "issue_key": "KAN-85",
            "steps": [
                {"action": "goto", "value": "https://example.com"},
                {"action": "expect_text", "value": "Welcome"},
            ],
            "happy_path": [],
            "negatives": [],
            "invented_ac": False,
        }
        with patch(
            "plugins.playwright_steps.generate_steps_from_jira",
            new=AsyncMock(return_value=fake),
        ) as mocked:
            result = asyncio.run(agent._execute_tool(
                {"function": {"name": "generate_playwright_steps", "arguments": {"issue_key": "KAN-85"}}},
                "generate from KAN-85",
                "t",
            ))
        mocked.assert_awaited_once()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["issue_key"], "KAN-85")


if __name__ == "__main__":
    unittest.main()
