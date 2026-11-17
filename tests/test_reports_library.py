"""KAN-247 / FR-REP-4: Reports library API + UI placement of section toggles."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402
from reports.exporter import get_saved_report, list_saved_reports  # noqa: E402


class ReportsLibraryTests(unittest.TestCase):
    def setUp(self):
        self._old_reports = os.environ.get("AI_TESTING_REPORTS")
        self._old_settings = os.environ.get("AI_TESTING_SETTINGS")
        self.reports = Path(tempfile.mkdtemp())
        self.settings_dir = Path(tempfile.mkdtemp())
        os.environ["AI_TESTING_REPORTS"] = str(self.reports)
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings_dir / "settings.json")
        self.client = TestClient(app)

    def tearDown(self):
        if self._old_reports is None:
            os.environ.pop("AI_TESTING_REPORTS", None)
        else:
            os.environ["AI_TESTING_REPORTS"] = self._old_reports
        if self._old_settings is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old_settings

    def test_empty_library(self):
        listed = list_saved_reports()
        self.assertEqual(listed["count"], 0)
        self.assertIn("No saved reports", listed["empty_hint"])
        res = self.client.get("/api/reports")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 0)

    def test_list_and_get_saved_report(self):
        older = self.reports / "old.md"
        newer = self.reports / "new.md"
        older.write_text("# Old\n", encoding="utf-8")
        newer.write_text("# New\n\nScreenshot: C:/missing.png\n", encoding="utf-8")
        (self.reports / "new.json").write_text(
            json.dumps({"timestamp": "2026-11-17T12:00:00", "request": "demo", "result": {}}),
            encoding="utf-8",
        )
        os.utime(older, (1_000_000, 1_000_000))
        os.utime(newer, (2_000_000, 2_000_000))
        listed = list_saved_reports()
        self.assertEqual(listed["count"], 2)
        self.assertEqual(listed["reports"][0]["id"], "new")
        detail = get_saved_report("new")
        self.assertTrue(detail["found"])
        self.assertIn("# New", detail["markdown"])
        self.assertFalse(detail["has_screenshot"])
        res = self.client.get("/api/reports/new")
        self.assertEqual(res.status_code, 200)
        self.assertIn("# New", res.json()["markdown"])
        missing = self.client.get("/api/reports/does-not-exist")
        self.assertEqual(missing.status_code, 404)

    def test_screenshot_endpoint(self):
        shot = self.reports / "shot.png"
        shot.write_bytes(b"\x89PNG\r\n")
        (self.reports / "with-shot.md").write_text(
            f"# Shot\n\nScreenshot: {shot}\n", encoding="utf-8"
        )
        (self.reports / "with-shot.json").write_text(
            json.dumps({"result": {"screenshot": str(shot)}}), encoding="utf-8"
        )
        detail = self.client.get("/api/reports/with-shot").json()
        self.assertTrue(detail["has_screenshot"])
        img = self.client.get("/api/reports/with-shot/screenshot")
        self.assertEqual(img.status_code, 200)
        self.assertTrue(img.content.startswith(b"\x89PNG"))

    def test_desktop_reports_is_library_settings_holds_toggles(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        settings_block = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        reports_block = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        self.assertIn('id="report-settings-heading"', settings_block)
        self.assertIn('id="rpt-summary"', settings_block)
        self.assertIn('id="rpt-save"', settings_block)
        self.assertNotIn('id="rpt-summary"', reports_block)
        self.assertIn('id="rpt-library-select"', reports_block)
        self.assertIn('id="rpt-open-settings"', reports_block)
        self.assertIn("Report library", reports_block)
        self.assertIn("openReportSettings", js)
        self.assertIn("/api/reports", js)
        self.assertIn("desk74", desk)
        self.assertIn("desk74", html)
        self.assertIn('id="settings-cat-report"', settings_block)
        self.assertIn("setSettingsCategory", js)

    def test_gradio_sections_live_under_settings_not_reports_lead(self):
        src = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        settings_idx = src.find('elem_id="gradio-area-settings"')
        reports_idx = src.find('elem_id="gradio-area-reports"')
        self.assertGreater(settings_idx, 0)
        self.assertGreater(reports_idx, settings_idx)
        settings_chunk = src[settings_idx:reports_idx]
        reports_chunk = src[reports_idx : reports_idx + 2500]
        self.assertIn("Report Settings", settings_chunk)
        self.assertIn("Save sections", settings_chunk)
        self.assertIn('label="Summary (status, counts, steps)"', settings_chunk)
        self.assertNotIn('label="Summary (status, counts, steps)"', reports_chunk)
        self.assertIn("Library", reports_chunk)
        self.assertIn("FR-REP-4", reports_chunk)


if __name__ == "__main__":
    unittest.main()
