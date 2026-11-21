"""Acceptance text drift (KAN-165 / C5 / FR-PLAN-3 / FR-JIRA-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.drift import (  # noqa: E402
    check_acceptance_drift,
    keep_acceptance_drafts,
    refresh_acceptance_drafts,
)
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    get_plan,
    upsert_jira_snapshot,
)
from settings.store import write_settings  # noqa: E402


def _issue(key: str, summary: str, ac: str, description: str = "") -> dict:
    return {
        "status": "ok",
        "key": key,
        "summary": summary,
        "acceptance_criteria": ac,
        "description": description,
        "has_acceptance_criteria": bool(ac),
    }


class AcceptanceDriftTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_check_marks_stale_and_shows_old_vs_new(self):
        created = create_plan(
            "Drift plan",
            intent="from KAN-1",
            sources={"jira_keys": ["KAN-1"], "documents": []},
        )
        plan_id = created["plan"]["id"]
        upsert_jira_snapshot(
            plan_id,
            "KAN-1",
            summary="Old title",
            acceptance_criteria="- Old AC bullet",
            stale=False,
        )
        add_case(
            plan_id,
            "Old AC bullet",
            jira_key="KAN-1",
            source_kind="jira",
            source_ref="Old AC bullet",
        )

        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(
                return_value=_issue("KAN-1", "New title", "- New AC bullet")
            ),
        ):
            out = await check_acceptance_drift(plan_id)

        self.assertEqual(out["status"], "ok")
        self.assertTrue(out["stale"])
        self.assertEqual(out["stale_count"], 1)
        self.assertFalse(out["jira_write"])
        item = out["stale_items"][0]
        self.assertEqual(item["key"], "KAN-1")
        self.assertEqual(item["old_summary"], "Old title")
        self.assertEqual(item["new_summary"], "New title")
        self.assertIn("Old AC", item["old_acceptance_criteria"])
        self.assertIn("New AC", item["new_acceptance_criteria"])
        loaded = get_plan(plan_id)
        self.assertTrue(loaded["plan"]["jira_snapshots"]["KAN-1"]["stale"])

    async def test_keep_clears_stale_without_changing_cases(self):
        created = create_plan(
            "Keep plan",
            sources={"jira_keys": ["KAN-2"], "documents": []},
        )
        plan_id = created["plan"]["id"]
        upsert_jira_snapshot(
            plan_id,
            "KAN-2",
            summary="A",
            acceptance_criteria="- one",
            stale=True,
        )
        added = add_case(
            plan_id,
            "one",
            jira_key="KAN-2",
            source_kind="jira",
            source_ref="one",
        )
        case_id = added["case"]["id"]

        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(return_value=_issue("KAN-2", "B", "- two")),
        ):
            out = await keep_acceptance_drafts(plan_id)

        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["action"], "keep")
        self.assertFalse(out["cases_changed"])
        plan = get_plan(plan_id)["plan"]
        snap = plan["jira_snapshots"]["KAN-2"]
        self.assertFalse(snap["stale"])
        self.assertEqual(snap["summary"], "B")
        cases = plan["suite"]["cases"]
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["id"], case_id)
        self.assertEqual(cases[0]["name"], "one")
        self.assertTrue(cases[0]["enabled"])

    async def test_refresh_disables_old_adds_new_preserves_runs(self):
        created = create_plan(
            "Refresh plan",
            sources={"jira_keys": ["KAN-3"], "documents": []},
        )
        plan_id = created["plan"]["id"]
        upsert_jira_snapshot(
            plan_id,
            "KAN-3",
            summary="S1",
            acceptance_criteria="- First bullet",
            stale=True,
        )
        added = add_case(
            plan_id,
            "First bullet",
            jira_key="KAN-3",
            source_kind="jira",
            source_ref="First bullet",
        )
        case_id = added["case"]["id"]
        add_run(plan_id, case_id, result="pass", note="kept")

        with patch(
            "plugins.jira_plugin.read_issue",
            new=AsyncMock(
                return_value=_issue(
                    "KAN-3",
                    "S2",
                    "- Second bullet\n- Third bullet",
                )
            ),
        ):
            out = await refresh_acceptance_drafts(plan_id)

        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["action"], "refresh")
        self.assertFalse(out["runs_deleted"])
        self.assertEqual(out["runs_before"], 1)
        self.assertEqual(out["runs_after"], 1)
        self.assertGreaterEqual(out["added_case_count"], 1)
        plan = get_plan(plan_id)["plan"]
        cases = {c["id"]: c for c in plan["suite"]["cases"]}
        self.assertIn(case_id, cases)
        self.assertFalse(cases[case_id]["enabled"])
        self.assertEqual(len(cases[case_id]["runs"]), 1)
        self.assertEqual(cases[case_id]["runs"][0]["result"], "pass")
        enabled = [c for c in plan["suite"]["cases"] if c.get("enabled", True)]
        self.assertGreaterEqual(len(enabled), 1)
        self.assertFalse(plan["jira_snapshots"]["KAN-3"]["stale"])
        # No silent delete of the old case
        self.assertEqual(len(plan["suite"]["cases"]), 1 + out["added_case_count"])

    def test_desktop_ui_has_drift_controls_desk105(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk105", html)
        self.assertIn("desk105", app)
        self.assertIn("plan-drift-check-btn", html)
        self.assertIn("plan-drift-keep-btn", html)
        self.assertIn("plan-drift-refresh-btn", html)
        self.assertIn("acceptance-drift", js)
        self.assertIn("/acceptance-drift/keep", js)
        self.assertIn("/acceptance-drift/refresh", js)


if __name__ == "__main__":
    unittest.main()
