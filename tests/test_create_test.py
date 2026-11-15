"""Mocked HTTP checks for create_test / update_status (KAN-65 / FR-JIRA-2/3/5). No network."""
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
    build_test_description,
    create_test,
    resolve_create,
    update_status,
)


def _response(key, status=201):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = {"key": key}
    return response


def _json_response(payload, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload
    return response


def _client(post_response=None, get_side_effect=None):
    client = MagicMock()
    client.post = AsyncMock(return_value=post_response or _response("KAN-100"))
    if get_side_effect is None:
        client.get = AsyncMock(side_effect=AssertionError("GET not allowed"))
    else:
        client.get = AsyncMock(side_effect=get_side_effect)
    client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class CreateTestUpdateStatusTests(unittest.TestCase):
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

    def test_build_description_sections_and_masks(self):
        body = build_test_description(
            story_key="KAN-65",
            steps=["Open story", "api_token=abc123 run pytest"],
            acceptance=["Given confirm, When create_test, Then linked"],
        )
        self.assertIn("Intro — verifies story KAN-65", body)
        self.assertIn("Test procedure", body)
        self.assertIn("1. Open story", body)
        self.assertIn("api_token=***", body)
        self.assertNotIn("abc123", body)
        self.assertIn("Acceptance criteria", body)

    def test_create_test_unconfigured(self):
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_test(story_key="KAN-65", steps=["Step one"])
            )
        self.assertEqual(result["status"], "unconfigured")
        self.assertTrue(result.get("message"))
        self.assertNotIn(self.token, json.dumps(result))
        ctor.assert_not_called()
        self.assertEqual(jira_plugin._PENDING, {})

    def test_create_test_preview_no_post(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(
                create_test(
                    story_key="kan-65",
                    steps=["Run pytest", "Check Relates link"],
                    acceptance=["Task labelled test"],
                    session_id="s-preview",
                )
            )
        self.assertEqual(result["status"], "confirmation_required")
        self.assertTrue(result["confirm_id"])
        self.assertEqual(result["preview"]["issue_type"], "Task")
        self.assertEqual(result["preview"]["labels"], ["test"])
        self.assertEqual(result["preview"]["relates_to"], "KAN-65")
        self.assertEqual(result["preview"]["project"], "KAN")
        self.assertIn("Test procedure", result["preview"]["description_preview"])
        ctor.assert_not_called()
        self.assertIn("s-preview", jira_plugin._PENDING)

    def test_create_test_requires_steps_or_acceptance(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(create_test(story_key="KAN-65"))
        self.assertEqual(result["status"], "error")
        self.assertIn("steps", result["message"].casefold())
        ctor.assert_not_called()

    def test_create_test_yes_posts_with_label_and_relates(self):
        self._configure()
        asyncio.run(
            create_test(
                story_key="KAN-65",
                summary="Test: create linked test tickets",
                steps=["Confirm create_test", "Assert label"],
                session_id="s-yes",
            )
        )
        client = _client(_response("KAN-200"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["key"], "KAN-200")
        self.assertEqual(client.post.await_count, 2)
        create_call = client.post.await_args_list[0]
        self.assertTrue(create_call.args[0].endswith("/rest/api/3/issue"))
        fields = create_call.kwargs["json"]["fields"]
        self.assertEqual(fields["issuetype"]["name"], "Task")
        self.assertEqual(fields["labels"], ["test"])
        self.assertEqual(fields["project"]["key"], "KAN")
        link_call = client.post.await_args_list[1]
        self.assertTrue(link_call.args[0].endswith("/rest/api/3/issueLink"))
        self.assertEqual(link_call.kwargs["json"]["type"]["name"], "Relates")
        self.assertEqual(link_call.kwargs["json"]["outwardIssue"]["key"], "KAN-65")
        self.assertNotIn(self.token, json.dumps(result))
        again = asyncio.run(resolve_create("s-yes", "yes"))
        self.assertIsNone(again)

    def test_create_test_no_confirm_cancels(self):
        self._configure()
        asyncio.run(create_test(story_key="KAN-65", steps=["A"], session_id="s-no"))
        client = _client(_response("KAN-1"))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            cancelled = asyncio.run(resolve_create("s-no", "no"))
        self.assertEqual(cancelled["status"], "cancelled")
        client.post.assert_not_called()

    def _update_gets(self, labels=("test",), current="To Do", transitions=None):
        if transitions is None:
            transitions = [
                {"id": "31", "name": "Done", "to": {"name": "Done"}},
                {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
            ]

        def side_effect(url, *args, **kwargs):
            if url.endswith("/transitions"):
                return _json_response({"transitions": transitions})
            return _json_response(
                {
                    "fields": {
                        "labels": list(labels),
                        "status": {"name": current},
                        "issuetype": {"name": "Task"},
                        "summary": "Test: cover KAN-65",
                    }
                }
            )

        return side_effect

    def test_update_status_preview_no_write(self):
        self._configure()
        client = _client(get_side_effect=self._update_gets())
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(
                update_status(
                    issue_key="kan-66",
                    coverage_evidence="pytest tests/test_create_test.py — 8 passed",
                    pytest_cmd="pytest tests/test_create_test.py -v",
                    session_id="s-upd",
                )
            )
        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["preview"]["issue_key"], "KAN-66")
        self.assertEqual(result["preview"]["target"], "Done")
        self.assertIn("test", result["preview"]["labels"])
        self.assertIn("Coverage evidence", result["preview"]["coverage_preview"])
        client.post.assert_not_called()

    def test_update_status_requires_evidence(self):
        self._configure()
        with patch("plugins.jira_plugin.httpx.AsyncClient") as ctor:
            result = asyncio.run(update_status(issue_key="KAN-66"))
        self.assertEqual(result["status"], "error")
        self.assertIn("coverage", result["message"].casefold())
        ctor.assert_not_called()

    def test_update_status_rejects_non_test_label(self):
        self._configure()
        client = _client(get_side_effect=self._update_gets(labels=["other"]))
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=client):
            result = asyncio.run(
                update_status(
                    issue_key="KAN-66",
                    coverage_evidence="all good",
                    session_id="s-bad-label",
                )
            )
        self.assertEqual(result["status"], "error")
        self.assertIn("labelled", result["message"].casefold())
        client.post.assert_not_called()

    def test_update_status_yes_comments_and_transitions(self):
        self._configure()
        preview_client = _client(get_side_effect=self._update_gets())
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=preview_client):
            asyncio.run(
                update_status(
                    issue_key="KAN-66",
                    coverage_evidence="8 passed",
                    session_id="s-upd-yes",
                )
            )

        comment_resp = _json_response({"id": "1001"}, status=201)
        transition_list = _json_response(
            {"transitions": [{"id": "31", "name": "Done", "to": {"name": "Done"}}]}
        )
        transition_post = MagicMock()
        transition_post.status_code = 204
        transition_post.json.return_value = {}

        resolve_client = MagicMock()
        resolve_client.post = AsyncMock(side_effect=[comment_resp, transition_post])
        resolve_client.get = AsyncMock(return_value=transition_list)
        resolve_client.put = AsyncMock(side_effect=AssertionError("PUT not allowed"))
        resolve_client.__aenter__ = AsyncMock(return_value=resolve_client)
        resolve_client.__aexit__ = AsyncMock(return_value=False)

        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=resolve_client):
            result = asyncio.run(resolve_create("s-upd-yes", "confirm"))
        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["issue_key"], "KAN-66")
        self.assertEqual(result["target"], "Done")
        self.assertTrue(result["commented"])
        self.assertEqual(resolve_client.post.await_count, 2)
        comment_url = resolve_client.post.await_args_list[0].args[0]
        self.assertTrue(comment_url.endswith("/rest/api/3/issue/KAN-66/comment"))
        transition_url = resolve_client.post.await_args_list[1].args[0]
        self.assertTrue(transition_url.endswith("/rest/api/3/issue/KAN-66/transitions"))
        self.assertEqual(
            resolve_client.post.await_args_list[1].kwargs["json"]["transition"]["id"],
            "31",
        )
        self.assertNotIn(self.token, json.dumps(result))

    def test_update_status_no_confirm_cancels(self):
        self._configure()
        preview_client = _client(get_side_effect=self._update_gets())
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=preview_client):
            asyncio.run(
                update_status(
                    issue_key="KAN-66",
                    coverage_evidence="ok",
                    session_id="s-upd-no",
                )
            )
        write_client = _client()
        with patch("plugins.jira_plugin.httpx.AsyncClient", return_value=write_client):
            cancelled = asyncio.run(resolve_create("s-upd-no", "nope"))
        self.assertEqual(cancelled["status"], "cancelled")
        write_client.post.assert_not_called()

    def test_agent_tools_registered_and_confirm_flag_ignored(self):
        self._configure()
        agent = Agent()
        names = [tool["function"]["name"] for tool in agent.tools]
        self.assertIn("create_test", names)
        self.assertIn("update_status", names)
        call = {
            "function": {
                "name": "create_test",
                "arguments": {
                    "story_key": "KAN-65",
                    "steps": ["Do it"],
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
