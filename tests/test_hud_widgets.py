"""KAN-107 — agent-home HUD widgets + latest report summary."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reports.exporter import latest_summary  # noqa: E402


class HudWidgetsShellTests(unittest.TestCase):
    def test_desktop_shell_has_hud_panels_and_toggles(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn('id="hud-security"', html)
        self.assertIn('id="hud-reports"', html)
        self.assertIn('id="hud-security-level"', html)
        self.assertIn('id="hud-reports-body"', html)
        self.assertIn('id="hud-security-toggle"', html)
        self.assertIn('id="hud-reports-toggle"', html)
        self.assertIn('data-widget="hud-security"', html)
        self.assertIn('data-widget="hud-reports"', html)
        self.assertIn("desktop-hud-widgets-v1", js)
        self.assertIn("/api/reports/latest-summary", js)
        self.assertIn("desktop-shell-layout-v1", js)

    def test_main_exposes_latest_summary_route(self):
        main_src = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('/api/reports/latest-summary', main_src)
        self.assertIn("latest_report_summary", main_src)


class LatestSummaryTests(unittest.TestCase):
    def test_empty_dir_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"AI_TESTING_REPORTS": tmp}):
                self.assertEqual(latest_summary(), {"available": False})

    def test_reads_newest_summary_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            older = {
                "timestamp": "2026-01-01T00:00:00",
                "sections": {
                    "summary": {
                        "tests_passed": 1,
                        "stories_covered": 1,
                        "pass_rate_percent": 10.0,
                    }
                },
            }
            newer = {
                "timestamp": "2026-11-16T10:00:00",
                "sections": {
                    "summary": {
                        "tests_passed": 12,
                        "stories_covered": 3,
                        "pass_rate_percent": 94.0,
                        "progress": {
                            "tests_passed": 12,
                            "stories_covered": 3,
                            "pass_rate_percent": 94.0,
                        },
                    }
                },
            }
            old_path = folder / "20260101-000000.json"
            new_path = folder / "20261116-100000.json"
            old_path.write_text(json.dumps(older), encoding="utf-8")
            new_path.write_text(json.dumps(newer), encoding="utf-8")
            os.utime(old_path, (1_700_000_000, 1_700_000_000))
            os.utime(new_path, (1_800_000_000, 1_800_000_000))
            with mock.patch.dict(os.environ, {"AI_TESTING_REPORTS": tmp}):
                payload = latest_summary()
            self.assertTrue(payload["available"])
            self.assertEqual(payload["tests_passed"], 12)
            self.assertEqual(payload["stories_covered"], 3)
            self.assertEqual(payload["pass_rate_percent"], 94.0)
            self.assertEqual(payload["timestamp"], "2026-11-16T10:00:00")

    def test_corrupt_json_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "broken.json").write_text("{not-json", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AI_TESTING_REPORTS": tmp}):
                self.assertEqual(latest_summary(), {"available": False})


if __name__ == "__main__":
    unittest.main()
