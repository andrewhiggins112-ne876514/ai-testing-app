"""LLM-emitted Playwright steps. Ollama and the browser are mocked."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import Agent  # noqa: E402
from plugins.playwright_runner import run_playwright  # noqa: E402

STEPS = [
    {"action": "goto", "value": "https://example.com"},
    {"action": "click", "selector": "text=More information"},
    {"action": "expect_url", "value": "iana"},
]


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
            return _Resp({
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "function": {
                            "name": "run_playwright",
                            "arguments": {"url": "https://example.com", "steps": STEPS},
                        }
                    }],
                }
            })
        return _Resp({"message": {"role": "assistant", "content": "done"}})


calls = []
seen = []


async def _fake_run(**kwargs):
    seen.append(kwargs)
    return {"status": "pass", "title": "t", "screenshot": None, "error": None, "steps": []}


class PlaywrightStepTests(unittest.TestCase):
    def test_mocked_llm_steps_reach_runner(self):
        calls.clear()
        seen.clear()
        agent = Agent()
        with patch("agent.agent.httpx.AsyncClient", _Client), patch(
            "plugins.playwright_runner.run_playwright", _fake_run
        ):
            reply = asyncio.run(agent.chat(
                "go to example.com, click 'More information', check the URL contains iana"
            ))
        self.assertEqual(reply, "done")
        self.assertEqual(seen[0]["steps"], STEPS)
        self.assertEqual(seen[0]["url"], "https://example.com")

    def test_unknown_action_rejected_without_browser(self):
        with patch("plugins.playwright_runner.async_playwright") as browser:
            result = asyncio.run(run_playwright(
                "https://example.com",
                steps=[{"action": "explode"}],
            ))
        browser.assert_not_called()
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["error"], "unknown action: explode")
        self.assertEqual(result["steps"], [])
        self.assertIsNone(result["screenshot"])


if __name__ == "__main__":
    unittest.main()
