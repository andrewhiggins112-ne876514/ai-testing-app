"""Click-heal scoring. Local pages only. No network and no LLM."""
import asyncio
import sys
import tempfile
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.playwright_runner import run_playwright  # noqa: E402

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def browser():
    loop = asyncio.new_event_loop()
    playwright = loop.run_until_complete(async_playwright().start())
    launched = loop.run_until_complete(playwright.chromium.launch(headless=False))
    yield launched, loop
    loop.run_until_complete(launched.close())
    loop.run_until_complete(playwright.stop())
    loop.close()


def _run(browser, html: str, selector: str):
    launched, loop = browser
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / "page.html"
        page.write_text(html, encoding="utf-8")
        target = page.as_uri()
        return loop.run_until_complete(run_playwright(
            target,
            steps=[
                {"action": "goto", "value": target},
                {"action": "click", "selector": selector},
            ],
            browser=launched,
            click_timeout=1000,
            retry_timeout=1000,
        ))


def test_learn_more_heals_to_learn_more_about(browser):
    result = _run(
        browser,
        "<!doctype html><title>Heal</title><a href=\"#ok\">learn more about</a>",
        'text="Learn more"',
    )
    assert result["status"] == "pass", result.get("error")
    click = result["steps"][1]
    assert click["healed"] is True
    assert click["original"] == "Learn more"
    assert click["used"] == "learn more about"
    assert click["score"] >= 0.6
    assert click["candidates"]


def test_more_information_does_not_heal_to_learn_more(browser):
    result = _run(
        browser,
        "<!doctype html><title>Heal</title><a href=\"#ok\">Learn more</a>",
        "text=More information",
    )
    click = result["steps"][1]
    assert click["status"] == "fail"
    assert "healed" not in click
    assert click["score"] < 0.6
    assert click["candidates"][0]["text"] == "Learn more"


def test_ambiguous_candidates_do_not_heal(browser):
    result = _run(
        browser,
        "<!doctype html><title>Heal</title>"
        "<a href=\"#a\">learn more about</a>"
        "<a href=\"#b\">learn more stuff</a>",
        'text="learn more"',
    )
    click = result["steps"][1]
    assert click["status"] == "fail"
    assert "healed" not in click
    scores = [item["score"] for item in click["candidates"]]
    assert len(scores) >= 2
    assert max(scores) - min(scores) <= 0.05
