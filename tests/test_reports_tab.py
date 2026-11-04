"""Reports tab reads the newest markdown file and its matching JSON."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("gradio_reports_under_test", ROOT / "ui" / "gradio_app.py")
gradio_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gradio_app)


class ReportsTabTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_REPORTS")
        self.folder = Path(tempfile.mkdtemp())
        os.environ["AI_TESTING_REPORTS"] = str(self.folder)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_REPORTS", None)
        else:
            os.environ["AI_TESTING_REPORTS"] = self._old

    def test_empty_folder_shows_no_reports(self):
        text, image, payload = gradio_app.latest_report()
        self.assertEqual(text, "No reports yet")
        self.assertIsNone(image)
        self.assertEqual(payload, "No JSON found")

    def test_newest_report_and_existing_screenshot(self):
        older = self.folder / "old.md"
        newer = self.folder / "new.md"
        shot = self.folder / "shot.png"
        missing = self.folder / "missing.png"
        older.write_text("# Old\n\nScreenshot: C:/missing.png\n", encoding="utf-8")
        newer.write_text(f"# New\n\nScreenshot: {missing}\n", encoding="utf-8")
        os.utime(older, (1_000_000, 1_000_000))
        os.utime(newer, (2_000_000, 2_000_000))
        text, image, payload = gradio_app.latest_report()
        self.assertIn("# New", text)
        self.assertNotIn("# Old", text)
        self.assertIsNone(image)
        self.assertEqual(payload, "No JSON found")
        shot.write_bytes(b"\x89PNG\r\n")
        newer.write_text(f"# New\n\nScreenshot: {shot}\n", encoding="utf-8")
        os.utime(newer, (3_000_000, 3_000_000))
        text, image, payload = gradio_app.latest_report()
        self.assertIn("# New", text)
        self.assertEqual(image, str(shot))
        self.assertEqual(payload, "No JSON found")

    def test_matching_json_for_newest_report(self):
        older = self.folder / "old.md"
        newer = self.folder / "new.md"
        older.write_text("# Old\n", encoding="utf-8")
        newer.write_text("# New\n", encoding="utf-8")
        (self.folder / "old.json").write_text(json.dumps({"request": "old"}), encoding="utf-8")
        (self.folder / "new.json").write_text(
            json.dumps({"request": "new", "status": "pass"}), encoding="utf-8"
        )
        os.utime(older, (1_000_000, 1_000_000))
        os.utime(self.folder / "old.json", (4_000_000, 4_000_000))
        os.utime(newer, (2_000_000, 2_000_000))
        text, image, payload = gradio_app.latest_report()
        self.assertIn("# New", text)
        self.assertIsNone(image)
        self.assertEqual(payload, {"request": "new", "status": "pass"})


if __name__ == "__main__":
    unittest.main()
