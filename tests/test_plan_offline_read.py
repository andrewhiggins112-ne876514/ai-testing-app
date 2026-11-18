"""Read last plan while Jira is down (KAN-201 / E5 / FR-CONN-1 + FR-PLAN-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from plans.offline_read import (  # noqa: E402
    annotate_trace_rows,
    offline_plan_view,
    offline_read_status,
)
from plans.search import search_plans  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    create_plan,
    upsert_jira_snapshot,
)
from plans.traceability import plan_traceability_matrix  # noqa: E402
from settings.store import write_settings  # noqa: E402


class PlanOfflineReadTests(unittest.TestCase):
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

    def _seed_plan(self):
        created = create_plan(
            name="Offline readable plan",
            intent="last plan while Jira down",
            sources={"jira_keys": ["KAN-201"]},
        )
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        case = add_case(pid, name="E5 case", jira_key="KAN-201", tags=["smoke"])
        self.assertEqual(case["status"], "ok")
        cid = case["case"]["id"]
        run = add_run(
            pid,
            cid,
            result="fail",
            failure_class="product_bug",
            finished_at="2026-11-17T12:00:00+00:00",
        )
        self.assertEqual(run["status"], "ok")
        snap = upsert_jira_snapshot(
            pid,
            "KAN-201",
            summary="E5 Read last plan while Jira is down",
            acceptance_criteria="- Search and matrix work offline",
        )
        self.assertEqual(snap["status"], "ok")
        return pid, cid

    def test_offline_status_disables_network_actions(self):
        with patch("plans.offline_read.degraded_status") as mock_deg:
            mock_deg.return_value = {
                "jira_up": False,
                "messages": {"jira": "Jira timed out."},
                "security_level": "OFFICIAL",
                "plans_available": True,
            }
            status = offline_read_status(probe=True)
        self.assertTrue(status["offline"])
        self.assertFalse(status["jira_available"])
        self.assertTrue(status["search_works_offline"])
        self.assertTrue(status["matrix_works_offline"])
        self.assertFalse(status["jira_write_while_offline"])
        disabled = status["network_actions_disabled"]
        self.assertGreaterEqual(len(disabled), 4)
        ids = {a["id"] for a in disabled}
        self.assertIn("draft_from_story", ids)
        self.assertIn("jira_write", ids)
        for action in disabled:
            self.assertFalse(action["enabled"])
            self.assertTrue(action["reason"])

    def test_search_and_matrix_work_with_fetch_times_when_jira_down(self):
        pid, _cid = self._seed_plan()
        with patch("plans.offline_read.degraded_status") as mock_deg:
            mock_deg.return_value = {
                "jira_up": False,
                "messages": {"jira": "Jira unreachable."},
                "security_level": "OFFICIAL",
                "plans_available": True,
            }
            view = offline_plan_view(pid)
        self.assertEqual(view["status"], "ok")
        self.assertTrue(view["offline"])
        self.assertEqual(view["stored_key_count"], 1)
        row = view["stored_keys"][0]
        self.assertEqual(row["jira_key"], "KAN-201")
        self.assertEqual(row["last_result"], "fail")
        self.assertTrue(row.get("snapshot_captured_at"))
        self.assertIn("2026-11-17T12:00:00", row["fetch_time_label"])
        self.assertIn("fetched", row["fetch_time_label"])

        found = search_plans("KAN-201")
        self.assertTrue(found["search_works_offline"])
        self.assertGreaterEqual(found["count"], 1)
        hit = found["hits"][0]
        self.assertTrue(hit.get("fetch_time_label"))
        self.assertIn("fetched", hit["fetch_time_label"])

        matrix = plan_traceability_matrix(pid)
        self.assertTrue(matrix["matrix_works_offline"])
        self.assertGreaterEqual(matrix["row_count"], 1)
        mrow = matrix["rows"][0]
        self.assertEqual(mrow["story_key"], "KAN-201")
        self.assertTrue(mrow.get("fetch_time_label"))
        self.assertIn("fetched", mrow["fetch_time_label"])

    def test_annotate_trace_uses_snapshot_summary(self):
        rows = annotate_trace_rows(
            {
                "jira_snapshots": {
                    "KAN-9": {
                        "summary": "From snapshot",
                        "acceptance_criteria": "ac",
                        "captured_at": "2026-01-01T00:00:00+00:00",
                        "stale": False,
                    }
                },
                "suite": {"cases": [{"id": "c1", "jira_key": "KAN-9", "name": "", "runs": []}]},
            },
            [{"story_key": "KAN-9", "summary": "", "case_count": 1, "last_result": "not_loaded"}],
        )
        self.assertEqual(rows[0]["summary"], "From snapshot")
        self.assertEqual(rows[0]["snapshot_captured_at"], "2026-01-01T00:00:00+00:00")

    def test_api_offline_read_and_desktop_ui_desk98(self):
        pid, _ = self._seed_plan()
        client = TestClient(main.app)
        with patch("plans.offline_read.degraded_status") as mock_deg:
            mock_deg.return_value = {
                "jira_up": False,
                "messages": {"jira": "Jira down for test."},
                "security_level": "OFFICIAL",
                "plans_available": True,
            }
            res = client.get("/api/plans/offline-read")
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertTrue(body["offline"])
            self.assertTrue(body["search_works_offline"])
            self.assertFalse(body["jira_write_while_offline"])

            plan_res = client.get(f"/api/plans/{pid}/offline-read")
            self.assertEqual(plan_res.status_code, 200)
            plan_body = plan_res.json()
            self.assertEqual(plan_body["status"], "ok")
            self.assertGreaterEqual(plan_body["stored_key_count"], 1)

            search = client.get("/api/plans/search", params={"q": "KAN-201"})
            self.assertEqual(search.status_code, 200)
            self.assertTrue(search.json().get("search_works_offline"))
            self.assertTrue(search.json()["hits"][0].get("fetch_time_label"))

            trace = client.get(f"/api/plans/{pid}/traceability")
            self.assertEqual(trace.status_code, 200)
            tbody = trace.json()
            self.assertTrue(tbody.get("matrix_works_offline"))
            self.assertTrue(tbody["rows"][0].get("fetch_time_label"))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk98", html)
        self.assertIn("desk98", desk)
        self.assertIn("plan-offline-banner", html)
        self.assertIn("refreshOfflineReadBanner", js)
        self.assertIn("applyOfflineNetworkActions", js)
        self.assertIn("fetch_time_label", js)
        self.assertIn("/api/plans/offline-read", js)


if __name__ == "__main__":
    unittest.main()
