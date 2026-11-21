"""Tags, priority, smoke/regression tag runs (KAN-169 / C7 / FR-PLAN-2)."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from plans.run_by_tag import (  # noqa: E402
    WELL_KNOWN_TAGS,
    run_cases_by_tag,
    select_cases_for_tag,
)
from plans.store import add_case, create_plan, get_plan, update_case  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanRunByTagTests(unittest.TestCase):
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

    def test_well_known_tags_include_smoke_and_regression(self):
        self.assertIn("smoke", WELL_KNOWN_TAGS)
        self.assertIn("regression", WELL_KNOWN_TAGS)

    def test_case_priority_and_tags_persist(self):
        created = create_plan("Tagged")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Smoke login", tags=["smoke"], priority=10)["case"]["id"]
        updated = update_case(
            pid,
            cid,
            tags=["smoke", "regression"],
            priority=5,
        )
        self.assertEqual(updated["status"], "ok", updated)
        self.assertEqual(updated["case"]["tags"], ["smoke", "regression"])
        self.assertEqual(updated["case"]["priority"], 5)
        reloaded = get_plan(pid)["plan"]
        case = [c for c in reloaded["suite"]["cases"] if c["id"] == cid][0]
        self.assertEqual(case["tags"], ["smoke", "regression"])
        self.assertEqual(case["priority"], 5)

    def test_select_omits_untagged_as_not_selected(self):
        created = create_plan("SelectTag")
        pid = created["plan"]["id"]
        smoke = add_case(pid, "A", tags=["smoke"], priority=2)["case"]["id"]
        both = add_case(pid, "B", tags=["smoke", "regression"], priority=9)["case"]["id"]
        other = add_case(pid, "C", tags=["other"])["case"]["id"]
        off = add_case(pid, "D", tags=["smoke"], enabled=False)["case"]["id"]
        plain = add_case(pid, "E")["case"]["id"]
        plan = get_plan(pid)["plan"]
        sel = select_cases_for_tag(plan, "smoke")
        self.assertEqual(sel.get("status"), "ok", sel)
        self.assertEqual(sel.get("tag"), "smoke")
        # Higher priority first
        self.assertEqual(sel.get("to_run"), [both, smoke])
        skipped = {s["case_id"]: s["reason"] for s in sel.get("skipped") or []}
        self.assertEqual(skipped.get(off), "disabled")
        not_sel = {s["case_id"] for s in sel.get("not_selected") or []}
        self.assertIn(other, not_sel)
        self.assertIn(plain, not_sel)
        self.assertNotIn(smoke, not_sel)

    def test_select_tag_required(self):
        created = create_plan("EmptyTag")
        plan = created["plan"]
        sel = select_cases_for_tag(plan, "  ")
        self.assertEqual(sel.get("error"), "tag_required")

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_by_tag_stores_suite_run_id_and_tag(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\tag.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("TagRun")
        pid = created["plan"]["id"]
        c1 = add_case(pid, "Smoke A", tags=["smoke"], priority=1)["case"]["id"]
        c2 = add_case(pid, "Smoke B", tags=["smoke"], priority=3)["case"]["id"]
        add_case(pid, "Other", tags=["regression"])
        out = asyncio.run(run_cases_by_tag(pid, "smoke"))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("tag"), "smoke")
        self.assertTrue(out.get("sequential"))
        suite_run_id = out.get("suite_run_id")
        self.assertTrue(suite_run_id)
        self.assertEqual(out.get("to_run"), [c2, c1])
        self.assertEqual(len(out.get("case_results") or []), 2)
        self.assertTrue(out.get("not_selected"))
        plan = get_plan(pid)["plan"]
        sr = [r for r in plan.get("suite_runs") or [] if r.get("id") == suite_run_id][0]
        self.assertEqual(sr.get("tag"), "smoke")
        self.assertEqual(sr.get("mode"), "tag")
        self.assertTrue(sr.get("finished_at"))
        linked = 0
        for case in plan["suite"]["cases"]:
            for run in case.get("runs") or []:
                if run.get("suite_run_id") == suite_run_id:
                    linked += 1
        self.assertEqual(linked, 2)
        self.assertEqual(mock_pw.await_count, 2)

    def test_api_run_by_tag_requires_tag(self):
        client = TestClient(main.app)
        created = create_plan("ApiTag")
        pid = created["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/run-by-tag", json={"tag": ""})
        body = res.json()
        self.assertEqual(body.get("error"), "tag_required")

    def test_api_preview_run_by_tag(self):
        client = TestClient(main.app)
        created = create_plan("PreviewTag")
        pid = created["plan"]["id"]
        add_case(pid, "S", tags=["smoke"])
        add_case(pid, "R", tags=["regression"])
        res = client.get(f"/api/plans/{pid}/run-by-tag", params={"tag": "smoke"})
        body = res.json()
        self.assertEqual(body.get("status"), "ok", body)
        self.assertEqual(body.get("tag"), "smoke")
        self.assertEqual(len(body.get("to_run") or []), 1)
        self.assertEqual(len(body.get("not_selected") or []), 1)

    def test_desktop_ui_has_tag_controls_desk107(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk107", html)
        self.assertIn("desk107", app)
        self.assertIn("plan-case-tags", html)
        self.assertIn("plan-case-priority", html)
        self.assertIn("plan-run-by-tag", html)
        self.assertIn("plan-run-tag-smoke", html)
        self.assertIn("plan-run-tag-regression", html)
        self.assertIn("runPlanByTag", js)
        self.assertIn("/run-by-tag", js)


if __name__ == "__main__":
    unittest.main()
