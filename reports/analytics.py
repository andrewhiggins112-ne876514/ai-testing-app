"""Local report visual analytics (KAN-384 / FR-REP-1 + FR-REP-4 deepen).

Charts consume saved report JSON only — no telemetry cloud.
Quiet empty when there are no real metrics (never invent pass/fail).
"""
from __future__ import annotations

from typing import Any, Mapping


def _as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _step_pass_fail(steps: list) -> tuple[int, int]:
    passed = failed = 0
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        status = str(step.get("status") or "").lower()
        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
    return passed, failed


def _failure_classes(steps: list) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        status = str(step.get("status") or "").lower()
        if status != "fail":
            continue
        label = (
            str(
                step.get("failure_class")
                or step.get("classification")
                or step.get("error_class")
                or "unclassified"
            ).strip()
            or "unclassified"
        )
        counts[label] = counts.get(label, 0) + 1
    return [
        {"label": key, "count": counts[key]}
        for key in sorted(counts.keys(), key=lambda k: (-counts[k], k.lower()))
    ]


def _bugs_by_story(sections: Mapping[str, Any], result: Mapping[str, Any]) -> list[dict[str, Any]]:
    bugs = sections.get("bugs") if isinstance(sections.get("bugs"), Mapping) else {}
    raw = bugs.get("counts_by_story") if isinstance(bugs, Mapping) else None
    if isinstance(raw, Mapping) and raw:
        items = [
            {"story": str(key), "count": int(value)}
            for key, value in raw.items()
            if _as_int(value) is not None and int(value) > 0
        ]
        items.sort(key=lambda row: (-row["count"], row["story"].lower()))
        return items
    # Fallback: count bug list by story_key when counts map missing.
    items_raw = bugs.get("items") if isinstance(bugs, Mapping) else None
    if not isinstance(items_raw, list):
        items_raw = result.get("bugs") if isinstance(result.get("bugs"), list) else []
    counts: dict[str, int] = {}
    for item in items_raw or []:
        if not isinstance(item, Mapping):
            continue
        story = str(item.get("story_key") or item.get("story") or "unlinked").strip() or "unlinked"
        counts[story] = counts.get(story, 0) + 1
    return [
        {"story": key, "count": counts[key]}
        for key in sorted(counts.keys(), key=lambda k: (-counts[k], k.lower()))
    ]


def _duration_seconds(result: Mapping[str, Any], summary: Mapping[str, Any]) -> float | None:
    for source in (summary, result):
        for key in ("duration_seconds", "duration_s", "elapsed_seconds"):
            value = _as_float(source.get(key))
            if value is not None and value >= 0:
                return value
        ms = _as_float(source.get("duration_ms") or source.get("elapsed_ms"))
        if ms is not None and ms >= 0:
            return round(ms / 1000.0, 3)
        duration = source.get("duration")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            # Heuristic: large ints are ms.
            raw = float(duration)
            if raw >= 1000:
                return round(raw / 1000.0, 3)
            if raw >= 0:
                return raw
    return None


def build_report_analytics(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Derive chart-ready metrics from a saved report JSON payload.

    Returns ``has_metrics`` False with a quiet empty hint when there is nothing
    real to chart (no invented zeros-as-success).
    """
    empty = {
        "has_metrics": False,
        "pass_fail": None,
        "coverage": None,
        "duration": None,
        "failure_classes": [],
        "bugs_by_story": [],
        "empty_hint": "No chart metrics in this report.",
    }
    if not isinstance(payload, Mapping):
        return empty
    if payload.get("message") and len(payload) <= 2:
        return empty

    sections = payload.get("sections") if isinstance(payload.get("sections"), Mapping) else {}
    summary = sections.get("summary") if isinstance(sections.get("summary"), Mapping) else {}
    stories = sections.get("stories") if isinstance(sections.get("stories"), Mapping) else {}
    result = payload.get("result") if isinstance(payload.get("result"), Mapping) else {}
    steps = list(summary.get("steps") or []) if isinstance(summary.get("steps"), list) else []
    if not steps and isinstance(result.get("steps"), list):
        steps = list(result.get("steps") or [])

    passed = _as_int(summary.get("tests_passed", summary.get("passed")))
    failed = _as_int(summary.get("tests_failed", summary.get("failed")))
    if passed is None or failed is None:
        step_passed, step_failed = _step_pass_fail(steps)
        if passed is None:
            passed = step_passed
        if failed is None:
            failed = step_failed

    stories_covered = _as_int(
        summary.get("stories_covered")
        or stories.get("covered_count")
        or stories.get("count")
    )
    story_keys: list[str] = []
    for key_name in ("keys", "covered"):
        raw_keys = stories.get(key_name)
        if isinstance(raw_keys, list):
            story_keys = [str(k).strip() for k in raw_keys if str(k).strip()]
            break
    if stories_covered is None:
        stories_covered = len(story_keys)

    has_step_signal = bool(steps) or (passed is not None and failed is not None and (passed + failed) > 0)
    has_coverage_signal = bool(story_keys) or (stories_covered is not None and stories_covered > 0)
    failure_classes = _failure_classes(steps)
    bugs_by_story = _bugs_by_story(sections, result)
    duration_s = _duration_seconds(result, summary)
    has_extra = bool(failure_classes) or bool(bugs_by_story) or duration_s is not None

    if not has_step_signal and not has_coverage_signal and not has_extra:
        return empty

    pass_fail = None
    if has_step_signal and passed is not None and failed is not None:
        total = passed + failed
        pass_fail = {
            "passed": passed,
            "failed": failed,
            "total": total,
            "pass_rate_percent": (
                round(100.0 * passed / total, 1) if total > 0 else None
            ),
        }

    coverage = None
    if has_coverage_signal:
        coverage = {
            "stories_covered": int(stories_covered or 0),
            "stories": story_keys,
        }

    duration = None
    if duration_s is not None:
        duration = {
            "seconds": duration_s,
            "label": f"{duration_s:g}s",
        }

    has_metrics = pass_fail is not None or coverage is not None or has_extra
    return {
        "has_metrics": has_metrics,
        "pass_fail": pass_fail,
        "coverage": coverage,
        "duration": duration,
        "failure_classes": failure_classes,
        "bugs_by_story": bugs_by_story,
        "empty_hint": "" if has_metrics else "No chart metrics in this report.",
    }
