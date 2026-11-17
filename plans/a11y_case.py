"""Accessibility opt-in on browser cases (KAN-227 / G6).

Optional check beside functional Playwright runs. Cases must opt in
(a11y_check flag or a11y/accessibility tag). Violations attach to the run
and never replace the functional result. Off by default.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plans.store import add_case, get_plan, update_case

_OPT_IN_TAGS = frozenset({"a11y", "accessibility"})


def case_has_a11y_check(case: dict[str, Any] | None) -> bool:
    """True only when the case explicitly opts in (never default-on)."""
    if not isinstance(case, dict):
        return False
    if bool(case.get("a11y_check")):
        return True
    tags = [str(t or "").strip().lower() for t in (case.get("tags") or [])]
    return bool(_OPT_IN_TAGS.intersection(tags))


def add_a11y_browser_case(
    plan_id: str,
    name: str = "",
    *,
    note: str = "",
    tags: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add a browser (manual-draft) case with accessibility check opted in."""
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    case_tags = list(tags or [])
    lowered = [t.lower() for t in case_tags]
    if "a11y" not in lowered and "accessibility" not in lowered:
        case_tags = ["a11y"] + case_tags

    label = (name or "").strip() or "Browser case + accessibility check"
    out = add_case(
        plan_id,
        label,
        note=note
        or (
            "Browser case with optional accessibility check — "
            "violations attach to the run; functional result is unchanged."
        ),
        tags=case_tags,
        source_kind="manual-draft",
        source_ref="",
        a11y_check=True,
        level=level,
    )
    if out.get("status") == "ok" and out.get("case"):
        out["a11y_opt_in"] = True
        out["message"] = (
            "Accessibility check enabled on browser case (opt-in). "
            "Disabled for cases that do not opt in."
        )
    return out


def enable_a11y_on_case(
    plan_id: str,
    case_id: str,
    *,
    enabled: bool = True,
    level: str | None = None,
) -> dict[str, Any]:
    """Toggle a11y opt-in on an existing browser case (not a new case kind)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "OFFICIAL").strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    target = None
    for case in (plan.get("suite") or {}).get("cases") or []:
        if case.get("id") == cid:
            target = case
            break
    if target is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    kind = str((target.get("source") or {}).get("kind") or "manual-draft")
    if kind in {"desktop", "api", "seed", "visual", "playwright"}:
        return {
            "status": "error",
            "error": "not_browser_case",
            "message": (
                "Accessibility checks attach to browser cases only "
                f"(got source.kind={kind})."
            ),
            "security_level": lvl,
        }

    tags = list(target.get("tags") or [])
    lowered = [str(t).lower() for t in tags]
    if enabled:
        if "a11y" not in lowered and "accessibility" not in lowered:
            tags = ["a11y"] + tags
    else:
        tags = [t for t in tags if str(t).lower() not in _OPT_IN_TAGS]

    out = update_case(
        plan_id,
        cid,
        tags=tags,
        a11y_check=bool(enabled),
        level=lvl,
    )
    if out.get("status") != "ok":
        return out
    case_out = None
    for case in (out.get("plan") or {}).get("suite", {}).get("cases") or []:
        if case.get("id") == cid:
            case_out = case
            break
    return {
        **out,
        "case": case_out,
        "a11y_opt_in": bool(enabled),
        "message": (
            "Accessibility check enabled on case."
            if enabled
            else "Accessibility check disabled on case."
        ),
    }


def write_a11y_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    a11y: dict[str, Any],
    functional_result: str = "",
) -> list[str]:
    """Persist a11y sidecar result; functional_result recorded but not replaced."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": a11y.get("plugin") or "accessibility_checks",
        "opted_in": a11y.get("opted_in"),
        "checked": a11y.get("checked"),
        "status": a11y.get("status"),
        "violation_count": a11y.get("violation_count"),
        "violations": a11y.get("violations") or [],
        "url": a11y.get("url"),
        "error": a11y.get("error"),
        "message": a11y.get("message"),
        "functional_result": functional_result,
        "replaces_functional": False,
    }
    path = folder / "accessibility_result.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
