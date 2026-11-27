"""Normalize ordered step outcomes for Case aside run story (KAN-496 / FR-PLAN-4).

Human labels only — never require the tester to read raw JSON.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


_ACTION_VERBS = {
    "goto": "Open",
    "click": "Click",
    "fill": "Fill",
    "expect_text": "Expect",
    "expect_url": "Expect URL",
    "expect_visible": "Expect visible",
}


def human_step_label(step: dict[str, Any] | None) -> str:
    """Plain-language verb + target for one Playwright/plan step."""
    raw = step if isinstance(step, dict) else {}
    action = str(raw.get("action") or "").strip().lower()
    selector = str(raw.get("selector") or "").strip()
    value = raw.get("value")
    value_text = "" if value is None else str(value).strip()
    verb = _ACTION_VERBS.get(action, action.title() or "Step")

    if action == "goto":
        target = _short_url(value_text) or value_text or "page"
        return f"{verb} {target}"
    if action == "click":
        return f"{verb} {selector or value_text or 'control'}"
    if action == "fill":
        shown = value_text
        if len(shown) > 40:
            shown = shown[:37] + "…"
        if selector and shown:
            return f"{verb} {selector} = {shown}"
        return f"{verb} {selector or shown or 'field'}"
    if action == "expect_text":
        shown = value_text or "text"
        if len(shown) > 48:
            shown = shown[:45] + "…"
        return f'{verb} "{shown}"'
    if action == "expect_url":
        return f"{verb} {_short_url(value_text) or value_text or 'URL'}"
    if action == "expect_visible":
        return f"{verb} {selector or value_text or 'element'}"
    if selector and value_text:
        return f"{verb} {selector} {value_text}"
    return f"{verb} {selector or value_text}".strip()


def _short_url(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    try:
        parsed = urlparse(text)
        if parsed.scheme and parsed.netloc:
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            if len(path) > 60:
                path = path[:57] + "…"
            return path
    except ValueError:
        pass
    return text[:60]


def normalize_step_outcomes(
    steps: Any,
    *,
    definitions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Persistable ordered step outcomes (status, label, error, optional shot)."""
    if not isinstance(steps, list):
        return []
    defs = list(definitions or [])
    out: list[dict[str, Any]] = []
    for idx, raw in enumerate(steps):
        if not isinstance(raw, dict):
            continue
        merged = dict(raw)
        if idx < len(defs) and isinstance(defs[idx], dict):
            for key in ("action", "selector", "value"):
                if not merged.get(key) and defs[idx].get(key) is not None:
                    merged[key] = defs[idx].get(key)
        status = str(merged.get("status") or "pending").strip().lower()
        if status not in {"pass", "fail", "error", "skipped", "pending"}:
            status = "fail" if merged.get("error") else "pending"
        duration = merged.get("duration_ms")
        try:
            duration_ms = int(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration_ms = None
        error = str(merged.get("error") or "").strip()[:500] or None
        shot = str(merged.get("screenshot") or "").strip()[:500] or None
        existing_label = str(merged.get("label") or "").strip()
        label = (existing_label or human_step_label(merged))[:200]
        out.append(
            {
                "index": idx + 1,
                "action": str(merged.get("action") or "").strip().lower()[:40],
                "label": label,
                "status": status,
                "duration_ms": duration_ms,
                "error": error,
                "screenshot": shot,
            }
        )
    return out


def build_step_outcomes_from_playwright(
    pw: dict[str, Any] | None,
    *,
    definitions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Map playwright_runner result steps (+ optional defs) to step_outcomes."""
    payload = pw if isinstance(pw, dict) else {}
    steps = payload.get("steps") or []
    return normalize_step_outcomes(steps, definitions=definitions)


def representative_screenshot(run: dict[str, Any] | None) -> str | None:
    """First PNG on the run evidence list (representative Case-aside shot)."""
    if not isinstance(run, dict):
        return None
    for item in run.get("evidence") or []:
        text = str(item or "").strip()
        if text.lower().endswith(".png"):
            return text
    return None


def honest_empty_reason(
    run: dict[str, Any] | None,
    *,
    case_tags: list[str] | None = None,
) -> str:
    """Why the aside shows None captured — never invent a green stand-in."""
    if not isinstance(run, dict):
        return "No run yet. This slot stays empty until a run writes evidence."
    if representative_screenshot(run):
        return ""
    result = str(run.get("result") or "").lower()
    note = str(run.get("note") or "").strip()
    tags = {str(t or "").strip().lower() for t in (case_tags or [])}
    smokeish = bool(tags & {"smoke", "golden", "golden-path", "golden_path"})
    if result == "pass":
        if smokeish:
            return (
                "None captured. This smoke/golden pass did not write a PNG "
                "(success evidence may be off). A green stand-in is not substituted."
            )
        return (
            "None captured. Success shots are off or were not written for this pass. "
            "A green stand-in is not substituted."
        )
    if note:
        return (
            "None captured. The runner did not write a PNG for this fail. "
            f"{note[:160]} A green stand-in is not substituted."
        )
    return (
        "None captured. The runner did not write a PNG for this fail. "
        "This slot stays empty. A green stand-in is not substituted."
    )
