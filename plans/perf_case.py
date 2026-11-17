"""Performance budget on plan cases (KAN-229 / G7).

Case stores optional numeric budget_ms. Over budget fails that case on run.
Cases without a budget are unchanged. Local duration collection only.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plans.store import add_case, get_plan, update_case
from plugins.performance_budget import (
    DEFAULT_BUDGET_MS,
    PLUGIN_NAME,
    coerce_budget_ms,
)

_OPT_IN_TAGS = frozenset({"perf", "performance", "budget"})


def case_performance_budget_ms(case: dict[str, Any] | None) -> int | None:
    """Return the case's numeric budget, or None when unset."""
    if not isinstance(case, dict):
        return None
    return coerce_budget_ms(case.get("performance_budget_ms"))


def add_perf_budget_case(
    plan_id: str,
    name: str = "",
    *,
    budget_ms: int | None = None,
    note: str = "",
    tags: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add a browser case with a numeric performance budget (local timing)."""
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    budget = coerce_budget_ms(budget_ms if budget_ms is not None else DEFAULT_BUDGET_MS)
    if budget is None:
        budget = DEFAULT_BUDGET_MS

    case_tags = list(tags or [])
    lowered = [str(t).lower() for t in case_tags]
    if not _OPT_IN_TAGS.intersection(lowered):
        case_tags = ["perf"] + case_tags

    label = (name or "").strip() or f"Browser case + perf budget ({budget} ms)"
    out = add_case(
        plan_id,
        label,
        note=note
        or (
            f"Browser case with local performance budget {budget} ms — "
            "over budget fails this case; cases without a budget are unchanged."
        ),
        tags=case_tags,
        source_kind="manual-draft",
        source_ref="",
        performance_budget_ms=budget,
        level=level,
    )
    if out.get("status") == "ok" and out.get("case"):
        out["performance_budget_ms"] = budget
        out["local_only"] = True
        out["cloud_apm"] = False
        out["message"] = (
            f"Performance budget {budget} ms set on case (local collection only)."
        )
    return out


def set_performance_budget(
    plan_id: str,
    case_id: str,
    *,
    budget_ms: int | None,
    level: str | None = None,
) -> dict[str, Any]:
    """Set or clear a numeric performance budget on an existing case."""
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

    budget = coerce_budget_ms(budget_ms)
    tags = list(target.get("tags") or [])
    lowered = [str(t).lower() for t in tags]
    if budget is not None:
        if not _OPT_IN_TAGS.intersection(lowered):
            tags = ["perf"] + tags
    else:
        tags = [t for t in tags if str(t).lower() not in _OPT_IN_TAGS]

    out = update_case(
        plan_id,
        cid,
        tags=tags,
        performance_budget_ms=budget,
        clear_performance_budget=(budget is None),
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
        "performance_budget_ms": budget,
        "local_only": True,
        "cloud_apm": False,
        "message": (
            f"Performance budget set to {budget} ms."
            if budget is not None
            else "Performance budget cleared — case result unchanged by budget."
        ),
    }


def write_perf_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    performance: dict[str, Any],
) -> list[str]:
    """Persist local performance-budget evaluation (no cloud APM)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": performance.get("plugin") or PLUGIN_NAME,
        "budget_ms": performance.get("budget_ms"),
        "duration_ms": performance.get("duration_ms"),
        "over_budget": performance.get("over_budget"),
        "status": performance.get("status"),
        "message": performance.get("message"),
        "local_only": True,
        "cloud_apm": False,
    }
    path = folder / "performance_budget.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
