"""load_settings accepts settings.json saved with a UTF-8 BOM."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from settings.store import load_settings  # noqa: E402


class SettingsBomTests(unittest.TestCase):
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

    def test_loads_utf8_bom_file(self):
        payload = {"security_level": "SECRET", "jira_url": "https://jira.example.com"}
        self.path.write_bytes(b"\xef\xbb\xbf" + json.dumps(payload).encode("utf-8"))
        data = load_settings()
        self.assertEqual(data["security_level"], "SECRET")
        self.assertEqual(data["jira_url"], "https://jira.example.com")
        self.assertEqual(data["jira_api_token"], "")


if __name__ == "__main__":
    unittest.main()
