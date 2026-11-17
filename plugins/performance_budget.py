"""Performance budget plugin (KAN-229 / G7 / FR-PLUG-1).

Case may store a numeric duration budget (ms). Local wall/run timing only —
no cloud APM. Over budget fails that case; cases without a budget are unchanged.
"""
from __future__ import annotations

from typing import Any

PLUGIN_NAME = "performance_budget"
DEFAULT_BUDGET_MS = 5000
_MIN_BUDGET_MS = 1
_MAX_BUDGET_MS = 3_600_000  # 1 hour ceiling


def coerce_budget_ms(value: Any) -> int | None:
    """Parse optional numeric budget. None / empty / invalid → no budget."""
    if value is None or value is False:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < _MIN_BUDGET_MS:
        return None
    return min(n, _MAX_BUDGET_MS)


def evaluate_performance_budget(
    *,
    duration_ms: int | None,
    budget_ms: int | None,
) -> dict[str, Any]:
    """Compare local duration to optional budget. Local collection only."""
    budget = coerce_budget_ms(budget_ms)
    try:
        duration = int(duration_ms) if duration_ms is not None else None
    except (TypeError, ValueError):
        duration = None

    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "budget_ms": budget,
        "duration_ms": duration,
        "over_budget": False,
        "applied": False,
        "status": "skipped",
        "message": "No performance budget on case — result unchanged.",
        "local_only": True,
        "cloud_apm": False,
    }
    if budget is None:
        return base

    if duration is None:
        return {
            **base,
            "applied": True,
            "status": "no_duration",
            "message": (
                f"Budget {budget} ms set but no local duration recorded — "
                "result unchanged."
            ),
        }

    over = duration > budget
    return {
        **base,
        "applied": True,
        "over_budget": over,
        "status": "fail" if over else "pass",
        "message": (
            f"Over performance budget: {duration} ms > {budget} ms (local)."
            if over
            else f"Within performance budget: {duration} ms ≤ {budget} ms (local)."
        ),
    }


def apply_performance_budget(
    *,
    result: str,
    duration_ms: int | None,
    budget_ms: int | None,
    note: str = "",
    failure_class: str | None = None,
) -> dict[str, Any]:
    """Apply budget: over budget fails the case; no budget leaves result alone."""
    perf = evaluate_performance_budget(duration_ms=duration_ms, budget_ms=budget_ms)
    out_result = str(result or "pending").strip().lower() or "pending"
    out_note = str(note or "")
    out_fc = failure_class

    if perf.get("over_budget") and out_result == "pass":
        out_result = "fail"
        out_fc = out_fc or "product_bug"
        msg = str(perf.get("message") or "Over performance budget.")
        out_note = (f"{out_note} | {msg}" if out_note else msg)[:2000]
    elif perf.get("over_budget") and out_result in {"fail", "error"}:
        msg = str(perf.get("message") or "Over performance budget.")
        out_note = (f"{out_note} | {msg}" if out_note else msg)[:2000]
        out_fc = out_fc or "product_bug"

    return {
        "result": out_result,
        "note": out_note,
        "failure_class": out_fc,
        "performance": perf,
    }
