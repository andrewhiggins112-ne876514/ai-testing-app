"""Regression: GET /api/plans must list plans (restored after KAN-375 regression)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class PlansListApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_get_plans_lists_created_plan(self) -> None:
        import main
        from plans.store import create_plan

        created = create_plan("OPERATE golden path", intent="regression list")
        self.assertEqual(created.get("status"), "ok")
        pid = created["plan"]["id"]

        client = TestClient(main.app)
        res = client.get("/api/plans")
        self.assertEqual(res.status_code, 200, res.text)
        payload = res.json()
        plans = payload.get("plans") or []
        ids = [p.get("id") for p in plans]
        names = [p.get("name") for p in plans]
        self.assertIn(pid, ids)
        self.assertIn("OPERATE golden path", names)

    def test_post_plans_still_creates(self) -> None:
        import main

        client = TestClient(main.app)
        res = client.post("/api/plans", json={"name": "ListApiCreate", "intent": "x"})
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertTrue((body.get("plan") or {}).get("id"))

    def test_open_trace_route_still_present(self) -> None:
        """KAN-375 open-trace must remain after restoring GET /api/plans."""
        import main

        paths = {route.path for route in main.app.routes}
        self.assertIn("/api/plans", paths)
        self.assertIn("/api/playwright-trace/open", paths)


if __name__ == "__main__":
    unittest.main()
