"""KAN-99 / NFR §4.3 — local audit log for confirmed Jira writes."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import jira_plugin  # noqa: E402
from plugins.jira_plugin import (  # noqa: E402
    create_bug,
    create_issue,
    jira_write_log_path,
    resolve_create,
)


def _response(key, status=201):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = {"key": key}
    return response


def _client(response):
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    client.get = AsyncMock(side_effect=AssertionError("GET not allowed"))
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class JiraWriteAuditTests(unittest.TestCase):
    def setUp(self):
        jira_plugin._PENDING.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.local = Path(self.tmp.name) / "local"
        self.local.mkdir()
        self._old = {
            key: os.environ.get(key)
            for key in ("AI_TESTING_SETTINGS", "JIRA_API_TOKEN", "JIRA_EMAIL", "LOCALAPPDATA")
        }
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ["LOCALAPPDATA"] = str(self.local)
        os.environ.pop("JIRA_API_TOKEN", None)
        os.environ.pop("JIRA_EMAIL", None)
        self.token = "secret-token-do-not-echo"

    def tearDown(self):
        jira_plugin._PENDING.clear()
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _configure(self):
        os.environ["JIRA_API_TOKEN"] = self.token
        os.environ["JIRA_EMAIL"] = "qa@example.com"
        self.settings.write_text(
            json.dumps(
                {
                    "jira_base_url": "https://jira.example.com",
                    "jira_url": "https://wrong.example.com",
                    "jira_project": "KAN",
                }
            ),
            encoding="utf-8",
        )

    def _read_audit(self):
        path = jira_write_log_path()
        if not path.is_file():
            return []
        lines = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                lines.append(json.loads(raw))
        return lines

    def test_confirmed_create_writes_audit_without_secrets(self):
        self._configure()
        asyncio.run(
            create_issue(
                project="KAN",
                summary="Audit create",
                description="plain",
                session_id="s-audit-yes",
            )
        )
        client = _client(_response("KAN-501"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(resolve_create("s-audit-yes", "yes"))
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["key"], "KAN-501")
        entries = self._read_audit()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["action"], "create")
        self.assertEqual(entry["issue_key"], "KAN-501")
        self.assertEqual(entry["session_id"], "s-audit-yes")
        self.assertEqual(entry["status"], "created")
        self.assertIn("timestamp", entry)
        blob = json.dumps(entry)
        self.assertNotIn(self.token, blob)
        self.assertNotIn("api_token", blob.lower())

    def test_declined_confirm_writes_no_success_audit(self):
        self._configure()
        asyncio.run(
            create_bug(
                symptom="X",
                actual="Y",
                replication_steps=["Z"],
                session_id="s-audit-no",
            )
        )
        client = _client(_response("KAN-1"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            cancelled = asyncio.run(resolve_create("s-audit-no", "no"))
        self.assertEqual(cancelled["status"], "cancelled")
        client.post.assert_not_called()
        self.assertEqual(self._read_audit(), [])
        self.assertFalse(jira_write_log_path().exists())


if __name__ == "__main__":
    unittest.main()
