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
        self.assertEqual(gradio_app.save_settings("SECRET", "https://jira.example.com"), "Saved.")
        self.assertEqual(gradio_app.current_settings(), ("SECRET", "https://jira.example.com"))
        saved = load_settings()
        self.assertEqual(saved["security_level"], "SECRET")
        self.assertEqual(saved["jira_url"], "https://jira.example.com")
        self.assertEqual(gradio_app.save_settings("PUBLIC", "https://other.example.com"), "Invalid security level.")
        reloaded = load_settings()
        self.assertEqual(reloaded["security_level"], "SECRET")
        self.assertEqual(reloaded["jira_url"], "https://jira.example.com")


if __name__ == "__main__":
    unittest.main()
