"""Locator heal beyond click: fill heal + assertion guardrails. Local pages only."""
import asyncio
import sys
import tempfile
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.playwright_runner import (  # noqa: E402
    _heal_proposal,
    run_playwright,
)

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


def _run(browser, html: str, steps: list):
    launched, loop = browser
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / "page.html"
        page.write_text(html, encoding="utf-8")
        target = page.as_uri()
        full = [{"action": "goto", "value": target}, *steps]
        return loop.run_until_complete(run_playwright(
            target,
            steps=full,
            browser=launched,
            click_timeout=1000,
            retry_timeout=1000,
        ))


def test_fill_heals_broken_selector_value_unchanged(browser):
    html = (
        "<!doctype html><title>Fill heal</title>"
        "<label for=\"em\">Email address</label>"
        "<input id=\"em\" type=\"text\" />"
    )
    result = _run(
        browser,
        html,
        [{"action": "fill", "selector": "#email", "value": "a@b.co"}],
    )
    assert result["status"] == "pass", result.get("error")
    fill = result["steps"][1]
    assert fill["healed"] is True
    assert fill["original"] == "email"
    assert fill["used"] == "Email address"
    assert fill["value"] == "a@b.co"
    assert "value unchanged" in fill["proposal"]
    assert fill["classification"] == "test_defect"
    assert fill["approver"] == "pending_review"


def test_fill_ambiguous_candidates_do_not_heal(browser):
    html = (
        "<!doctype html><title>Fill ambig</title>"
        "<label for=\"a\">Email home</label><input id=\"a\" />"
        "<label for=\"b\">Email work</label><input id=\"b\" />"
    )
    result = _run(
        browser,
        html,
        [{"action": "fill", "selector": "#email", "value": "x"}],
    )
    fill = result["steps"][1]
    assert fill["status"] == "fail"
    assert "healed" not in fill
    assert len(fill["candidates"]) >= 2


def test_expect_text_failure_stays_red_no_heal(browser):
    html = "<!doctype html><title>Assert</title><p>hello</p>"
    result = _run(
        browser,
        html,
        [{"action": "expect_text", "value": "goodbye"}],
    )
    step = result["steps"][1]
    assert result["status"] == "fail"
    assert step["status"] == "fail"
    assert step.get("healed") is False
    assert step["heal_refused"] == "assertion_unchanged"
    assert step["classification"] == "product_bug"
    assert "goodbye" in step["error"]


def test_heal_proposal_never_mentions_value_change():
    text = _heal_proposal("fill", "Email", "Email address", value="keep-me")
    assert "locator only" in text
    assert "value unchanged: 'keep-me'" in text
    assert "auto-committed" in text
