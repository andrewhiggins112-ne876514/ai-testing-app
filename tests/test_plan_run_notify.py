"""Local notification when a run finishes (KAN-189 / D6 / FR-UI-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from plans.run_by_tag import run_cases_by_tag  # noqa: E402
from plans.run_case import run_single_case  # noqa: E402
from plans.run_notify import (  # noqa: E402
    DEFAULT_ENABLED,
    attach_suite_notice,
    build_notice,
    clear_notify_state,
    counts_from_case_results,
    is_notify_enabled,
    notify_info,
    notify_run_finished,
    set_notify_enabled,
)
from plans.store import add_case, create_plan, update_case  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class PlanRunNotifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})
        clear_notify_state()

    def tearDown(self):
        clear_notify_state()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_notice_states_pass_fail_counts_only(self):
        notice = build_notice(3, 1, kind="suite")
        self.assertEqual(notice["pass"], 3)
        self.assertEqual(notice["fail"], 1)
        self.assertIn("3 passed", notice["body"])
        self.assertIn("1 failed", notice["body"])
        self.assertFalse(notice["email"])
        self.assertFalse(notice["cloud_push"])
        self.assertEqual(notice["channel"], "local")
        self.assertFalse(notice["has_secrets"])
        self.assertFalse(notice["has_page_text"])
        blob = (notice["title"] + " " + notice["body"]).lower()
        self.assertNotIn("password", blob)
        self.assertNotIn("token", blob)
        self.assertNotIn("http://", blob)
        self.assertNotIn("secret", blob)

    def test_default_enabled_and_can_turn_off(self):
        self.assertTrue(DEFAULT_ENABLED)
        self.assertTrue(is_notify_enabled())
        info = notify_info()
        self.assertTrue(info["run_finish_notify_enabled"])
        self.assertFalse(info["email"])
        self.assertFalse(info["cloud_push"])

        off = set_notify_enabled(False)
        self.assertFalse(off["run_finish_notify_enabled"])
        self.assertFalse(is_notify_enabled())
        self.assertIsNone(notify_run_finished(2, 0, deliver=False))

        on = set_notify_enabled(True)
        self.assertTrue(on["run_finish_notify_enabled"])
        notice = notify_run_finished(2, 1, deliver=False)
        self.assertIsNotNone(notice)
        self.assertEqual(notice["pass"], 2)
        self.assertEqual(notice["fail"], 1)
        self.assertFalse(load_settings().get("run_finish_notify_enabled") is False)

    def test_counts_from_case_results(self):
        passed, failed = counts_from_case_results(
            [
                {"result": "pass"},
                {"result": "fail"},
                {"result": "error"},
                {"result": "skipped"},
            ]
        )
        self.assertEqual(passed, 1)
        self.assertEqual(failed, 2)

    def test_attach_suite_notice_respects_off(self):
        set_notify_enabled(False)
        out = attach_suite_notice(
            {"status": "ok", "message": "done"},
            [{"result": "pass"}, {"result": "fail"}],
            kind="tag",
        )
        self.assertEqual(out["pass"], 1)
        self.assertEqual(out["fail"], 1)
        self.assertNotIn("local_notice", out)

    @patch("plans.run_notify._windows_toast", return_value=True)
    def test_notify_does_not_email_or_cloud(self, _toast):
        notice = notify_run_finished(1, 0, kind="case", deliver=True)
        self.assertIsNotNone(notice)
        self.assertFalse(notice["email"])
        self.assertFalse(notice["cloud_push"])
        self.assertEqual(notice["channel"], "local")

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_standalone_case_run_includes_local_notice(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "click", "status": "ok"}],
        }
        from settings import store as settings_store

        settings_store.update_setting("target_url", "https://example.com", confirm=True)
        created = create_plan("NotifyPlan")
        pid = created["plan"]["id"]
        added = add_case(pid, "Smoke")
        cid = added["case"]["id"]

        import asyncio

        payload = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(payload.get("status"), "ok")
        notice = payload.get("local_notice")
        self.assertIsNotNone(notice)
        self.assertEqual(notice.get("pass"), 1)
        self.assertEqual(notice.get("fail"), 0)
        self.assertIn("passed", notice.get("body", ""))

    @patch("plans.run_by_tag._execute_case", new_callable=AsyncMock)
    def test_tag_run_includes_pass_fail_notice(self, mock_exec):
        created = create_plan("TagNotify")
        pid = created["plan"]["id"]
        a = add_case(pid, "A")["case"]["id"]
        b = add_case(pid, "B")["case"]["id"]
        update_case(pid, a, tags=["smoke"])
        update_case(pid, b, tags=["smoke"])

        async def _fake(plan_id, case_id, **_kwargs):
            return {
                "status": "ok",
                "message": "ok",
                "run": {
                    "id": "run-" + case_id,
                    "result": "pass" if case_id == a else "fail",
                },
            }

        mock_exec.side_effect = _fake

        import asyncio

        payload = asyncio.run(run_cases_by_tag(pid, tag="smoke"))
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("pass"), 1)
        self.assertEqual(payload.get("fail"), 1)
        notice = payload.get("local_notice")
        self.assertIsNotNone(notice)
        self.assertEqual(notice.get("pass"), 1)
        self.assertEqual(notice.get("fail"), 1)

    def test_api_and_desktop_ui_desk72(self):
        client = TestClient(main.app)
        get_res = client.get("/api/plans/run-notify")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("run_finish_notify_enabled"))
        self.assertFalse(data.get("email"))
        self.assertFalse(data.get("cloud_push"))

        off = client.post("/api/plans/run-notify", json={"enabled": False})
        self.assertEqual(off.status_code, 200)
        self.assertFalse(off.json().get("run_finish_notify_enabled"))

        settings = client.get("/api/app-settings")
        self.assertEqual(settings.status_code, 200)
        self.assertFalse(settings.json().get("run_finish_notify_enabled"))

        on = client.post(
            "/api/app-settings",
            json={"run_finish_notify_enabled": True},
        )
        self.assertEqual(on.status_code, 200)
        self.assertTrue(on.json().get("run_finish_notify_enabled"))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("set-run-finish-notify", html)
        self.assertIn("run-finish-toast", html)
        self.assertIn("showLocalRunNotice", js)
        self.assertIn("desk72", html)
        self.assertIn("desk72", desk)


if __name__ == "__main__":
    unittest.main()
