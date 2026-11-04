"""
Playwright runner plugin.
Supports browser testing and basic headed mode.
"""
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

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


async def _run_step(page, step: Dict[str, Any]) -> None:
    action = step["action"]
    selector = step.get("selector")
    value = step.get("value")
    if action == "goto":
        await page.goto(value)
    elif action == "click":
        await page.click(selector)
    elif action == "fill":
        await page.fill(selector, value)
    elif action == "expect_text":
        if value not in await page.content():
            raise RuntimeError(f"text not found: {value}")
    elif action == "expect_url":
        if value not in page.url:
            raise RuntimeError(f"url does not contain: {value}")


async def _save_screenshot(page, result: Dict[str, Any]) -> None:
    shot_dir = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "screenshots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot = shot_dir / f"{time.strftime('%Y%m%d-%H%M%S')}.png"
    await page.screenshot(path=str(shot), full_page=True)
    result["screenshot"] = str(shot)


async def run_playwright(
    url: str,
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
                            await _run_step(page, step)
                        except Exception as e:
                            result["steps"].append({
                                "action": step.get("action"),
                                "status": "fail",
                                "error": str(e),
                            })
                            result["error"] = str(e)
                            break
                        result["steps"].append({"action": step["action"], "status": "pass"})
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
