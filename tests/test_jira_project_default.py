"""KAN-93 / FR-LEARN-4: jira_project default for list_stories and App Settings."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.jira_plugin import jira_action, list_stories  # noqa: E402
from settings.store import (  # noqa: E402
    app_settings_status,
    load_settings,
    save_app_settings,
    write_settings,
)


class JiraProjectDefaultTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings(load_settings())

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_list_stories_uses_settings_jira_project(self):
        data = load_settings()
        data["jira_url"] = "https://example.atlassian.net"
        data["jira_email"] = "a@b.com"
        data["jira_api_token"] = "tok"
        data["jira_project"] = "KAN"
        write_settings(data)

        mock_result = {
            "status": "ok",
            "stories": [{"key": "KAN-1", "summary": "x", "status": "To Do", "type": "Story"}],
        }
        with patch(
            "plugins.jira_plugin._list_search",
            new=AsyncMock(return_value=mock_result),
        ) as mocked:
            result = asyncio.run(list_stories())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stories"][0]["key"], "KAN-1")
        mocked.assert_awaited_once()
        args = mocked.await_args.args
        self.assertEqual(args[3], "KAN")

    def test_list_stories_empty_settings_asks_for_project(self):
        result = asyncio.run(list_stories())
        self.assertEqual(result["status"], "error")
        self.assertIn("jira_project", result["message"])
        self.assertIn("required", result["message"].lower())

    def test_list_stories_explicit_project_overrides_settings(self):
        data = load_settings()
        data["jira_url"] = "https://example.atlassian.net"
        data["jira_email"] = "a@b.com"
        data["jira_api_token"] = "tok"
        data["jira_project"] = "KAN"
        write_settings(data)

        mock_result = {"status": "ok", "stories": []}
        with patch(
            "plugins.jira_plugin._list_search",
            new=AsyncMock(return_value=mock_result),
        ) as mocked:
            result = asyncio.run(list_stories(project="ABC"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(mocked.await_args.args[3], "ABC")

    def test_jira_action_defaults_to_settings_project(self):
        data = load_settings()
        data["jira_url"] = "https://example.atlassian.net"
        data["jira_email"] = "a@b.com"
        data["jira_api_token"] = "tok"
        data["jira_project"] = "KAN"
        write_settings(data)

        with patch(
            "plugins.jira_plugin._search",
            new=AsyncMock(return_value={"stories": [], "project": "KAN"}),
        ) as mocked:
            result = asyncio.run(jira_action("list_stories"))
        self.assertEqual(result.get("project"), "KAN")
        self.assertEqual(mocked.await_args.args[3], "KAN")

    def test_jira_action_empty_asks_for_project(self):
        result = asyncio.run(jira_action("list_stories"))
        self.assertIn("error", result)
        self.assertIn("jira_project", result["error"])

    def test_save_and_status_expose_jira_project(self):
        bad = save_app_settings(jira_project="bad key")
        self.assertEqual(bad["status"], "error")
        self.assertIn("project", bad["message"].lower())

        ok = save_app_settings(jira_project="kan")
        self.assertEqual(ok["status"], "updated")
        self.assertEqual(ok["jira_project"], "KAN")
        self.assertEqual(load_settings()["jira_project"], "KAN")
        status = app_settings_status()
        self.assertEqual(status["jira_project"], "KAN")
        self.assertIn("Jira project: KAN", status["summary"])

        cleared = save_app_settings(jira_project="")
        self.assertEqual(cleared["status"], "updated")
        self.assertEqual(cleared["jira_project"], "")

    def test_api_get_post_jira_project(self):
        from main import app

        client = TestClient(app)
        get_res = client.get("/api/app-settings")
        self.assertEqual(get_res.status_code, 200)
        self.assertIn("jira_project", get_res.json())

        post_res = client.post(
            "/api/app-settings",
            json={"jira_project": "KAN"},
        )
        self.assertEqual(post_res.status_code, 200)
        body = post_res.json()
        self.assertEqual(body["status"], "updated")
        self.assertEqual(body["jira_project"], "KAN")
        self.assertEqual(load_settings()["jira_project"], "KAN")

        partial = client.post(
            "/api/app-settings",
            json={"playwright_mode": "headed"},
        )
        self.assertEqual(partial.json().get("jira_project"), "KAN")

    def test_desktop_exposes_jira_project_field(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('id="set-jira-project"', html)
        self.assertIn("jira_project", js)
        self.assertIn("desk31", html)
        self.assertIn("desk31", desk)


if __name__ == "__main__":
    unittest.main()
