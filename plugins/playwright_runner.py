"""
Playwright runner plugin.
Supports browser testing and basic headed mode.
Locator self-heal may change *how* an element is found, never *what* is asserted (FR-HEAL-1).
"""
import difflib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from reports.exporter import export_run

_ACTIONS = {"goto", "click", "fill", "expect_text", "expect_url"}
_ASSERT_ACTIONS = frozenset({"expect_text", "expect_url"})
_CLICK_ROLES = ("link", "button")
_FILL_ROLES = ("textbox", "searchbox", "combobox", "spinbutton")


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
    if selector.startswith("text="):
        text = selector[5:]
    elif selector.startswith("label="):
        text = selector[6:]
    elif selector.startswith("placeholder="):
        text = selector[12:]
    elif selector.startswith("#"):
        # #user-email → "user email" for heal scoring against labels
        text = selector[1:].replace("-", " ").replace("_", " ")
    else:
        text = selector
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
    score = max(full, jaccard)
    # "#email" → "Email address": all intended words appear in the label
    if left and right and left <= right:
        score = max(score, 0.7)
    return score


async def _accessible_label(item) -> str:
    """Best-effort accessible name for heal scoring (labels, aria, placeholder, name, text)."""
    raw = await item.evaluate(
        """(el) => {
          const fromLabels = el.labels && el.labels.length
            ? Array.from(el.labels).map(l => l.innerText || l.textContent || '').join(' ')
            : '';
          return [
            fromLabels,
            el.getAttribute('aria-label') || '',
            el.getAttribute('placeholder') || '',
            el.getAttribute('name') || '',
            el.innerText || el.textContent || '',
          ].join(' ');
        }"""
    )
    return " ".join((raw or "").split())


async def _visible_role_labels(page, roles: Tuple[str, ...]) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    for role in roles:
        loc = page.get_by_role(role)
        for index in range(await loc.count()):
            if len(found) >= 30:
                return found
            item = loc.nth(index)
            if not await item.is_visible():
                continue
            label = await _accessible_label(item)
            if label:
                found.append((role, label))
    return found


class _NoHeal(Exception):
    def __init__(
        self,
        message: str,
        score: float = 0.0,
        candidates: Optional[List[Dict[str, Any]]] = None,
        classification: str = "test_defect",
    ):
        super().__init__(message)
        self.score = score
        self.candidates = candidates or []
        self.classification = classification


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


def _heal_proposal(action: str, original: str, used: str, value: Optional[str] = None) -> str:
    lines = [
        f"Heal proposal ({action}): locator only (FR-HEAL-1).",
        f"- original locator intent: {original}",
        f"- proposed locator: role/name exact → {used}",
    ]
    if value is not None:
        lines.append(f"- value unchanged: {value!r}")
    lines.append("- suite file not auto-committed (FR-HEAL-2).")
    return "\n".join(lines)


def _heal_log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "ai_testing_app" if base else Path.home() / ".ai_testing_app"
    return root / "heal_audit.jsonl"


def _append_heal_log(entry: Dict[str, Any]) -> None:
    path = _heal_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _record_heal(action: str, payload: Dict[str, Any], value: Optional[str] = None) -> Dict[str, Any]:
    proposal = _heal_proposal(action, payload["original"], payload["used"], value)
    logged = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "classification": "test_defect",
        "evidence": {
            "original": payload["original"],
            "used": payload["used"],
            "score": payload["score"],
            "candidates": payload.get("candidates") or [],
        },
        "approver": "pending_review",
        "proposal": proposal,
        "value_unchanged": value,
    }
    try:
        _append_heal_log(logged)
    except Exception:
        pass
    out = dict(payload)
    out["proposal"] = proposal
    out["classification"] = "test_defect"
    out["approver"] = "pending_review"
    return out


