"""Mocked HTTP checks for epic parent linking. No network and no real credentials."""
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
from plugins.jira_plugin import create_issue, resolve_create, set_parent  # noqa: E402


def _typed(name, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"fields": {"issuetype": {"name": name}}}
    return response


def _created(key="KAN-20"):
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"key": key}
    return response


def _saved():
    response = MagicMock()
    response.status_code = 204
    return response


def _client(get_response=None, post_response=None, put_response=None):
    client = MagicMock()
    client.get = AsyncMock(return_value=get_response or _typed("Epic"))
    client.post = AsyncMock(return_value=post_response or _created())
    client.put = AsyncMock(return_value=put_response or _saved())
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class EpicLinkTests(unittest.TestCase):
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

    def test_preview_makes_no_write(self):
        self._configure()
        client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            created = asyncio.run(create_issue(
                "KAN", "Hello", parent_key="kan-5", session_id="s-create",
            ))
            linked = asyncio.run(set_parent("kan-2", "KAN-5", session_id="s-link"))
        self.assertEqual(created["status"], "confirmation_required")
        self.assertEqual(created["preview"]["parent_key"], "KAN-5")
        self.assertEqual(linked["status"], "confirmation_required")
        self.assertEqual(linked["preview"], {"issue_key": "KAN-2", "epic_key": "KAN-5"})
        client.post.assert_not_called()
        client.put.assert_not_called()
        self.assertNotIn(self.token, json.dumps(created) + json.dumps(linked))

    def test_confirm_writes_once(self):
        self._configure()
        asyncio.run(create_issue("KAN", "Hello", parent_key="KAN-5", session_id="s-create"))
        poster = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=poster):
            created = asyncio.run(resolve_create("s-create", "yes"))
            again = asyncio.run(resolve_create("s-create", "yes"))
        self.assertEqual(created["status"], "created")
        self.assertIsNone(again)
        self.assertEqual(poster.post.await_count, 1)
        fields = poster.post.await_args.kwargs["json"]["fields"]
        self.assertEqual(fields["parent"], {"key": "KAN-5"})
        poster.put.assert_not_called()

        client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            asyncio.run(set_parent("KAN-2", "KAN-5", session_id="s-link"))
            linked = asyncio.run(resolve_create("s-link", "yes"))
            again = asyncio.run(resolve_create("s-link", "yes"))
        self.assertEqual(linked, {"status": "linked", "issue_key": "KAN-2", "epic_key": "KAN-5"})
        self.assertIsNone(again)
        self.assertEqual(client.put.await_count, 1)
        self.assertTrue(client.put.await_args.args[0].endswith("/rest/api/3/issue/KAN-2"))
        self.assertEqual(client.put.await_args.kwargs["json"], {"fields": {"parent": {"key": "KAN-5"}}})
        self.assertNotIn(self.token, json.dumps(linked))

    def test_non_epic_parent_rejected(self):
        self._configure()
        client = _client(get_response=_typed("Story"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(set_parent("KAN-2", "KAN-4", session_id="s-story"))
        self.assertEqual(result, {"status": "error", "message": "parent is not an Epic"})
        client.put.assert_not_called()
        client.post.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_bad_key_rejected(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            bad_parent = asyncio.run(create_issue("KAN", "Hello", parent_key="KAN-4 OR 1=1"))
            bad_issue = asyncio.run(set_parent("nope", "KAN-5"))
            bad_epic = asyncio.run(set_parent("KAN-2", "KAN-4 OR 1=1"))
        self.assertEqual(bad_parent["status"], "error")
        self.assertEqual(bad_issue["status"], "error")
        self.assertEqual(bad_epic["status"], "error")
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})


if __name__ == "__main__":
    unittest.main()
