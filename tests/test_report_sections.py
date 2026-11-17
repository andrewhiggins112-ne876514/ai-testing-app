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
            {
                "summary": True,
                "stories": True,
                "bugs": True,
                "evidence": True,
                "known_issues": True,
            },
        )
        result = {
            "status": "pass",
            "title": "Demo",
            "screenshot": "C:/shot.png",
            "steps": [{"action": "goto", "status": "pass"}],
            "jira_keys": ["KAN-51"],
        }
        sections = build_sections(result, "cover KAN-51", default_sections())
        self.assertEqual(
            set(sections), {"summary", "stories", "bugs", "evidence", "known_issues"}
        )
        text = render_markdown(sections)
        self.assertIn("## Summary", text)
        self.assertIn("Overall: pass", text)
        self.assertIn("| goto | pass |", text)
        self.assertIn("## Stories", text)
        self.assertIn("- KAN-51", text)
        self.assertIn("## Bugs", text)
        self.assertIn("## Evidence", text)
        self.assertIn("Screenshot: C:/shot.png", text)
        self.assertIn("## Known issues", text)

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
            {
                "summary": True,
                "stories": False,
                "bugs": False,
                "evidence": False,
                "known_issues": False,
            }
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
        self.assertNotIn("## Known issues", text)
        self.assertNotIn("KAN-99", text)
        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        self.assertEqual(set(payload["sections"]), {"summary"})
        self.assertNotIn("stories", payload["sections"])
        self.assertNotIn("bugs", payload["sections"])
        self.assertNotIn("evidence", payload["sections"])
        self.assertNotIn("known_issues", payload["sections"])

    def test_saved_settings_drive_export(self):
        from reports.sections import save_report_sections

        save_report_sections(
            {
                "summary": False,
                "stories": True,
                "bugs": True,
                "evidence": False,
                "known_issues": False,
            }
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

    def test_richer_metrics_stories_covered_and_bugs_by_story_area(self):
        """FR-REP-1: story coverage + bugs raised per story/area in enabled sections."""
        result = {
            "status": "fail",
            "title": "Coverage report",
            "functional_area": "reporting",
            "jira_keys": ["KAN-67"],
            "steps": [
                {"action": "goto", "status": "pass"},
                {
                    "action": "expect_text",
                    "status": "fail",
                    "classification": "product_bug",
                    "error": "missing metrics",
                    "story_key": "KAN-67",
                },
            ],
            "bugs": [
                {
                    "key": "KAN-101",
                    "summary": "Export omits story counts",
                    "story_key": "KAN-67",
                    "area": "reporting",
                },
                {
                    "key": "KAN-102",
                    "summary": "Login flash",
                    "relates_to": "KAN-12",
                    "functional_area": "auth",
                },
            ],
        }
        sections = build_sections(result, "cover KAN-67 and KAN-12", default_sections())
        summary = sections["summary"]
        self.assertEqual(summary["tests_passed"], 1)
        self.assertEqual(summary["tests_failed"], 1)
        self.assertEqual(summary["pass_rate_percent"], 50.0)
        self.assertEqual(summary["stories_covered"], 2)
        self.assertEqual(summary["bugs_raised"], 3)
        self.assertEqual(summary["progress"]["stories_covered"], 2)

        stories = sections["stories"]
        self.assertEqual(stories["covered_count"], 2)
        self.assertEqual(set(stories["covered"]), {"KAN-67", "KAN-12"})
        self.assertTrue(stories["by_key"]["KAN-67"]["covered"])
        self.assertEqual(stories["by_key"]["KAN-67"]["bugs_raised"], 2)

        bugs = sections["bugs"]
        self.assertEqual(bugs["raised_count"], 3)
        self.assertEqual(set(bugs["keys"]), {"KAN-101", "KAN-102"})
        self.assertEqual(bugs["counts_by_story"]["KAN-67"], 2)
        self.assertEqual(bugs["counts_by_story"]["KAN-12"], 1)
        self.assertEqual(bugs["counts_by_area"]["reporting"], 2)
        self.assertEqual(bugs["counts_by_area"]["auth"], 1)

        text = render_markdown(sections)
        self.assertIn("Stories covered: 2", text)
        self.assertIn("Bugs raised: 3", text)
        self.assertIn("Covered: 2", text)
        self.assertIn("By story:", text)
        self.assertIn("- KAN-67: 2", text)
        self.assertIn("By area:", text)
        self.assertIn("- reporting: 2", text)
        self.assertIn("Bug keys: KAN-101, KAN-102", text)

    def test_richer_metrics_respect_section_toggles(self):
        result = {
            "status": "fail",
            "jira_keys": ["KAN-67"],
            "bugs": [{"key": "KAN-101", "story_key": "KAN-67", "summary": "x"}],
            "steps": [],
        }
        flags = normalize_sections(
            {
                "summary": True,
                "stories": False,
                "bugs": False,
                "evidence": False,
                "known_issues": False,
            }
        )
        sections = build_sections(result, "KAN-67", flags)
        self.assertEqual(set(sections), {"summary"})
        self.assertEqual(sections["summary"]["stories_covered"], 1)
        self.assertEqual(sections["summary"]["bugs_raised"], 1)
        text = render_markdown(sections)
        self.assertIn("## Summary", text)
        self.assertNotIn("## Stories", text)
        self.assertNotIn("## Bugs", text)
        self.assertNotIn("By story:", text)

    def test_evidence_includes_notes_when_section_on(self):
        """KAN-155 / B7: notes appear in export when evidence section is on."""
        result = {
            "status": "fail",
            "title": "With notes",
            "screenshot": "C:/shot.png",
            "case_note": "Explorer saw blank panel",
            "tester_note": "Reproduced on second click",
            "case_name": "Panel open",
            "run_id": "r1",
            "steps": [],
        }
        on = build_sections(
            result,
            "",
            normalize_sections(
                {
                    "evidence": True,
                    "summary": False,
                    "stories": False,
                    "bugs": False,
                    "known_issues": False,
                }
            ),
        )
        self.assertEqual(set(on), {"evidence"})
        notes = on["evidence"].get("notes") or []
        texts = [n.get("text") for n in notes if isinstance(n, dict)]
        self.assertIn("Explorer saw blank panel", texts)
        self.assertIn("Reproduced on second click", texts)
        md = render_markdown(on)
        self.assertIn("## Evidence", md)
        self.assertIn("Notes:", md)
        self.assertIn("Explorer saw blank panel", md)
        off = build_sections(
            result,
            "",
            normalize_sections(
                {
                    "evidence": False,
                    "summary": True,
                    "stories": False,
                    "bugs": False,
                    "known_issues": False,
                }
            ),
        )
        self.assertNotIn("evidence", off)
        self.assertNotIn("Explorer saw blank panel", render_markdown(off))

    def test_known_issues_section_include_exclude(self):
        result = {
            "status": "fail",
            "title": "With known",
            "known_issues": [
                {
                    "case_name": "Login flash",
                    "result": "fail",
                    "note": "Tracked elsewhere",
                    "jira_key": "KAN-200",
                }
            ],
            "steps": [],
        }
        on = build_sections(
            result,
            "",
            normalize_sections({"known_issues": True, "summary": False, "stories": False, "bugs": False, "evidence": False}),
        )
        self.assertEqual(set(on), {"known_issues"})
        self.assertEqual(on["known_issues"]["count"], 1)
        md = render_markdown(on)
        self.assertIn("## Known issues", md)
        self.assertIn("KAN-200", md)
        self.assertIn("labelled known", md)
        off = build_sections(
            result,
            "",
            normalize_sections({"known_issues": False, "summary": True, "stories": False, "bugs": False, "evidence": False}),
        )
        self.assertNotIn("known_issues", off)
        self.assertNotIn("## Known issues", render_markdown(off))


if __name__ == "__main__":
    unittest.main()
