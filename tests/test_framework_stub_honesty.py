"""KAN-267 / FR-PLUG-3 — Framework stub honesty (labels, default, disable Run)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
from plans.framework_case import add_framework_case, parse_framework_ref
from plugins.framework_switch import (
    DEFAULT_FRAMEWORK,
    framework_status,
    is_runnable,
    list_frameworks,
    ui_label,
)


class FrameworkStubHonestyTests(unittest.TestCase):
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

    def test_labels_ready_vs_never_pass(self):
        payload = list_frameworks()
        self.assertTrue(payload.get("stub_honesty"))
        by_id = {f["id"]: f for f in payload["frameworks"]}
        self.assertEqual(by_id["playwright"]["status"], "ready")
        self.assertTrue(by_id["playwright"]["runnable"])
        self.assertIn("ready", by_id["playwright"]["ui_label"].lower())
        for stub in ("selenium", "cypress"):
            self.assertEqual(by_id[stub]["status"], "not_implemented")
            self.assertFalse(by_id[stub]["runnable"])
            self.assertTrue(by_id[stub]["never_pass"])
            label = by_id[stub]["ui_label"].lower()
            self.assertIn("not implemented", label)
            self.assertIn("never pass", label)
        self.assertTrue(is_runnable("playwright"))
        self.assertFalse(is_runnable("selenium"))
        self.assertIn("ready", ui_label("playwright").lower())

    def test_default_framework_case_is_playwright(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "HonestyDefault"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        empty = add_framework_case(pid, framework="")
        self.assertEqual(empty.get("status"), "ok", empty)
        self.assertEqual(
            parse_framework_ref(empty["case"]["source"]["ref"])["framework"],
            DEFAULT_FRAMEWORK,
        )
        api = client.post(f"/api/plans/{pid}/cases/framework", json={})
        self.assertEqual(api.status_code, 200)
        body = api.json()
        self.assertEqual(body.get("status"), "ok", body)
        self.assertEqual(
            parse_framework_ref(body["case"]["source"]["ref"])["framework"],
            "playwright",
        )

    def test_stubs_remain_available(self):
        status = framework_status()
        ids = {f["id"] for f in status["frameworks"]}
        self.assertEqual(ids, {"playwright", "selenium", "cypress"})

    def test_desktop_ui_stub_honesty_desk87(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk87", html)
        self.assertIn("desk87", desk)
        self.assertIn('data-stub-honesty="1"', html)
        self.assertIn("plan-framework-run-hint", html)

        # Plans select defaults to Playwright — never Selenium selected.
        plan_sel = html.split('id="plan-framework-select"', 1)[1].split("</select>", 1)[0]
        self.assertIn('value="playwright" selected', plan_sel)
        self.assertNotIn('value="selenium" selected', plan_sel)
        self.assertNotIn('value="cypress" selected', plan_sel)
        self.assertIn("Playwright (ready)", plan_sel)
        self.assertIn("Selenium (not implemented — never pass)", plan_sel)
        self.assertIn("Cypress (not implemented — never pass)", plan_sel)

        settings_sel = html.split('id="set-test-framework"', 1)[1].split("</select>", 1)[0]
        self.assertIn('value="playwright" selected', settings_sel)
        self.assertIn("never pass", settings_sel.lower())

        self.assertIn("syncFrameworkStubHonestyUi", js)
        self.assertIn("planCaseRun.disabled", js)
        self.assertIn('framework: fw || "playwright"', js)
        self.assertNotIn('framework: fw || "selenium"', js)
        self.assertNotIn(': "selenium";', js.split("addFrameworkCaseToOpenPlan", 1)[1][:800])


if __name__ == "__main__":
    unittest.main()
