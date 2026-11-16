"""Connect-once health checks (KAN-127 / FR-CONN-1)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.connection_health import connection_checklist, connection_health  # noqa: E402
from settings.store import (  # noqa: E402
    load_settings,
    set_security_level,
    write_settings,
)


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class ConnectionHealthTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings(load_settings())

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_checklist_uses_existing_keys_and_hides_secrets(self):
        data = load_settings()
        data["jira_url"] = "https://jira.example.com"
        data["jira_project"] = "KAN"
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        data["target_url"] = "https://app.example.com"
        data["target_app_path"] = r"C:\Apps\Demo.exe"
        data["api_endpoint"] = "amqps://broker.example.com/vhost"
        write_settings(data)

        checklist = connection_checklist()
        self.assertEqual(checklist["jira_url"], "https://jira.example.com")
        self.assertEqual(checklist["jira_project"], "KAN")
        self.assertEqual(checklist["target_url"], "https://app.example.com")
        self.assertEqual(checklist["target_app_path"], r"C:\Apps\Demo.exe")
        self.assertEqual(checklist["api_endpoint"], "amqps://broker.example.com/vhost")
        self.assertTrue(checklist["jira_credentials_configured"])
        self.assertTrue(checklist["level_switch_requires_confirm"])
        self.assertNotIn("super-secret-token-value", str(checklist))
        self.assertNotIn("agent@example.com", str(checklist))

    def test_level_switch_still_requires_confirm(self):
        first = set_security_level("SECRET", confirm=False)
        self.assertEqual(first.get("status"), "confirmation_required")
        self.assertEqual(load_settings().get("security_level"), "OFFICIAL")
        second = set_security_level("SECRET", confirm=True)
        self.assertEqual(second.get("status"), "updated")
        self.assertEqual(load_settings().get("security_level"), "SECRET")

    @patch("settings.connection_health._client")
    def test_health_reports_up_down_without_secrets(self, client_cls):
        data = load_settings()
        data["jira_url"] = "https://jira.example.com"
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "super-secret-token-value"
        data["target_url"] = "https://app.example.com/login"
        write_settings(data)

        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client

        def _get(url, **kwargs):
            if "/myself" in url:
                return _FakeResponse(200, {"displayName": "Tester"})
            if "/api/tags" in url:
                return _FakeResponse(200, {"models": [{"name": "qwen2.5-coder:7b"}]})
            if "app.example.com" in url:
                return _FakeResponse(200)
            return _FakeResponse(500)

        client.get.side_effect = _get
        client.head.side_effect = lambda url, **kwargs: _FakeResponse(200)

        payload = connection_health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["overall"], "up")
        by_id = {c["id"]: c for c in payload["checks"]}
        self.assertTrue(by_id["jira"]["up"])
        self.assertTrue(by_id["ollama"]["up"])
        self.assertTrue(by_id["target"]["up"])
        blob = str(payload)
        self.assertNotIn("super-secret-token-value", blob)
        self.assertNotIn("agent@example.com", blob)

    @patch("settings.connection_health._client")
    def test_health_marks_unreachable_as_down(self, client_cls):
        data = load_settings()
        data["jira_url"] = "https://jira.example.com"
        data["jira_email"] = "agent@example.com"
        data["jira_api_token"] = "tok"
        data["target_url"] = "https://down.example.com"
        write_settings(data)

        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client

        import httpx

        client.get.side_effect = httpx.ConnectError("refused")
        client.head.side_effect = httpx.ConnectError("refused")

        payload = connection_health()
        self.assertIn(payload["overall"], {"down", "degraded"})
        for check in payload["checks"]:
            self.assertFalse(check["up"])
        self.assertNotIn("tok", str(payload))

    def test_api_endpoint_returns_health(self):
        from main import app

        with patch("settings.connection_health._client") as client_cls:
            client = MagicMock()
            client_cls.return_value.__enter__.return_value = client
            client.get.side_effect = lambda url, **kwargs: _FakeResponse(
                200, {"models": []} if "/api/tags" in url else {}
            )
            client.head.side_effect = lambda url, **kwargs: _FakeResponse(200)

            http = TestClient(app)
            res = http.get("/api/connection-health")
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body.get("status"), "ok")
            self.assertIn("checks", body)
            self.assertIn("checklist", body)
            ids = {c["id"] for c in body["checks"]}
            self.assertEqual(ids, {"jira", "ollama", "target"})
            self.assertNotIn("jira_api_token", str(body))


if __name__ == "__main__":
    unittest.main()
