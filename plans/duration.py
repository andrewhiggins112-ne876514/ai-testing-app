"""Duration on the run and the case (KAN-191 / D7 / FR-PLAN-4 / FR-REP-1).

Each case run and suite run stores duration locally. History compare can show
duration change so a suite that got much slower is a signal. No cloud upload
or perf analytics.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def duration_info() -> dict[str, Any]:
    """Public defaults for UI / API — local only."""
    return {
        "status": "ok",
        "channel": "local",
        "upload": False,
        "cloud_perf": False,
        "message": (
            "Each case and suite run stores duration locally. "
            "History compare can show duration change. No upload."
        ),
    }


def parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def wall_duration_ms(started_at: Any, finished_at: Any) -> int | None:
    """Wall-clock duration between two ISO timestamps, in milliseconds."""
    start = parse_iso(started_at)
    end = parse_iso(finished_at)
    if start is None or end is None:
        return None
    delta = int((end - start).total_seconds() * 1000)
    return max(0, delta)


def coerce_duration_ms(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    return n


def duration_delta_ms(a: Any, b: Any) -> int | None:
    """Signed change from a → b (positive = slower). None if either missing."""
    left = coerce_duration_ms(a)
    right = coerce_duration_ms(b)
    if left is None or right is None:
        return None
    return right - left


def resolve_suite_duration_ms(
    suite_run: dict[str, Any] | None,
    *,
    case_duration_sum_ms: int | None = None,
) -> int | None:
    """Prefer case-duration sum (signal), else stored, else wall clock.

    Wall timestamps are second-precision, so sub-second suites often store 0;
    case sums remain the useful signal for “got slower”.
    """
    if not isinstance(suite_run, dict):
        return None
    if case_duration_sum_ms is not None:
        return max(0, int(case_duration_sum_ms))
    stored = coerce_duration_ms(suite_run.get("duration_ms"))
    if stored is not None and stored > 0:
        return stored
    wall = wall_duration_ms(suite_run.get("started_at"), suite_run.get("finished_at"))
    if wall is not None:
        return wall
    return stored
