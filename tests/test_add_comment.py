"""Mocked HTTP checks for add_comment. No network and no real credentials."""
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
from plugins.jira_plugin import add_comment, resolve_create  # noqa: E402


def _response(status_code, payload):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def _client(post=None):
    client = MagicMock()
    client.get = AsyncMock(side_effect=AssertionError("GET not allowed"))
    client.post = AsyncMock(return_value=post or _response(201, {"id": "10001"}))
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class AddCommentTests(unittest.TestCase):
    def setUp(self):
        jira_plugin._PENDING.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = {
            key: os.environ.get(key)
            for key in ("AI_TESTING_SETTINGS", "JIRA_API_TOKEN", "JIRA_EMAIL", "LOCALAPPDATA")
        }
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
        client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(add_comment("kan-4", "hello there", session_id="s-preview"))
        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["preview"], {"issue_key": "KAN-4", "body": "hello there"})
        client.post.assert_not_called()
        self.assertNotIn(self.token, json.dumps(result))

    def test_confirm_posts_once(self):
        self._configure()
        client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            asyncio.run(add_comment("KAN-4", "Noted", session_id="s-yes"))
            result = asyncio.run(resolve_create("s-yes", "yes"))
            again = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertEqual(result, {"status": "commented", "issue_key": "KAN-4", "comment_id": "10001"})
        self.assertIsNone(again)
        self.assertEqual(client.post.await_count, 1)
        self.assertTrue(client.post.await_args.args[0].endswith("/rest/api/3/issue/KAN-4/comment"))
        posted = client.post.await_args.kwargs["json"]["body"]
        self.assertEqual(posted["content"][0]["content"][0]["text"], "Noted")
        self.assertNotIn(self.token, json.dumps(result))

    def test_too_long_body_rejected(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(add_comment("KAN-4", "a" * 5001, session_id="s-long"))
        self.assertEqual(result["status"], "error")
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_report_summary_included(self):
        self._configure()
        os.environ["LOCALAPPDATA"] = self.tmp.name
        root = Path(self.tmp.name) / "ai_testing_app" / "reports"
        root.mkdir(parents=True)
        shot = str(root / "shot.png")
        report = root / "run.json"
        report.write_text(json.dumps({
            "result": {
                "status": "pass",
                "screenshot": shot,
                "steps": [
                    {"action": "goto", "status": "pass"},
                    {"action": "click", "status": "fail"},
                ],
            }
        }), encoding="utf-8")
        client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            preview = asyncio.run(add_comment(
                "KAN-4", "See the run", report_path=str(report), session_id="s-report",
            ))
            result = asyncio.run(resolve_create("s-report", "yes"))
        self.assertIn("Report overall: pass", preview["preview"]["body"])
        self.assertIn("- goto: pass", preview["preview"]["body"])
        self.assertIn("- click: fail", preview["preview"]["body"])
        self.assertNotIn("shot.png", json.dumps(preview))
        posted = json.dumps(client.post.await_args.kwargs["json"])
        self.assertIn("Report overall: pass", posted)
        self.assertIn("goto", posted)
        self.assertNotIn("shot.png", posted)
        self.assertEqual(result["comment_id"], "10001")
        self.assertEqual(client.post.await_count, 1)

    def test_report_outside_local_reports_rejected(self):
        self._configure()
        os.environ["LOCALAPPDATA"] = str(Path(self.tmp.name) / "local")
        outside = Path(self.tmp.name) / "other.json"
        outside.write_text("{}", encoding="utf-8")
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(add_comment("KAN-4", "hi", report_path=str(outside), session_id="s-out"))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "report path must be inside the local reports folder")
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})


if __name__ == "__main__":
    unittest.main()
