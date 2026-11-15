"""FR-REP-2: report section toggles shape Markdown/JSON export."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reports.exporter import export_run  # noqa: E402
from reports.sections import (  # noqa: E402
    build_sections,
    default_sections,
    normalize_sections,
    render_markdown,
)


class ReportSectionsTests(unittest.TestCase):
    def setUp(self):
        self._old_reports = os.environ.get("AI_TESTING_REPORTS")
        self._old_settings = os.environ.get("AI_TESTING_SETTINGS")
        self.reports = Path(tempfile.mkdtemp())
        self.settings_dir = Path(tempfile.mkdtemp())
        os.environ["AI_TESTING_REPORTS"] = str(self.reports)
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings_dir / "settings.json")

    def tearDown(self):
        if self._old_reports is None:
            os.environ.pop("AI_TESTING_REPORTS", None)
        else:
            os.environ["AI_TESTING_REPORTS"] = self._old_reports
        if self._old_settings is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old_settings

    def test_defaults_include_all_core_sections(self):
        self.assertEqual(
            default_sections(),
            {"summary": True, "stories": True, "bugs": True, "evidence": True},
        )
        result = {
            "status": "pass",
            "title": "Demo",
            "screenshot": "C:/shot.png",
            "steps": [{"action": "goto", "status": "pass"}],
            "jira_keys": ["KAN-51"],
        }
        sections = build_sections(result, "cover KAN-51", default_sections())
        self.assertEqual(set(sections), {"summary", "stories", "bugs", "evidence"})
        text = render_markdown(sections)
        self.assertIn("## Summary", text)
        self.assertIn("Overall: pass", text)
        self.assertIn("| goto | pass |", text)
        self.assertIn("## Stories", text)
        self.assertIn("- KAN-51", text)
        self.assertIn("## Bugs", text)
        self.assertIn("## Evidence", text)
        self.assertIn("Screenshot: C:/shot.png", text)

    def test_omitted_sections_absent_from_markdown_and_json(self):
        result = {
            "status": "fail",
            "title": "Broken",
            "screenshot": "C:/x.png",
            "steps": [
                {
                    "action": "expect_text",
                    "status": "fail",
                    "classification": "product_bug",
                    "error": "missing",
                }
            ],
        }
        flags = normalize_sections(
            {"summary": True, "stories": False, "bugs": False, "evidence": False}
        )
        export_run(result, "run for KAN-99", "sess", sections=flags)
        md_files = list(self.reports.glob("*.md"))
        json_files = list(self.reports.glob("*.json"))
        self.assertEqual(len(md_files), 1)
        text = md_files[0].read_text(encoding="utf-8")
        self.assertIn("## Summary", text)
        self.assertNotIn("## Stories", text)
        self.assertNotIn("## Bugs", text)
        self.assertNotIn("## Evidence", text)
        self.assertNotIn("KAN-99", text)
        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        self.assertEqual(set(payload["sections"]), {"summary"})
        self.assertNotIn("stories", payload["sections"])
        self.assertNotIn("bugs", payload["sections"])
        self.assertNotIn("evidence", payload["sections"])

    def test_saved_settings_drive_export(self):
        from reports.sections import save_report_sections

        save_report_sections(
            {"summary": False, "stories": True, "bugs": True, "evidence": False}
        )
        result = {
            "status": "pass",
            "title": "Stories only",
            "screenshot": "C:/s.png",
            "steps": [],
            "bugs": [{"summary": "login broken"}],
        }
        export_run(result, "track KAN-12", "sess")
        text = (list(self.reports.glob("*.md"))[0]).read_text(encoding="utf-8")
        self.assertNotIn("## Summary", text)
        self.assertIn("## Stories", text)
        self.assertIn("- KAN-12", text)
        self.assertIn("## Bugs", text)
        self.assertIn("login broken", text)
        self.assertNotIn("## Evidence", text)
        payload = json.loads(list(self.reports.glob("*.json"))[0].read_text(encoding="utf-8"))
        self.assertEqual(set(payload["sections"]), {"stories", "bugs"})


if __name__ == "__main__":
    unittest.main()
