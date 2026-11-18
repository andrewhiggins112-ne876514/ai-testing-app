"""Tester HUD widget pack on orb home (KAN-203 / F1 / FR-UI-1 + FR-UI-6)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from plans.quarantine import set_quarantine  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    start_suite_run,
)
from plans.tester_hud import tester_hud_summary as build_tester_hud  # noqa: E402
from settings.store import write_settings  # noqa: E402


def _future(hours: int = 48) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(hours=hours)
    ).replace(microsecond=0).isoformat()


class TesterHudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def _seed(self):
        created = create_plan(
            name="Tester HUD plan",
            intent="F1 widgets",
            sources={"jira_keys": ["KAN-203"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        cid_ok = add_case(pid, name="passes", tags=["smoke"])["case"]["id"]
        cid_fail = add_case(pid, name="breaks", tags=["smoke"])["case"]["id"]
        cid_q = add_case(pid, name="flaky", tags=["regression"])["case"]["id"]

        sr = start_suite_run(pid, mode="suite")
        self.assertEqual(sr["status"], "ok")
        sid = sr["suite_run"]["id"]
        rid_ok = add_run(
            pid, cid_ok, result="pass", duration_ms=100, suite_run_id=sid
        )["run"]["id"]
        rid_fail = add_run(
            pid,
            cid_fail,
            result="fail",
            duration_ms=200,
            failure_class="product_bug",
            suite_run_id=sid,
        )["run"]["id"]
        finished = finish_suite_run(
            pid,
            sid,
            case_runs=[
                {"case_id": cid_ok, "run_id": rid_ok},
                {"case_id": cid_fail, "run_id": rid_fail},
            ],
        )
        self.assertEqual(finished["status"], "ok")

        q = set_quarantine(
            pid, cid_q, reason="flake for F1", expires_at=_future()
        )
        self.assertEqual(q["status"], "ok")
        return pid, cid_ok, cid_fail, cid_q

    def test_summary_connection_last_run_fails_quarantine(self):
        pid, _cid_ok, cid_fail, cid_q = self._seed()
        fake_health = {
            "status": "ok",
            "overall": "degraded",
            "summary": "Jira: up | Ollama: down | Target URL: up",
            "message": "Connection health: degraded.",
            "checks": [
                {
                    "id": "jira",
                    "label": "Jira",
                    "state": "up",
                    "up": True,
                    "message": "ok",
                },
                {
                    "id": "ollama",
                    "label": "Ollama",
                    "state": "down",
                    "up": False,
                    "message": "offline",
                },
            ],
        }
        with patch(
            "settings.connection_health.connection_health",
            return_value=fake_health,
        ):
            payload = build_tester_hud(probe_connection=True)

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["home_only"])
        self.assertFalse(payload["separate_tester_home"])
        self.assertEqual(payload["connection"]["overall"], "degraded")
        self.assertEqual(len(payload["connection"]["checks"]), 2)
        self.assertIsNotNone(payload["last_run"])
        self.assertEqual(payload["last_run"]["plan_id"], pid)
        self.assertEqual(payload["last_run"]["pass"], 1)
        self.assertEqual(payload["last_run"]["fail"], 1)
        self.assertEqual(payload["failed_count"], 1)
        self.assertEqual(payload["failed_cases"][0]["case_id"], cid_fail)
        self.assertEqual(payload["quarantined_count"], 1)
        self.assertEqual(payload["quarantined_cases"][0]["case_id"], cid_q)

    def test_api_tester_hud_and_desktop_ui_desk87(self):
        self._seed()
        with patch(
            "settings.connection_health.connection_health",
            return_value={
                "status": "ok",
                "overall": "up",
                "summary": "all up",
                "message": "Connection health: up.",
                "checks": [],
            },
        ):
            client = TestClient(main.app)
            res = client.get("/api/plans/tester-hud")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["separate_tester_home"])
        self.assertTrue(body["home_only"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk87", html)
        self.assertIn("desk87", desk)
        self.assertIn('id="hud-tester-conn"', html)
        self.assertIn('id="hud-tester-last"', html)
        self.assertIn('id="hud-tester-fails"', html)
        self.assertIn('id="hud-tester-quarantine"', html)
        self.assertIn("hud-tester-conn-toggle", html)
        self.assertIn("hud-tester-last-toggle", html)
        self.assertIn("hud-tester-fails-toggle", html)
        self.assertIn("hud-tester-quarantine-toggle", html)
        self.assertIn("/api/plans/tester-hud", js)
        self.assertIn("openPlansOnCase", js)
        self.assertIn("Tester HUD pack", html)


if __name__ == "__main__":
    unittest.main()
