"""
Playwright runner plugin.
Supports browser testing and basic headed mode.
Locator self-heal may change *how* an element is found, never *what* is asserted (FR-HEAL-1).
"""
import difflib
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from plugins.heal_policy import HealProposal, evaluate_and_log, locator_diff
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
        heal_refused: Optional[str] = None,
    ):
        super().__init__(message)
        self.score = score
        self.candidates = candidates or []
        self.classification = classification
        self.heal_refused = heal_refused


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


def _record_heal(action: str, payload: Dict[str, Any], value: Optional[str] = None) -> Dict[str, Any]:
    """Locator-only heal via central policy (FR-HEAL). Refuses if classification missing."""
    used = payload["used"]
    original = payload["original"]
    proposal_text = locator_diff(
        original,
        f"role/name exact → {used}",
        value=value,
    )
    decision = evaluate_and_log(
        HealProposal(
            kind="locator",
            original=original,
            proposed=f"role/name exact → {used}",
            classification="test_defect",
            value_unchanged=value,
            evidence={
                "action": action,
                "original": original,
                "used": used,
                "score": payload["score"],
                "candidates": payload.get("candidates") or [],
                "value_unchanged": value,
            },
        ),
        approver="pending_review",
    )
    if not decision.allowed:
        raise _NoHeal(
            decision.message,
            score=payload.get("score") or 0.0,
            candidates=payload.get("candidates") or [],
            classification=decision.classification or "test_defect",
            heal_refused=decision.reason or "policy_refused",
        )
    out = dict(payload)
    out["proposal"] = decision.proposal_diff or proposal_text
    out["classification"] = decision.classification or "test_defect"
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
            decision = evaluate_and_log(
                HealProposal(
                    kind="assertion",
                    original="toHaveText / expect_text",
                    proposed="toBeVisible",
                    classification="product_bug",
                    evidence={"action": "expect_text", "expected": value},
                )
            )
            raise _NoHeal(
                f"text not found: {value}",
                classification="product_bug",
                heal_refused=decision.reason or "assertion_unchanged",
            )
    elif action == "expect_url":
        if value not in page.url:
            decision = evaluate_and_log(
                HealProposal(
                    kind="assertion",
                    original="toHaveURL / expect_url",
                    proposed="toBeVisible",
                    classification="product_bug",
                    evidence={"action": "expect_url", "expected": value},
                )
            )
            raise _NoHeal(
                f"url does not contain: {value}",
                classification="product_bug",
                heal_refused=decision.reason or "assertion_unchanged",
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

    from settings.store import browser_profile_dir, get_security_level

    level = (security_level or "").strip().upper() or get_security_level()
    result["security_level"] = level
    started = None
    context = None
    try:
        if browser is None:
            # FR-SEC-1: isolated persistent profile per OFFICIAL / SECRET level.
            started = await async_playwright().start()
            profile = browser_profile_dir(level)
            profile.mkdir(parents=True, exist_ok=True)
            result["browser_profile"] = str(profile)
            context = await started.chromium.launch_persistent_context(
                str(profile),
                headless=False,  # headed for visibility on laptop
            )
        else:
            # Injected browser (tests): ephemeral context, caller owns lifecycle.
            context = await browser.new_context()
        page = await context.new_page()
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
                        refused = getattr(e, "heal_refused", None)
                        if step.get("action") in _ASSERT_ACTIONS:
                            failed["healed"] = False
                            failed["heal_refused"] = refused or "assertion_unchanged"
                        elif refused:
                            failed["healed"] = False
                            failed["heal_refused"] = refused
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
            if context is not None:
                await context.close()
    except Exception as e:
        result["status"] = "fail"
        if not result.get("error"):
            result["error"] = str(e)
    finally:
        if started is not None:
            await started.stop()
    return export_run(result, request_text, session_id)
