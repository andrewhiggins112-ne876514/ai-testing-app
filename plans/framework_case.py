"""Another framework runner on the same in-app suite (KAN-233 / G9 / FR-PLUG-3).

Cases can select Playwright / Selenium / Cypress. Playwright remains the
default ready runner. Until Selenium/Cypress runners exist, those selections
return not-implemented and never mark the run as passed. Framework switch
settings stub is kept (not deleted).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plans.store import add_case, get_plan
from plugins.framework_switch import (
    DEFAULT_FRAMEWORK,
    normalize_framework,
)


def parse_framework_ref(ref: str) -> dict[str, Any]:
    """Parse source.ref: bare id, or JSON ``{\"framework\":\"selenium\"}``."""
    text = (ref or "").strip()
    if not text:
        return {"framework": DEFAULT_FRAMEWORK}
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"framework": normalize_framework(text[:40])}
        if isinstance(parsed, dict):
            return {
                "framework": normalize_framework(
                    str(
                        parsed.get("framework")
                        or parsed.get("test_framework")
                        or parsed.get("id")
                        or ""
                    )
                )
            }
    return {"framework": normalize_framework(text[:40])}


def encode_framework_ref(framework: str = "") -> str:
    """Encode selected framework id into source.ref (cap 40)."""
    return normalize_framework(framework)[:40]


def add_framework_case(
    plan_id: str,
    name: str = "",
    *,
    framework: str = "selenium",
    note: str = "",
    tags: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add a framework-selection case to an existing plan suite."""
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    fw = normalize_framework(framework or "selenium")
    # Prefer an explicit non-playwright pick for G9 “another” runner UX;
    # unknown values still normalize to playwright via framework_switch.
    if not (framework or "").strip():
        fw = "selenium"
    elif (framework or "").strip().lower() not in {"playwright", "selenium", "cypress"}:
        return {
            "status": "error",
            "error": "unknown_framework",
            "message": (
                f"Unknown framework {framework!r}. "
                "Choose playwright, selenium, or cypress."
            ),
            "security_level": loaded.get("security_level"),
        }
    else:
        fw = (framework or "").strip().lower()

    label = (name or "").strip() or f"Framework — {fw}"
    case_tags = list(tags or [])
    lowered = [t.lower() for t in case_tags]
    if "framework" not in lowered:
        case_tags = ["framework", fw] + case_tags
    elif fw not in lowered:
        case_tags = case_tags + [fw]

    ready = fw == DEFAULT_FRAMEWORK
    default_note = (
        f"Framework case — {fw} "
        + (
            "(default ready runner)."
            if ready
            else "(not implemented yet; run must not mark passed)."
        )
    )
    return add_case(
        plan_id,
        label,
        note=note or default_note,
        tags=case_tags,
        source_kind="framework",
        source_ref=encode_framework_ref(fw),
        level=level,
    )


def write_framework_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    framework_result: dict[str, Any],
) -> list[str]:
    """Persist framework attempt result as evidence (same run model)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": framework_result.get("plugin") or "framework_switch",
        "framework": framework_result.get("framework"),
        "status": framework_result.get("status"),
        "ok": framework_result.get("ok"),
        "action": framework_result.get("action"),
        "message": framework_result.get("message"),
        "implemented": framework_result.get("implemented"),
    }
    path = folder / "framework_result.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
