"""Flake score and quarantine (KAN-181 / D2 / FR-PLAN-2 + FR-PLAN-4)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from plans.quarantine import (  # noqa: E402
    clear_quarantine,
    flake_score,
    is_actively_quarantined,
    set_quarantine,
    suite_flake_report,
)
from plans.run_by_tag import select_cases_for_tag  # noqa: E402
from plans.run_case import case_detail  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    cases_for_run,
    create_plan,
    get_plan,
)
from settings.store import write_settings  # noqa: E402


def _future(days: int = 7) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)
    ).isoformat()


def _past(days: int = 1) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=days)
    ).isoformat()


class PlanQuarantineTests(unittest.TestCase):
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

    def test_flake_score_last_n_runs(self):
        created = create_plan("Flake suite", intent="d2")
        pid = created["plan"]["id"]
        case = add_case(pid, "Flipper", tags=["smoke"])["case"]
        for result in ("pass", "fail", "fail", "pass", "error"):
            add_run(pid, case["id"], result=result, evidence=["e.txt"])
        plan = get_plan(pid)["plan"]
        target = plan["suite"]["cases"][0]
        flake = flake_score(target, window=5)
        self.assertEqual(flake["fail_count"], 3)
        self.assertEqual(flake["runs_in_window"], 5)
        self.assertEqual(flake["flake_label"], "3/5")
        self.assertIsNotNone(flake["last_failure"])
        self.assertEqual(flake["last_failure"]["result"], "error")

        report = suite_flake_report(plan, window=5)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["cases"][0]["fail_count"], 3)

    def test_quarantine_requires_reason_and_expiry(self):
        created = create_plan("Q req", intent="d2")
        pid = created["plan"]["id"]
        case = add_case(pid, "Needs reason")["case"]
        add_run(pid, case["id"], result="fail", evidence=["f.png"])

        no_reason = set_quarantine(pid, case["id"], reason="", expires_at=_future())
        self.assertEqual(no_reason["status"], "error")
        self.assertEqual(no_reason["error"], "quarantine_reason_required")

        no_exp = set_quarantine(pid, case["id"], reason="flake", expires_at="")
        self.assertEqual(no_exp["status"], "error")
        self.assertEqual(no_exp["error"], "quarantine_expiry_required")

        past = set_quarantine(pid, case["id"], reason="flake", expires_at=_past())
        self.assertEqual(past["status"], "error")
        self.assertEqual(past["error"], "quarantine_expiry_past")

    def test_quarantine_skips_run_keeps_last_failure_not_pass(self):
        created = create_plan("Q skip", intent="d2")
        pid = created["plan"]["id"]
        case = add_case(pid, "Flaky", tags=["smoke"])["case"]
        add_run(
            pid,
            case["id"],
            result="fail",
            failure_class="test_defect",
            evidence=["fail.png"],
        )
        ok = set_quarantine(
            pid, case["id"], reason="Intermittent timeout", expires_at=_future(3)
        )
        self.assertEqual(ok["status"], "ok", ok)
        self.assertTrue(ok["quarantine"]["quarantined"])
        self.assertFalse(ok["counted_as_pass"])
        self.assertEqual(ok["last_failure"]["result"], "fail")
        self.assertEqual(len(ok["case"]["runs"]), 1)

        runnable = cases_for_run(pid)
        self.assertNotIn(case["id"], [c["id"] for c in runnable["cases"]])
        reasons = {s["case_id"]: s["reason"] for s in runnable["skipped"]}
        self.assertEqual(reasons.get(case["id"]), "quarantined")

        plan = get_plan(pid)["plan"]
        sel = select_cases_for_tag(plan, "smoke")
        self.assertNotIn(case["id"], sel["to_run"])
        skip_reasons = {s["case_id"]: s["reason"] for s in sel["skipped"]}
        self.assertEqual(skip_reasons.get(case["id"]), "quarantined")

        client = TestClient(app)
        refused = client.post(f"/api/plans/{pid}/cases/{case['id']}/run").json()
        self.assertEqual(refused.get("status"), "error")
        self.assertEqual(refused.get("error"), "case_quarantined")
        self.assertFalse(refused.get("counted_as_pass"))

        detail = case_detail(get_plan(pid)["plan"], case["id"])
        self.assertTrue(detail["quarantined"])
        self.assertEqual(detail["last_failure"]["result"], "fail")
        self.assertEqual(detail["run_count"], 1)

    def test_expiry_returns_to_selectable(self):
        created = create_plan("Q expiry", intent="d2")
        pid = created["plan"]["id"]
        case = add_case(pid, "Was flaky", tags=["regression"])["case"]
        # Set with future, then rewind expires_at on disk via clear path + direct flag
        set_quarantine(pid, case["id"], reason="old flake", expires_at=_future(2))
        plan = get_plan(pid)["plan"]
        target = plan["suite"]["cases"][0]
        # Simulate expired quarantine without going through set (past expiry)
        target["quarantine"] = {
            "reason": "old flake",
            "expires_at": _past(1),
            "active": True,
        }
        target["quarantined"] = True
        from plans.store import _write_plan

        _write_plan(plan, level="OFFICIAL")
        reloaded = get_plan(pid)["plan"]["suite"]["cases"][0]
        self.assertFalse(is_actively_quarantined(reloaded))
        runnable = cases_for_run(pid)
        self.assertIn(case["id"], [c["id"] for c in runnable["cases"]])

        # Manual clear also restores
        set_quarantine(pid, case["id"], reason="again", expires_at=_future())
        cleared = clear_quarantine(pid, case["id"])
        self.assertEqual(cleared["status"], "ok")
        self.assertFalse(cleared["quarantine"]["quarantined"])
        self.assertIn(case["id"], [c["id"] for c in cases_for_run(pid)["cases"]])

    def test_api_flake_and_desktop_ui_desk93(self):
        created = create_plan("API flake", intent="d2-api")
        pid = created["plan"]["id"]
        case = add_case(pid, "API flaky")["case"]
        add_run(pid, case["id"], result="fail")
        add_run(pid, case["id"], result="pass")

        client = TestClient(app)
        flake = client.get(f"/api/plans/{pid}/flake?window=10").json()
        self.assertEqual(flake["status"], "ok", flake)
        self.assertEqual(flake["cases"][0]["fail_count"], 1)
        self.assertEqual(flake["cases"][0]["flake_label"], "1/2")

        bad = client.post(
            f"/api/plans/{pid}/cases/{case['id']}/quarantine",
            json={"reason": "", "expires_at": _future()},
        ).json()
        self.assertEqual(bad["status"], "error")

        good = client.post(
            f"/api/plans/{pid}/cases/{case['id']}/quarantine",
            json={"reason": "flake score high", "expires_at": _future()},
        ).json()
        self.assertEqual(good["status"], "ok", good)
        self.assertTrue(good["quarantine"]["quarantined"])
        self.assertFalse(good["counted_as_pass"])
        self.assertEqual(good["last_failure"]["result"], "fail")

        detail = client.get(f"/api/plans/{pid}/cases/{case['id']}").json()
        self.assertTrue(detail["quarantined"])
        self.assertEqual(detail["flake"]["fail_count"], 1)
        self.assertIsNotNone(detail["last_failure"])

        cleared = client.post(
            f"/api/plans/{pid}/cases/{case['id']}/quarantine/clear"
        ).json()
        self.assertEqual(cleared["status"], "ok", cleared)
        self.assertFalse(cleared["quarantine"]["quarantined"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk93", html)
        self.assertIn("desk93", desk)
        self.assertIn("plan-quarantine-reason", html)
        self.assertIn("plan-quarantine-set", html)
        self.assertIn("plan-flake-summary", html)
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("planQuarantineSet", js)
        self.assertIn("refreshFlakeReport", js)
        self.assertIn("/flake", js)


if __name__ == "__main__":
    unittest.main()
