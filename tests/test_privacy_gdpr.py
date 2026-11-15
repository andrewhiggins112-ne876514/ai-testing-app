"""GDPR local deletion + telemetry defaults (KAN-69 / FR-SEC-2)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.privacy import (  # noqa: E402
    delete_local_data,
    privacy_status,
    telemetry_enabled,
)
from settings.store import app_data_dir, load_settings, write_settings  # noqa: E402


class PrivacyGdprTests(unittest.TestCase):
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

    def _seed_artifacts(self):
        root = app_data_dir()
        reports = root / "reports"
        shots = root / "screenshots"
        sessions = root / "sessions"
        profiles = root / "browser_profiles" / "OFFICIAL"
        reports.mkdir(parents=True, exist_ok=True)
        shots.mkdir(parents=True, exist_ok=True)
        sessions.mkdir(parents=True, exist_ok=True)
        profiles.mkdir(parents=True, exist_ok=True)
        (reports / "run.json").write_text("{}", encoding="utf-8")
        (shots / "fail.png").write_bytes(b"png")
        (sessions / "chat.json").write_text("[]", encoding="utf-8")
        (root / "heal_audit.jsonl").write_text("{}\n", encoding="utf-8")
        (profiles / "cookie.txt").write_text("x", encoding="utf-8")
        return reports, shots, sessions, root / "heal_audit.jsonl", profiles

    def test_telemetry_off_by_default(self):
        self.assertFalse(telemetry_enabled())
        status = privacy_status()
        self.assertFalse(status["telemetry_enabled"])
        self.assertTrue(status["consent_required_for_extracted_data"])
        settings = load_settings()
        self.assertFalse(settings.get("telemetry_enabled", True))

    def test_delete_requires_confirm_and_preserves_data(self):
        reports, shots, sessions, audit, profiles = self._seed_artifacts()
        propose = delete_local_data(
            ["reports", "screenshots", "heal_audit", "sessions"],
            confirm=False,
        )
        self.assertEqual(propose["status"], "confirmation_required")
        self.assertTrue(reports.joinpath("run.json").is_file())
        self.assertTrue(shots.joinpath("fail.png").is_file())
        self.assertTrue(sessions.joinpath("chat.json").is_file())
        self.assertTrue(audit.is_file())
        self.assertTrue(profiles.joinpath("cookie.txt").is_file())

    def test_delete_with_confirm_removes_artifacts_keeps_settings(self):
        reports, shots, sessions, audit, profiles = self._seed_artifacts()
        write_settings({**load_settings(), "orb_style": "mystic", "jira_url": "https://example.com"})
        result = delete_local_data(
            ["reports", "screenshots", "heal_audit", "sessions"],
            confirm=True,
        )
        self.assertEqual(result["status"], "deleted")
        self.assertFalse((reports / "run.json").exists())
        self.assertFalse((shots / "fail.png").exists())
        self.assertFalse((sessions / "chat.json").exists())
        self.assertFalse(audit.exists())
        # browser_profiles not selected — remains
        self.assertTrue(profiles.joinpath("cookie.txt").is_file())
        # settings + credentials path untouched
        self.assertTrue(self.path.is_file())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("orb_style"), "mystic")
        reloaded = load_settings()
        self.assertEqual(reloaded.get("jira_url"), "https://example.com")

    def test_browser_profiles_optional_wipe(self):
        _, _, _, _, profiles = self._seed_artifacts()
        result = delete_local_data(["browser_profiles"], confirm=True)
        self.assertEqual(result["status"], "deleted")
        self.assertFalse(profiles.joinpath("cookie.txt").exists())
        self.assertTrue((app_data_dir() / "browser_profiles").is_dir())


if __name__ == "__main__":
    unittest.main()
