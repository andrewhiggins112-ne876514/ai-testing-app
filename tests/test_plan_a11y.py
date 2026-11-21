"""Accessibility checks on browser cases (KAN-227 / G6 / FR-PLUG-1)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.a11y_case import (
    add_a11y_browser_case,
    case_has_a11y_check,
    enable_a11y_on_case,
)
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, create_plan
from plugins.accessibility_checks import run_accessibility_check, scan_html
from plugins.registry import list_plugins


BAD_HTML = """<!doctype html><html><head></head><body>
<img src="/x.png">
<input type="text" name="q">
<button></button>
<a href="/go"></a>
</body></html>"""

GOOD_HTML = """<!doctype html><html lang="en"><head><title>Home</title></head>
<body>
<img src="/x.png" alt="Logo">
<label for="q">Search</label>
<input id="q" type="text" name="q">
<button aria-label="Submit">Go</button>
<a href="/go" aria-label="Continue">Next</a>
</body></html>"""


class PlanA11yTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_scan_finds_violations(self):
        bad = scan_html(BAD_HTML)
        self.assertGreater(bad.get("violation_count") or 0, 0)
        self.assertEqual(bad.get("replaces_functional"), False)
        ids = {v["id"] for v in bad.get("violations") or []}
        self.assertIn("html-lang", ids)
        self.assertIn("image-alt", ids)
        good = scan_html(GOOD_HTML)
        self.assertEqual(good.get("violation_count"), 0)
        self.assertEqual(good.get("status"), "pass")

    def test_disabled_unless_opted_in(self):
        skipped = run_accessibility_check(html=BAD_HTML, opted_in=False)
        self.assertFalse(skipped.get("checked"))
        self.assertEqual(skipped.get("status"), "skipped")
        self.assertEqual(skipped.get("violation_count"), 0)
        self.assertIn("opt in", (skipped.get("message") or "").lower())

        on = run_accessibility_check(html=BAD_HTML, opted_in=True)
        self.assertTrue(on.get("checked"))
        self.assertGreater(on.get("violation_count") or 0, 0)
        self.assertFalse(on.get("replaces_functional"))

    def test_add_a11y_case_opts_in(self):
        created = create_plan("A11ySuite")
        pid = created["plan"]["id"]
        out = add_a11y_browser_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertTrue(case.get("a11y_check"))
        self.assertTrue(case_has_a11y_check(case))
        self.assertEqual(case["source"]["kind"], "manual-draft")
        detail = case_detail(out["plan"], case["id"])
        self.assertTrue(detail.get("a11y_check"))

        plain = add_case(pid, "Plain browser")
        self.assertFalse(case_has_a11y_check(plain["case"]))
        detail_plain = case_detail(plain["plan"], plain["case"]["id"])
        self.assertFalse(detail_plain.get("a11y_check"))

    def test_enable_on_existing_browser_case(self):
        created = create_plan("A11yToggle")
        pid = created["plan"]["id"]
        plain = add_case(pid, "Browser")
        cid = plain["case"]["id"]
        self.assertFalse(case_has_a11y_check(plain["case"]))
        enabled = enable_a11y_on_case(pid, cid, enabled=True)
        self.assertEqual(enabled.get("status"), "ok")
        self.assertTrue(enabled.get("a11y_opt_in"))
        self.assertTrue(case_has_a11y_check(enabled["case"]))
        disabled = enable_a11y_on_case(pid, cid, enabled=False)
        self.assertFalse(disabled.get("a11y_opt_in"))
        self.assertFalse(case_has_a11y_check(disabled["case"]))

    def test_plugin_registered(self):
        payload = list_plugins()
        ids = {p.get("id") for p in payload.get("plugins") or []}
        self.assertIn("accessibility_checks", ids)

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_violations_attach_without_replacing_functional(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "error": None,
            "screenshot": None,
            "playwright_mode": "headed",
            "steps": [{"action": "goto", "status": "pass"}],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("A11yRun")
        pid = created["plan"]["id"]
        out = add_a11y_browser_case(pid)
        cid = out["case"]["id"]

        with patch(
            "plugins.accessibility_checks.fetch_html",
            return_value={"status": "ok", "html": BAD_HTML, "url": "http://x", "error": None},
        ):
            result = asyncio.run(
                run_single_case(pid, cid, session_id="test", level="OFFICIAL")
            )

        self.assertEqual(result.get("status"), "ok")
        run = result.get("run") or {}
        # Functional pass must stay pass even with a11y violations.
        self.assertEqual(run.get("result"), "pass")
        a11y = run.get("a11y") or result.get("a11y") or {}
        self.assertTrue(a11y.get("checked") or a11y.get("opted_in"))
        self.assertFalse(a11y.get("replaces_functional", True))
        self.assertGreater(int(a11y.get("violation_count") or 0), 0)
        evidence = run.get("evidence") or []
        self.assertTrue(any("accessibility_result" in str(p) for p in evidence))

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_functional_fail_unchanged_when_a11y_clean(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "fail",
            "error": "element not found",
            "screenshot": None,
            "playwright_mode": "headed",
            "steps": [
                {
                    "action": "click",
                    "status": "fail",
                    "error": "element not found",
                    "classification": "product_bug",
                }
            ],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("A11yFail")
        pid = created["plan"]["id"]
        out = add_a11y_browser_case(pid)
        cid = out["case"]["id"]
        with patch(
            "plugins.accessibility_checks.fetch_html",
            return_value={"status": "ok", "html": GOOD_HTML, "url": "http://x", "error": None},
        ):
            result = asyncio.run(
                run_single_case(pid, cid, session_id="test", level="OFFICIAL")
            )
        self.assertEqual((result.get("run") or {}).get("result"), "fail")
        a11y = result.get("a11y") or (result.get("run") or {}).get("a11y") or {}
        self.assertEqual(int(a11y.get("violation_count") or 0), 0)

    def test_api_a11y_and_ui_desk107(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "A11yAPI"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        added = client.post(f"/api/plans/{pid}/cases/a11y", json={})
        self.assertEqual(added.status_code, 200)
        body = added.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertTrue(body["case"].get("a11y_check"))
        self.assertIn("a11y", [t.lower() for t in body["case"].get("tags") or []])

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        self.assertIn("plan-add-a11y-btn", html)
        self.assertIn("desk107", html)
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk107", desk)
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        self.assertIn("cases/a11y", js)
        self.assertIn("plan-add-a11y-btn", js)


if __name__ == "__main__":
    unittest.main()
