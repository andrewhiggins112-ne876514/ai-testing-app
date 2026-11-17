"""Seed data and fixtures on plan cases (KAN-223 / G4 / FR-PLUG-1)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
from plans.run_case import case_detail, run_single_case
from plans.seed_case import add_seed_case, parse_seed_ref
from plans.store import create_plan
from plugins.seed_fixture import (
    apply_seed_fixture,
    default_fixture_name,
    ensure_default_fixture,
    fixtures_dir,
)


class PlanSeedFixtureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_seed_ref(self):
        parsed = parse_seed_ref('{"fixture":"seed_user.json"}')
        self.assertEqual(parsed["fixture"], "seed_user.json")
        bare = parse_seed_ref("seed_user.json")
        self.assertEqual(bare["fixture"], "seed_user.json")

    def test_fixture_is_level_scoped_named_file(self):
        path = ensure_default_fixture(level="OFFICIAL")
        self.assertTrue(path.is_file())
        folder = fixtures_dir(level="OFFICIAL")
        self.assertEqual(path.parent, folder)
        self.assertIn("fixtures", str(folder).replace("\\", "/"))
        self.assertIn("OFFICIAL", str(folder))
        secret = fixtures_dir(level="SECRET")
        self.assertNotEqual(folder.resolve(), secret.resolve())

    def test_add_seed_case_names_fixture(self):
        created = create_plan("SeedSuite")
        pid = created["plan"]["id"]
        out = add_seed_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "seed")
        parsed = parse_seed_ref(case["source"]["ref"])
        self.assertEqual(parsed["fixture"], default_fixture_name())
        detail = case_detail(out["plan"], case["id"])
        self.assertEqual(detail.get("runner"), "seed_fixture")
        self.assertEqual(detail.get("seed_fixture"), default_fixture_name())
        self.assertTrue(detail.get("seed_case"))

    def test_run_stores_fixture_name(self):
        created = create_plan("SeedRun")
        pid = created["plan"]["id"]
        cid = add_seed_case(pid, "Named seed")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("runner"), "seed_fixture")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertEqual(run.get("seed_fixture"), default_fixture_name())
        note = run.get("note") or ""
        self.assertIn("seed_fixture=", note)
        seed = out.get("seed") or {}
        self.assertEqual(seed.get("fixture"), default_fixture_name())

    def test_missing_fixture_fails_as_environment(self):
        created = create_plan("MissingSeed")
        pid = created["plan"]["id"]
        cid = add_seed_case(pid, fixture="does_not_exist.json")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "error")
        self.assertEqual(run.get("failure_class"), "environment")
        self.assertEqual(run.get("seed_fixture"), "does_not_exist.json")
        seed = apply_seed_fixture(fixture="does_not_exist.json")
        self.assertEqual(seed.get("status"), "fail")
        self.assertEqual(seed.get("classification"), "environment")

    def test_no_silent_global_injection(self):
        # Empty name + no steps → fail environment; never auto-picks default.
        seed = apply_seed_fixture(fixture="")
        self.assertEqual(seed.get("status"), "fail")
        self.assertEqual(seed.get("classification"), "environment")
        self.assertIn("no seed fixture", (seed.get("error") or "").lower())
        # Inline steps without a name also refuse silent injection.
        seed2 = apply_seed_fixture(fixture="", steps=[{"action": "ensure_user"}])
        self.assertEqual(seed2.get("status"), "fail")
        self.assertIn("silent", (seed2.get("error") or "").lower())

    def test_api_seed_and_ui_desk80(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "SeedApi"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/seed", json={})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        case = body.get("case") or {}
        self.assertEqual(case.get("source", {}).get("kind"), "seed")
        parsed = parse_seed_ref(case.get("source", {}).get("ref") or "")
        self.assertEqual(parsed["fixture"], default_fixture_name())

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        self.assertIn("plan-add-seed-btn", html)
        self.assertIn("desk80", html)
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk80", desk)
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        self.assertIn("cases/seed", js)
        self.assertIn("plan-add-seed-btn", js)


if __name__ == "__main__":
    unittest.main()
