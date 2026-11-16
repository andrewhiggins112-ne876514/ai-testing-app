"""Empty-lab home status + starter template (KAN-135 / FR-UI-1 / FR-UI-6 / FR-PLAN-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.starter import create_starter_plan, lab_home_status  # noqa: E402
from plans.store import get_plan, list_plans, update_case  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanStarterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_empty_home_offers_checklist(self):
        home = lab_home_status()
        self.assertEqual(home["status"], "ok")
        self.assertTrue(home["empty"])
        self.assertEqual(home["plan_count"], 0)
        ids = [item["id"] for item in home["checklist"]]
        self.assertEqual(
            ids,
            ["check_connection", "draft_from_story", "start_template"],
        )

    def test_starter_creates_editable_cases_and_clears_empty(self):
        created = create_starter_plan()
        self.assertEqual(created["status"], "ok", created)
        self.assertFalse(created.get("jira_write"))
        plan = created["plan"]
        self.assertIsNotNone(plan)
        cases = plan["suite"]["cases"]
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(c.get("enabled", True) for c in cases))
        self.assertTrue(all(c.get("source", {}).get("kind") == "manual-draft" for c in cases))

        first = cases[0]
        updated = update_case(
            plan["id"],
            first["id"],
            name="Renamed starter case",
            note="Edited after template",
            enabled=False,
        )
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(updated["case"]["name"], "Renamed starter case")
        self.assertEqual(updated["case"]["note"], "Edited after template")
        self.assertFalse(updated["case"]["enabled"])

        reloaded = get_plan(plan["id"])
        self.assertEqual(reloaded["status"], "ok")
        renamed = [
            c for c in reloaded["plan"]["suite"]["cases"] if c["id"] == first["id"]
        ][0]
        self.assertEqual(renamed["name"], "Renamed starter case")
        self.assertFalse(renamed["enabled"])

        home = lab_home_status()
        self.assertFalse(home["empty"])
        self.assertEqual(home["plan_count"], 1)
        self.assertEqual(home["checklist"], [])
        self.assertEqual(list_plans()["count"], 1)

    def test_official_secret_isolation_for_empty_state(self):
        create_starter_plan(level="OFFICIAL")
        off = lab_home_status("OFFICIAL")
        sec = lab_home_status("SECRET")
        self.assertFalse(off["empty"])
        self.assertTrue(sec["empty"])
        self.assertEqual(len(sec["checklist"]), 3)


if __name__ == "__main__":
    unittest.main()
