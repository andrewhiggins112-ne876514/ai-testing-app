"""FR-AGENT-6 / KAN-61: JSON-in-text tool fallback + grounded failure replies."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import (  # noqa: E402
    Agent,
    grounded_tool_reply,
    parse_tool_calls_from_text,
    tool_result_failed,
)

calls = []


class _Resp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class _Client:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None):
        calls.append(json)
        if len(calls) == 1:
            return _Resp({"message": first_message})
        return _Resp({"message": {"role": "assistant", "content": second_content}})


first_message = {}
second_content = "Done."


class ToolCallingTests(unittest.TestCase):
    def setUp(self):
        calls.clear()
        global first_message, second_content
        first_message = {}
        second_content = "Done."

    def test_parse_plain_json_name_arguments(self):
        parsed = parse_tool_calls_from_text(
            '{"name":"list_plugins","arguments":{}}'
        )
        self.assertEqual(parsed, [{"name": "list_plugins", "arguments": {}}])

    def test_parse_json_in_prose_with_parameters(self):
        text = (
            "Sure, I will call the tool now.\n"
            '{"name":"list_stories","parameters":{"project":"KAN"}}\n'
            "Waiting for result."
        )
        parsed = parse_tool_calls_from_text(text)
        self.assertEqual(
            parsed,
            [{"name": "list_stories", "arguments": {"project": "KAN"}}],
        )

    def test_parse_fenced_tool_calls_array(self):
        text = """```json
{"tool_calls":[{"function":{"name":"run_playwright","arguments":{"url":"https://example.com"}}}]}
```"""
        parsed = parse_tool_calls_from_text(text)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["name"], "run_playwright")
        self.assertEqual(parsed[0]["arguments"]["url"], "https://example.com")

    def test_parse_ignores_unknown_tool(self):
        self.assertEqual(
            parse_tool_calls_from_text('{"name":"rm_rf","arguments":{}}'),
            [],
        )

    def test_tool_result_failed_statuses(self):
        self.assertTrue(tool_result_failed({"status": "fail", "error": "x"}))
        self.assertTrue(tool_result_failed({"error": "boom"}))
        self.assertTrue(tool_result_failed({"status": "reject", "rejected": True}))
        self.assertFalse(tool_result_failed({"status": "ok"}))
        self.assertFalse(tool_result_failed({"status": "pass"}))

    def test_grounded_reply_blocks_success_claim(self):
        reply = grounded_tool_reply(
            [{"status": "fail", "message": "plugin disabled"}],
            "The desktop smoke test succeeded.",
        )
        self.assertIn("did not succeed", reply.lower())
        self.assertIn("plugin disabled", reply.lower())
        self.assertNotIn("succeeded", reply.lower())

    def test_chat_runs_tool_from_json_text_without_tool_calls_field(self):
        global first_message, second_content
        first_message = {
            "role": "assistant",
            "content": 'Here you go:\n{"name":"list_plugins","arguments":{}}',
        }
        second_content = "Listed plugins."
        agent = Agent()
        with patch("agent.agent.httpx.AsyncClient", _Client), patch(
            "plugins.registry.list_plugins",
            return_value={"status": "ok", "plugins": []},
        ):
            reply = asyncio.run(agent.chat("list plugins", "s-json-text"))
        self.assertEqual(reply, "Listed plugins.")
        self.assertEqual(len(calls), 2)
        self.assertIn("tools", calls[0])
        self.assertEqual(calls[0].get("think"), False)
        self.assertEqual(calls[0].get("options", {}).get("num_ctx"), 8192)
        # Second Ollama turn should include a tool role message
        roles = [m.get("role") for m in calls[1]["messages"]]
        self.assertIn("tool", roles)

    def test_chat_does_not_claim_success_on_tool_failure(self):
        global first_message, second_content
        first_message = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "run_desktop",
                    "arguments": {"exe_path": "C:\\\\Windows\\\\notepad.exe"},
                }
            }],
        }
        second_content = "Desktop smoke completed successfully."
        agent = Agent()
        with patch("agent.agent.httpx.AsyncClient", _Client), patch(
            "plugins.desktop_runner.run_desktop",
            return_value={
                "status": "fail",
                "message": "Enable plugin_desktop_enabled in Settings.",
                "error": "plugin_disabled",
            },
        ):
            reply = asyncio.run(agent.chat("run notepad smoke", "s-fail"))
        self.assertIn("did not succeed", reply.lower())
        self.assertNotRegex(reply.lower(), r"success(?:fully)?|succeeded")


if __name__ == "__main__":
    unittest.main()
