"""Reports tab reads the newest markdown file. Uses a temp directory."""
import importlib.util
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
        text, image = gradio_app.latest_report()
        self.assertEqual(text, "No reports yet")
        self.assertIsNone(image)

    def test_newest_report_and_existing_screenshot(self):
        older = self.folder / "old.md"
        newer = self.folder / "new.md"
        shot = self.folder / "shot.png"
        missing = self.folder / "missing.png"
        older.write_text("# Old\n\nScreenshot: C:/missing.png\n", encoding="utf-8")
        newer.write_text(f"# New\n\nScreenshot: {missing}\n", encoding="utf-8")
        os.utime(older, (1_000_000, 1_000_000))
        os.utime(newer, (2_000_000, 2_000_000))
        text, image = gradio_app.latest_report()
        self.assertIn("# New", text)
        self.assertNotIn("# Old", text)
        self.assertIsNone(image)
        shot.write_bytes(b"\x89PNG\r\n")
        newer.write_text(f"# New\n\nScreenshot: {shot}\n", encoding="utf-8")
        os.utime(newer, (3_000_000, 3_000_000))
        text, image = gradio_app.latest_report()
        self.assertIn("# New", text)
        self.assertEqual(image, str(shot))


if __name__ == "__main__":
    unittest.main()
