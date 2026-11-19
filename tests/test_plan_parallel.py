"""Sequential default and parallel cap (KAN-179 / D1 / FR-PLAN-2)."""
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
from plans.parallel import (  # noqa: E402
    DEFAULT_PARALLEL,
    MAX_PARALLEL,
    map_cases_with_parallel,
    parallel_cap_info,
    resolve_parallel_count,
)
from plans.run_by_tag import run_cases_by_tag  # noqa: E402
from plans.store import add_case, create_plan, get_plan  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanParallelTests(unittest.TestCase):
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

    def test_cap_defaults(self):
        self.assertEqual(DEFAULT_PARALLEL, 1)
        self.assertEqual(MAX_PARALLEL, 2)
        info = parallel_cap_info()
        self.assertEqual(info["parallel_default"], 1)
        self.assertEqual(info["parallel_max"], 2)

    def test_resolve_default_and_refuse_above_cap(self):
        ok = resolve_parallel_count(None)
        self.assertEqual(ok.get("status"), "ok")
        self.assertEqual(ok.get("parallel_count"), 1)
        self.assertTrue(ok.get("sequential"))

        two = resolve_parallel_count(2)
        self.assertEqual(two.get("status"), "ok")
        self.assertEqual(two.get("parallel_count"), 2)
        self.assertFalse(two.get("sequential"))

        refused = resolve_parallel_count(3)
        self.assertEqual(refused.get("status"), "error")
        self.assertEqual(refused.get("error"), "parallel_above_cap")

        bad = resolve_parallel_count("nope")
        self.assertEqual(bad.get("error"), "parallel_invalid")

    def test_map_cases_preserves_order_with_parallel(self):
        async def _run():
            started: list[str] = []

            async def one(cid: str):
                started.append(cid)
                await asyncio.sleep(0.01 if cid == "a" else 0.001)
                return {"case_id": cid}

            return await map_cases_with_parallel(["a", "b", "c"], 2, one)

        out = asyncio.run(_run())
        self.assertEqual([r["case_id"] for r in out], ["a", "b", "c"])

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_tag_run_stores_parallel_count_default_one(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\parallel.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("ParallelDefault")
        pid = created["plan"]["id"]
        add_case(pid, "A", tags=["smoke"])
        add_case(pid, "B", tags=["smoke"])
        out = asyncio.run(run_cases_by_tag(pid, "smoke"))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("parallel_count"), 1)
        self.assertTrue(out.get("sequential"))
        suite_run_id = out.get("suite_run_id")
        plan = get_plan(pid)["plan"]
        sr = [r for r in plan.get("suite_runs") or [] if r.get("id") == suite_run_id][0]
        self.assertEqual(sr.get("parallel_count"), 1)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_tag_run_parallel_two_stored(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\parallel2.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("ParallelTwo")
        pid = created["plan"]["id"]
        add_case(pid, "A", tags=["smoke"])
        add_case(pid, "B", tags=["smoke"])
        out = asyncio.run(run_cases_by_tag(pid, "smoke", parallel=2))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("parallel_count"), 2)
        self.assertFalse(out.get("sequential"))
        suite_run_id = out.get("suite_run_id")
        plan = get_plan(pid)["plan"]
        sr = [r for r in plan.get("suite_runs") or [] if r.get("id") == suite_run_id][0]
        self.assertEqual(sr.get("parallel_count"), 2)
        self.assertEqual(mock_pw.await_count, 2)

    def test_api_refuses_above_cap_and_exposes_cap(self):
        client = TestClient(main.app)
        cap = client.get("/api/plans/parallel-cap").json()
        self.assertEqual(cap.get("status"), "ok")
        self.assertEqual(cap.get("parallel_default"), 1)
        self.assertEqual(cap.get("parallel_max"), 2)

        created = create_plan("ApiCap")
        pid = created["plan"]["id"]
        add_case(pid, "S", tags=["smoke"])
        res = client.post(
            f"/api/plans/{pid}/run-by-tag",
            json={"tag": "smoke", "parallel": 9},
        )
        body = res.json()
        self.assertEqual(body.get("error"), "parallel_above_cap")

        rerun = client.post(
            f"/api/plans/{pid}/rerun-failed",
            json={"parallel": 5},
        )
        self.assertEqual(rerun.json().get("error"), "parallel_above_cap")

    def test_desktop_ui_has_parallel_controls_desk103(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk103", html)
        self.assertIn("desk103", app)
        self.assertIn("plan-parallel-count", html)
        self.assertIn("Suite parallel", html)
        self.assertIn("selectedParallelCount", js)
        self.assertIn("parallel:", js)
        self.assertIn("1 — sequential (default)", html)
        self.assertIn("2 — max this stage", html)
        self.assertIn("Cap this stage: 2", html)


if __name__ == "__main__":
    unittest.main()
