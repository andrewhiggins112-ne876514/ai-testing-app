"""D4 credential status without revealing secrets (KAN-185 / KAN-186)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.credential_status import (  # noqa: E402
    CLEARABLE_SECRETS,
    clear_secret,
    credential_field_status,
    credentials_audit_path,
    set_target_secret,
)
from settings.credential_status import test_connection as probe_test_connection  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class CredentialStatusTests(unittest.TestCase):
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

    def test_status_shows_set_missing_never_values(self):
        data = load_settings()
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        data["target_secret"] = "aut-password-xyz"
        write_settings(data)

        status = credential_field_status()
        self.assertEqual(status["jira_email"], "set")
        self.assertEqual(status["jira_api_token"], "set")
        self.assertEqual(status["target_secret"], "set")
        blob = str(status)
        self.assertNotIn("agent@example.com", blob)
        self.assertNotIn("super-secret-token-value", blob)
        self.assertNotIn("aut-password-xyz", blob)
        keys = {row["key"] for row in status["fields"]}
        self.assertEqual(keys, set(CLEARABLE_SECRETS))
        for row in status["fields"]:
            self.assertIn(row["state"], ("set", "missing"))

        empty = load_settings()
        empty["jira_email"] = ""
        empty["jira_api_token"] = ""
        empty["target_secret"] = ""
        write_settings(empty)
        missing = credential_field_status()
        self.assertEqual(missing["jira_email"], "missing")
        self.assertEqual(missing["jira_api_token"], "missing")
        self.assertEqual(missing["target_secret"], "missing")

    @patch("settings.connection_health.check_jira_auth")
    def test_connection_uses_stored_secret_and_human_auth_error(self, probe):
        data = load_settings()
        data["jira_url"] = "https://jira.example.com"
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        write_settings(data)

        probe.return_value = {
            "id": "jira",
            "label": "Jira",
            "state": "up",
            "up": True,
            "message": "Jira reachable.",
        }
        ok = probe_test_connection()
        self.assertTrue(ok["success"])
        self.assertEqual(ok["result"], "success")
        self.assertTrue(ok["used_stored_secret"])
        self.assertNotIn("super-secret-token-value", str(ok))

        probe.return_value = {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": "Jira auth failed (check email/token in local store).",
        }
        bad = probe_test_connection()
        self.assertFalse(bad["success"])
        self.assertEqual(bad["result"], "auth_error")
        self.assertIn("auth", bad["message"].lower())
        self.assertNotIn("super-secret-token-value", str(bad))
        self.assertNotIn("agent@example.com", str(bad))

    def test_clear_secret_requires_confirm_and_audit_has_no_old_value(self):
        data = load_settings()
        data["jira_api_token"] = "super-secret-token-value"
        data["target_secret"] = "aut-password-xyz"
        write_settings(data)

        proposed = clear_secret("jira_api_token", confirm=False)
        self.assertEqual(proposed["status"], "confirmation_required")
        self.assertEqual(load_settings().get("jira_api_token"), "super-secret-token-value")
        self.assertNotIn("super-secret-token-value", str(proposed))

        cleared = clear_secret("jira_api_token", confirm=True)
        self.assertEqual(cleared["status"], "cleared")
        self.assertEqual(load_settings().get("jira_api_token") or "", "")
        self.assertFalse(cleared.get("audit_has_old_value"))
        self.assertNotIn("super-secret-token-value", str(cleared))

        audit_path = credentials_audit_path()
        self.assertTrue(audit_path.exists())
        lines = [
            ln for ln in audit_path.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
        self.assertTrue(lines)
        last = json.loads(lines[-1])
        self.assertEqual(last["action"], "clear_secret")
        self.assertEqual(last["key"], "jira_api_token")
        self.assertTrue(last["was_set"])
        self.assertNotIn("old_value", last)
        self.assertNotIn("value", last)
        self.assertNotIn("super-secret-token-value", json.dumps(last))

        set_target_secret("aut-password-xyz", confirm=True)
        self.assertEqual(credential_field_status()["target_secret"], "set")
        clear_secret("target_secret", confirm=True)
        self.assertEqual(load_settings().get("target_secret") or "", "")
        self.assertEqual(credential_field_status()["target_secret"], "missing")

        bad_key = clear_secret("not_a_secret", confirm=True)
        self.assertEqual(bad_key["status"], "error")

    def test_api_endpoints_hide_secrets(self):
        from main import app

        data = load_settings()
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        data["target_secret"] = "aut-password-xyz"
        write_settings(data)

        client = TestClient(app)
        status = client.get("/api/credentials/status")
        self.assertEqual(status.status_code, 200)
        body = status.json()
        self.assertEqual(body["jira_email"], "set")
        self.assertEqual(body["jira_api_token"], "set")
        self.assertEqual(body["target_secret"], "set")
        self.assertNotIn("super-secret-token-value", str(body))
        self.assertNotIn("agent@example.com", str(body))
        self.assertNotIn("aut-password-xyz", str(body))

        app_settings = client.get("/api/app-settings").json()
        self.assertIn("credential_fields", app_settings)
        self.assertEqual(app_settings["jira_email_status"], "set")
        self.assertNotIn("jira_api_token", app_settings)
        self.assertNotIn("target_secret", app_settings)
        self.assertNotIn("super-secret-token-value", str(app_settings))

        with patch("settings.connection_health.check_jira_auth") as probe:
            probe.return_value = {
                "id": "jira",
                "label": "Jira",
                "state": "down",
                "up": False,
                "message": "Jira auth failed (check email/token in local store).",
            }
            test_res = client.post("/api/credentials/test-connection")
        self.assertEqual(test_res.status_code, 200)
        test_body = test_res.json()
        self.assertEqual(test_body["result"], "auth_error")
        self.assertNotIn("super-secret-token-value", str(test_body))

        propose = client.post(
            "/api/credentials/clear",
            json={"key": "target_secret", "confirm": False},
        ).json()
        self.assertEqual(propose["status"], "confirmation_required")
        self.assertEqual(load_settings().get("target_secret"), "aut-password-xyz")

        done = client.post(
            "/api/credentials/clear",
            json={"key": "target_secret", "confirm": True},
        ).json()
        self.assertEqual(done["status"], "cleared")
        self.assertEqual(load_settings().get("target_secret") or "", "")
        self.assertNotIn("aut-password-xyz", str(done))

        saved = client.post(
            "/api/credentials/target-secret",
            json={"value": "new-aut-secret", "confirm": True},
        ).json()
        self.assertEqual(saved["status"], "updated")
        self.assertEqual(saved["target_secret"], "set")
        self.assertNotIn("new-aut-secret", str(saved))
        self.assertEqual(load_settings().get("target_secret"), "new-aut-secret")

    def test_desktop_ui_has_credential_controls_desk70(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk70", html)
        self.assertIn("desk70", desk)
        self.assertIn("cred-status-list", html)
        self.assertIn("cred-test-btn", html)
        self.assertIn("cred-clear-confirm-btn", html)
        self.assertIn("set-target-secret", html)
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("/api/credentials/test-connection", js)
        self.assertIn("/api/credentials/clear", js)


if __name__ == "__main__":
    unittest.main()
