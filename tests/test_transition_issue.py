"""Mocked HTTP checks for transition_issue. No network and no real credentials."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import jira_plugin  # noqa: E402
from plugins.jira_plugin import resolve_create, transition_issue  # noqa: E402

_STATUS = {"fields": {"status": {"name": "To Do"}}}
_TRANSITIONS = {"transitions": [
    {"id": "21", "name": "Start Progress", "to": {"name": "In Progress"}},
    {"id": "31", "name": "Done", "to": {"name": "Done"}},
]}
_ONLY_DONE = {"transitions": [{"id": "31", "name": "Done", "to": {"name": "Done"}}]}


def _response(status_code, payload):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def _client(gets, post=None):
    client = MagicMock()
    client.get = AsyncMock(side_effect=[_response(200, item) for item in gets])
    client.post = AsyncMock(return_value=post or _response(204, {}))
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class TransitionIssueTests(unittest.TestCase):
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
        self.settings.write_text(json.dumps({"jira_url": "https://jira.example.com"}), encoding="utf-8")

    def test_preview_makes_no_post(self):
        self._configure()
        client = _client([_STATUS, _TRANSITIONS])
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(transition_issue("kan-4", "in progress", session_id="s-preview"))
        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["preview"], {
            "issue_key": "KAN-4", "current_status": "To Do", "target": "In Progress",
        })
        client.post.assert_not_called()
        self.assertNotIn(self.token, json.dumps(result))

    def test_confirm_posts_once(self):
        self._configure()
        client = _client([_STATUS, _TRANSITIONS, _TRANSITIONS])
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            asyncio.run(transition_issue("KAN-4", "In Progress", session_id="s-yes"))
            result = asyncio.run(resolve_create("s-yes", "yes"))
            again = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertEqual(result, {"status": "transitioned", "issue_key": "KAN-4", "target": "In Progress"})
        self.assertIsNone(again)
        self.assertEqual(client.post.await_count, 1)
        self.assertTrue(client.post.await_args.args[0].endswith("/rest/api/3/issue/KAN-4/transitions"))
        self.assertEqual(client.post.await_args.kwargs["json"], {"transition": {"id": "21"}})
        self.assertNotIn(self.token, json.dumps(result))

    def test_confirm_rechecks_transition(self):
        self._configure()
        client = _client([_STATUS, _TRANSITIONS, _ONLY_DONE])
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            asyncio.run(transition_issue("KAN-4", "In Progress", session_id="s-stale"))
            result = asyncio.run(resolve_create("s-stale", "yes"))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["options"], ["Done"])
        client.post.assert_not_called()

    def test_invalid_target_lists_options(self):
        self._configure()
        client = _client([_STATUS, _TRANSITIONS])
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(transition_issue("KAN-4", "Closed", session_id="s-bad"))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["options"], ["In Progress", "Done"])
        client.post.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_bad_key_rejected(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            nope = asyncio.run(transition_issue("nope", "In Progress"))
            injected = asyncio.run(transition_issue("KAN-4 OR 1=1", "In Progress"))
        self.assertEqual(nope["status"], "error")
        self.assertEqual(injected["status"], "error")
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})


if __name__ == "__main__":
    unittest.main()
