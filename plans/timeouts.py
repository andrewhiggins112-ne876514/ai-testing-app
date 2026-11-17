"""Case step timeouts (KAN-187 / D5 / FR-PLAN-2).

Hangs are an explicit budget. Default matches the Playwright runner's
current step click timeout (10_000 ms). Silent timeout inflation heal
is out of scope.
"""
from __future__ import annotations

from typing import Any

# Matches plugins.playwright_runner.run_playwright(click_timeout=10000).
DEFAULT_STEP_TIMEOUT_MS = 10000
# Guardrails so a typo cannot freeze the lab for hours.
MIN_STEP_TIMEOUT_MS = 500
MAX_STEP_TIMEOUT_MS = 300_000


def step_timeout_info() -> dict[str, Any]:
    """Public defaults for UI / API."""
    return {
        "status": "ok",
        "step_timeout_ms_default": DEFAULT_STEP_TIMEOUT_MS,
        "step_timeout_ms_min": MIN_STEP_TIMEOUT_MS,
        "step_timeout_ms_max": MAX_STEP_TIMEOUT_MS,
        "message": (
            f"Case step timeout defaults to {DEFAULT_STEP_TIMEOUT_MS} ms "
            f"(matches the current runner). Range "
            f"{MIN_STEP_TIMEOUT_MS}–{MAX_STEP_TIMEOUT_MS} ms."
        ),
    }


def resolve_step_timeout_ms(requested: Any = None) -> dict[str, Any]:
    """Validate step timeout. Default matches runner; refuse out of range."""
    if requested is None or requested == "":
        value = DEFAULT_STEP_TIMEOUT_MS
    else:
        try:
            value = int(requested)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "error": "step_timeout_invalid",
                "message": (
                    f"Step timeout must be an integer from "
                    f"{MIN_STEP_TIMEOUT_MS} to {MAX_STEP_TIMEOUT_MS} ms."
                ),
                **{k: v for k, v in step_timeout_info().items() if k != "status"},
            }
    if value < MIN_STEP_TIMEOUT_MS or value > MAX_STEP_TIMEOUT_MS:
        return {
            "status": "error",
            "error": "step_timeout_out_of_range",
            "message": (
                f"Step timeout {value} ms is outside "
                f"{MIN_STEP_TIMEOUT_MS}–{MAX_STEP_TIMEOUT_MS} ms."
            ),
            "requested": value,
            **{k: v for k, v in step_timeout_info().items() if k != "status"},
        }
    return {
        "status": "ok",
        "step_timeout_ms": value,
        "is_default": value == DEFAULT_STEP_TIMEOUT_MS,
        "step_timeout_ms_default": DEFAULT_STEP_TIMEOUT_MS,
        "step_timeout_ms_min": MIN_STEP_TIMEOUT_MS,
        "step_timeout_ms_max": MAX_STEP_TIMEOUT_MS,
    }


def case_step_timeout_ms(case: dict[str, Any] | None) -> int:
    """Read a case's step timeout, falling back to the runner default."""
    if not isinstance(case, dict):
        return DEFAULT_STEP_TIMEOUT_MS
    resolved = resolve_step_timeout_ms(case.get("step_timeout_ms"))
    if resolved.get("status") != "ok":
        return DEFAULT_STEP_TIMEOUT_MS
    return int(resolved["step_timeout_ms"])


def is_timeout_error(text: str | None) -> bool:
    """True when an error string is a timeout (Playwright / asyncio / budget)."""
    err = (text or "").strip().lower()
    if not err:
        return False
    return "timeout" in err or "timed out" in err or "time out" in err


def timeout_failure_message(
    raw_error: str | None,
    *,
    step_timeout_ms: int | None = None,
) -> str:
    """Ensure timeout failures say 'timeout' clearly (KAN-187 AC2)."""
    err = (raw_error or "").strip()
    budget = int(step_timeout_ms) if step_timeout_ms is not None else DEFAULT_STEP_TIMEOUT_MS
    if not is_timeout_error(err):
        return err[:500]
    if "timeout" not in err.lower():
        err = f"Timeout: {err}"
    marker = f"step timeout {budget} ms"
    if marker not in err.lower():
        err = f"{err} ({marker})"
    return err[:500]
