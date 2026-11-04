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

from reports.exporter import export_run

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


_STOP = frozenset("a an the and or of to in on for with at by from as is it be this that".split())


def _words(text: str) -> set:
    return {word for word in text.lower().split() if word and word not in _STOP}


def _match_score(intended: str, label: str) -> float:
    full = difflib.SequenceMatcher(None, intended.lower(), label.lower()).ratio()
    left, right = _words(intended), _words(label)
    if not left or not right:
        jaccard = 0.0
    else:
        jaccard = len(left & right) / len(left | right)
    return max(full, jaccard)


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


class _NoHeal(Exception):
    def __init__(self, message: str, score: float, candidates: List[Dict[str, Any]]):
        super().__init__(message)
        self.score = score
        self.candidates = candidates


def _best_control(intended: str, controls: List[Tuple[str, str]]):
    scored = [
        (role, label, _match_score(intended, label))
        for role, label in controls
    ]
    scored.sort(key=lambda item: item[2], reverse=True)
    if not scored or scored[0][2] < 0.6:
        return None, scored
    top = scored[0][2]
    close = [item for item in scored if top - item[2] <= 0.05]
    if len(close) >= 2:
        return None, scored
    return scored[0], scored


async def _click(page, selector: str):
    intended = _intended_text(selector)
    try:
        await page.click(selector, timeout=10000)
        return None
    except PlaywrightTimeout as exc:
        match, scored = _best_control(intended, await _visible_controls(page))
        candidates = [
            {"role": role, "text": label, "score": round(score, 3)}
            for role, label, score in scored
        ]
        best_score = round(scored[0][2], 3) if scored else 0.0
        if not match:
            raise _NoHeal(str(exc), best_score, candidates)
        role, label, score = match
        try:
            await page.get_by_role(role, name=label, exact=True).click(timeout=5000)
        except Exception:
            await page.get_by_text(label, exact=True).click(timeout=5000)
        return {
            "healed": True,
            "original": intended,
            "used": label,
            "score": round(score, 3),
            "candidates": candidates,
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
    security_level: str = "OFFICIAL",
    request_text: str = "",
    session_id: str = "default",
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "fail", "title": None, "screenshot": None, "error": None}
    if steps:
        invalid = _validate_steps(steps)
        if invalid:
            result["error"] = invalid
            result["steps"] = []
            return export_run(result, request_text, session_id)

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
                            failed = {
                                "action": step.get("action"),
                                "status": "fail",
                                "error": str(e),
                            }
                            if getattr(e, "candidates", None) is not None:
                                failed["score"] = e.score
                                failed["candidates"] = e.candidates
                            result["steps"].append(failed)
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
    return export_run(result, request_text, session_id)
