"""API / messaging cases on the same suite (KAN-219 / G2 / FR-LEARN-3)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from plans.api_case import add_api_case, parse_api_ref
from plans.run_case import case_detail, run_single_case
from plans.store import add_case, create_plan, get_plan
from plugins.api_messaging_runner import run_api_check


class PlanApiCaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_api_ref(self):
        self.assertEqual(parse_api_ref("")["endpoint"], "")
        self.assertEqual(
            parse_api_ref("https://example.com/health")["endpoint"],
            "https://example.com/health",
        )
        parsed = parse_api_ref('{"endpoint":"https://x.test","method":"POST","expect_status":201}')
        self.assertEqual(parsed["method"], "POST")
        self.assertEqual(parsed["expect_status"], 201)

    def test_add_api_case_source_kind(self):
        from settings import store as settings_store

        settings_store.update_setting(
            "api_endpoint", "https://example.com/api", confirm=True
        )
        created = create_plan("ApiSuite")
        pid = created["plan"]["id"]
        out = add_api_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "api")
        tags = [t.lower() for t in (case.get("tags") or [])]
        self.assertTrue("api" in tags or "messaging" in tags)
        detail = case_detail(out["plan"], case["id"])
        self.assertTrue(detail.get("api_case"))
        self.assertEqual(detail.get("runner"), "api_messaging_runner")

    @patch("plugins.api_messaging_runner.run_api_check")
    def test_api_case_stores_status_and_redacted_summary(self, mock_api):
        mock_api.return_value = {
            "status": "pass",
            "plugin": "api_messaging_runner",
            "endpoint_label": "https://example.com/api",
            "method": "GET",
            "http_status": 200,
            "body_summary": '{"ok":true,"token":"[REDACTED]"}',
            "redaction_hits": 1,
            "expect_status": None,
            "transport": "http",
            "error": None,
            "message": "HTTP 200.",
        }
        from settings import store as settings_store

        settings_store.update_setting(
            "api_endpoint", "https://example.com/api", confirm=True
        )
        created = create_plan("ApiRun")
        pid = created["plan"]["id"]
        added = add_api_case(pid, "Health")
        cid = added["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("runner"), "api_messaging_runner")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertIsNone(run.get("failure_class"))
        self.assertTrue(run.get("evidence"))
        note = run.get("note") or ""
        self.assertIn("[REDACTED]", note)
        self.assertNotIn("super-secret-token-value", note)
        mock_api.assert_called_once()
        plan = get_plan(pid)["plan"]
        cases = (plan.get("suite") or {}).get("cases") or []
        self.assertEqual(len(cases[0].get("runs") or []), 1)

    @patch("plugins.api_messaging_runner.run_api_check")
    def test_api_failures_class_like_other_cases(self, mock_api):
        mock_api.return_value = {
            "status": "fail",
            "plugin": "api_messaging_runner",
            "endpoint_label": "https://example.com/api",
            "method": "GET",
            "http_status": 500,
            "body_summary": "boom",
            "redaction_hits": 0,
            "expect_status": None,
            "transport": "http",
            "error": "HTTP 500.",
            "message": "HTTP 500.",
        }
        from settings import store as settings_store

        settings_store.update_setting(
            "api_endpoint", "https://example.com/api", confirm=True
        )
        created = create_plan("ApiFail")
        pid = created["plan"]["id"]
        cid = add_api_case(pid)["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "fail")
        self.assertEqual(run.get("failure_class"), "product_bug")

        mock_api.return_value = {
            "status": "fail",
            "plugin": "api_messaging_runner",
            "endpoint_label": "(empty)",
            "method": "GET",
            "http_status": None,
            "body_summary": "",
            "redaction_hits": 0,
            "transport": "none",
            "error": "No messaging/API endpoint configured.",
            "message": "No messaging/API endpoint configured.",
        }
        settings_store.update_setting("api_endpoint", "", confirm=True)
        created2 = create_plan("ApiEnv")
        pid2 = created2["plan"]["id"]
        cid2 = add_api_case(pid2)["case"]["id"]
        out2 = asyncio.run(run_single_case(pid2, cid2))
        run2 = out2.get("run") or {}
        self.assertEqual(run2.get("result"), "error")
        self.assertEqual(run2.get("failure_class"), "environment")

    def test_runner_redacts_secrets_in_body(self):
        class _Resp:
            status = 200
            headers = type("H", (), {"get_content_charset": lambda self: "utf-8"})()

            def read(self, _n=4096):
                return b'{"password":"hunter2secret","ok":true}'

            def getcode(self):
                return 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with patch("plugins.api_messaging_runner.urlopen", return_value=_Resp()):
            out = run_api_check(endpoint="https://example.com/v1", timeout_s=2)
        self.assertEqual(out.get("status"), "pass")
        summary = out.get("body_summary") or ""
        self.assertIn("[REDACTED]", summary)
        self.assertNotIn("hunter2secret", summary)
        self.assertGreaterEqual(int(out.get("redaction_hits") or 0), 1)

    def test_messaging_settings_field_still_present(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        # Settings messaging field must remain (OOS: do not remove).
        self.assertIn("set-api-endpoint", html)
        self.assertIn("Messaging / API endpoint", html)

    def test_api_add_and_ui_desk100(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "API Msg"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/api", json={})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body["case"]["source"]["kind"], "api")

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk100", html)
        self.assertIn("desk100", desk)
        self.assertIn("plan-add-api-btn", html)
        self.assertIn("addApiCaseToOpenPlan", js)
        self.assertIn("cases/api", js)

    def test_browser_and_desktop_cases_unchanged_path(self):
        """Manual/browser case still goes through playwright path (not api runner)."""
        from unittest.mock import AsyncMock

        with patch(
            "plugins.playwright_runner.run_playwright", new_callable=AsyncMock
        ) as mock_pw, patch("plans.run_case._check_target") as mock_tgt:
            mock_tgt.return_value = {"up": True, "message": "ok"}
            mock_pw.return_value = {
                "status": "pass",
                "playwright_mode": "headed",
                "screenshot": r"C:\tmp\ok.png",
                "error": None,
                "steps": [{"action": "goto", "status": "pass"}],
            }
            from settings import store as settings_store

            settings_store.update_setting(
                "target_url", "https://example.com", confirm=True
            )
            created = create_plan("BrowserStayApi")
            pid = created["plan"]["id"]
            cid = add_case(pid, "Browser case", note="open home")["case"]["id"]
            out = asyncio.run(run_single_case(pid, cid))
            self.assertEqual(out.get("run", {}).get("result"), "pass")
            self.assertNotEqual(out.get("runner"), "api_messaging_runner")
            mock_pw.assert_called_once()


if __name__ == "__main__":
    unittest.main()
