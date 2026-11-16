"""Edit plan before run (KAN-133 / FR-PLAN-1 / FR-PLAN-2)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.store import (  # noqa: E402
    add_case,
    cases_for_run,
    create_plan,
    get_plan,
    reorder_cases,
    update_case,
)
from settings.store import write_settings  # noqa: E402


class PlanEditTests(unittest.TestCase):
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

    def test_rename_note_disable_reorder_persist(self):
        created = create_plan("Editable", intent="before run")
        plan_id = created["plan"]["id"]
        a = add_case(plan_id, "A", jira_key="KAN-133")["case"]
        b = add_case(plan_id, "B", jira_key="KAN-133")["case"]
        c = add_case(plan_id, "C", jira_key="KAN-133")["case"]

        updated = update_case(
            plan_id,
            b["id"],
            name="Renamed B",
            note="Check tomorrow",
            enabled=False,
        )
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(updated["case"]["name"], "Renamed B")
        self.assertEqual(updated["case"]["note"], "Check tomorrow")
        self.assertFalse(updated["case"]["enabled"])

        reordered = reorder_cases(plan_id, [c["id"], a["id"], b["id"]])
        self.assertEqual(reordered["status"], "ok", reordered)
        names = [case["name"] for case in reordered["plan"]["suite"]["cases"]]
        self.assertEqual(names, ["C", "A", "Renamed B"])

        runnable = cases_for_run(plan_id)
        self.assertEqual(runnable["status"], "ok", runnable)
        self.assertEqual(runnable["count"], 2)
        self.assertIn(b["id"], runnable["skipped_case_ids"])
        runnable_names = [case["name"] for case in runnable["cases"]]
        self.assertEqual(runnable_names, ["C", "A"])

        # Closing and reopening shows the same plan (reload from disk).
        reloaded = get_plan(plan_id)
        self.assertEqual(reloaded["status"], "ok")
        disk_names = [case["name"] for case in reloaded["plan"]["suite"]["cases"]]
        self.assertEqual(disk_names, ["C", "A", "Renamed B"])
        disabled = [
            case for case in reloaded["plan"]["suite"]["cases"] if case["id"] == b["id"]
        ][0]
        self.assertFalse(disabled["enabled"])
        self.assertEqual(disabled["note"], "Check tomorrow")

        # Edits stay under local plans dir JSON.
        path = Path(self.tmp.name) / "plans" / "OFFICIAL" / f"{plan_id}.json"
        # plans live under app_data_dir which is settings parent
        from settings.store import app_data_dir

        path = app_data_dir() / "plans" / "OFFICIAL" / f"{plan_id}.json"
        self.assertTrue(path.is_file())
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["suite"]["cases"][0]["name"], "C")


if __name__ == "__main__":
    unittest.main()
