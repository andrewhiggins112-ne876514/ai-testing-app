"""Sandbox chosen as the run environment (KAN-231 / G8 / FR-PLUG-1)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.parallel import MAX_PARALLEL
from plans.run_case import run_single_case
from plans.sandbox_run import list_run_sandboxes, resolve_run_sandbox
from plans.store import add_case, add_run, create_plan, get_plan
from plugins.multi_sandbox import orchestrate, set_plugin_enabled


class PlanSandboxRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_list_empty_when_plugin_disabled(self):
        set_plugin_enabled(False)
        out = list_run_sandboxes()
        self.assertEqual(out.get("status"), "ok")
        self.assertFalse(out.get("plugin_enabled"))
        self.assertEqual(out.get("sandboxes"), [])
        self.assertTrue(out.get("default_profile"))
        self.assertEqual(out.get("parallel_max"), MAX_PARALLEL)

    def test_resolve_default_profile_when_blank(self):
        set_plugin_enabled(True)
        out = resolve_run_sandbox("")
        self.assertEqual(out.get("status"), "ok")
        self.assertIsNone(out.get("sandbox_name"))
        self.assertTrue(out.get("default_profile"))
        self.assertIsNone(out.get("profile_dir"))

    def test_resolve_refuses_when_plugin_disabled(self):
        set_plugin_enabled(False)
        out = resolve_run_sandbox("primary")
        self.assertEqual(out.get("status"), "error")
        self.assertEqual(out.get("error"), "sandbox_plugin_disabled")

    def test_resolve_existing_sandbox_prepares_profile(self):
        set_plugin_enabled(True)
        upserted = orchestrate(
            action="upsert",
            sandbox_id="labone",
            label="Lab One",
            url="https://labone.example",
        )
        self.assertEqual(upserted.get("status"), "ok", upserted)
        out = resolve_run_sandbox("labone")
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("sandbox_name"), "labone")
        self.assertFalse(out.get("default_profile"))
        profile = Path(out.get("profile_dir") or "")
        self.assertTrue(profile.is_dir())
        self.assertIn("sandbox-", str(profile))
        self.assertEqual(out.get("url"), "https://labone.example")

    def test_resolve_unknown_sandbox(self):
        set_plugin_enabled(True)
        orchestrate(action="list")
        out = resolve_run_sandbox("nope-box")
        self.assertEqual(out.get("status"), "error")
        self.assertEqual(out.get("error"), "sandbox_not_found")

    def test_add_run_stores_sandbox_name(self):
        created = create_plan("SandboxStore")
        pid = created["plan"]["id"]
        case = add_case(pid, "Browser")
        cid = case["case"]["id"]
        recorded = add_run(pid, cid, result="pass", duration_ms=10, sandbox="labone")
        self.assertEqual(recorded["run"].get("sandbox"), "labone")
        plain = add_run(pid, cid, result="pass", duration_ms=5)
        self.assertIsNone(plain["run"].get("sandbox"))

    def test_run_single_case_stores_sandbox_and_uses_profile(self):
        set_plugin_enabled(True)
        orchestrate(
            action="upsert",
            sandbox_id="runbox",
            label="Run Box",
            url="https://example.com",
        )
        created = create_plan("SandboxRun")
        pid = created["plan"]["id"]
        case = add_case(pid, "Go")
        cid = case["case"]["id"]

        async def _fake_pw(**kwargs):
            profile = str(kwargs.get("profile_dir") or "")
            self.assertIn("sandbox-runbox", profile)
            return {
                "status": "pass",
                "error": None,
                "screenshot": None,
                "steps": [],
                "playwright_mode": "headed",
                "browser_profile": kwargs.get("profile_dir"),
            }

        with patch("plugins.playwright_runner.run_playwright", new=AsyncMock(side_effect=_fake_pw)):
            with patch("httpx.Client") as client_cls:
                client = client_cls.return_value.__enter__.return_value
                client.get.return_value.status_code = 200
                out = asyncio.run(run_single_case(pid, cid, sandbox_id="runbox"))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertEqual(out.get("sandbox"), "runbox")
        self.assertFalse(out.get("default_profile"))
        run = out.get("run") or {}
        self.assertEqual(run.get("sandbox"), "runbox")

    def test_run_without_sandbox_keeps_default_profile(self):
        created = create_plan("DefaultProfile")
        pid = created["plan"]["id"]
        case = add_case(pid, "Plain")
        cid = case["case"]["id"]

        async def _fake_pw(**kwargs):
            self.assertIn(kwargs.get("profile_dir"), (None, ""))
            return {
                "status": "pass",
                "error": None,
                "steps": [],
                "playwright_mode": "headed",
            }

        with patch(
            "plans.run_case._check_target",
            return_value={"up": True, "message": "ok"},
        ):
            with patch(
                "settings.store.load_settings",
                return_value={
                    "target_url": "https://example.com",
                    "security_level": "OFFICIAL",
                },
            ):
                with patch(
                    "plugins.playwright_runner.run_playwright",
                    new=AsyncMock(side_effect=_fake_pw),
                ):
                    out = asyncio.run(run_single_case(pid, cid, sandbox_id=None))
        self.assertEqual(out.get("status"), "ok", out)
        self.assertIsNone(out.get("sandbox"))
        self.assertTrue(out.get("default_profile"))

    def test_api_run_sandboxes_and_ui_desk99(self):
        client = TestClient(main.app)
        disabled = client.get("/api/plans/run-sandboxes")
        self.assertEqual(disabled.status_code, 200)
        body = disabled.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertFalse(body.get("plugin_enabled"))

        set_plugin_enabled(True)
        orchestrate(
            action="upsert",
            sandbox_id="apiBox",
            label="API Box",
            url="https://api.example",
        )
        enabled = client.get("/api/plans/run-sandboxes")
        payload = enabled.json()
        self.assertTrue(payload.get("plugin_enabled"))
        ids = [s.get("id") for s in payload.get("sandboxes") or []]
        self.assertIn("apibox", ids)

        # Sandboxes screen still manages records
        manage = client.post(
            "/api/multi-sandbox/orchestrate",
            json={"action": "list"},
        )
        self.assertEqual(manage.status_code, 200)
        self.assertEqual(manage.json().get("status"), "ok")

        # Parallel still exposes D1 cap
        cap = client.get("/api/plans/parallel-cap")
        self.assertEqual(cap.json().get("parallel_max"), MAX_PARALLEL)

        html = client.get("/ui/desktop/index.html").text
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("plan-sandbox-select", html)
        self.assertIn("plan-sandbox-hint", html)
        self.assertIn("desk99", html)
        self.assertIn("desk99", desk)

    def test_api_case_run_refuses_sandbox_when_disabled(self):
        set_plugin_enabled(False)
        created = create_plan("RefuseSandbox")
        pid = created["plan"]["id"]
        case = add_case(pid, "Case")
        cid = case["case"]["id"]
        client = TestClient(main.app)
        res = client.post(
            f"/api/plans/{pid}/cases/{cid}/run",
            json={"sandbox_id": "primary"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "error")
        self.assertEqual(body.get("error"), "sandbox_plugin_disabled")


if __name__ == "__main__":
    unittest.main()
