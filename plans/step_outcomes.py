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


def _smokeish_tags(case_tags: list[str] | None) -> bool:
    tags = {str(t or "").strip().lower() for t in (case_tags or [])}
    return bool(tags & {"smoke", "golden", "golden-path", "golden_path"})


def _evidence_pngs(run: dict[str, Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in run.get("evidence") or []:
        text = str(item or "").strip()
        if not text.lower().endswith(".png"):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _hide_pass_shots(
    *,
    case_tags: list[str] | None,
    success_shots_enabled: bool,
) -> bool:
    """AC: success-shots-off hides pass PNGs for non-smoke runs in deep view."""
    if success_shots_enabled:
        return False
    return not _smokeish_tags(case_tags)


def deep_view_captured_pages(
    run: dict[str, Any] | None,
    *,
    case_tags: list[str] | None = None,
    success_shots_enabled: bool = True,
) -> list[dict[str, Any]]:
    """Captured page thumbs for Plans deep view (KAN-498).

    Uses per-step screenshot refs when present; otherwise attaches unattached
    evidence PNGs to the fail step (or last step). Never invents images from
    trace.zip. Strip omits steps with no file.
    """
    if not isinstance(run, dict):
        return []
    outcomes = normalize_step_outcomes(run.get("step_outcomes") or [])
    hide_pass = _hide_pass_shots(
        case_tags=case_tags,
        success_shots_enabled=success_shots_enabled,
    )
    pages: list[dict[str, Any]] = []
    used: set[str] = set()

    def _append(
        path: str,
        *,
        step_index: int | None,
        label: str,
        status: str,
    ) -> None:
        text = (path or "").strip()
        if not text.lower().endswith(".png"):
            return
        key = text.lower()
        if key in used:
            return
        if hide_pass and str(status or "").lower() == "pass":
            return
        used.add(key)
        pages.append(
            {
                "path": text[:500],
                "step_index": step_index,
                "label": (label or "Captured page")[:200],
                "status": str(status or "").strip().lower()[:20] or "pending",
            }
        )

    for step in outcomes:
        shot = str(step.get("screenshot") or "").strip()
        if not shot:
            continue
        _append(
            shot,
            step_index=int(step.get("index") or 0) or None,
            label=str(step.get("label") or step.get("action") or "Step"),
            status=str(step.get("status") or ""),
        )

    leftover = [p for p in _evidence_pngs(run) if p.lower() not in used]
    if leftover:
        fail_step = next(
            (
                s
                for s in outcomes
                if str(s.get("status") or "").lower() in {"fail", "error"}
            ),
            None,
        )
        attach = fail_step or (outcomes[-1] if outcomes else None)
        run_result = str(run.get("result") or "").lower()
        for idx, path in enumerate(leftover):
            if attach and idx == 0:
                _append(
                    path,
                    step_index=int(attach.get("index") or 0) or None,
                    label=str(attach.get("label") or attach.get("action") or "Step"),
                    status=str(attach.get("status") or run_result),
                )
            else:
                # Extra unattached PNGs stay in the strip without inventing a step.
                _append(
                    path,
                    step_index=None,
                    label="Captured page",
                    status=run_result or "pending",
                )
    return pages


def run_allows_shot_path(run: dict[str, Any] | None, path: str) -> bool:
    """True when path is a PNG listed on the run (evidence or step outcome)."""
    if not isinstance(run, dict):
        return False
    want = (path or "").strip().lower()
    if not want.endswith(".png"):
        return False
    for item in _evidence_pngs(run):
        if item.lower() == want:
            return True
    for step in normalize_step_outcomes(run.get("step_outcomes") or []):
        shot = str(step.get("screenshot") or "").strip()
        if shot.lower() == want:
            return True
    return False


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
    smokeish = _smokeish_tags(case_tags)
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
