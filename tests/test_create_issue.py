"""Mocked HTTP checks for create_issue. No network and no real credentials."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import Agent  # noqa: E402
from plugins import jira_plugin  # noqa: E402
from plugins.jira_plugin import create_issue, resolve_create  # noqa: E402


def _response(key):
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"key": key}
    return response


def _client(response):
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    client.get = AsyncMock(side_effect=AssertionError("GET not allowed"))
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class CreateIssueTests(unittest.TestCase):
    def setUp(self):
        jira_plugin._PENDING.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = {key: os.environ.get(key) for key in ("AI_TESTING_SETTINGS", "JIRA_API_TOKEN", "JIRA_EMAIL")}
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ.pop("JIRA_API_TOKEN", None)
        os.environ.pop("JIRA_EMAIL", None)
        self.token = "x" * 20

    def tearDown(self):
        jira_plugin._PENDING.clear()
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _configure(self):
        os.environ["JIRA_API_TOKEN"] = self.token
        os.environ["JIRA_EMAIL"] = "qa@example.com"
        self.settings.write_text(json.dumps({
            "jira_base_url": "https://jira.example.com",
            "jira_url": "https://wrong.example.com",
        }), encoding="utf-8")

    def test_unconfigured(self):
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(create_issue("KAN", "AI app smoke test"))
        self.assertEqual(result["status"], "unconfigured")
        self.assertTrue(result.get("message"))
        self.assertNotIn(self.token, json.dumps(result))
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_preview_makes_no_post(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(create_issue("kan", "Hello", session_id="s-preview"))
        self.assertEqual(result["status"], "confirmation_required")
        self.assertTrue(result["confirm_id"])
        self.assertEqual(result["preview"]["project"], "KAN")
        self.assertEqual(result["preview"]["summary"], "Hello")
        self.assertEqual(result["preview"]["issue_type"], "Task")
        ctor.assert_not_called()

    def _posted(self, session_id, word, key):
        client = _client(_response(key))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(resolve_create(session_id, word))
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["key"], key)
        self.assertEqual(client.post.await_count, 1)
        endpoint = client.post.await_args.args[0]
        self.assertTrue(endpoint.endswith("/rest/api/3/issue"))
        fields = client.post.await_args.kwargs["json"]["fields"]
        self.assertEqual(fields["project"]["key"], "KAN")
        self.assertEqual(fields["issuetype"]["name"], "Task")
        self.assertEqual(client.post.await_args.kwargs["auth"], ("qa@example.com", self.token))
        self.assertNotIn(self.token, json.dumps(result))
        again = asyncio.run(resolve_create(session_id, word))
        self.assertIsNone(again)
        self.assertEqual(client.post.await_count, 1)
        return fields

    def test_yes_posts_once(self):
        self._configure()
        asyncio.run(create_issue("KAN", "Hello", description="Details", session_id="s-yes"))
        fields = self._posted("s-yes", "yes", "KAN-99")
        self.assertEqual(fields["summary"], "Hello")
        self.assertEqual(fields["description"]["content"][0]["content"][0]["text"], "Details")

    def test_confirm_word_posts_once(self):
        self._configure()
        asyncio.run(create_issue("KAN", "Hello", session_id="s-confirm"))
        fields = self._posted("s-confirm", "confirm", "KAN-100")
        self.assertNotIn("description", fields)

    def test_expired_other_session_and_no_make_no_post(self):
        self._configure()
        with patch("plugins.jira_plugin.time.monotonic", return_value=1000):
            asyncio.run(create_issue("KAN", "Hello", session_id="s-expire"))
        client = _client(_response("KAN-1"))
        with patch("plugins.jira_plugin.time.monotonic", return_value=1301):
            with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
                expired = asyncio.run(resolve_create("s-expire", "yes"))
        self.assertEqual(expired["status"], "expired")
        client.post.assert_not_called()

        asyncio.run(create_issue("KAN", "Hello", session_id="s-a"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            other = asyncio.run(resolve_create("s-b", "yes"))
        self.assertIsNone(other)
        client.post.assert_not_called()
        self.assertIn("s-a", jira_plugin._PENDING)

        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            cancelled = asyncio.run(resolve_create("s-a", "no"))
        self.assertEqual(cancelled["status"], "cancelled")
        client.post.assert_not_called()
        self.assertNotIn("s-a", jira_plugin._PENDING)
        self.assertIsNone(asyncio.run(resolve_create("s-a", "yes")))

    def test_tool_confirm_flag_does_not_post(self):
        self._configure()
        agent = Agent()
        call = {"function": {"name": "create_issue", "arguments": {
            "project": "KAN", "summary": "Hello", "confirm": True,
        }}}
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(agent._execute_tool(call, "please confirm yes", "s-tool"))
        self.assertEqual(result["status"], "confirmation_required")
        ctor.assert_not_called()
        names = [tool["function"]["name"] for tool in agent.tools]
        self.assertIn("create_issue", names)
        schema = next(tool for tool in agent.tools if tool["function"]["name"] == "create_issue")
        self.assertNotIn("confirm", schema["function"]["parameters"]["properties"])

    def test_user_yes_posts_without_calling_the_model(self):
        self._configure()
        asyncio.run(create_issue("KAN", "Hello", session_id="s-chat"))
        client = _client(_response("KAN-99"))

        def factory(*args, **kwargs):
            if kwargs.get("timeout") == 20.0:
                return client
            raise AssertionError("model called")

        agent = Agent()
        with patch("plugins.jira_plugin.httpx.AsyncClient", side_effect=factory):
            reply = asyncio.run(agent.chat("yes", "s-chat"))
        self.assertEqual(reply, "Created KAN-99.")
        self.assertEqual(client.post.await_count, 1)

        def no_second_post(*args, **kwargs):
            if kwargs.get("timeout") == 20.0:
                raise AssertionError("second POST")
            fake = MagicMock()
            fake.post = AsyncMock(return_value=MagicMock(
                json=MagicMock(return_value={"message": {"content": "ok"}})
            ))
            fake.__aenter__ = AsyncMock(return_value=fake)
            fake.__aexit__ = AsyncMock(return_value=False)
            return fake

        with patch("plugins.jira_plugin.httpx.AsyncClient", side_effect=no_second_post):
            asyncio.run(agent.chat("yes", "s-chat"))
        self.assertEqual(client.post.await_count, 1)


if __name__ == "__main__":
    unittest.main()
