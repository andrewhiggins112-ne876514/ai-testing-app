"""Performance budget plugin (KAN-229 / G7 / FR-PLUG-1)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.perf_case import (
    add_perf_budget_case,
    case_performance_budget_ms,
    set_performance_budget,
)
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, add_run, create_plan
from plugins.performance_budget import (
    DEFAULT_BUDGET_MS,
    apply_performance_budget,
    evaluate_performance_budget,
)
from plugins.registry import list_plugins


class PlanPerformanceBudgetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_evaluate_over_and_within(self):
        over = evaluate_performance_budget(duration_ms=6000, budget_ms=5000)
        self.assertTrue(over.get("over_budget"))
        self.assertEqual(over.get("status"), "fail")
        self.assertTrue(over.get("local_only"))
        self.assertFalse(over.get("cloud_apm"))

        within = evaluate_performance_budget(duration_ms=1000, budget_ms=5000)
        self.assertFalse(within.get("over_budget"))
        self.assertEqual(within.get("status"), "pass")

        skipped = evaluate_performance_budget(duration_ms=9000, budget_ms=None)
        self.assertFalse(skipped.get("over_budget"))
        self.assertEqual(skipped.get("status"), "skipped")
        self.assertFalse(skipped.get("applied"))

    def test_apply_fails_pass_when_over_budget(self):
        adj = apply_performance_budget(
            result="pass",
            duration_ms=8000,
            budget_ms=1000,
            note="",
        )
        self.assertEqual(adj["result"], "fail")
        self.assertTrue((adj["performance"] or {}).get("over_budget"))
        self.assertIn("budget", (adj["note"] or "").lower())

        unchanged = apply_performance_budget(
            result="pass",
            duration_ms=8000,
            budget_ms=None,
        )
        self.assertEqual(unchanged["result"], "pass")

    def test_add_perf_case_stores_budget(self):
        created = create_plan("PerfSuite")
        pid = created["plan"]["id"]
        out = add_perf_budget_case(pid, budget_ms=2500)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case_performance_budget_ms(case), 2500)
        self.assertEqual(case["performance_budget_ms"], 2500)
        self.assertIn("perf", [t.lower() for t in case.get("tags") or []])
        detail = case_detail(out["plan"], case["id"])
        self.assertEqual(detail.get("performance_budget_ms"), 2500)

        plain = add_case(pid, "Plain")
        self.assertIsNone(case_performance_budget_ms(plain["case"]))
        detail_plain = case_detail(plain["plan"], plain["case"]["id"])
        self.assertIsNone(detail_plain.get("performance_budget_ms"))

    def test_set_and_clear_budget(self):
        created = create_plan("PerfToggle")
        pid = created["plan"]["id"]
        plain = add_case(pid, "Browser")
        cid = plain["case"]["id"]
        set_on = set_performance_budget(pid, cid, budget_ms=3000)
        self.assertEqual(set_on.get("status"), "ok")
        self.assertEqual(set_on.get("performance_budget_ms"), 3000)
        cleared = set_performance_budget(pid, cid, budget_ms=None)
        self.assertIsNone(cleared.get("performance_budget_ms"))
        self.assertIsNone(case_performance_budget_ms(cleared["case"]))

    def test_add_run_applies_budget(self):
        created = create_plan("PerfRunStore")
        pid = created["plan"]["id"]
        with_budget = add_perf_budget_case(pid, budget_ms=100)
        cid = with_budget["case"]["id"]
        recorded = add_run(pid, cid, result="pass", duration_ms=500)
        self.assertEqual(recorded["run"]["result"], "fail")
        perf = recorded["run"].get("performance") or {}
        self.assertTrue(perf.get("over_budget"))
        self.assertTrue(perf.get("local_only"))
        evidence = recorded["run"].get("evidence") or []
        self.assertTrue(any("performance_budget" in str(p) for p in evidence))

        plain = add_case(pid, "NoBudget")
        ok = add_run(pid, plain["case"]["id"], result="pass", duration_ms=50_000)
        self.assertEqual(ok["run"]["result"], "pass")
        self.assertIsNone(ok["run"].get("performance"))

    def test_plugin_registered(self):
        payload = list_plugins()
        ids = {p.get("id") for p in payload.get("plugins") or []}
        self.assertIn("performance_budget", ids)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_over_budget_fails_case(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}

        async def slow_pw(**_kwargs):
            await asyncio.sleep(0.05)
            return {
                "status": "pass",
                "error": None,
                "screenshot": None,
                "playwright_mode": "headed",
                "steps": [{"action": "goto", "status": "pass"}],
            }

        mock_pw.side_effect = slow_pw
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("PerfLive")
        pid = created["plan"]["id"]
        out = add_perf_budget_case(pid, budget_ms=1)
        cid = out["case"]["id"]
        result = asyncio.run(run_single_case(pid, cid, session_id="test", level="OFFICIAL"))
        self.assertEqual(result.get("status"), "ok")
        run = result.get("run") or {}
        self.assertEqual(run.get("result"), "fail")
        perf = run.get("performance") or {}
        self.assertTrue(perf.get("over_budget"))
        self.assertEqual(perf.get("budget_ms"), 1)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_without_budget_unchanged(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "error": None,
            "screenshot": None,
            "playwright_mode": "headed",
            "steps": [{"action": "goto", "status": "pass"}],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("PerfPlain")
        pid = created["plan"]["id"]
        plain = add_case(pid, "Plain browser")
        cid = plain["case"]["id"]
        result = asyncio.run(run_single_case(pid, cid, session_id="test", level="OFFICIAL"))
        self.assertEqual((result.get("run") or {}).get("result"), "pass")
        self.assertIsNone((result.get("run") or {}).get("performance"))

    def test_api_perf_and_ui_desk104(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "PerfAPI"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        added = client.post(
            f"/api/plans/{pid}/cases/perf",
            json={"budget_ms": 4000},
        )
        self.assertEqual(added.status_code, 200)
        body = added.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body["case"].get("performance_budget_ms"), 4000)
        self.assertTrue(body.get("local_only"))
        self.assertFalse(body.get("cloud_apm"))
        self.assertIn("perf", [t.lower() for t in body["case"].get("tags") or []])

        set_budget = client.post(
            f"/api/plans/{pid}/cases/{body['case']['id']}/perf",
            json={"budget_ms": 1500},
        )
        self.assertEqual(set_budget.status_code, 200)
        self.assertEqual(set_budget.json().get("performance_budget_ms"), 1500)

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        self.assertIn("plan-add-perf-btn", html)
        self.assertIn("desk104", html)
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk104", desk)
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        self.assertIn("cases/perf", js)
        self.assertIn("plan-add-perf-btn", js)
        self.assertEqual(DEFAULT_BUDGET_MS, 5000)


if __name__ == "__main__":
    unittest.main()
