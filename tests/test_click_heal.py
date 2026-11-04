"""One-shot click heal against a local page. No network and no LLM."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.playwright_runner import run_playwright  # noqa: E402


class ClickHealTests(unittest.TestCase):
    def test_more_information_heals_to_learn_more(self):
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "page.html"
            page.write_text(
                "<!doctype html><title>Heal</title>"
                "<a href=\"#healed\">Learn more</a>",
                encoding="utf-8",
            )
            target = page.as_uri()
            result = asyncio.run(run_playwright(target, steps=[
                {"action": "goto", "value": target},
                {"action": "click", "selector": "text=More information"},
            ]))
        self.assertEqual(result["status"], "pass", result.get("error"))
        click = result["steps"][1]
        self.assertEqual(click["status"], "pass")
        self.assertTrue(click["healed"])
        self.assertEqual(click["original"], "More information")
        self.assertEqual(click["used"], "Learn more")
        self.assertGreaterEqual(click["score"], 0.6)


if __name__ == "__main__":
    unittest.main()
