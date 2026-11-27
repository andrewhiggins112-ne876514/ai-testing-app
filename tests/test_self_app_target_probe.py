"""KAN-494 — local demo AUT target probe must not nested-HTTP the same app."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class SelfAppTargetProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_is_self_app_url_loopback_8765(self) -> None:
        from settings.connection_health import is_self_app_url

        self.assertTrue(is_self_app_url("http://127.0.0.1:8765/demo-aut/"))
        self.assertTrue(is_self_app_url("http://localhost:8765/demo-aut/"))
        self.assertFalse(is_self_app_url("https://staging.example.com"))
        self.assertFalse(is_self_app_url("http://127.0.0.1:9999/"))

    def test_check_target_demo_aut_skips_http_and_is_up(self) -> None:
        from settings.connection_health import _check_target
        from settings.store import update_setting

        update_setting(
            "target_url", "http://127.0.0.1:8765/demo-aut/", confirm=True
        )
        with patch("settings.connection_health._client") as client_factory:
            result = _check_target()
            client_factory.assert_not_called()
        self.assertTrue(result.get("up"), result)
        self.assertTrue(result.get("self_app"))
        self.assertIn("demo aut", (result.get("message") or "").lower())

    def test_run_smoke_case_not_environment_timeout(self) -> None:
        """Smoke case against local demo AUT must not die as Target timed out."""
        import asyncio

        from plans.store import add_case, create_plan
        from plans.run_case import run_single_case
        from settings.store import update_setting

        update_setting(
            "target_url", "http://127.0.0.1:8765/demo-aut/", confirm=True
        )
        created = create_plan("OPERATE golden path probe")
        pid = created["plan"]["id"]
        added = add_case(
            pid,
            "Smoke: open Operate demo AUT",
            tags=["smoke", "operate-demo-aut"],
            note='Open the demo AUT home page. Expect text "Operate Demo AUT".',
        )
        cid = added["case"]["id"]

        mock_pw = AsyncMock(
            return_value={
                "status": "pass",
                "playwright_mode": "headed",
                "screenshot": None,
                "error": None,
                "steps": [
                    {"action": "goto", "status": "pass"},
                    {"action": "expect_text", "status": "pass"},
                ],
            }
        )
        with patch(
            "plugins.playwright_runner.run_playwright", new=mock_pw
        ):
            out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertNotEqual(run.get("failure_class"), "environment", out)
        self.assertNotIn("timed out", (run.get("note") or "").lower())
        self.assertEqual(run.get("result"), "pass", out)
        mock_pw.assert_called_once()

    def test_connection_health_api_self_target(self) -> None:
        from settings.store import update_setting

        update_setting(
            "target_url", "http://127.0.0.1:8765/demo-aut/", confirm=True
        )
        import main

        client = TestClient(main.app)
        res = client.get("/api/connection-health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        target = next(
            (c for c in (body.get("checks") or []) if c.get("id") == "target"),
            {},
        )
        self.assertTrue(target.get("up"), target)


if __name__ == "__main__":
    unittest.main()