async def _click(page, selector: str, click_timeout: int = 10000, retry_timeout: int = 5000):
    intended = _intended_text(selector)
    try:
        await page.click(selector, timeout=click_timeout)
        return None
    except PlaywrightTimeout as exc:
        match, scored = _best_control(intended, await _visible_role_labels(page, _CLICK_ROLES))
        candidates = [
            {"role": role, "text": label, "score": round(score, 3)}
            for role, label, score in scored
        ]
        best_score = round(scored[0][2], 3) if scored else 0.0
        if not match:
            raise _NoHeal(str(exc), best_score, candidates, classification="test_defect")
        role, label, score = match
        try:
            await page.get_by_role(role, name=label, exact=True).click(timeout=retry_timeout)
        except Exception:
            await page.get_by_text(label, exact=True).click(timeout=retry_timeout)
        return _record_heal(
            "click",
            {
                "healed": True,
                "original": intended,
                "used": label,
                "score": round(score, 3),
                "candidates": candidates,
            },
        )


async def _fill(page, selector: str, value: str, fill_timeout: int = 10000, retry_timeout: int = 5000):
    """Fill with optional locator heal; never changes the filled value (FR-HEAL-1)."""
    intended = _intended_text(selector)
    try:
        await page.fill(selector, value, timeout=fill_timeout)
        return None
    except PlaywrightTimeout as exc:
        match, scored = _best_control(intended, await _visible_role_labels(page, _FILL_ROLES))
        candidates = [
            {"role": role, "text": label, "score": round(score, 3)}
            for role, label, score in scored
        ]
        best_score = round(scored[0][2], 3) if scored else 0.0
        if not match:
            raise _NoHeal(str(exc), best_score, candidates, classification="test_defect")
        role, label, score = match
        await page.get_by_role(role, name=label, exact=True).fill(value, timeout=retry_timeout)
        return _record_heal(
            "fill",
            {
                "healed": True,
                "original": intended,
                "used": label,
                "score": round(score, 3),
                "candidates": candidates,
                "value": value,
            },
            value=value,
        )


async def _run_step(page, step: Dict[str, Any], click_timeout: int = 10000, retry_timeout: int = 5000):
    action = step["action"]
    selector = step.get("selector")
    value = step.get("value")
    if action == "goto":
        await page.goto(value)
    elif action == "click":
        return await _click(page, selector, click_timeout, retry_timeout)
    elif action == "fill":
        return await _fill(page, selector, value, click_timeout, retry_timeout)
    elif action == "expect_text":
        # Assertions are never self-healed (FR-HEAL-1 / FR-HEAL-3); stay red.
        if value not in await page.content():
            raise _NoHeal(
                f"text not found: {value}",
                classification="product_bug",
            )
    elif action == "expect_url":
        if value not in page.url:
            raise _NoHeal(
                f"url does not contain: {value}",
                classification="product_bug",
            )
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
    click_timeout: int = 10000,
    retry_timeout: int = 5000,
    browser=None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "fail", "title": None, "screenshot": None, "error": None}
    if steps:
        invalid = _validate_steps(steps)
        if invalid:
            result["error"] = invalid
            result["steps"] = []
            return export_run(result, request_text, session_id)

    started = None
    try:
        if browser is None:
            started = await async_playwright().start()
            browser = await started.chromium.launch(headless=False)  # headed for visibility on laptop
        page = await (await browser.new_context()).new_page()
        try:
            if steps:
                result["steps"] = []
                for step in steps:
                    try:
                        healed = await _run_step(page, step, click_timeout, retry_timeout)
                    except Exception as e:
                        failed = {
                            "action": step.get("action"),
                            "status": "fail",
                            "error": str(e),
                        }
                        if getattr(e, "candidates", None) is not None:
                            failed["score"] = e.score
                            failed["candidates"] = e.candidates
                        if getattr(e, "classification", None):
                            failed["classification"] = e.classification
                        # FR-HEAL-3/4: product bugs and assertion failures stay red — no heal.
                        if step.get("action") in _ASSERT_ACTIONS:
                            failed["healed"] = False
                            failed["heal_refused"] = "assertion_unchanged"
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
            await page.context.close()
    except Exception as e:
        result["status"] = "fail"
        if not result.get("error"):
            result["error"] = str(e)
    finally:
        if started is not None:
            if browser is not None:
                await browser.close()
            await started.stop()
    return export_run(result, request_text, session_id)
