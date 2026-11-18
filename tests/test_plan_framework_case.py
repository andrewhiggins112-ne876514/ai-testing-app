"""Another framework runner on plan cases (KAN-233 / G9 / FR-PLUG-3)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
from plans.framework_case import add_framework_case, parse_framework_ref
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, create_plan
from plugins.framework_switch import get_framework, set_framework


class PlanFrameworkCaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        os.environ["AI_TESTING_SETTINGS"] = str(
            Path(self._tmp.name) / "ai_testing_app" / "settings.json"
        )
        Path(os.environ["AI_TESTING_SETTINGS"]).parent.mkdir(parents=True, exist_ok=True)
        Path(os.environ["AI_TESTING_SETTINGS"]).write_text("{}", encoding="utf-8")
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_framework_ref(self):
        self.assertEqual(parse_framework_ref("selenium")["framework"], "selenium")
        self.assertEqual(
            parse_framework_ref('{"framework":"cypress"}')["framework"], "cypress"
        )
        self.assertEqual(parse_framework_ref("")["framework"], "playwright")

    def test_playwright_remains_default_setting(self):
        self.assertEqual(get_framework(), "playwright")

    def test_add_framework_case_selects_runner(self):
        created = create_plan("FwSuite")
        pid = created["plan"]["id"]
        out = add_framework_case(pid, framework="selenium")
        self.assertEqual(out.get("status"), "ok", out)
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "framework")
        self.assertEqual(parse_framework_ref(case["source"]["ref"])["framework"], "selenium")
        detail = case_detail(out["plan"], case["id"])
        self.assertEqual(detail.get("runner"), "framework_switch")
        self.assertTrue(detail.get("framework_case"))
        self.assertEqual(detail.get("framework"), "selenium")

    def test_selenium_run_not_implemented_not_passed(self):
        created = create_plan("FwSelenium")
        pid = created["plan"]["id"]
        cid = add_framework_case(pid, framework="selenium")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("runner"), "framework_switch")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "error")
        self.assertNotEqual(run.get("result"), "pass")
        self.assertEqual(run.get("framework"), "selenium")
        self.assertEqual(run.get("failure_class"), "tool")
        fw = out.get("framework") or {}
        self.assertEqual(fw.get("status"), "not_implemented")
        self.assertFalse(fw.get("implemented"))
        self.assertFalse(fw.get("passed"))

    def test_cypress_run_not_implemented_not_passed(self):
        created = create_plan("FwCypress")
        pid = created["plan"]["id"]
        cid = add_framework_case(pid, framework="cypress")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "error")
        self.assertEqual(run.get("framework"), "cypress")
        self.assertNotEqual(run.get("result"), "pass")

    def test_playwright_framework_case_can_pass_ready(self):
        created = create_plan("FwPw")
        pid = created["plan"]["id"]
        cid = add_framework_case(pid, framework="playwright")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertEqual(run.get("framework"), "playwright")
        fw = out.get("framework") or {}
        self.assertTrue(fw.get("implemented"))

    def test_settings_selenium_blocks_browser_case_pass(self):
        created = create_plan("FwSettingsBlock")
        pid = created["plan"]["id"]
        cid = add_case(pid, "Browser smoke", source_kind="manual-draft")["case"]["id"]
        set_framework("selenium")
        self.assertEqual(get_framework(), "selenium")
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "error")
        self.assertNotEqual(run.get("result"), "pass")
        self.assertEqual(run.get("framework"), "selenium")
        self.assertEqual(out.get("runner"), "framework_switch")
        set_framework("playwright")

    def test_api_framework_and_ui_desk99(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "FwApi"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(
            f"/api/plans/{pid}/cases/framework",
            json={"framework": "selenium"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        case = body.get("case") or {}
        self.assertEqual(case.get("source", {}).get("kind"), "framework")
        self.assertEqual(
            parse_framework_ref(case.get("source", {}).get("ref") or "")["framework"],
            "selenium",
        )

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        self.assertIn("plan-add-framework-btn", html)
        self.assertIn("plan-framework-select", html)
        self.assertIn("desk99", html)
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk99", desk)
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        self.assertIn("cases/framework", js)
        self.assertIn("plan-add-framework-btn", js)


if __name__ == "__main__":
    unittest.main()
