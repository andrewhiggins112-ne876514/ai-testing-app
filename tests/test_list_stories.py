"""Mocked HTTP checks for list_stories. No network and no real credentials."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.jira_plugin import list_stories  # noqa: E402


def _response(status_code, payload=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.raise_for_status.return_value = None
    response.text = ""
    return response


def _client(response):
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(side_effect=AssertionError("POST not allowed"))
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class ListStoriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = {key: os.environ.get(key) for key in ("AI_TESTING_SETTINGS", "JIRA_API_TOKEN", "JIRA_EMAIL")}
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ.pop("JIRA_API_TOKEN", None)
        os.environ.pop("JIRA_EMAIL", None)
        self.token = "x" * 20

    def tearDown(self):
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_unconfigured(self):
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(list_stories("TEST"))
        self.assertEqual(result["status"], "unconfigured")
        self.assertTrue(result.get("message"))
        ctor.assert_not_called()

        self.settings.write_text(json.dumps({"jira_url": "https://jira.example.com"}), encoding="utf-8")
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(list_stories("TEST"))
        self.assertEqual(result["status"], "unconfigured")
        self.assertNotIn(self.token, json.dumps(result))
        ctor.assert_not_called()

    def test_bad_project_key_skips_http(self):
        os.environ["JIRA_API_TOKEN"] = self.token
        self.settings.write_text(json.dumps({"jira_base_url": "https://jira.example.com"}), encoding="utf-8")
        for key in ("bad key", "ABC_DEF", "ABCDEFGHIJK", ""):
            with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
                result = asyncio.run(list_stories(key))
            self.assertEqual(result["status"], "error")
            ctor.assert_not_called()

    def test_happy_path(self):
        os.environ["JIRA_API_TOKEN"] = self.token
        os.environ["JIRA_EMAIL"] = "qa@example.com"
        self.settings.write_text(json.dumps({
            "jira_base_url": "https://jira.example.com",
            "jira_url": "https://wrong.example.com",
            "jira_api_token": "y" * 20,
            "jira_email": "store@example.com",
        }), encoding="utf-8")
        payload = {"issues": [{
            "id": "10001",
            "key": "TEST-1",
            "fields": {"summary": "First story", "status": {"name": "To Do"}, "description": "hidden"},
        }]}
        client = _client(_response(200, payload))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(list_stories("TEST", max=3))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stories"], [{"key": "TEST-1", "summary": "First story", "status": "To Do"}])
        self.assertEqual(list(result["stories"][0].keys()), ["key", "summary", "status"])
        endpoint = client.get.await_args.args[0]
        self.assertTrue(endpoint.startswith("https://jira.example.com/rest/api/3/search/jql"))
        self.assertEqual(client.get.await_args.kwargs["params"]["maxResults"], 3)
        self.assertEqual(client.get.await_args.kwargs["auth"], ("qa@example.com", self.token))
        client.post.assert_not_called()
        client.put.assert_not_called()
        self.assertNotIn(self.token, json.dumps(result))

    def test_auth_error(self):
        os.environ["JIRA_API_TOKEN"] = self.token
        os.environ["JIRA_EMAIL"] = "qa@example.com"
        self.settings.write_text(json.dumps({"jira_url": "https://jira.example.com"}), encoding="utf-8")
        response = _response(401)
        response.json.side_effect = AssertionError("must not read the body")
        response.text = self.token
        response.raise_for_status.side_effect = AssertionError("must not raise on 401")
        client = _client(response)
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(list_stories("test"))
        self.assertEqual(result["status"], "unauthorized")
        self.assertTrue(result.get("message"))
        self.assertNotIn(self.token, json.dumps(result))
        client.post.assert_not_called()
        client.put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
