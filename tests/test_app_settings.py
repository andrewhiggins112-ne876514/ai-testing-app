"""Desktop App Settings API (KAN-73 / FR-UI-1 / FR-SET-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.store import (  # noqa: E402
    app_settings_status,
    load_settings,
    save_jira_url,
    write_settings,
)


class AppSettingsTests(unittest.TestCase):
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

    def test_status_hides_secrets_and_shows_store(self):
        data = load_settings()
        data["jira_url"] = "https://jira.example.com"
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        write_settings(data)
        status = app_settings_status()
        self.assertEqual(status["jira_url"], "https://jira.example.com")
        self.assertEqual(status["jira_credentials_status"], "configured")
        self.assertIn("Local store:", status["summary"])
        self.assertIn(str(self.path), status["settings_path"])
        self.assertNotIn("super-secret-token-value", status["summary"])
        self.assertNotIn("agent@example.com", status["summary"])
        self.assertNotIn("super-secret-token-value", str(status))
        self.assertNotIn("agent@example.com", str(status))

    def test_save_jira_url_persists_and_rejects_bad_scheme(self):
        bad = save_jira_url("ftp://not-http.example")
        self.assertEqual(bad["status"], "error")
        self.assertIn("http", bad["message"].lower())
        self.assertEqual(load_settings().get("jira_url") or "", "")

        ok = save_jira_url("https://desk.example.atlassian.net")
        self.assertEqual(ok["status"], "updated")
        self.assertEqual(ok["jira_url"], "https://desk.example.atlassian.net")
        self.assertEqual(
            load_settings()["jira_url"], "https://desk.example.atlassian.net"
        )

        reloaded = app_settings_status()
        self.assertEqual(reloaded["jira_url"], "https://desk.example.atlassian.net")

    def test_api_get_post_app_settings(self):
        from main import app

        client = TestClient(app)
        get_res = client.get("/api/app-settings")
        self.assertEqual(get_res.status_code, 200)
        body = get_res.json()
        self.assertIn("settings_path", body)
        self.assertIn("jira_credentials_status", body)
        self.assertNotIn("jira_api_token", body)
        self.assertNotIn("jira_email", body)

        post_res = client.post(
            "/api/app-settings",
            json={"jira_url": "https://api.example.atlassian.net"},
        )
        self.assertEqual(post_res.status_code, 200)
        saved = post_res.json()
        self.assertEqual(saved["status"], "updated")
        self.assertEqual(saved["jira_url"], "https://api.example.atlassian.net")
        self.assertEqual(
            load_settings()["jira_url"], "https://api.example.atlassian.net"
        )

        again = client.get("/api/app-settings").json()
        self.assertEqual(again["jira_url"], "https://api.example.atlassian.net")


if __name__ == "__main__":
    unittest.main()
