"""Traceability matrix (KAN-167 / C6 / FR-REP-1 + FR-PLAN-4)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.store import add_case, add_run, create_plan, set_known_issue_link  # noqa: E402
from plans.traceability import (  # noqa: E402
    plan_traceability_matrix,
    traceability_from_plan,
)
from reports.sections import build_sections, default_sections, render_markdown  # noqa: E402
from settings.store import write_settings  # noqa: E402


class TraceabilityMatrixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings(
            {
                "security_level": "OFFICIAL",
                "orb_style": "mystic",
                "jira_project": "KAN",
            }
        )

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_no_runs_are_not_loaded_never_pass(self):
        plan = {
            "id": "p1",
            "sources": {"jira_keys": ["KAN-1", "KAN-2"], "documents": []},
            "suite": {
                "cases": [
                    {
                        "id": "c1",
                        "name": "Login",
                        "jira_key": "KAN-1",
                        "enabled": True,
                        "archived": False,
                        "runs": [],
                    }
                ]
            },
        }
        out = traceability_from_plan(plan)
        self.assertEqual(out["status"], "ok")
        by_key = {r["story_key"]: r for r in out["rows"]}
        self.assertEqual(by_key["KAN-1"]["last_result"], "not_loaded")
        self.assertEqual(by_key["KAN-1"]["case_count"], 1)
        self.assertEqual(by_key["KAN-1"]["primary_case_id"], "c1")
        self.assertEqual(by_key["KAN-2"]["last_result"], "not_loaded")
        self.assertEqual(by_key["KAN-2"]["case_count"], 0)
        self.assertIsNone(by_key["KAN-2"]["primary_case_id"])
        for row in out["rows"]:
            self.assertNotEqual(row["last_result"], "pass")

    def test_pass_only_after_real_run_and_known_bug_keys(self):
        created = create_plan(
            name="Trace plan",
            intent="c6",
            sources={"jira_keys": ["KAN-10"], "documents": []},
        )
        plan_id = created["plan"]["id"]
        added = add_case(plan_id, name="AC 1", jira_key="KAN-10")
        case_id = added["case"]["id"]
        add_run(plan_id, case_id, result="pass", note="ok")
        set_known_issue_link(
            plan_id,
            case_id,
            note="flaky locator",
            jira_key="KAN-99",
        )
        out = plan_traceability_matrix(plan_id)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["jira_write"])
        row = out["rows"][0]
        self.assertEqual(row["story_key"], "KAN-10")
        self.assertEqual(row["last_result"], "pass")
        self.assertEqual(row["case_count"], 1)
        self.assertTrue(row["known_issue"])
        self.assertIn("KAN-99", row["linked_bug_keys"])
        self.assertNotIn("KAN-10", row["linked_bug_keys"])
        self.assertEqual(row["primary_case_id"], case_id)

    def test_filter_by_story_or_bug_key(self):
        plan = {
            "id": "p2",
            "sources": {"jira_keys": ["KAN-1", "KAN-2"], "documents": []},
            "suite": {
                "cases": [
                    {
                        "id": "c1",
                        "jira_key": "KAN-1",
                        "name": "One",
                        "enabled": True,
                        "archived": False,
                        "known_issue": {
                            "note": "known",
                            "jira_key": "KAN-50",
                            "linked": True,
                        },
                        "runs": [{"id": "r1", "result": "fail"}],
                    },
                    {
                        "id": "c2",
                        "jira_key": "KAN-2",
                        "name": "Two",
                        "enabled": True,
                        "archived": False,
                        "runs": [{"id": "r2", "result": "fail"}],
                    },
                ]
            },
        }
        filtered = traceability_from_plan(plan, filter_text="KAN-50")
        self.assertEqual([r["story_key"] for r in filtered["rows"]], ["KAN-1"])

    def test_export_section_includes_matrix_when_enabled(self):
        rows = [
            {
                "story_key": "KAN-1",
                "case_count": 1,
                "last_result": "not_loaded",
                "linked_bug_keys": [],
                "known_issue": False,
            }
        ]
        flags = default_sections()
        self.assertIn("traceability", flags)
        self.assertTrue(flags["traceability"])
        sections = build_sections(
            {"status": "fail", "steps": [], "traceability": rows},
            "",
            flags,
        )
        self.assertIn("traceability", sections)
        self.assertEqual(sections["traceability"]["count"], 1)
        md = render_markdown(sections)
        self.assertIn("## Traceability", md)
        self.assertIn("not_loaded", md)
        self.assertIn("KAN-1", md)

        off = dict(flags)
        off["traceability"] = False
        sections_off = build_sections(
            {"status": "fail", "steps": [], "traceability": rows},
            "",
            off,
        )
        self.assertNotIn("traceability", sections_off)
        self.assertNotIn("## Traceability", render_markdown(sections_off))

    def test_desktop_ui_has_traceability_controls_desk113(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk113", html)
        self.assertIn("desk113", app)
        self.assertIn("plan-trace-matrix", html)
        self.assertIn("plan-trace-btn", html)
        self.assertIn("rpt-traceability", html)
        self.assertIn("refreshTraceabilityMatrix", js)
        self.assertIn("openTraceabilityRow", js)
        self.assertIn("/traceability", js)
        self.assertIn("plan-trace-row", js)


if __name__ == "__main__":
    unittest.main()
