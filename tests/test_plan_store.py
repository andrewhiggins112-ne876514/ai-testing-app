"""In-app plan / suite / case / run model (KAN-125 / FR-PLAN-1 / FR-PLAN-2)."""
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
    add_run,
    create_plan,
    get_plan,
    list_plans,
    plans_dir,
)
from settings.store import (  # noqa: E402
    app_data_dir,
    get_security_level,
    load_settings,
    set_security_level,
    write_settings,
)


class PlanStoreTests(unittest.TestCase):
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

    def test_create_plan_contains_suite_cases_and_runs(self):
        created = create_plan(
            "Alpha plan",
            intent="Cover login happy path",
            sources={"jira_keys": ["KAN-125"], "documents": ["spec.md"]},
        )
        self.assertEqual(created["status"], "ok", created)
        plan = created["plan"]
        self.assertEqual(plan["security_level"], "OFFICIAL")
        self.assertEqual(plan["name"], "Alpha plan")
        self.assertIn("suite", plan)
        self.assertIsInstance(plan["suite"]["cases"], list)

        added = add_case(
            plan["id"],
            "Login succeeds",
            jira_key="KAN-125",
            tags=["smoke"],
            source_kind="jira",
            source_ref="AC: user can sign in",
        )
        self.assertEqual(added["status"], "ok", added)
        case = added["case"]
        self.assertEqual(case["jira_key"], "KAN-125")
        self.assertEqual(case["source"]["kind"], "jira")

        ran = add_run(
            plan["id"],
            case["id"],
            result="fail",
            duration_ms=1234,
            failure_class="product_bug",
            evidence=["screenshots/fail.png"],
        )
        self.assertEqual(ran["status"], "ok", ran)
        self.assertEqual(ran["run"]["result"], "fail")
        self.assertEqual(ran["run"]["duration_ms"], 1234)

        loaded = get_plan(plan["id"])
        self.assertEqual(loaded["status"], "ok", loaded)
        cases = loaded["plan"]["suite"]["cases"]
        self.assertEqual(len(cases), 1)
        self.assertEqual(len(cases[0]["runs"]), 1)
        self.assertEqual(cases[0]["runs"][0]["failure_class"], "product_bug")

        listed = list_plans()
        self.assertEqual(listed["status"], "ok")
        self.assertEqual(listed["security_level"], "OFFICIAL")
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["plans"][0]["case_count"], 1)
        self.assertEqual(listed["plans"][0]["run_count"], 1)

    def test_official_and_secret_plans_are_not_listed_together(self):
        off = create_plan("Official only")
        self.assertEqual(off["status"], "ok")
        off_id = off["plan"]["id"]

        set_security_level("SECRET", confirm=True)
        self.assertEqual(get_security_level(), "SECRET")
        sec = create_plan("Secret only")
        self.assertEqual(sec["status"], "ok")
        sec_id = sec["plan"]["id"]

        secret_list = list_plans()
        self.assertEqual(secret_list["security_level"], "SECRET")
        ids = [p["id"] for p in secret_list["plans"]]
        self.assertIn(sec_id, ids)
        self.assertNotIn(off_id, ids)
        self.assertEqual(get_plan(off_id).get("status"), "error")

        set_security_level("OFFICIAL", confirm=True)
        official_list = list_plans()
        ids = [p["id"] for p in official_list["plans"]]
        self.assertIn(off_id, ids)
        self.assertNotIn(sec_id, ids)
        self.assertEqual(get_plan(sec_id).get("status"), "error")

        # Files really sit under separate level folders
        self.assertTrue((plans_dir("OFFICIAL") / f"{off_id}.json").is_file())
        self.assertTrue((plans_dir("SECRET") / f"{sec_id}.json").is_file())
        self.assertFalse((plans_dir("SECRET") / f"{off_id}.json").is_file())

    def test_create_does_not_rewrite_settings_reports_or_playwright_files(self):
        root = app_data_dir()
        reports = root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        report_file = reports / "existing.json"
        report_file.write_text('{"keep": true}', encoding="utf-8")

        pw_project = Path(self.tmp.name) / "pw_project"
        pw_project.mkdir()
        pw_file = pw_project / "playwright.config.ts"
        pw_file.write_text("// keep me\n", encoding="utf-8")

        settings_before = self.settings.read_text(encoding="utf-8")
        report_before = report_file.read_text(encoding="utf-8")
        pw_before = pw_file.read_text(encoding="utf-8")
        settings_mtime = self.settings.stat().st_mtime_ns
        report_mtime = report_file.stat().st_mtime_ns
        pw_mtime = pw_file.stat().st_mtime_ns

        created = create_plan("Safe create")
        self.assertEqual(created["status"], "ok", created)
        add_case(created["plan"]["id"], "Case A")

        self.assertEqual(self.settings.read_text(encoding="utf-8"), settings_before)
        self.assertEqual(report_file.read_text(encoding="utf-8"), report_before)
        self.assertEqual(pw_file.read_text(encoding="utf-8"), pw_before)
        self.assertEqual(self.settings.stat().st_mtime_ns, settings_mtime)
        self.assertEqual(report_file.stat().st_mtime_ns, report_mtime)
        self.assertEqual(pw_file.stat().st_mtime_ns, pw_mtime)

        # Plan file exists under OFFICIAL only
        plan_path = plans_dir("OFFICIAL") / f"{created['plan']['id']}.json"
        self.assertTrue(plan_path.is_file())
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(data["security_level"], "OFFICIAL")
        # Shared settings still load with prior orb style
        self.assertEqual(load_settings().get("orb_style"), "mystic")


if __name__ == "__main__":
    unittest.main()
