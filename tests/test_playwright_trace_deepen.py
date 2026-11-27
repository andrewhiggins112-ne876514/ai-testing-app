"""KAN-372 / KAN-373 — TRACE-DEEPEN real Playwright trace.zip on failure."""
from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class TraceDeepenBundleTests(unittest.TestCase):
    def test_failure_bundle_prefers_zip_not_notice(self) -> None:
        from plans.evidence_bundle import write_failure_bundle

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            zip_path = local / "run-trace.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("trace.network", "{}")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                bundle = write_failure_bundle(
                    run_id="r-trace",
                    plan_id="p1",
                    case_id="c1",
                    playwright={
                        "status": "fail",
                        "screenshot": str(local / "shot.png"),
                        "trace": str(zip_path),
                        "steps": [{"action": "click", "error": "timeout"}],
                        "error": "timeout",
                    },
                )
            data = bundle["bundle"]
            self.assertEqual(data.get("trace"), str(zip_path))
            self.assertIn(str(zip_path), bundle.get("paths") or [])
            notice = local / "ai_testing_app" / "evidence" / "r-trace" / "trace.notice.txt"
            self.assertFalse(notice.exists())
            manifest = Path(bundle["bundle_path"])
            written = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(written.get("trace"), str(zip_path))
            self.assertNotIn("trace.notice", json.dumps(written))

    def test_failure_bundle_without_zip_omits_notice(self) -> None:
        from plans.evidence_bundle import write_failure_bundle

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                bundle = write_failure_bundle(
                    run_id="r-none",
                    plan_id="p1",
                    case_id="c1",
                    playwright={
                        "status": "fail",
                        "screenshot": None,
                        "steps": [],
                        "error": "boom",
                    },
                )
            self.assertIsNone(bundle["bundle"].get("trace"))
            notice = local / "ai_testing_app" / "evidence" / "r-none" / "trace.notice.txt"
            self.assertFalse(notice.exists())
            paths = bundle.get("paths") or []
            self.assertTrue(all("trace.notice" not in p for p in paths))


class TraceDeepenRunnerTests(unittest.TestCase):
    def test_failed_step_run_writes_trace_zip(self) -> None:
        import os

        from playwright.async_api import async_playwright

        from plugins.playwright_runner import run_playwright

        html = "<!doctype html><title>Ok</title><body>Hello</body>"

        async def _go():
            tmp_obj = tempfile.TemporaryDirectory()
            tmp = Path(tmp_obj.name)
            try:
                page = tmp / "page.html"
                page.write_text(html, encoding="utf-8")
                local = tmp / "appdata"
                local.mkdir()
                env = {
                    "LOCALAPPDATA": str(local),
                    "AI_TESTING_REPORTS": str(tmp / "reports"),
                }
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=True)
                try:
                    with patch.dict(os.environ, env, clear=False):
                        result = await run_playwright(
                            page.as_uri(),
                            mode="run",
                            steps=[
                                {"action": "goto", "value": page.as_uri()},
                                {
                                    "action": "expect_text",
                                    "value": "definitely-missing-xyz",
                                },
                            ],
                            browser=browser,
                            success_evidence=False,
                            headless=True,
                        )
                    return result, local, tmp_obj
                finally:
                    await browser.close()
                    await pw.stop()
            except Exception:
                tmp_obj.cleanup()
                raise

        result, local, tmp_obj = asyncio.run(_go())
        try:
            self.assertEqual(result.get("status"), "fail")
            self.assertTrue(result.get("tracing"))
            trace = result.get("trace")
            self.assertTrue(trace, result)
            self.assertTrue(str(trace).endswith(".zip"))
            self.assertTrue(Path(trace).is_file())
            self.assertTrue(zipfile.is_zipfile(trace))
            self.assertTrue(
                str(Path(trace).resolve()).startswith(str(local.resolve()))
            )
        finally:
            tmp_obj.cleanup()


class TraceDeepenUiTests(unittest.TestCase):
    def test_ui_markers_and_copy_desk146(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk146", html)
        self.assertIn("desk146", desk)
        self.assertIn('data-playwright-trace="1"', html)
        self.assertIn("Trace: no Playwright trace for this run.", html)
        self.assertNotIn("not hooked yet", html)
        self.assertNotIn("notice file is not a Playwright trace", html)
        self.assertIn("EVIDENCE_TRACE_CAPTURED", js)
        self.assertIn("EVIDENCE_TRACE_NONE", js)
        self.assertNotIn("not hooked yet", js)
        self.assertNotIn('id="trace-run"', html)


if __name__ == "__main__":
    unittest.main()
