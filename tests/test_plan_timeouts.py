"""Case step timeouts visible and editable (KAN-187 / D5 / FR-PLAN-2)."""
from __future__ import annotations

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
from plans.run_case import run_single_case  # noqa: E402
from plans.store import add_case, create_plan, get_plan, update_case  # noqa: E402
from plans.timeouts import (  # noqa: E402
    DEFAULT_STEP_TIMEOUT_MS,
    case_step_timeout_ms,
    is_timeout_error,
    resolve_step_timeout_ms,
    step_timeout_info,
    timeout_failure_message,
)
from settings.store import write_settings  # noqa: E402


class PlanTimeoutsTests(unittest.TestCase):
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

    def test_default_matches_runner(self):
        self.assertEqual(DEFAULT_STEP_TIMEOUT_MS, 10000)
        info = step_timeout_info()
        self.assertEqual(info["step_timeout_ms_default"], 10000)
        ok = resolve_step_timeout_ms(None)
        self.assertEqual(ok.get("status"), "ok")
        self.assertEqual(ok.get("step_timeout_ms"), 10000)
        self.assertTrue(ok.get("is_default"))

    def test_resolve_refuses_out_of_range(self):
        low = resolve_step_timeout_ms(100)
        self.assertEqual(low.get("error"), "step_timeout_out_of_range")
        high = resolve_step_timeout_ms(999_999)
        self.assertEqual(high.get("error"), "step_timeout_out_of_range")
        bad = resolve_step_timeout_ms("nope")
        self.assertEqual(bad.get("error"), "step_timeout_invalid")

    def test_timeout_failure_message_says_timeout(self):
        self.assertTrue(is_timeout_error("Timeout 10000ms exceeded."))
        msg = timeout_failure_message(
            "Timeout 500ms exceeded while waiting for selector",
            step_timeout_ms=500,
        )
        self.assertIn("timeout", msg.lower())
        self.assertIn("500", msg)
        plain = timeout_failure_message("Timed out waiting for navigation", step_timeout_ms=1000)
        self.assertIn("timeout", plain.lower())

    def test_case_stores_and_updates_step_timeout(self):
        created = create_plan("TimeoutPlan")
        pid = created["plan"]["id"]
        added = add_case(pid, "Hang check")
        case = added["case"]
        self.assertEqual(case.get("step_timeout_ms"), DEFAULT_STEP_TIMEOUT_MS)
        self.assertEqual(case_step_timeout_ms(case), 10000)

        updated = update_case(pid, case["id"], step_timeout_ms=2500)
        self.assertEqual(updated.get("status"), "ok")
        self.assertEqual(updated["case"].get("step_timeout_ms"), 2500)

        refused = update_case(pid, case["id"], step_timeout_ms=50)
        self.assertEqual(refused.get("status"), "error")
        self.assertEqual(refused.get("error"), "step_timeout_out_of_range")

        loaded = get_plan(pid)
        persisted = loaded["plan"]["suite"]["cases"][0]
        self.assertEqual(persisted.get("step_timeout_ms"), 2500)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_uses_case_step_timeout_and_labels_timeout(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "fail",
            "playwright_mode": "headed",
            "error": "Timeout 2500ms exceeded.",
            "steps": [{"action": "click", "status": "fail", "error": "Timeout 2500ms exceeded."}],
            "screenshot": r"C:\tmp\timeout.png",
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("RunTimeout")
        pid = created["plan"]["id"]
        added = add_case(pid, "Slow click")
        cid = added["case"]["id"]
        update_case(pid, cid, step_timeout_ms=2500)

        import asyncio

        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("step_timeout_ms"), 2500)
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "fail")
        note = (run.get("note") or "").lower()
        self.assertIn("timeout", note)
        self.assertIn("2500", note)
        kwargs = mock_pw.await_args.kwargs
        self.assertEqual(kwargs.get("click_timeout"), 2500)
        self.assertEqual(kwargs.get("retry_timeout"), 1250)

    def test_api_step_timeout_and_desktop_ui_desk60(self):
        client = TestClient(main.app)
        info = client.get("/api/plans/step-timeout").json()
        self.assertEqual(info.get("status"), "ok")
        self.assertEqual(info.get("step_timeout_ms_default"), 10000)

        created = create_plan("ApiTimeout")
        pid = created["plan"]["id"]
        added = add_case(pid, "Editable")
        cid = added["case"]["id"]
        res = client.post(
            f"/api/plans/{pid}/cases/{cid}",
            json={"step_timeout_ms": 8000},
        ).json()
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res["case"].get("step_timeout_ms"), 8000)

        detail = client.get(f"/api/plans/{pid}/cases/{cid}").json()
        self.assertEqual(detail.get("step_timeout_ms"), 8000)

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk60", html)
        self.assertIn("desk60", desk)
        self.assertIn("plan-case-step-timeout", html)
        self.assertIn("planCaseStepTimeout", js)
        self.assertIn("step_timeout_ms", js)


if __name__ == "__main__":
    unittest.main()
