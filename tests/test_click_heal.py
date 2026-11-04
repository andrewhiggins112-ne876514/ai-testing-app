"""Click-heal scoring. Local pages only. No network and no LLM."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.playwright_runner import run_playwright  # noqa: E402


def _run(html: str, selector: str):
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / "page.html"
        page.write_text(html, encoding="utf-8")
        target = page.as_uri()
        return asyncio.run(run_playwright(target, steps=[
            {"action": "goto", "value": target},
            {"action": "click", "selector": selector},
        ]))


class ClickHealTests(unittest.TestCase):
    def test_learn_more_heals_to_learn_more_about(self):
        result = _run(
            "<!doctype html><title>Heal</title><a href=\"#ok\">learn more about</a>",
            'text="Learn more"',
        )
        self.assertEqual(result["status"], "pass", result.get("error"))
        click = result["steps"][1]
        self.assertTrue(click["healed"])
        self.assertEqual(click["original"], "Learn more")
        self.assertEqual(click["used"], "learn more about")
        self.assertGreaterEqual(click["score"], 0.6)
        self.assertTrue(click["candidates"])

    def test_more_information_does_not_heal_to_learn_more(self):
        result = _run(
            "<!doctype html><title>Heal</title><a href=\"#ok\">Learn more</a>",
            "text=More information",
        )
        click = result["steps"][1]
        self.assertEqual(click["status"], "fail")
        self.assertNotIn("healed", click)
        self.assertLess(click["score"], 0.6)
        self.assertEqual(click["candidates"][0]["text"], "Learn more")

    def test_ambiguous_candidates_do_not_heal(self):
        result = _run(
            "<!doctype html><title>Heal</title>"
            "<a href=\"#a\">learn more about</a>"
            "<a href=\"#b\">learn more stuff</a>",
            'text="learn more"',
        )
        click = result["steps"][1]
        self.assertEqual(click["status"], "fail")
        self.assertNotIn("healed", click)
        scores = [item["score"] for item in click["candidates"]]
        self.assertGreaterEqual(len(scores), 2)
        self.assertLessEqual(max(scores) - min(scores), 0.05)


if __name__ == "__main__":
    unittest.main()
