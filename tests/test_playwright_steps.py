"""Playwright step generation, quality checks, and evidence (KAN-57)."""
import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import Agent  # noqa: E402
from plugins.playwright_runner import run_playwright  # noqa: E402
from plugins.playwright_steps import (  # noqa: E402
    assess_steps,
    generate_steps_from_spec,
    validate_steps_quality,
)

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

    def test_assess_flags_happy_path_without_outcome(self):
        draft = [
            {"action": "goto", "value": "https://example.com"},
            {"action": "click", "selector": "text=Submit"},
            {"action": "expect_visible", "selector": "text=Nearby"},
        ]
        assessment = assess_steps(draft)
        self.assertTrue(assessment["incomplete"])
        self.assertTrue(assessment["has_weak_only"])
        self.assertFalse(assessment["has_outcome_assertion"])
        rejected = validate_steps_quality(draft, reject_incomplete=True)
        self.assertEqual(rejected["status"], "reject")
        self.assertTrue(rejected["rejected"])

    def test_assess_ok_with_expect_url(self):
        assessment = assess_steps(STEPS)
        self.assertTrue(assessment["complete"])
        self.assertTrue(assessment["has_outcome_assertion"])

    def test_generate_includes_assertion_and_negatives(self):
        pack = generate_steps_from_spec(
            "go to https://example.com click Login fill Email with a@b.com "
            "and expect text Welcome",
        )
        self.assertEqual(pack["status"], "ok")
        actions = [s["action"] for s in pack["steps"]]
        self.assertIn("expect_text", actions)
        self.assertTrue(pack["assessment"]["complete"])
        self.assertGreaterEqual(len(pack["negatives"]), 1)
        for variant in pack["negatives"]:
            self.assertTrue(variant["assessment"]["has_outcome_assertion"])

    def test_reject_incomplete_before_browser(self):
        with patch("plugins.playwright_runner.async_playwright") as browser:
            result = asyncio.run(run_playwright(
                "https://example.com",
                steps=[
                    {"action": "goto", "value": "https://example.com"},
                    {"action": "click", "selector": "text=Go"},
                ],
                reject_incomplete=True,
            ))
        browser.assert_not_called()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["step_quality"]["rejected"])
        self.assertIn("outcome", (result.get("error") or "").lower())

    def test_failure_screenshot_under_local_app_data(self):
        from playwright.async_api import async_playwright

        html = "<!doctype html><title>Fail</title><body>hello</body>"

        async def _go():
            with tempfile.TemporaryDirectory() as tmp:
                page = Path(tmp) / "page.html"
                page.write_text(html, encoding="utf-8")
                shot_root = Path(tmp) / "appdata"
                shot_root.mkdir()
                env = {
                    "LOCALAPPDATA": str(shot_root),
                    "AI_TESTING_REPORTS": str(Path(tmp) / "reports"),
                }
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=True)
                try:
                    with patch.dict(os.environ, env, clear=False):
                        result = await run_playwright(
                            page.as_uri(),
                            steps=[
                                {"action": "goto", "value": page.as_uri()},
                                {"action": "expect_text", "value": "definitely-missing-xyz"},
                            ],
                            browser=browser,
                            success_evidence=False,
                        )
                    shot = result.get("screenshot")
                    exists = bool(shot) and Path(shot).is_file()
                    under_root = bool(shot) and str(Path(shot).resolve()).startswith(
                        str(shot_root.resolve())
                    )
                    return {
                        "status": result.get("status"),
                        "shot": shot,
                        "exists": exists,
                        "under_root": under_root,
                        "evidence_kind": result.get("evidence_kind"),
                    }
                finally:
                    await browser.close()
                    await pw.stop()

        info = asyncio.run(_go())
        self.assertEqual(info["status"], "fail")
        self.assertTrue(info["exists"], info)
        self.assertTrue(info["under_root"], info)
        self.assertIn("screenshots", (info["shot"] or "").replace("\\", "/"))
        self.assertEqual(info["evidence_kind"], "failure")

    def test_success_evidence_optional(self):
        from playwright.async_api import async_playwright

        html = "<!doctype html><title>Ok</title><body>Welcome home</body>"

        async def _go():
            with tempfile.TemporaryDirectory() as tmp:
                page = Path(tmp) / "page.html"
                page.write_text(html, encoding="utf-8")
                shot_root = Path(tmp) / "appdata"
                shot_root.mkdir()
                env = {
                    "LOCALAPPDATA": str(shot_root),
                    "AI_TESTING_REPORTS": str(Path(tmp) / "reports"),
                }
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=True)
                try:
                    with patch.dict(os.environ, env, clear=False):
                        no_shot = await run_playwright(
                            page.as_uri(),
                            steps=[
                                {"action": "goto", "value": page.as_uri()},
                                {"action": "expect_text", "value": "Welcome"},
                            ],
                            browser=browser,
                            success_evidence=False,
                        )
                        with_shot = await run_playwright(
                            page.as_uri(),
                            steps=[
                                {"action": "goto", "value": page.as_uri()},
                                {"action": "expect_text", "value": "Welcome"},
                            ],
                            browser=browser,
                            success_evidence=True,
                        )
                    return {
                        "no_status": no_shot.get("status"),
                        "no_shot": no_shot.get("screenshot"),
                        "yes_status": with_shot.get("status"),
                        "yes_shot": with_shot.get("screenshot"),
                        "yes_exists": bool(with_shot.get("screenshot"))
                        and Path(with_shot["screenshot"]).is_file(),
                        "yes_kind": with_shot.get("evidence_kind"),
                    }
                finally:
                    await browser.close()
                    await pw.stop()

        info = asyncio.run(_go())
        self.assertEqual(info["no_status"], "pass")
        self.assertIsNone(info["no_shot"])
        self.assertEqual(info["yes_status"], "pass")
        self.assertTrue(info["yes_exists"], info)
        self.assertEqual(info["yes_kind"], "success")


if __name__ == "__main__":
    unittest.main()
