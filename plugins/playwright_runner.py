"""
Playwright runner plugin.
Supports browser testing and basic headed mode.
"""
import difflib
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

_ACTIONS = {"goto", "click", "fill", "expect_text", "expect_url"}


def _validate_steps(steps: Any) -> Optional[str]:
    if not isinstance(steps, list):
        return "steps must be a list"
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return f"step {index} must be an object"
        action = step.get("action")
        if action not in _ACTIONS:
            return f"unknown action: {action}"
        selector = step.get("selector")
        value = step.get("value")
        if selector is not None and not isinstance(selector, str):
            return "selector must be a string"
        if value is not None and not isinstance(value, str):
            return "value must be a string"
        if action in {"goto", "expect_text", "expect_url"} and not value:
            return f"{action} requires value"
        if action == "click" and not selector:
            return "click requires selector"
        if action == "fill" and not (selector and value):
            return "fill requires selector and value"
    return None


def _intended_text(selector: str) -> str:
    text = selector[5:] if selector.startswith("text=") else selector
    return text.strip().strip("'\"")


def _tokens(text: str) -> List[str]:
    return [word for word in text.lower().split() if len(word) >= 4]


def _match_score(intended: str, label: str) -> float:
    best = difflib.SequenceMatcher(None, intended.lower(), label.lower()).ratio()
    for left in _tokens(intended):
        for right in _tokens(label):
            best = max(best, difflib.SequenceMatcher(None, left, right).ratio())
    return best


async def _visible_controls(page) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    for role in ("link", "button"):
        loc = page.get_by_role(role)
        for index in range(await loc.count()):
            if len(found) >= 30:
                return found
            item = loc.nth(index)
            if not await item.is_visible():
                continue
            label = " ".join((await item.inner_text() or "").split())
            if label:
                found.append((role, label))
    return found


def _best_control(intended: str, controls: List[Tuple[str, str]]):
    best = None
    best_score = 0.0
    best_full = -1.0
    for role, label in controls:
        score = _match_score(intended, label)
        full = difflib.SequenceMatcher(None, intended.lower(), label.lower()).ratio()
        if score > best_score or (score == best_score and full > best_full):
            best, best_score, best_full = (role, label), score, full
    if best_score >= 0.6:
        return best, best_score
    return None, best_score


async def _click(page, selector: str):
    intended = _intended_text(selector)
    try:
        await page.click(selector, timeout=10000)
        return None
    except PlaywrightTimeout:
        match, score = _best_control(intended, await _visible_controls(page))
        if not match:
            raise
        role, label = match
        try:
            await page.get_by_role(role, name=label, exact=True).click(timeout=5000)
        except Exception:
            await page.get_by_text(label, exact=True).click(timeout=5000)
        return {
            "healed": True,
            "original": intended,
            "used": label,
            "score": round(score, 3),
        }


async def _run_step(page, step: Dict[str, Any]):
    action = step["action"]
    selector = step.get("selector")
    value = step.get("value")
    if action == "goto":
        await page.goto(value)
    elif action == "click":
        return await _click(page, selector)
    elif action == "fill":
        await page.fill(selector, value)
    elif action == "expect_text":
        if value not in await page.content():
            raise RuntimeError(f"text not found: {value}")
    elif action == "expect_url":
        if value not in page.url:
            raise RuntimeError(f"url does not contain: {value}")
    return None


async def _save_screenshot(page, result: Dict[str, Any]) -> None:
    shot_dir = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "screenshots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot = shot_dir / f"{time.strftime('%Y%m%d-%H%M%S')}.png"
    await page.screenshot(path=str(shot), full_page=True)
    result["screenshot"] = str(shot)


async def run_playwright(
    url: str = "",
    mode: str = "generate",
    steps: Optional[List[Dict[str, Any]]] = None,
    security_level: str = "OFFICIAL"
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "fail", "title": None, "screenshot": None, "error": None}
    if steps:
        invalid = _validate_steps(steps)
        if invalid:
            result["error"] = invalid
            result["steps"] = []
            return result

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # headed for visibility on laptop
            try:
                page = await (await browser.new_context()).new_page()
                if steps:
                    result["steps"] = []
                    for step in steps:
                        try:
                            healed = await _run_step(page, step)
                        except Exception as e:
                            result["steps"].append({
                                "action": step.get("action"),
                                "status": "fail",
                                "error": str(e),
                            })
                            result["error"] = str(e)
                            break
                        passed = {"action": step["action"], "status": "pass"}
                        if healed:
                            passed.update(healed)
                        result["steps"].append(passed)
                    else:
                        result["status"] = "pass"
                    try:
                        result["title"] = await page.title()
                    except Exception:
                        pass
                    await _save_screenshot(page, result)
                else:
                    await page.goto(url)
                    result["title"] = await page.title()
                    await _save_screenshot(page, result)
                    result["status"] = "pass"
            finally:
                await browser.close()
    except Exception as e:
        result["status"] = "fail"
        if not result.get("error"):
            result["error"] = str(e)
    return result
