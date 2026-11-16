"""KAN-89 / FR-JIRA-1: read story description + AC via tool, list flag, and API."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import TOOL_NAMES, Agent  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
from plugins.jira_plugin import list_stories, read_issue  # noqa: E402


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
            "content": [{"type": "text", "text": "Given a valid key Then AC text is returned"}],
        },
    ],
}


class _Resp:
    def __init__(self, status_code: int, data=None):
        self.status_code = status_code
        self._data = data if data is not None else {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                "err", request=httpx.Request("GET", "https://example.com"), response=self
            )


class _Client:
    def __init__(self, response, *args, **kwargs):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        return self._response


class ReadIssueUxTests(unittest.TestCase):
    def test_agent_exposes_read_issue_tool(self):
        self.assertIn("read_issue", TOOL_NAMES)
        tools = Agent().tools
        names = [t["function"]["name"] for t in tools]
        self.assertIn("read_issue", names)
        list_tool = next(t for t in tools if t["function"]["name"] == "list_stories")
        self.assertIn("include_description", list_tool["function"]["parameters"]["properties"])

    def test_read_issue_unauthorized_no_token_echo(self):
        with patch(
            "plugins.jira_plugin._list_creds",
            return_value={
                "url": "https://example.atlassian.net",
                "email": "u@example.com",
                "token": "super-secret-token",
            },
        ), patch(
            "plugins.jira_plugin.httpx.AsyncClient",
            lambda *a, **k: _Client(_Resp(401)),
        ):
            result = asyncio.run(read_issue("KAN-89"))
        self.assertEqual(result["status"], "unauthorized")
        blob = str(result)
        self.assertNotIn("super-secret-token", blob)
        self.assertIn("credential", result["message"].lower())

    def test_list_stories_include_description(self):
        payload = {
            "total": 1,
            "issues": [
                {
                    "key": "KAN-89",
                    "fields": {
                        "summary": "Read AC",
                        "status": {"name": "To Do"},
                        "issuetype": {"name": "Story"},
                        "description": ADF,
                    },
                }
            ],
        }
        with patch(
            "plugins.jira_plugin._list_creds",
            return_value={
                "url": "https://example.atlassian.net",
                "email": "u@example.com",
                "token": "tok",
            },
        ), patch(
            "plugins.jira_plugin.httpx.AsyncClient",
            lambda *a, **k: _Client(_Resp(200, payload)),
        ):
            result = asyncio.run(
                list_stories("KAN", max=5, include_description=True)
            )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["stories"]), 1)
        story = result["stories"][0]
        self.assertTrue(story["has_acceptance_criteria"])
        self.assertIn("AC text is returned", story["acceptance_criteria"])
        self.assertNotIn("jira_api_token", str(result))
        self.assertNotIn('"token"', str(result))

    def test_api_jira_issue_get(self):
        fetched = {
            "status": "ok",
            "key": "KAN-89",
            "summary": "Read story",
            "issue_status": "To Do",
            "type": "Story",
            "description": "Acceptance criteria\nGiven x",
            "acceptance_criteria": "Given x",
            "has_acceptance_criteria": True,
        }

        async def _fake(key: str):
            self.assertEqual(key.upper(), "KAN-89")
            return fetched

        with patch("plugins.jira_plugin.read_issue", side_effect=_fake):
            client = TestClient(app)
            res = client.get("/api/jira-issue/KAN-89")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["has_acceptance_criteria"])
        self.assertNotIn("token", body)
        self.assertNotIn("jira_api_token", body)

    def test_api_jira_issue_missing(self):
        async def _missing(key: str):
            return {"status": "error", "message": f"issue {key} not found"}

        with patch("plugins.jira_plugin.read_issue", side_effect=_missing):
            client = TestClient(app)
            res = client.post("/api/jira-issue", json={"issue_key": "KAN-99999"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "error")
        self.assertIn("not found", body["message"])

    def test_desktop_html_has_read_controls(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (root / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn('id="jira-read-key"', html)
        self.assertIn('id="jira-read-btn"', html)
        self.assertIn("/api/jira-issue/", js)
        self.assertIn("desk28", html)


if __name__ == "__main__":
    unittest.main()
