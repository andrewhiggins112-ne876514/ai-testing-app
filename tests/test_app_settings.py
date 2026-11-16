"""Desktop App Settings API (KAN-73 / KAN-77 / FR-UI-1 / FR-LEARN-2/3)."""
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
    save_app_settings,
    save_jira_url,
    set_security_level,
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

    def test_save_target_fields_level_scoped(self):
        bad = save_app_settings(
            target_url="ftp://bad",
            target_app_path=r"C:\Apps\Demo.exe",
            api_endpoint="amqp://broker.local/vhost",
        )
        self.assertEqual(bad["status"], "error")
        self.assertIn("target url", bad["message"].lower())

        bad_msg = save_app_settings(api_endpoint="ftp://not-messaging")
        self.assertEqual(bad_msg["status"], "error")
        self.assertIn("messaging", bad_msg["message"].lower())

        ok = save_app_settings(
            jira_url="https://jira.example.com",
            target_url="https://app.example.com/login",
            target_app_path=r"C:\Apps\Demo.exe",
            api_endpoint="amqps://broker.example.com/vhost",
        )
        self.assertEqual(ok["status"], "updated")
        data = load_settings()
        self.assertEqual(data["target_url"], "https://app.example.com/login")
        self.assertEqual(data["target_app_path"], r"C:\Apps\Demo.exe")
        self.assertEqual(data["api_endpoint"], "amqps://broker.example.com/vhost")
        status = app_settings_status()
        self.assertEqual(status["target_url"], "https://app.example.com/login")
        self.assertEqual(status["api_endpoint"], "amqps://broker.example.com/vhost")
        self.assertIn("Target URL:", status["summary"])

        set_security_level("SECRET", confirm=True)
        secret = load_settings()
        self.assertEqual(secret.get("target_url") or "", "")
        self.assertEqual(secret.get("target_app_path") or "", "")
        self.assertEqual(secret.get("api_endpoint") or "", "")

        set_security_level("OFFICIAL", confirm=True)
        back = load_settings()
        self.assertEqual(back["target_url"], "https://app.example.com/login")
        self.assertEqual(back["api_endpoint"], "amqps://broker.example.com/vhost")

    def test_api_get_post_app_settings(self):
        from main import app

        client = TestClient(app)
        get_res = client.get("/api/app-settings")
        self.assertEqual(get_res.status_code, 200)
        body = get_res.json()
        self.assertIn("settings_path", body)
        self.assertIn("jira_credentials_status", body)
        self.assertIn("target_url", body)
        self.assertIn("api_endpoint", body)
        self.assertNotIn("jira_api_token", body)
        self.assertNotIn("jira_email", body)

        post_res = client.post(
            "/api/app-settings",
            json={
                "jira_url": "https://api.example.atlassian.net",
                "target_url": "https://aut.example.com",
                "target_app_path": r"D:\bin\aut.exe",
                "api_endpoint": "wss://events.example.com/bus",
            },
        )
        self.assertEqual(post_res.status_code, 200)
        saved = post_res.json()
        self.assertEqual(saved["status"], "updated")
        self.assertEqual(saved["jira_url"], "https://api.example.atlassian.net")
        self.assertEqual(saved["target_url"], "https://aut.example.com")
        self.assertEqual(saved["target_app_path"], r"D:\bin\aut.exe")
        self.assertEqual(saved["api_endpoint"], "wss://events.example.com/bus")
        loaded = load_settings()
        self.assertEqual(loaded["jira_url"], "https://api.example.atlassian.net")
        self.assertEqual(loaded["target_url"], "https://aut.example.com")
        self.assertEqual(loaded["api_endpoint"], "wss://events.example.com/bus")

        again = client.get("/api/app-settings").json()
        self.assertEqual(again["jira_url"], "https://api.example.atlassian.net")
        self.assertEqual(again["target_url"], "https://aut.example.com")
        self.assertEqual(again["api_endpoint"], "wss://events.example.com/bus")

    def test_partial_post_does_not_clear_other_fields(self):
        from main import app

        client = TestClient(app)
        client.post(
            "/api/app-settings",
            json={
                "jira_url": "https://keep.example.atlassian.net",
                "target_url": "https://keep.example.com",
            },
        )
        partial = client.post(
            "/api/app-settings",
            json={"playwright_mode": "headless"},
        )
        self.assertEqual(partial.status_code, 200)
        body = partial.json()
        self.assertEqual(body.get("status"), "updated")
        self.assertEqual(body.get("playwright_mode"), "headless")
        self.assertEqual(body.get("jira_url"), "https://keep.example.atlassian.net")
        self.assertEqual(body.get("target_url"), "https://keep.example.com")
        loaded = load_settings()
        self.assertEqual(loaded["jira_url"], "https://keep.example.atlassian.net")
        self.assertEqual(loaded["target_url"], "https://keep.example.com")
        self.assertTrue(loaded.get("playwright_headless"))


if __name__ == "__main__":
    unittest.main()
