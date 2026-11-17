"""Search plans, cases, and failures (KAN-173 / C9 / FR-PLAN-1)."""
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
from plans.search import search_plans  # noqa: E402
from plans.store import add_case, add_run, create_plan  # noqa: E402
from settings.store import get_security_level, set_security_level, write_settings  # noqa: E402


class PlanSearchTests(unittest.TestCase):
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
        official = create_plan(
            name="Login regression suite",
            intent="cover login",
            sources={"jira_keys": ["KAN-9"]},
        )
        self.assertEqual(official["status"], "ok")
        pid = official["plan"]["id"]
        c1 = add_case(
            pid,
            name="Valid credentials",
            jira_key="KAN-9",
            tags=["smoke", "login"],
        )
        self.assertEqual(c1["status"], "ok")
        cid1 = c1["case"]["id"]
        run = add_run(pid, cid1, result="fail", failure_class="product_bug")
        self.assertEqual(run["status"], "ok")
        c2 = add_case(
            pid,
            name="Forgot password link",
            jira_key="KAN-10",
            tags=["regression"],
        )
        self.assertEqual(c2["status"], "ok")

        set_security_level("SECRET", confirm=True)
        self.assertEqual(get_security_level(), "SECRET")
        secret = create_plan(name="Secret vault checks", intent="secret only")
        self.assertEqual(secret["status"], "ok")
        spid = secret["plan"]["id"]
        sc = add_case(spid, name="Vault unlock", jira_key="KAN-99", tags=["smoke"])
        self.assertEqual(sc["status"], "ok")
        set_security_level("OFFICIAL", confirm=True)
        self.assertEqual(get_security_level(), "OFFICIAL")
        return {
            "official_plan_id": pid,
            "case_id": cid1,
            "case2_id": c2["case"]["id"],
            "secret_plan_id": spid,
        }

    def test_matches_plan_name_case_name_jira_tag_failure_class(self):
        ids = self._seed()
        by_plan = search_plans("login regression")
        self.assertEqual(by_plan["status"], "ok")
        self.assertEqual(by_plan["security_level"], "OFFICIAL")
        self.assertFalse(by_plan["cross_level"])
        self.assertGreaterEqual(by_plan["count"], 1)
        self.assertTrue(
            any("plan_name" in (h.get("matched_fields") or []) for h in by_plan["hits"])
        )

        by_case = search_plans("forgot password")
        self.assertEqual(by_case["count"], 1)
        self.assertEqual(by_case["hits"][0]["case_id"], ids["case2_id"])
        self.assertIn("case_name", by_case["hits"][0]["matched_fields"])

        by_jira = search_plans("kan-9")
        self.assertGreaterEqual(by_jira["count"], 1)
        self.assertTrue(
            any(h.get("jira_key") == "KAN-9" for h in by_jira["hits"])
        )

        by_tag = search_plans("smoke")
        self.assertGreaterEqual(by_tag["count"], 1)
        self.assertTrue(
            any("tag" in (h.get("matched_fields") or []) for h in by_tag["hits"])
        )
        # SECRET smoke case must not appear while OFFICIAL is active
        self.assertFalse(
            any(h.get("plan_id") == ids["secret_plan_id"] for h in by_tag["hits"])
        )

        by_fc = search_plans("product_bug")
        self.assertGreaterEqual(by_fc["count"], 1)
        hit = by_fc["hits"][0]
        self.assertEqual(hit["case_id"], ids["case_id"])
        self.assertIn("failure_class", hit["matched_fields"])
        self.assertEqual(hit["failure_class"], "product_bug")

    def test_active_level_only_no_cross_level(self):
        ids = self._seed()
        out = search_plans("vault")
        self.assertEqual(out["count"], 0)
        self.assertFalse(out["cross_level"])

        set_security_level("SECRET", confirm=True)
        secret_hits = search_plans("vault")
        self.assertGreaterEqual(secret_hits["count"], 1)
        self.assertEqual(secret_hits["security_level"], "SECRET")
        self.assertTrue(
            any(h.get("plan_id") == ids["secret_plan_id"] for h in secret_hits["hits"])
        )
        self.assertFalse(
            any(h.get("plan_id") == ids["official_plan_id"] for h in secret_hits["hits"])
        )
        set_security_level("OFFICIAL", confirm=True)

    def test_empty_query_returns_no_hits(self):
        self._seed()
        out = search_plans("  ")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["count"], 0)
        self.assertEqual(out["hits"], [])

    def test_api_search_and_desktop_ui_desk73(self):
        ids = self._seed()
        client = TestClient(app)
        res = client.get("/api/plans/search", params={"q": "product_bug"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertGreaterEqual(body["count"], 1)
        self.assertEqual(body["hits"][0]["case_id"], ids["case_id"])

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk73", html)
        self.assertIn("desk73", desk)
        self.assertIn("plan-search-q", html)
        self.assertIn("plan-search-btn", html)
        self.assertIn("plan-search-results", html)
        self.assertIn("/api/plans/search", js)
        self.assertIn("openPlanSearchHit", js)
        self.assertIn("runPlanSearch", js)


if __name__ == "__main__":
    unittest.main()
