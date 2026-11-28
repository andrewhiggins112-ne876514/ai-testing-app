"""KAN-375 / KAN-376 — OPERATE-1 open / reveal Playwright trace.zip."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


class OperateOpenTraceResolveTests(unittest.TestCase):
    def test_allows_zip_under_traces(self) -> None:
        from plugins.playwright_trace_open import open_playwright_trace

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            traces = local / "ai_testing_app" / "traces"
            traces.mkdir(parents=True)
            zip_path = traces / "demo-trace.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("trace.network", "{}")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                result = open_playwright_trace(
                    str(zip_path), action="validate", launch=False
                )
            self.assertTrue(result.get("ok"), result)
            self.assertEqual(result.get("action"), "validate")
            self.assertTrue(str(result.get("path", "")).endswith("demo-trace.zip"))

    def test_rejects_outside_appdata(self) -> None:
        from plugins.playwright_trace_open import open_playwright_trace

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            outside = local / "elsewhere" / "evil-trace.zip"
            outside.parent.mkdir(parents=True)
            with zipfile.ZipFile(outside, "w") as zf:
                zf.writestr("x", "1")
            appdata = local / "appdata"
            appdata.mkdir()
            with patch.dict("os.environ", {"LOCALAPPDATA": str(appdata)}):
                result = open_playwright_trace(
                    str(outside), action="show_trace", launch=False
                )
            self.assertFalse(result.get("ok"))
            self.assertIn("outside", (result.get("error") or "").lower())

    def test_rejects_non_zip(self) -> None:
        from plugins.playwright_trace_open import open_playwright_trace

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            traces = local / "ai_testing_app" / "traces"
            traces.mkdir(parents=True)
            notice = traces / "trace.notice.txt"
            notice.write_text("not a zip", encoding="utf-8")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                result = open_playwright_trace(
                    str(notice), action="reveal", launch=False
                )
            self.assertFalse(result.get("ok"))
            self.assertIn("zip", (result.get("error") or "").lower())

    def test_show_trace_launches_playwright(self) -> None:
        from plugins.playwright_trace_open import open_playwright_trace

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            traces = local / "ai_testing_app" / "traces"
            traces.mkdir(parents=True)
            zip_path = traces / "run-trace.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("trace.network", "{}")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                with patch("plugins.playwright_trace_open.subprocess.Popen") as popen:
                    result = open_playwright_trace(
                        str(zip_path), action="show_trace", launch=True
                    )
            self.assertTrue(result.get("ok"), result)
            self.assertTrue(result.get("launched"))
            self.assertTrue(popen.called)
            args = popen.call_args[0][0]
            self.assertIn("playwright", args)
            self.assertIn("show-trace", args)
            self.assertEqual(args[-1], str(zip_path.resolve()))


class OperateOpenTraceApiTests(unittest.TestCase):
    def test_api_validate_and_reject(self) -> None:
        from main import app

        client = TestClient(app)
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            traces = local / "ai_testing_app" / "traces"
            traces.mkdir(parents=True)
            zip_path = traces / "api-trace.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("trace.network", "{}")
            with patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
                ok = client.post(
                    "/api/playwright-trace/open",
                    json={
                        "path": str(zip_path),
                        "action": "validate",
                        "launch": False,
                    },
                )
                bad = client.post(
                    "/api/playwright-trace/open",
                    json={
                        "path": str(local / "nope.zip"),
                        "action": "show_trace",
                        "launch": False,
                    },
                )
        self.assertEqual(ok.status_code, 200)
        body = ok.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(bad.status_code, 400)


class OperateOpenTraceUiTests(unittest.TestCase):
    def test_marker_controls_and_desk163(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk163", html)
        self.assertIn("desk163", desk)
        self.assertIn('data-operate-open-trace="1"', html)
        self.assertIn("Open Playwright Trace", js)
        self.assertIn("Reveal in Explorer", js)
        self.assertIn("Copy path", js)
        self.assertIn("/api/playwright-trace/open", js)
        self.assertIn("ensureEvidenceTraceActions", js)
        self.assertIn("setEvidenceTraceActions", js)
        self.assertIn("evidence-first-trace-actions", css)
        # Absent zip → actions stay hidden via setEvidenceTraceActions
        self.assertIn("actions.hidden = !show", js)


if __name__ == "__main__":
    unittest.main()
