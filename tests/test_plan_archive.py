"""Archive a case without deleting history (KAN-177 / C11 / FR-PLAN-2)."""
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
from plans.run_case import case_detail  # noqa: E402
from plans.store import (  # noqa: E402
    add_case,
    add_run,
    cases_for_run,
    create_plan,
    get_plan,
    update_case,
)
from settings.store import write_settings  # noqa: E402


class PlanArchiveTests(unittest.TestCase):
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

    def test_archive_hides_from_runnable_keeps_runs_unarchive_restores(self):
        created = create_plan("Archive suite", intent="c11")
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        active = add_case(pid, "Keep me", jira_key="KAN-177")["case"]
        obsolete = add_case(pid, "Obsolete story", jira_key="KAN-177")["case"]

        recorded = add_run(
            pid,
            obsolete["id"],
            result="fail",
            duration_ms=42,
            failure_class="product_bug",
            evidence=["obs.png"],
            note="pre-archive evidence",
        )
        self.assertEqual(recorded["status"], "ok", recorded)
        self.assertEqual(len(recorded["case"]["runs"]), 1)

        archived = update_case(pid, obsolete["id"], archived=True)
        self.assertEqual(archived["status"], "ok", archived)
        self.assertTrue(archived["case"]["archived"])
        # Evidence / runs must survive archive (no hard delete).
        self.assertEqual(len(archived["case"]["runs"]), 1)
        self.assertEqual(archived["case"]["runs"][0]["result"], "fail")
        self.assertEqual(archived["case"]["runs"][0]["evidence"], ["obs.png"])

        runnable = cases_for_run(pid)
        self.assertEqual(runnable["status"], "ok", runnable)
        runnable_ids = [c["id"] for c in runnable["cases"]]
        self.assertIn(active["id"], runnable_ids)
        self.assertNotIn(obsolete["id"], runnable_ids)
        self.assertIn(obsolete["id"], runnable["skipped_case_ids"])

        client = TestClient(app)
        refused = client.post(f"/api/plans/{pid}/cases/{obsolete['id']}/run").json()
        self.assertEqual(refused.get("status"), "error")
        self.assertEqual(refused.get("error"), "case_archived")

        detail = case_detail(get_plan(pid)["plan"], obsolete["id"])
        self.assertTrue(detail["archived"])
        self.assertEqual(detail["run_count"], 1)
        self.assertEqual(detail["last_run"]["result"], "fail")

        restored = update_case(pid, obsolete["id"], archived=False)
        self.assertEqual(restored["status"], "ok", restored)
        self.assertFalse(restored["case"]["archived"])
        self.assertEqual(len(restored["case"]["runs"]), 1)

        runnable2 = cases_for_run(pid)
        self.assertIn(obsolete["id"], [c["id"] for c in runnable2["cases"]])

    def test_api_archive_and_desktop_ui_desk100(self):
        created = create_plan("API archive", intent="c11-api")
        pid = created["plan"]["id"]
        case = add_case(pid, "To archive")["case"]
        add_run(pid, case["id"], result="pass", evidence=["a.txt"])

        client = TestClient(app)
        res = client.post(
            f"/api/plans/{pid}/cases/{case['id']}",
            json={"archived": True},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok", body)
        self.assertTrue(body["case"]["archived"])
        self.assertEqual(len(body["case"]["runs"]), 1)

        detail = client.get(f"/api/plans/{pid}/cases/{case['id']}").json()
        self.assertTrue(detail["archived"])
        self.assertEqual(detail["run_count"], 1)

        un = client.post(
            f"/api/plans/{pid}/cases/{case['id']}",
            json={"archived": False},
        ).json()
        self.assertEqual(un["status"], "ok", un)
        self.assertFalse(un["case"]["archived"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk100", html)
        self.assertIn("desk100", desk)
        self.assertIn("plan-case-archived", html)
        self.assertIn("plan-show-archived", html)
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("planCaseArchived", js)
        self.assertIn("planShowArchived", js)
        self.assertIn("archived", js)


if __name__ == "__main__":
    unittest.main()
