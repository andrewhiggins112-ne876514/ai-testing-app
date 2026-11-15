"""Settings tab save/load. Uses a temp settings file, not the real one."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("gradio_app_under_test", ROOT / "ui" / "gradio_app.py")
gradio_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gradio_app)

from settings.store import load_settings  # noqa: E402


class SettingsTabTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.path = Path(tempfile.gettempdir()) / "ai_testing_app_settings_tab_test.json"
        if self.path.exists():
            self.path.unlink()
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old

    def test_save_reload_and_reject_invalid_level(self):
        status, summary = gradio_app.save_settings("SECRET", "https://jira.example.com")
        self.assertEqual(status, "Saved.")
        self.assertIn("Local store:", summary)
        self.assertEqual(gradio_app.current_settings(), ("SECRET", "https://jira.example.com"))
        saved = load_settings()
        self.assertEqual(saved["security_level"], "SECRET")
        self.assertEqual(saved["jira_url"], "https://jira.example.com")
        status, _ = gradio_app.save_settings("PUBLIC", "https://other.example.com")
        self.assertEqual(status, "Invalid security level.")
        reloaded = load_settings()
        self.assertEqual(reloaded["security_level"], "SECRET")
        self.assertEqual(reloaded["jira_url"], "https://jira.example.com")

    def test_store_summary_hides_secrets(self):
        from settings.store import write_settings

        data = load_settings()
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        write_settings(data)
        summary = gradio_app.settings_store_summary()
        self.assertIn("Local store:", summary)
        self.assertIn("configured", summary.lower())
        self.assertNotIn("super-secret-token-value", summary)
        self.assertNotIn("agent@example.com", summary)


if __name__ == "__main__":
    unittest.main()
