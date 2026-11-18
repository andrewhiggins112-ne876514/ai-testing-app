"""Named environments (KAN-183 / D3 / FR-CONN-1 + FR-LEARN-2)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from plans.run_by_tag import run_cases_by_tag  # noqa: E402
from plans.store import add_case, create_plan, get_plan  # noqa: E402
from settings.environments import (  # noqa: E402
    activate_environment,
    list_environments,
    upsert_environment,
)
from settings.store import (  # noqa: E402
    get_security_level,
    load_settings,
    set_security_level,
    write_settings,
)


class NamedEnvironmentsTests(unittest.TestCase):
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

    def test_can_store_more_than_one_named_target(self):
        a = upsert_environment(
            name="local",
            target_url="https://local.example.com",
            activate=True,
        )
        self.assertEqual(a.get("status"), "ok")
        b = upsert_environment(
            name="staging",
            target_url="https://staging.example.com",
            activate=False,
        )
        self.assertEqual(b.get("status"), "ok")
        listed = list_environments()
        names = {e["name"] for e in listed.get("environments") or []}
        self.assertEqual(names, {"local", "staging"})
        self.assertEqual(listed.get("active_environment_name"), "local")
        self.assertFalse(listed.get("credentials_in_plan"))

    def test_switching_env_does_not_switch_security_level(self):
        self.assertEqual(get_security_level(), "OFFICIAL")
        upsert_environment(
            name="local",
            target_url="https://local.example.com",
            activate=True,
        )
        staging = upsert_environment(
            name="staging",
            target_url="https://staging.example.com",
            activate=False,
        )
        env_id = staging["environment"]["id"]
        switched = activate_environment(env_id)
        self.assertEqual(switched.get("status"), "ok")
        self.assertTrue(switched.get("level_unchanged"))
        self.assertEqual(switched.get("security_level"), "OFFICIAL")
        self.assertEqual(get_security_level(), "OFFICIAL")
        data = load_settings()
        self.assertEqual(data.get("target_url"), "https://staging.example.com")
        # Secrets keys remain level-scoped and are not written onto plans.
        self.assertNotIn("jira_api_token", staging.get("environment") or {})

    def test_activate_keeps_secret_level_when_secret(self):
        set_security_level("SECRET", confirm=True)
        upsert_environment(
            name="secret-local",
            target_url="https://secret.example.com",
            activate=True,
        )
        other = upsert_environment(
            name="secret-staging",
            target_url="https://secret-staging.example.com",
            activate=False,
        )
        out = activate_environment(other["environment"]["id"])
        self.assertEqual(out.get("security_level"), "SECRET")
        self.assertTrue(out.get("level_unchanged"))
        self.assertEqual(get_security_level(), "SECRET")

    @patch("plugins.playwright_runner.run_playwright", new_callable=AsyncMock)
    @patch("plans.run_case._check_target")
    def test_run_records_environment_name(self, mock_tgt, mock_pw):
        mock_tgt.return_value = {"up": True, "message": "ok"}
        mock_pw.return_value = {
            "status": "pass",
            "playwright_mode": "headed",
            "error": None,
            "steps": [{"action": "goto", "status": "pass"}],
            "screenshot": r"C:\tmp\env.png",
        }
        upsert_environment(
            name="staging",
            target_url="https://staging.example.com",
            activate=True,
        )
        created = create_plan("EnvRun")
        pid = created["plan"]["id"]
        add_case(pid, "A", tags=["smoke"])
        import asyncio

        out = asyncio.run(run_cases_by_tag(pid, "smoke"))
        self.assertEqual(out.get("status"), "ok")
        plan = get_plan(pid)["plan"]
        suite_run = (plan.get("suite_runs") or [])[-1]
        self.assertEqual(suite_run.get("environment_name"), "staging")
        case = (plan.get("suite") or {}).get("cases") or []
        run = (case[0].get("runs") or [])[-1]
        self.assertEqual(run.get("environment_name"), "staging")
        # Plan must not receive credential fields from the environment switch.
        blob = str(plan)
        self.assertNotIn("jira_api_token", blob)
        self.assertNotIn("password", blob.lower())

    def test_api_and_desktop_ui_desk94(self):
        client = TestClient(main.app)
        created = client.post(
            "/api/environments",
            json={
                "name": "local",
                "target_url": "https://local.example.com",
                "activate": True,
            },
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json().get("status"), "ok")
        listed = client.get("/api/environments")
        self.assertEqual(listed.status_code, 200)
        body = listed.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("active_environment_name"), "local")
        self.assertTrue(body.get("level_unchanged"))
        settings = client.get("/api/app-settings")
        self.assertEqual(settings.status_code, 200)
        sbody = settings.json()
        self.assertEqual(sbody.get("active_environment_name"), "local")
        self.assertTrue(any(e.get("name") == "local" for e in sbody.get("named_environments") or []))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk94", html)
        self.assertIn("desk94", desk)
        self.assertIn("set-env-active", html)
        self.assertIn("plan-env-active", html)
        self.assertIn("/api/environments", js)
        self.assertIn("Named environments", html)


if __name__ == "__main__":
    unittest.main()
