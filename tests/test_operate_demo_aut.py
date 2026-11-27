"""KAN-377 / KAN-378 — OPERATE-2 home-PC demo AUT fixture + golden-path seed."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


class OperateDemoFixtureTests(unittest.TestCase):
    def test_fixture_files_present_with_marker(self) -> None:
        from plugins.operate_demo import fixture_index_path, fixture_present

        present = fixture_present()
        self.assertTrue(present.get("ok"), present)
        self.assertTrue(present.get("exists"))
        self.assertTrue(present.get("marker"))
        index = fixture_index_path()
        self.assertTrue(index.is_file())
        text = index.read_text(encoding="utf-8")
        self.assertIn('data-operate-demo-aut="1"', text)
        self.assertIn("Operate Demo AUT", text)
        self.assertEqual(present.get("mount_path"), "/demo-aut")

    def test_demo_aut_url_shape(self) -> None:
        from plugins.operate_demo import demo_aut_url

        self.assertEqual(
            demo_aut_url(),
            "http://127.0.0.1:8765/demo-aut/",
        )
        self.assertEqual(
            demo_aut_url(host="localhost", port=9000),
            "http://localhost:9000/demo-aut/",
        )


class OperateDemoMountTests(unittest.TestCase):
    def test_demo_aut_served_by_fastapi(self) -> None:
        import main

        client = TestClient(main.app)
        resp = client.get("/demo-aut/")
        self.assertEqual(resp.status_code, 200)
        body = resp.text
        self.assertIn("Operate Demo AUT", body)
        self.assertIn('data-operate-demo-aut="1"', body)

    def test_demo_aut_index_html_direct(self) -> None:
        import main

        client = TestClient(main.app)
        resp = client.get("/demo-aut/index.html")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome, tester", resp.text)


class OperateDemoSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_seed_creates_smoke_plan_and_sets_target(self) -> None:
        from plugins.operate_demo import (
            FAIL_DEMO_TAG,
            INTENTIONAL_FAIL_TEXT,
            PLAN_NAME,
            SMOKE_TAG,
            seed_operate_demo,
        )
        from settings.store import load_settings

        out = seed_operate_demo(level="OFFICIAL", set_target_url=True)
        self.assertEqual(out.get("status"), "ok", out)
        self.assertTrue(out.get("created"))
        self.assertEqual(out.get("case_count"), 2)
        self.assertTrue(out.get("smoke_case_id"))
        self.assertTrue(out.get("fail_case_id"))
        self.assertEqual(
            (load_settings().get("target_url") or "").rstrip("/"),
            "http://127.0.0.1:8765/demo-aut",
        )

        plan = out.get("plan") or {}
        self.assertEqual(plan.get("name"), PLAN_NAME)
        cases = list((plan.get("suite") or {}).get("cases") or [])
        self.assertEqual(len(cases), 2)
        smoke = [c for c in cases if SMOKE_TAG in (c.get("tags") or []) and FAIL_DEMO_TAG not in (c.get("tags") or [])]
        fail = [c for c in cases if FAIL_DEMO_TAG in (c.get("tags") or [])]
        self.assertEqual(len(smoke), 1)
        self.assertEqual(len(fail), 1)
        self.assertIn("Operate Demo AUT", smoke[0].get("note") or "")
        self.assertIn(INTENTIONAL_FAIL_TEXT, fail[0].get("note") or "")

    def test_seed_idempotent(self) -> None:
        from plugins.operate_demo import seed_operate_demo
        from plans.store import list_plans

        first = seed_operate_demo(level="OFFICIAL", set_target_url=True)
        second = seed_operate_demo(level="OFFICIAL", set_target_url=True)
        self.assertEqual(first.get("status"), "ok", first)
        self.assertEqual(second.get("status"), "ok", second)
        self.assertTrue(first.get("created"))
        self.assertFalse(second.get("created"))
        self.assertEqual(first.get("plan_id"), second.get("plan_id"))
        plans = list_plans("OFFICIAL").get("plans") or []
        named = [p for p in plans if p.get("name") == "OPERATE golden path"]
        self.assertEqual(len(named), 1)

    def test_seed_refuses_missing_fixture(self) -> None:
        from plugins import operate_demo as od

        with patch.object(od, "fixture_present", return_value={"ok": False, "index": "x"}):
            out = od.seed_operate_demo(set_target_url=False)
        self.assertEqual(out.get("status"), "error")
        self.assertIn("fixture", (out.get("message") or "").lower())


class DailyLoopDocTests(unittest.TestCase):
    def test_daily_loop_names_home_pc_aut_only(self) -> None:
        text = (ROOT / "docs" / "ops" / "DAILY_LOOP.md").read_text(encoding="utf-8")
        self.assertIn("fixtures/operate_demo", text)
        self.assertIn("seed_operate_demo.py", text)
        self.assertIn("http://127.0.0.1:8765/demo-aut/", text)
        self.assertIn("desktop_app.py", text)
        lower = text.lower()
        self.assertIn("never require vpn", lower)
        self.assertIn("home pc", lower)
        self.assertIn("employer browser", lower)
        self.assertIn("not your workplace app", lower)
        self.assertNotIn("company vpn required", lower)


if __name__ == "__main__":
    unittest.main()
