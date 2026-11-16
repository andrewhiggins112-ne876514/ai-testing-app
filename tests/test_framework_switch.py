"""Dynamic framework switching stub (KAN-79 / FR-PLUG-3)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.framework_switch import (  # noqa: E402
    attempt_run,
    get_framework,
    set_framework,
)
from plugins.registry import get_plugin, list_plugins  # noqa: E402
from settings.store import app_settings_status, load_settings, write_settings  # noqa: E402


class FrameworkSwitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        self.settings.write_text("{}", encoding="utf-8")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_default_framework_is_playwright(self):
        self.assertEqual(get_framework(), "playwright")
        status = app_settings_status()
        self.assertEqual(status["test_framework"], "playwright")
        self.assertIn("Test framework: playwright", status["summary"])

    def test_registry_lists_framework_switch_and_active(self):
        payload = list_plugins()
        ids = [p["id"] for p in payload["plugins"]]
        self.assertIn("framework_switch", ids)
        self.assertEqual(payload.get("test_framework"), "playwright")
        fw = get_plugin("framework_switch")
        self.assertIsNotNone(fw)
        assert fw is not None
        self.assertTrue(fw["enabled"])

    def test_non_playwright_run_is_not_implemented(self):
        set_framework("selenium")
        self.assertEqual(get_framework(), "selenium")
        result = attempt_run()
        self.assertEqual(result["status"], "not_implemented")
        self.assertFalse(result.get("ok", True))
        msg = (result.get("message") or "").lower()
        self.assertTrue("not implemented" in msg or "playwright" in msg)

        cypress = attempt_run(framework="cypress")
        self.assertEqual(cypress["status"], "not_implemented")
        self.assertEqual(cypress.get("framework"), "cypress")

    def test_playwright_attempt_run_ok_stub(self):
        set_framework("playwright")
        result = attempt_run()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result.get("framework"), "playwright")

    def test_api_get_post_and_run(self):
        from main import app

        client = TestClient(app)
        get_res = client.get("/api/test-framework")
        self.assertEqual(get_res.status_code, 200)
        body = get_res.json()
        self.assertEqual(body.get("active") or body.get("test_framework"), "playwright")

        post_res = client.post("/api/test-framework", json={"test_framework": "selenium"})
        self.assertEqual(post_res.status_code, 200)
        saved = post_res.json()
        self.assertEqual(saved.get("status"), "updated")
        self.assertEqual(load_settings().get("test_framework"), "selenium")

        run_res = client.post("/api/test-framework/run", json={"action": "run"})
        self.assertEqual(run_res.status_code, 200)
        run_body = run_res.json()
        self.assertEqual(run_body.get("status"), "not_implemented")

        app_post = client.post(
            "/api/app-settings",
            json={"test_framework": "playwright"},
        )
        self.assertEqual(app_post.status_code, 200)
        self.assertEqual(app_post.json().get("test_framework"), "playwright")

        write_settings(load_settings())
        suite_blocked = client.post("/api/playwright-suite/run", json={})
        # with playwright active, suite may fail for missing path — but not not_implemented
        self.assertNotEqual(suite_blocked.json().get("status"), "not_implemented")

        client.post("/api/test-framework", json={"test_framework": "cypress"})
        blocked = client.post("/api/playwright-suite/run", json={})
        self.assertEqual(blocked.json().get("status"), "not_implemented")


if __name__ == "__main__":
    unittest.main()
