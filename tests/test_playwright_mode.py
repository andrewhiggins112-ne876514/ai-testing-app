"""Playwright headed/headless mode setting (KAN-83 / FR-TEST-2)."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins import playwright_suite as suite  # noqa: E402
from plugins.playwright_runner import _headless_enabled, run_playwright  # noqa: E402
from plugins.playwright_suite import run_suite  # noqa: E402
from settings.store import (  # noqa: E402
    app_settings_status,
    get_playwright_headless,
    load_settings,
    save_app_settings,
    write_settings,
)


class PlaywrightModeTests(unittest.TestCase):
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

    def test_default_is_headed(self):
        self.assertFalse(get_playwright_headless())
        self.assertFalse(_headless_enabled())
        status = app_settings_status()
        self.assertFalse(status["playwright_headless"])
        self.assertEqual(status["playwright_mode"], "headed")
        self.assertIn("Playwright mode: headed", status["summary"])

    def test_settings_persist_headless(self):
        saved = save_app_settings(playwright_mode="headless")
        self.assertEqual(saved["status"], "updated")
        self.assertTrue(get_playwright_headless())
        self.assertEqual(saved["playwright_mode"], "headless")
        self.assertTrue(load_settings().get("playwright_headless"))

        back = save_app_settings(playwright_mode="headed")
        self.assertFalse(back["playwright_headless"])
        self.assertEqual(back["playwright_mode"], "headed")

    def test_invalid_mode_rejected(self):
        bad = save_app_settings(playwright_mode="invisible")
        self.assertEqual(bad["status"], "error")
        self.assertIn("headed", (bad.get("message") or "").lower())
        self.assertFalse(get_playwright_headless())

    def test_run_override_beats_settings(self):
        write_settings({**load_settings(), "playwright_headless": True})
        self.assertTrue(_headless_enabled())
        self.assertFalse(_headless_enabled(False))
        self.assertTrue(_headless_enabled(True))

    def test_api_app_settings_mode(self):
        from main import app

        client = TestClient(app)
        get_res = client.get("/api/app-settings")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json().get("playwright_mode"), "headed")

        post_res = client.post(
            "/api/app-settings",
            json={"playwright_mode": "headless"},
        )
        self.assertEqual(post_res.status_code, 200)
        body = post_res.json()
        self.assertEqual(body.get("status"), "updated")
        self.assertEqual(body.get("playwright_mode"), "headless")
        self.assertTrue(body.get("playwright_headless"))

    def test_runner_launches_with_settings_headless(self):
        write_settings({**load_settings(), "playwright_headless": True})
        captured: dict = {}

        class _FakeCtx:
            async def new_page(self):
                page = MagicMock()
                page.goto = AsyncMock()
                page.title = AsyncMock(return_value="ok")
                page.screenshot = AsyncMock(return_value=b"")
                return page

            async def close(self):
                return None

        class _FakeChromium:
            async def launch_persistent_context(self, *_a, **kwargs):
                captured.update(kwargs)
                return _FakeCtx()

        class _FakePw:
            chromium = _FakeChromium()

            async def stop(self):
                return None

        class _Starter:
            async def start(self):
                return _FakePw()

        async def _run():
            with patch(
                "plugins.playwright_runner.async_playwright",
                return_value=_Starter(),
            ):
                return await run_playwright(
                    steps=[{"action": "goto", "value": "https://example.com"}],
                    success_evidence=False,
                )

        result = asyncio.run(_run())
        self.assertTrue(captured.get("headless") is True)
        self.assertTrue(result.get("headless"))
        self.assertEqual(result.get("playwright_mode"), "headless")

    def test_suite_passes_headed_flag_by_default(self):
        project = Path(self.tmp.name) / "pw"
        project.mkdir()
        (project / "package.json").write_text(
            '{"devDependencies":{"@playwright/test":"1.40.0"}}',
            encoding="utf-8",
        )
        (project / "playwright.config.ts").write_text("export default {}", encoding="utf-8")
        tests = project / "tests"
        tests.mkdir()
        (tests / "a.spec.ts").write_text("test('x', async () => {});", encoding="utf-8")

        seen: list = []

        def _fake_cli(args, cwd, timeout_s=300.0):
            seen.append(list(args))
            return {
                "ok": True,
                "error": None,
                "stdout": '{"stats":{"expected":1,"unexpected":0,"skipped":0},"suites":[]}',
                "stderr": "",
                "returncode": 0,
            }

        with patch.object(suite, "_npx_playwright", side_effect=_fake_cli):
            headed = run_suite(suite_path=str(project))
        self.assertIn("--headed", seen[0])
        self.assertEqual(headed.get("playwright_mode"), "headed")

        write_settings({**load_settings(), "playwright_headless": True})
        seen.clear()
        with patch.object(suite, "_npx_playwright", side_effect=_fake_cli):
            headless = run_suite(suite_path=str(project))
        self.assertNotIn("--headed", seen[0])
        self.assertEqual(headless.get("playwright_mode"), "headless")

    def test_desktop_settings_html_exposes_mode(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="set-playwright-mode"', html)
        self.assertIn("value=\"headless\"", html)
        self.assertIn("value=\"headed\"", html)


if __name__ == "__main__":
    unittest.main()
