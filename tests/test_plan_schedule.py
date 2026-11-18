"""Scheduled local tagged run (KAN-239 / G12 / FR-PLAN-2)."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from plans.schedule import (  # noqa: E402
    FIRE_WINDOW_MINUTES,
    clear_schedule,
    clear_schedule_state,
    evaluate_due,
    schedule_info,
    set_schedule,
    tick_schedule,
)
from plans.store import add_case, create_plan  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings(
            {
                "security_level": "OFFICIAL",
                "orb_style": "mystic",
                "target_url": "https://example.test/",
            }
        )
        clear_schedule_state("OFFICIAL")

    def tearDown(self):
        clear_schedule_state("OFFICIAL")
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_off_until_created(self):
        info = schedule_info()
        self.assertEqual(info.get("status"), "ok")
        self.assertFalse(info.get("enabled"))
        self.assertTrue(info.get("off_until_created"))
        self.assertIsNone(info.get("schedule"))
        self.assertFalse(info.get("cloud_hosted"))

    def test_set_schedule_sequential_and_local(self):
        created = create_plan("Sched")
        pid = created["plan"]["id"]
        add_case(pid, "Smoke", tags=["smoke"])
        out = set_schedule(pid, "smoke", "08:30")
        self.assertEqual(out.get("status"), "ok", out)
        self.assertTrue(out.get("enabled"))
        sch = out.get("schedule") or {}
        self.assertEqual(sch.get("tag"), "smoke")
        self.assertEqual(sch.get("time_local"), "08:30")
        self.assertEqual(sch.get("parallel_count"), 1)
        self.assertTrue(sch.get("sequential"))
        self.assertFalse(sch.get("cloud"))
        self.assertFalse(out.get("cloud_hosted"))

    def test_clear_turns_off(self):
        created = create_plan("ClearSched")
        pid = created["plan"]["id"]
        set_schedule(pid, "regression", "09:00")
        cleared = clear_schedule()
        self.assertFalse(cleared.get("enabled"))
        self.assertTrue(cleared.get("off_until_created"))

    def _backdate_created(self, before: datetime) -> None:
        from plans.schedule import _load_state, _write_state

        state = _load_state("OFFICIAL")
        sch = state["schedule"]
        early = (before - timedelta(hours=1)).astimezone(ZoneInfo("UTC"))
        sch["created_at"] = early.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        state["schedule"] = sch
        _write_state(state, "OFFICIAL")

    def test_missed_schedule_is_not_run_not_pass(self):
        created = create_plan("MissSched")
        pid = created["plan"]["id"]
        set_schedule(pid, "smoke", "07:00")
        tz = datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
        # Well past the fire window → PC was off.
        now = datetime.now(tz).replace(hour=12, minute=0, second=0, microsecond=0)
        due = now.replace(hour=7, minute=0, second=0, microsecond=0)
        self._backdate_created(due)
        evaluated = evaluate_due(now=now, fire=False)
        misses = evaluated.get("recorded_misses") or []
        self.assertTrue(misses, evaluated)
        item = misses[-1]
        self.assertEqual(item.get("outcome"), "not_run")
        self.assertNotEqual(item.get("outcome"), "pass")
        self.assertIsNone(item.get("pass"))
        self.assertIsNone(item.get("result"))
        self.assertIn("missed", str(item.get("reason") or ""))

    def test_no_saved_connection_records_not_run(self):
        from settings.store import update_setting

        # Clear level-scoped connection keys (write_settings alone may leave credentials).
        update_setting("target_url", "", confirm=True)
        update_setting("target_app_path", "", confirm=True)
        update_setting("jira_url", "", confirm=True)
        update_setting("jira_email", "", confirm=True)
        update_setting("jira_api_token", "", confirm=True)
        created = create_plan("NoConn")
        pid = created["plan"]["id"]
        set_schedule(pid, "smoke", "08:00")
        tz = datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
        now = datetime.now(tz).replace(hour=8, minute=5, second=0, microsecond=0)
        due = now.replace(hour=8, minute=0, second=0, microsecond=0)
        self._backdate_created(due)
        evaluated = evaluate_due(now=now, fire=True)
        misses = evaluated.get("recorded_misses") or []
        self.assertTrue(misses, evaluated)
        no_conn = [m for m in misses if m.get("reason") == "no_saved_connection"]
        self.assertTrue(no_conn, evaluated)
        self.assertEqual(no_conn[-1].get("outcome"), "not_run")
        self.assertIsNone(no_conn[-1].get("pass"))

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_tick_fires_sequential_tag_run(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\sched.png",
        }
        created = create_plan("FireSched")
        pid = created["plan"]["id"]
        add_case(pid, "Smoke A", tags=["smoke"])
        set_schedule(pid, "smoke", "08:00")
        tz = datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
        now = datetime.now(tz).replace(hour=8, minute=3, second=0, microsecond=0)
        due = now.replace(hour=8, minute=0, second=0, microsecond=0)
        self._backdate_created(due)
        # Ensure still inside window
        self.assertLessEqual(3, FIRE_WINDOW_MINUTES)
        result = asyncio.run(tick_schedule(now=now, fire=True))
        self.assertEqual(result.get("status"), "ok", result)
        self.assertTrue(result.get("fired"), result)
        run = result.get("run") or {}
        self.assertEqual(run.get("parallel_count"), 1)
        self.assertTrue(run.get("sequential"))
        self.assertTrue(run.get("suite_run_id"))
        hist = (result.get("history") or [])[-1]
        self.assertEqual(hist.get("outcome"), "ran")

    def test_api_schedule_and_desktop_ui_desk97(self):
        created = create_plan("ApiSched")
        pid = created["plan"]["id"]
        add_case(pid, "S", tags=["smoke"])
        client = TestClient(main.app)
        off = client.get("/api/plans/schedule")
        self.assertEqual(off.status_code, 200)
        self.assertFalse(off.json().get("enabled"))

        saved = client.post(
            "/api/plans/schedule",
            json={"plan_id": pid, "tag": "smoke", "time_local": "06:45"},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        body = saved.json()
        self.assertTrue(body.get("enabled"))
        self.assertEqual(body["schedule"]["time_local"], "06:45")
        self.assertEqual(body["schedule"]["parallel_count"], 1)

        tick = client.post("/api/plans/schedule/tick", json={"fire": False})
        self.assertEqual(tick.status_code, 200)
        tick_body = tick.json()
        self.assertEqual(tick_body.get("status"), "ok")
        # Any recorded miss must not be pass.
        for item in tick_body.get("recorded_misses") or []:
            self.assertEqual(item.get("outcome"), "not_run")
            self.assertNotEqual(item.get("result"), "pass")

        cleared = client.post("/api/plans/schedule/clear")
        self.assertFalse(cleared.json().get("enabled"))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk97", html)
        self.assertIn("desk97", app)
        self.assertIn("desktop.js?v=desk97", html)
        self.assertIn("plan-schedule-save", html)
        self.assertIn("plan-schedule-clear", html)
        self.assertIn("plan-schedule-tick", html)
        self.assertIn("/api/plans/schedule", desk)
        self.assertIn("Scheduled local run", html)


if __name__ == "__main__":
    unittest.main()
