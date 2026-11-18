"""Desktop-typed cases on the same suite (KAN-217 / G1 / FR-TEST-3)."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.desktop_case import add_desktop_case, parse_desktop_ref
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, create_plan, get_plan


class PlanDesktopCaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_desktop_ref_path_and_steps(self):
        self.assertEqual(parse_desktop_ref(""), {"exe_path": "", "steps": None})
        self.assertEqual(
            parse_desktop_ref(r"C:\Apps\Demo.exe"),
            {"exe_path": r"C:\Apps\Demo.exe", "steps": None},
        )
        parsed = parse_desktop_ref('[{"action":"launch"},{"action":"close"}]')
        self.assertEqual(parsed["exe_path"], "")
        self.assertEqual(len(parsed["steps"] or []), 2)

    def test_add_desktop_case_source_kind(self):
        from settings import store as settings_store

        settings_store.update_setting(
            "target_app_path", sys.executable, confirm=True
        )
        created = create_plan("DeskSuite")
        pid = created["plan"]["id"]
        out = add_desktop_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "desktop")
        self.assertIn("desktop", case.get("tags") or [])
        detail = case_detail(out["plan"], case["id"])
        self.assertTrue(detail.get("desktop_case"))
        self.assertEqual(detail.get("runner"), "desktop_runner")

    @patch("plugins.desktop_runner.run_desktop")
    def test_desktop_case_uses_desktop_runner_same_run_model(self, mock_desk):
        mock_desk.return_value = {
            "status": "pass",
            "exe_path": sys.executable,
            "pid": 1,
            "error": None,
            "logs": "smoke ok",
            "plugin": "desktop_runner",
            "steps": [],
        }
        from settings import store as settings_store

        settings_store.update_setting(
            "target_app_path", sys.executable, confirm=True
        )
        settings_store.update_setting("plugin_desktop_enabled", True, confirm=True)
        created = create_plan("DeskRun")
        pid = created["plan"]["id"]
        added = add_desktop_case(pid, "Smoke exe")
        cid = added["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("runner"), "desktop_runner")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertTrue(run.get("evidence"))
        mock_desk.assert_called_once()
        # Same plan/run model: case.runs grew
        plan = get_plan(pid)["plan"]
        cases = (plan.get("suite") or {}).get("cases") or []
        self.assertEqual(len(cases[0].get("runs") or []), 1)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_browser_cases_unchanged(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "screenshot": r"C:\tmp\ok.png",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("BrowserStay")
        pid = created["plan"]["id"]
        added = add_case(pid, "Browser case", note="open home")
        cid = added["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("run", {}).get("result"), "pass")
        mock_pw.assert_called_once()
        self.assertNotEqual(out.get("runner"), "desktop_runner")

    def test_api_add_desktop_and_ui_desk86(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "API Desk"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/desktop", json={})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body["case"]["source"]["kind"], "desktop")

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk86", html)
        self.assertIn("desk86", desk)
        self.assertIn("plan-add-desktop-btn", html)
        self.assertIn("addDesktopCaseToOpenPlan", js)
        self.assertIn("cases/desktop", js)

    def test_desktop_area_smoke_endpoint_still_works(self):
        client = TestClient(main.app)
        # Plugin status endpoint (Desktop area)
        status = client.get("/api/desktop-plugin")
        self.assertEqual(status.status_code, 200)
        self.assertIn("plugin_desktop_enabled", status.json())
        # Smoke with missing path fails gracefully (does not 500)
        smoke = client.post("/api/desktop-smoke", json={"exe_path": "", "timeout_s": 0.5})
        self.assertEqual(smoke.status_code, 200)
        payload = smoke.json()
        self.assertEqual(payload.get("plugin"), "desktop_runner")
        self.assertIn(payload.get("status"), ("fail", "disabled", "pass"))


if __name__ == "__main__":
    unittest.main()
