"""OFFICIAL / SECRET credential and browser-profile isolation (KAN-15 / FR-SEC-1)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.store import (  # noqa: E402
    browser_profile_dir,
    credentials_path,
    get_security_level,
    load_settings,
    security_status,
    set_security_level,
    update_setting,
    write_settings,
)


class SecurityIsolationTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_migrate_flat_credentials_into_official(self):
        self.path.write_text(
            json.dumps(
                {
                    "security_level": "OFFICIAL",
                    "jira_url": "https://jira.example.com",
                    "jira_api_token": "tok-official",
                    "orb_style": "mystic",
                }
            ),
            encoding="utf-8",
        )
        data = load_settings()
        self.assertEqual(data["security_level"], "OFFICIAL")
        self.assertEqual(data["jira_url"], "https://jira.example.com")
        self.assertEqual(data["jira_api_token"], "tok-official")
        self.assertEqual(data["orb_style"], "mystic")
        shared = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("jira_api_token", shared)
        self.assertNotIn("jira_url", shared)
        creds = json.loads(credentials_path("OFFICIAL").read_text(encoding="utf-8"))
        self.assertEqual(creds["jira_api_token"], "tok-official")

    def test_switch_requires_confirm_and_isolates_creds(self):
        update_setting("jira_url", "https://official.example.com", confirm=True)
        update_setting("jira_api_token", "tok-official", confirm=True)
        propose = set_security_level("SECRET", confirm=False)
        self.assertEqual(propose["status"], "confirmation_required")
        self.assertEqual(get_security_level(), "OFFICIAL")
        self.assertEqual(load_settings()["jira_api_token"], "tok-official")

        applied = set_security_level("SECRET", confirm=True)
        self.assertEqual(applied["status"], "updated")
        self.assertEqual(get_security_level(), "SECRET")
        self.assertEqual(load_settings().get("jira_api_token") or "", "")
        update_setting("jira_api_token", "tok-secret", confirm=True)
        self.assertEqual(load_settings()["jira_api_token"], "tok-secret")

        set_security_level("OFFICIAL", confirm=True)
        self.assertEqual(load_settings()["jira_api_token"], "tok-official")
        self.assertEqual(load_settings()["jira_url"], "https://official.example.com")

    def test_browser_profiles_differ_by_level(self):
        official = browser_profile_dir("OFFICIAL")
        secret = browser_profile_dir("SECRET")
        self.assertNotEqual(official, secret)
        self.assertTrue(str(official).endswith(os.path.join("browser_profiles", "OFFICIAL")))
        self.assertTrue(str(secret).endswith(os.path.join("browser_profiles", "SECRET")))

    def test_security_status_never_echoes_tokens(self):
        update_setting("jira_email", "agent@example.com", confirm=True)
        update_setting("jira_api_token", "super-secret-token-value", confirm=True)
        status = security_status()
        blob = json.dumps(status)
        self.assertNotIn("super-secret-token-value", blob)
        self.assertNotIn("agent@example.com", blob)
        self.assertTrue(status["jira_credentials_configured"])
        self.assertIn("browser_profiles", status["browser_profile"])

    def test_write_settings_splits_scoped_keys(self):
        data = load_settings()
        data["jira_url"] = "https://split.example.com"
        data["jira_api_token"] = "tok-split"
        data["orb_style"] = "aether"
        write_settings(data)
        shared = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(shared["orb_style"], "aether")
        self.assertNotIn("jira_api_token", shared)
        reloaded = load_settings()
        self.assertEqual(reloaded["jira_url"], "https://split.example.com")
        self.assertEqual(reloaded["jira_api_token"], "tok-split")


if __name__ == "__main__":
    unittest.main()
