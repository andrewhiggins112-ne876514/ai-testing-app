"""Report export writes outside the repo. Uses a temp directory."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reports.exporter import export_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class ReportExportTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_REPORTS")
        self.folder = Path(tempfile.mkdtemp())
        os.environ["AI_TESTING_REPORTS"] = str(self.folder)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_REPORTS", None)
        else:
            os.environ["AI_TESTING_REPORTS"] = self._old

    def test_writes_json_and_markdown_outside_repo(self):
        result = {
            "status": "pass",
            "title": "Example Domain",
            "screenshot": "C:/shot.png",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
        }
        self.assertEqual(export_run(result, "go to example.com", "sess-1"), result)
        export_run({"status": "fail", "title": "Two", "steps": []}, "second", "sess-1")
        json_files = sorted(self.folder.glob("*.json"))
        md_files = sorted(self.folder.glob("*.md"))
        self.assertEqual(len(json_files), 2)
        self.assertEqual(len(md_files), 2)
        self.assertEqual({path.stem for path in json_files}, {path.stem for path in md_files})
        saved_path = next(
            path for path in json_files
            if json.loads(path.read_text(encoding="utf-8"))["request"] == "go to example.com"
        )
        saved = json.loads(saved_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["session_id"], "sess-1")
        self.assertEqual(saved["result"]["status"], "pass")
        self.assertIn("timestamp", saved)
        text = saved_path.with_suffix(".md").read_text(encoding="utf-8")
        self.assertIn("# Example Domain", text)
        self.assertIn("Overall: pass", text)
        self.assertIn("| goto | pass |", text)
        self.assertIn("Screenshot: C:/shot.png", text)
        for path in json_files + md_files:
            self.assertNotEqual(ROOT.resolve(), path.resolve())
            self.assertNotIn(ROOT.resolve(), path.resolve().parents)

    def test_refuses_to_write_inside_repo(self):
        target = ROOT / "not_reports"
        os.environ["AI_TESTING_REPORTS"] = str(target)
        result = {"status": "fail", "title": None, "steps": []}
        self.assertEqual(export_run(result, "nope", "sess"), result)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
