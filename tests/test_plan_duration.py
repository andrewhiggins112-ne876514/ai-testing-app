"""Duration on the run and the case (KAN-191 / D7 / FR-PLAN-4 / FR-REP-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from plans.duration import (  # noqa: E402
    duration_delta_ms,
    duration_info,
    resolve_suite_duration_ms,
    wall_duration_ms,
)
from plans.history import compare_suite_runs, list_suite_history  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    get_plan,
    start_suite_run,
)
from settings.store import write_settings  # noqa: E402


class PlanDurationTests(unittest.TestCase):
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

    def test_duration_info_is_local_only(self):
        info = duration_info()
        self.assertEqual(info["status"], "ok")
        self.assertEqual(info["channel"], "local")
        self.assertFalse(info["upload"])
        self.assertFalse(info["cloud_perf"])

    def test_case_and_suite_run_store_duration(self):
        created = create_plan(name="Duration store", intent="d7")
        pid = created["plan"]["id"]
        cid = add_case(pid, name="Timed case")["case"]["id"]
        sr = start_suite_run(pid, mode="suite")
        sid = sr["suite_run"]["id"]
        time.sleep(0.02)
        rid = add_run(pid, cid, result="pass", duration_ms=250, suite_run_id=sid)[
            "run"
        ]["id"]
        finished = finish_suite_run(
            pid, sid, case_runs=[{"case_id": cid, "run_id": rid}]
        )
        self.assertEqual(finished["status"], "ok")
        suite_run = finished["suite_run"]
        self.assertIsNotNone(suite_run.get("duration_ms"))
        self.assertGreaterEqual(int(suite_run["duration_ms"]), 0)

        plan = get_plan(pid)["plan"]
        case = next(c for c in plan["suite"]["cases"] if c["id"] == cid)
        self.assertEqual(case["runs"][-1]["duration_ms"], 250)
        stored_sr = next(s for s in plan["suite_runs"] if s["id"] == sid)
        self.assertIsNotNone(stored_sr.get("duration_ms"))

        hist = list_suite_history(pid)
        self.assertEqual(hist["status"], "ok")
        self.assertEqual(hist["runs"][0]["duration_ms"], stored_sr["duration_ms"])

    def test_compare_shows_duration_change(self):
        created = create_plan(name="Duration compare")
        pid = created["plan"]["id"]
        c_flip = add_case(pid, name="Result flip")["case"]["id"]
        c_slow = add_case(pid, name="Same result slower")["case"]["id"]

        s1 = start_suite_run(pid)["suite_run"]["id"]
        r1a = add_run(pid, c_flip, result="pass", duration_ms=100, suite_run_id=s1)[
            "run"
        ]["id"]
        r1b = add_run(pid, c_slow, result="pass", duration_ms=200, suite_run_id=s1)[
            "run"
        ]["id"]
        finish_suite_run(
            pid,
            s1,
            case_runs=[
                {"case_id": c_flip, "run_id": r1a},
                {"case_id": c_slow, "run_id": r1b},
            ],
        )

        s2 = start_suite_run(pid)["suite_run"]["id"]
        r2a = add_run(pid, c_flip, result="fail", duration_ms=150, suite_run_id=s2)[
            "run"
        ]["id"]
        r2b = add_run(pid, c_slow, result="pass", duration_ms=500, suite_run_id=s2)[
            "run"
        ]["id"]
        finish_suite_run(
            pid,
            s2,
            case_runs=[
                {"case_id": c_flip, "run_id": r2a},
                {"case_id": c_slow, "run_id": r2b},
            ],
        )

        out = compare_suite_runs(pid, s1, s2)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["upload"])
        self.assertFalse(out["cloud_perf"])
        self.assertEqual(out["changed"], 1)
        self.assertEqual(out["changes"][0]["case_id"], c_flip)
        self.assertEqual(out["changes"][0]["duration_delta_ms"], 50)

        self.assertEqual(out["duration_changed"], 1)
        dur = out["duration_changes"][0]
        self.assertEqual(dur["case_id"], c_slow)
        self.assertEqual(dur["duration_ms_a"], 200)
        self.assertEqual(dur["duration_ms_b"], 500)
        self.assertEqual(dur["duration_delta_ms"], 300)
        self.assertIsNotNone(out.get("duration_delta_ms"))

    def test_helpers(self):
        self.assertEqual(duration_delta_ms(100, 250), 150)
        self.assertIsNone(duration_delta_ms(None, 10))
        self.assertEqual(
            wall_duration_ms(
                "2026-11-17T10:00:00+00:00", "2026-11-17T10:00:01+00:00"
            ),
            1000,
        )
        self.assertEqual(
            resolve_suite_duration_ms({"duration_ms": 42}, case_duration_sum_ms=99),
            99,
        )
        self.assertEqual(
            resolve_suite_duration_ms({"duration_ms": 42}),
            42,
        )
        self.assertEqual(
            resolve_suite_duration_ms({}, case_duration_sum_ms=99),
            99,
        )

    def test_api_and_desktop_ui_desk80(self):
        created = create_plan(name="Duration API")
        pid = created["plan"]["id"]
        cid = add_case(pid, name="A")["case"]["id"]
        s1 = start_suite_run(pid)["suite_run"]["id"]
        r1 = add_run(pid, cid, result="pass", duration_ms=100, suite_run_id=s1)[
            "run"
        ]["id"]
        finish_suite_run(pid, s1, case_runs=[{"case_id": cid, "run_id": r1}])
        s2 = start_suite_run(pid)["suite_run"]["id"]
        r2 = add_run(pid, cid, result="pass", duration_ms=300, suite_run_id=s2)[
            "run"
        ]["id"]
        finish_suite_run(pid, s2, case_runs=[{"case_id": cid, "run_id": r2}])

        client = TestClient(app)
        info = client.get("/api/plans/duration")
        self.assertEqual(info.status_code, 200)
        body = info.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertFalse(body.get("upload"))

        cmp_res = client.get(
            f"/api/plans/{pid}/suite-compare",
            params={"a": s1, "b": s2},
        )
        cmp_body = cmp_res.json()
        self.assertEqual(cmp_body.get("status"), "ok")
        self.assertEqual(cmp_body.get("duration_changed"), 1)
        self.assertFalse(cmp_body.get("upload"))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk80", html)
        self.assertIn("desk80", desk)
        self.assertIn("duration_changes", js)
        self.assertIn("formatDurationDelta", js)
        self.assertIn("Duration changes (same result)", js)
        self.assertIn("no upload", html)
        self.assertIn("changed result or duration", html)


if __name__ == "__main__":
    unittest.main()
