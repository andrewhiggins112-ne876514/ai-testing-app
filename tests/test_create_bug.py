"""Mocked HTTP checks for create_bug (KAN-63 / FR-JIRA-4/5). No network."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import Agent  # noqa: E402
from plugins import jira_plugin  # noqa: E402
from plugins.jira_plugin import (  # noqa: E402
    build_bug_description,
    create_bug,
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


class CreateBugTests(unittest.TestCase):
    def setUp(self):
        jira_plugin._PENDING.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = {
            key: os.environ.get(key)
            for key in ("AI_TESTING_SETTINGS", "JIRA_API_TOKEN", "JIRA_EMAIL", "LOCALAPPDATA")
        }
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
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

    def _configure(self, **extra):
        os.environ["JIRA_API_TOKEN"] = self.token
        os.environ["JIRA_EMAIL"] = "qa@example.com"
        payload = {
            "jira_base_url": "https://jira.example.com",
            "jira_url": "https://wrong.example.com",
            "jira_project": "KAN",
            **extra,
        }
        self.settings.write_text(json.dumps(payload), encoding="utf-8")

    def test_build_description_sections_and_masks_secrets(self):
        body = build_bug_description(
            symptom="Login fails",
            expected="Dashboard",
            actual="api_token=abc123 still broken",
            environment="OFFICIAL",
            replication_steps=["Open app", "Click Sign in"],
            evidence_paths=[r"C:\shots\fail.png"],
        )
        self.assertIn("Symptom", body)
        self.assertIn("Replication steps", body)
        self.assertIn("1. Open app", body)
        self.assertIn("2. Click Sign in", body)
        self.assertIn("api_token=***", body)
        self.assertNotIn("abc123", body)

    def test_unconfigured_clear_message(self):
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_bug(
                    project="KAN",
                    symptom="Boom",
                    actual="Boom",
                    replication_steps=["Step one"],
                )
            )
        self.assertEqual(result["status"], "unconfigured")
        self.assertTrue(result.get("message"))
        self.assertNotIn(self.token, json.dumps(result))
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_preview_makes_no_post(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_bug(
                    symptom="Checkout total wrong",
                    expected="£10.00",
                    actual="£0.00",
                    environment="Windows desktop, OFFICIAL",
                    replication_steps=["Add item", "Open cart"],
                    evidence_paths=["D:/shots/a.png"],
                    classification="product_bug",
                    session_id="s-preview",
                )
            )
        self.assertEqual(result["status"], "confirmation_required")
        self.assertTrue(result["confirm_id"])
        self.assertEqual(result["preview"]["issue_type"], "Bug")
        self.assertEqual(result["preview"]["project"], "KAN")
        self.assertIn("Replication steps", result["preview"]["description_preview"])
        ctor.assert_not_called()
        self.assertIn("s-preview", jira_plugin._PENDING)

    def test_non_product_bug_refused(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_bug(
                    symptom="Flaky locator",
                    actual="timeout",
                    replication_steps=["Run again"],
                    classification="test_defect",
                )
            )
        self.assertEqual(result["status"], "error")
        self.assertIn("product_bug", result["message"])
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_yes_posts_bug_once(self):
        self._configure()
        asyncio.run(
            create_bug(
                project="kan",
                summary="Cart total regression",
                symptom="Total wrong",
                expected="£10",
                actual="£0",
                environment="OFFICIAL",
                replication_steps=["Add SKU", "Open cart"],
                relates_to="KAN-1",
                session_id="s-yes",
            )
        )
        client = _client(_response("KAN-200"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["key"], "KAN-200")
        # issue create + Relates link
        self.assertEqual(client.post.await_count, 2)
        create_call = client.post.await_args_list[0]
        self.assertTrue(create_call.args[0].endswith("/rest/api/3/issue"))
        fields = create_call.kwargs["json"]["fields"]
        self.assertEqual(fields["issuetype"]["name"], "Bug")
        self.assertEqual(fields["project"]["key"], "KAN")
        self.assertEqual(fields["summary"], "Cart total regression")
        desc_text = "\n".join(
            node["content"][0]["text"]
            for node in fields["description"]["content"]
            if node.get("content")
        )
        self.assertIn("Symptom", desc_text)
        self.assertIn("1. Add SKU", desc_text)
        link_call = client.post.await_args_list[1]
        self.assertTrue(link_call.args[0].endswith("/rest/api/3/issueLink"))
        self.assertEqual(link_call.kwargs["json"]["type"]["name"], "Relates")
        self.assertNotIn(self.token, json.dumps(result))
        again = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertIsNone(again)

    def test_no_confirmation_cancels_without_post(self):
        self._configure()
        asyncio.run(
            create_bug(
                symptom="X",
                actual="Y",
                replication_steps=["Z"],
                session_id="s-no",
            )
        )
        client = _client(_response("KAN-1"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            cancelled = asyncio.run(resolve_create("s-no", "no"))
        self.assertEqual(cancelled["status"], "cancelled")
        client.post.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_from_report_path(self):
        self._configure()
        local = Path(self.tmp.name) / "local"
        reports = local / "ai_testing_app" / "reports"
        reports.mkdir(parents=True)
        os.environ["LOCALAPPDATA"] = str(local)
        report = reports / "run1.json"
        report.write_text(
            json.dumps(
                {
                    "result": {
                        "status": "fail",
                        "error": "Expected text missing",
                        "title": "Shop",
                        "security_level": "OFFICIAL",
                        "screenshot": str(local / "shot.png"),
                        "classification": "product_bug",
                        "steps": [
                            {"action": "goto", "status": "pass"},
                            {"action": "expect_text", "selector": "text=Buy", "status": "fail"},
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_bug(report_path=str(report), session_id="s-report")
            )
        self.assertEqual(result["status"], "confirmation_required")
        self.assertIn("Expected text missing", result["preview"]["summary"])
        self.assertIn("Replication steps", result["preview"]["description_preview"])
        ctor.assert_not_called()

    def test_agent_tool_registered_and_confirm_flag_ignored(self):
        self._configure()
        agent = Agent()
        names = [tool["function"]["name"] for tool in agent.tools]
        self.assertIn("create_bug", names)
        call = {
            "function": {
                "name": "create_bug",
                "arguments": {
                    "symptom": "Fail",
                    "actual": "Fail",
                    "replication_steps": ["Do it"],
                    "confirm": True,
                },
            }
        }
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(agent._execute_tool(call, "confirm yes", "s-tool"))
        self.assertEqual(result["status"], "confirmation_required")
        ctor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
