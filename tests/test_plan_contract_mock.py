"""Contract / mock responses on API cases (KAN-221 / G3 / FR-PLUG-1)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from plans.api_case import add_api_case, add_contract_case, parse_api_ref
from plans.run_case import case_detail, run_single_case
from plans.store import create_plan, get_plan
from plugins.contract_mock import (
    default_fixture_name,
    ensure_default_fixture,
    run_mock_response,
)


class PlanContractMockTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_api_ref_mock_fixture(self):
        parsed = parse_api_ref('{"mock_fixture":"contract_ok.json","expect_status":200}')
        self.assertEqual(parsed["mock_fixture"], "contract_ok.json")
        self.assertEqual(parsed["expect_status"], 200)
        live = parse_api_ref("https://example.com/api")
        self.assertEqual(live["mock_fixture"], "")

    def test_add_contract_case_points_at_local_fixture(self):
        created = create_plan("MockSuite")
        pid = created["plan"]["id"]
        out = add_contract_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "api")
        ref = case["source"]["ref"]
        self.assertIn("mock_fixture", ref)
        parsed = parse_api_ref(ref)
        self.assertEqual(parsed["mock_fixture"], default_fixture_name())
        path = ensure_default_fixture()
        self.assertTrue(path.is_file())
        detail = case_detail(out["plan"], case["id"])
        self.assertEqual(detail.get("runner"), "contract_mock")
        self.assertEqual(detail.get("mock_fixture"), default_fixture_name())

    def test_run_record_says_mock(self):
        created = create_plan("MockRun")
        pid = created["plan"]["id"]
        cid = add_contract_case(pid, "Stable mock")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("runner"), "contract_mock")
        run = out.get("run") or {}
        self.assertTrue(run.get("mock"))
        self.assertEqual(run.get("result"), "pass")
        note = run.get("note") or ""
        self.assertIn("mock", note.lower())
        api = out.get("api") or {}
        self.assertTrue(api.get("mock"))
        self.assertEqual(api.get("transport"), "mock")

    @patch("plugins.api_messaging_runner.run_api_check")
    def test_live_endpoint_cases_unchanged(self, mock_api):
        mock_api.return_value = {
            "status": "pass",
            "plugin": "api_messaging_runner",
            "endpoint_label": "https://example.com/api",
            "method": "GET",
            "http_status": 200,
            "body_summary": '{"ok":true}',
            "redaction_hits": 0,
            "expect_status": None,
            "transport": "http",
            "error": None,
            "message": "HTTP 200.",
            "mock": False,
        }
        from settings import store as settings_store

        settings_store.update_setting(
            "api_endpoint", "https://example.com/api", confirm=True
        )
        created = create_plan("LiveApi")
        pid = created["plan"]["id"]
        cid = add_api_case(pid, "Live")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("runner"), "api_messaging_runner")
        run = out.get("run") or {}
        self.assertFalse(run.get("mock"))
        mock_api.assert_called_once()

    def test_mocks_off_unless_case_selects_one(self):
        """Empty mock_fixture → live path; selected fixture → mock path."""
        live = parse_api_ref("")
        self.assertFalse(live.get("mock_fixture"))
        selected = parse_api_ref('{"mock_fixture":"contract_ok.json"}')
        self.assertTrue(selected.get("mock_fixture"))

        created = create_plan("Selective")
        pid = created["plan"]["id"]
        live_case = add_api_case(pid, "Live no mock")["case"]
        mock_case = add_contract_case(pid, "With mock")["case"]
        self.assertNotIn("mock_fixture", live_case["source"].get("ref") or "")
        self.assertIn("mock_fixture", mock_case["source"].get("ref") or "")

    def test_missing_fixture_is_environment(self):
        created = create_plan("MissingFix")
        pid = created["plan"]["id"]
        cid = add_api_case(
            pid, "Gone", mock_fixture="does_not_exist_xyz.json"
        )["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "error")
        self.assertEqual(run.get("failure_class"), "environment")
        self.assertTrue(run.get("mock"))

    def test_runner_loads_fixture_without_network(self):
        ensure_default_fixture()
        out = run_mock_response(fixture=default_fixture_name())
        self.assertEqual(out.get("status"), "pass")
        self.assertTrue(out.get("mock"))
        self.assertEqual(out.get("transport"), "mock")
        self.assertEqual(out.get("http_status"), 200)

    def test_api_contract_and_ui_desk101(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "Contract"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/contract", json={})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body["case"]["source"]["kind"], "api")
        self.assertIn("mock_fixture", body["case"]["source"]["ref"])

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk101", html)
        self.assertIn("desk101", desk)
        self.assertIn("plan-add-contract-btn", html)
        self.assertIn("addContractCaseToOpenPlan", js)
        self.assertIn("cases/contract", js)
        # Live API button remains (G2 unchanged).
        self.assertIn("plan-add-api-btn", html)


if __name__ == "__main__":
    unittest.main()
