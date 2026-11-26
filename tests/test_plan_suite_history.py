"""Suite history and compare two runs (KAN-175 / C10 / FR-PLAN-4)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from plans.history import compare_suite_runs, list_suite_history  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    finish_suite_run,
    get_plan,
    set_known_issue_link,
    start_suite_run,
)
from settings.store import get_security_level, set_security_level, write_settings  # noqa: E402


class PlanSuiteHistoryTests(unittest.TestCase):
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

    def _seed_two_runs(self):
        created = create_plan(name="History suite", intent="c10")
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        c_pass = add_case(pid, name="Always pass", tags=["smoke"])["case"]["id"]
        c_flip = add_case(pid, name="Flips result", tags=["regression"])["case"]["id"]
        c_known = add_case(pid, name="Known fail", tags=["smoke"])["case"]["id"]

        sr1 = start_suite_run(pid, mode="tag", tag="smoke")
        self.assertEqual(sr1["status"], "ok")
        sid1 = sr1["suite_run"]["id"]
        r1a = add_run(
            pid, c_pass, result="pass", duration_ms=100, suite_run_id=sid1
        )["run"]["id"]
        r1b = add_run(
            pid, c_flip, result="pass", duration_ms=200, suite_run_id=sid1
        )["run"]["id"]
        r1c = add_run(
            pid,
            c_known,
            result="fail",
            duration_ms=50,
            failure_class="known_issue",
            suite_run_id=sid1,
        )["run"]["id"]
        set_known_issue_link(
            pid, c_known, note="Known flake", jira_key="KAN-99", run_id=r1c
        )
        finish_suite_run(
            pid,
            sid1,
            case_runs=[
                {"case_id": c_pass, "run_id": r1a},
                {"case_id": c_flip, "run_id": r1b},
                {"case_id": c_known, "run_id": r1c},
            ],
        )

        sr2 = start_suite_run(pid, mode="tag", tag="smoke")
        self.assertEqual(sr2["status"], "ok")
        sid2 = sr2["suite_run"]["id"]
        r2a = add_run(
            pid, c_pass, result="pass", duration_ms=110, suite_run_id=sid2
        )["run"]["id"]
        r2b = add_run(
            pid, c_flip, result="fail", duration_ms=300, suite_run_id=sid2
        )["run"]["id"]
        r2c = add_run(
            pid,
            c_known,
            result="fail",
            duration_ms=55,
            failure_class="known_issue",
            suite_run_id=sid2,
        )["run"]["id"]
        set_known_issue_link(
            pid, c_known, note="Known flake", jira_key="KAN-99", run_id=r2c
        )
        finish_suite_run(
            pid,
            sid2,
            case_runs=[
                {"case_id": c_pass, "run_id": r2a},
                {"case_id": c_flip, "run_id": r2b},
                {"case_id": c_known, "run_id": r2c},
            ],
        )
        return {
            "plan_id": pid,
            "run_a": sid1,
            "run_b": sid2,
            "flip_case": c_flip,
            "known_case": c_known,
        }

    def test_history_lists_time_duration_pass_fail_tag(self):
        ids = self._seed_two_runs()
        out = list_suite_history(ids["plan_id"])
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["security_level"], "OFFICIAL")
        self.assertFalse(out["cross_level"])
        self.assertEqual(out["count"], 2)
        newest = out["runs"][0]
        self.assertEqual(newest["id"], ids["run_b"])
        self.assertEqual(newest["tag"], "smoke")
        self.assertTrue(newest.get("finished_at"))
        self.assertEqual(newest["pass"], 1)
        self.assertEqual(newest["fail"], 2)
        self.assertGreaterEqual(newest["duration_ms"] or 0, 100)
        self.assertGreaterEqual(newest["known_issues"], 1)

    def test_compare_shows_changed_results_and_known_labels(self):
        ids = self._seed_two_runs()
        out = compare_suite_runs(ids["plan_id"], ids["run_a"], ids["run_b"])
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["cross_level"])
        self.assertEqual(out["changed"], 1)
        self.assertEqual(out["unchanged"], 2)
        change = out["changes"][0]
        self.assertEqual(change["case_id"], ids["flip_case"])
        self.assertEqual(change["result_a"], "pass")
        self.assertEqual(change["result_b"], "fail")
        # Known case did not change result — still labelled in history summaries
        self.assertEqual(out["run_a"]["known_issues"], 1)
        self.assertEqual(out["run_b"]["known_issues"], 1)

    def test_compare_labels_known_when_changed(self):
        created = create_plan(name="Known change")
        pid = created["plan"]["id"]
        cid = add_case(pid, name="Known flip")["case"]["id"]
        s1 = start_suite_run(pid)["suite_run"]["id"]
        r1 = add_run(pid, cid, result="pass", suite_run_id=s1)["run"]["id"]
        finish_suite_run(pid, s1, case_runs=[{"case_id": cid, "run_id": r1}])
        s2 = start_suite_run(pid)["suite_run"]["id"]
        r2 = add_run(
            pid, cid, result="fail", failure_class="known_issue", suite_run_id=s2
        )["run"]["id"]
        set_known_issue_link(pid, cid, note="known", jira_key="KAN-7", run_id=r2)
        finish_suite_run(pid, s2, case_runs=[{"case_id": cid, "run_id": r2}])
        out = compare_suite_runs(pid, s1, s2)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["changed"], 1)
        self.assertTrue(out["changes"][0]["known_issue"])
        self.assertIn("known", out["changes"][0]["known_issue_label"] or "")

    def test_history_stays_in_active_level(self):
        ids = self._seed_two_runs()
        set_security_level("SECRET", confirm=True)
        self.assertEqual(get_security_level(), "SECRET")
        secret = create_plan(name="Secret history")
        spid = secret["plan"]["id"]
        cid = add_case(spid, name="Secret case")["case"]["id"]
        sid = start_suite_run(spid)["suite_run"]["id"]
        rid = add_run(spid, cid, result="pass", suite_run_id=sid)["run"]["id"]
        finish_suite_run(spid, sid, case_runs=[{"case_id": cid, "run_id": rid}])

        secret_hist = list_suite_history(spid)
        self.assertEqual(secret_hist["status"], "ok")
        self.assertEqual(secret_hist["security_level"], "SECRET")
        self.assertFalse(secret_hist["cross_level"])
        self.assertEqual(secret_hist["count"], 1)

        # OFFICIAL plan id is not visible under SECRET
        missing = list_suite_history(ids["plan_id"])
        self.assertNotEqual(missing.get("status"), "ok")

        set_security_level("OFFICIAL", confirm=True)
        official = list_suite_history(ids["plan_id"])
        self.assertEqual(official["status"], "ok")
        self.assertEqual(official["count"], 2)
        # SECRET plan not on OFFICIAL
        cross = list_suite_history(spid)
        self.assertNotEqual(cross.get("status"), "ok")

    def test_api_history_and_compare_and_desktop_ui_desk126(self):
        ids = self._seed_two_runs()
        client = TestClient(app)
        hist = client.get(f"/api/plans/{ids['plan_id']}/suite-history")
        body = hist.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertFalse(body.get("cross_level"))
        self.assertEqual(body.get("count"), 2)

        cmp_res = client.get(
            f"/api/plans/{ids['plan_id']}/suite-compare",
            params={"a": ids["run_a"], "b": ids["run_b"]},
        )
        cmp_body = cmp_res.json()
        self.assertEqual(cmp_body.get("status"), "ok")
        self.assertEqual(cmp_body.get("changed"), 1)

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk126", html)
        self.assertIn("desk126", desk)
        self.assertIn("plan-history-list", html)
        self.assertIn("plan-history-a", html)
        self.assertIn("plan-compare-btn", html)
        self.assertIn("plan-compare-out", html)
        self.assertIn("refreshSuiteHistory", js)
        self.assertIn("/suite-history", js)
        self.assertIn("/suite-compare", js)


if __name__ == "__main__":
    unittest.main()
