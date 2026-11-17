"""KAN-159 / C2 — export chosen run + heal review filtered by run_id."""
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

from plans.run_report import export_plan_run, list_exportable_runs  # noqa: E402
from plans.store import add_run, create_plan  # noqa: E402
from plugins.heal_policy import (  # noqa: E402
    HealProposal,
    evaluate_and_log,
    heal_run_context,
    list_pending_heals,
)


class PlanRunReportTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(
            os.environ, {"LOCALAPPDATA": self._tmpdir.name}, clear=False
        )
        self.env.start()
        self._settings = mock.patch(
            "settings.store.get_security_level", return_value="OFFICIAL"
        )
        self._settings.start()

    def tearDown(self):
        self._settings.stop()
        self.env.stop()
        self._tmpdir.cleanup()

    def _seed_plan_run(self):
        created = create_plan(name="Export plan", intent="c2", level="OFFICIAL")
        self.assertEqual(created.get("status"), "ok")
        plan = created["plan"]
        pid = plan["id"]
        from plans.store import add_case

        added = add_case(
            pid,
            name="Login case",
            jira_key="KAN-159",
            note="case note",
            level="OFFICIAL",
        )
        case = added["case"]
        cid = case["id"]
        recorded = add_run(
            pid,
            cid,
            result="fail",
            duration_ms=120,
            failure_class="product_bug",
            evidence=[str(Path(self._tmpdir.name) / "shot.png")],
            note="locator miss",
            run_id="r-export-1",
            level="OFFICIAL",
        )
        self.assertEqual(recorded.get("status"), "ok")
        return pid, cid, "r-export-1"

    def test_list_and_export_chosen_run_respects_sections(self):
        pid, cid, rid = self._seed_plan_run()
        listed = list_exportable_runs(level="OFFICIAL")
        self.assertEqual(listed["status"], "ok")
        self.assertGreaterEqual(listed["count"], 1)
        self.assertTrue(any(r["run_id"] == rid for r in listed["runs"]))

        out = export_plan_run(
            pid,
            cid,
            rid,
            sections={
                "summary": True,
                "stories": True,
                "bugs": False,
                "evidence": True,
                "known_issues": False,
            },
            level="OFFICIAL",
            session_id="test-export",
        )
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["run_id"], rid)
        self.assertFalse(out["sections"]["bugs"])
        self.assertTrue(out["sections"]["evidence"])
        result = out["result"]
        self.assertEqual(result.get("run_id"), rid)
        self.assertIn("KAN-159", result.get("stories") or result.get("jira_keys") or [])

        reports = Path(self._tmpdir.name) / "ai_testing_app" / "reports"
        json_files = list(reports.glob("*.json"))
        self.assertTrue(json_files)
        payload = json.loads(json_files[-1].read_text(encoding="utf-8"))
        sections = payload.get("sections") or {}
        self.assertIn("summary", sections)
        self.assertIn("stories", sections)
        self.assertIn("evidence", sections)
        self.assertNotIn("bugs", sections)
        self.assertNotIn("known_issues", sections)

    def test_heal_stamped_with_run_id_and_filter(self):
        with heal_run_context(run_id="r-heal-9", plan_id="p1", case_id="c1"):
            decision = evaluate_and_log(
                HealProposal(
                    kind="locator",
                    original="#submit",
                    proposed="Submit",
                    classification="test_defect",
                    evidence={"original": "#submit", "proposed": "Submit"},
                )
            )
        self.assertTrue(decision.allowed)
        from plugins.heal_policy import heal_log_path

        path = heal_log_path()
        all_pending = list_pending_heals(path=path)
        self.assertEqual(all_pending["count"], 1)
        self.assertEqual(all_pending["pending"][0]["run_id"], "r-heal-9")
        filtered = list_pending_heals(path=path, run_id="r-heal-9")
        self.assertEqual(filtered["count"], 1)
        other = list_pending_heals(path=path, run_id="r-other")
        self.assertEqual(other["count"], 0)

    def test_desktop_markup_has_run_export_and_heal_filter(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('id="rpt-run-select"', html)
        self.assertIn('id="rpt-export-run"', html)
        self.assertIn('id="heal-run-filter"', html)
        self.assertIn("exportChosenRun", js)
        self.assertIn("/api/plans/exportable-runs", js)
        self.assertIn("exportable-runs", main)
        self.assertIn("/runs/{run_id}/export", main)
        self.assertIn("desk41", desk)
        self.assertIn('id="app-section-reports"', html)
        self.assertIn('id="app-section-heal"', html)


if __name__ == "__main__":
    unittest.main()
