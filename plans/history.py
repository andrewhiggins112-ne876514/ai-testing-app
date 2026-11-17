"""Suite run history and compare two runs (KAN-175 / C10 / FR-PLAN-4).

Lists past suite runs with time, duration, pass/fail, and tag.
Compare highlights cases whose result changed; known issues stay labelled.
History is always scoped to the active security level (never cross-level).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from plans.known_issue import is_known_labelled, normalize_known_issue
from plans.store import get_plan


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _wall_duration_ms(suite_run: dict[str, Any]) -> int | None:
    start = _parse_iso(suite_run.get("started_at"))
    end = _parse_iso(suite_run.get("finished_at"))
    if start is None or end is None:
        return None
    delta = int((end - start).total_seconds() * 1000)
    return max(0, delta)


def _plan_cases(plan: dict[str, Any]) -> list[dict[str, Any]]:
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    return [c for c in cases if isinstance(c, dict)]


def _case_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for case in _plan_cases(plan):
        cid = str(case.get("id") or "").strip()
        if cid:
            out[cid] = case
    return out


def _run_by_ids(plan: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for case in _plan_cases(plan):
        cid = str(case.get("id") or "").strip()
        if not cid:
            continue
        for run in case.get("runs") or []:
            if not isinstance(run, dict):
                continue
            rid = str(run.get("id") or "").strip()
            if rid:
                found[(cid, rid)] = run
    return found


def _runs_for_suite(
    plan: dict[str, Any],
    suite_run: dict[str, Any],
) -> list[dict[str, Any]]:
    """Resolve case outcomes for one suite run (linked case_runs + suite_run_id)."""
    cases = _case_map(plan)
    by_ids = _run_by_ids(plan)
    sid = str(suite_run.get("id") or "").strip()
    rows: list[dict[str, Any]] = []
    seen_cases: set[str] = set()

    for link in suite_run.get("case_runs") or []:
        if not isinstance(link, dict):
            continue
        cid = str(link.get("case_id") or "").strip()
        rid = str(link.get("run_id") or "").strip()
        if not cid or not rid:
            continue
        case = cases.get(cid) or {}
        run = by_ids.get((cid, rid))
        if run is None:
            continue
        seen_cases.add(cid)
        rows.append(_case_outcome_row(case, run, cid))

    # Also pick up case runs stamped with suite_run_id but missing from case_runs links.
    if sid:
        for case in _plan_cases(plan):
            cid = str(case.get("id") or "").strip()
            if not cid or cid in seen_cases:
                continue
            for run in case.get("runs") or []:
                if not isinstance(run, dict):
                    continue
                if str(run.get("suite_run_id") or "").strip() != sid:
                    continue
                seen_cases.add(cid)
                rows.append(_case_outcome_row(case, run, cid))
                break

    for skip in suite_run.get("skipped") or []:
        if not isinstance(skip, dict):
            continue
        cid = str(skip.get("case_id") or "").strip()
        if not cid or cid in seen_cases:
            continue
        case = cases.get(cid) or {}
        reason = str(skip.get("reason") or "").strip()[:80]
        rows.append(
            {
                "case_id": cid,
                "case_name": str(case.get("name") or "")[:200],
                "run_id": None,
                "result": "skipped",
                "duration_ms": None,
                "failure_class": None,
                "known_issue": False,
                "known_issue_label": None,
                "skip_reason": reason or None,
            }
        )
        seen_cases.add(cid)

    return rows


def _case_outcome_row(
    case: dict[str, Any],
    run: dict[str, Any],
    case_id: str,
) -> dict[str, Any]:
    result = str(run.get("result") or "pending").strip().lower() or "pending"
    if result not in {"pass", "fail", "error", "pending", "skipped"}:
        result = "pending"
    known = is_known_labelled(run) or is_known_labelled(case)
    ki = normalize_known_issue(run.get("known_issue")) or normalize_known_issue(
        case.get("known_issue")
    )
    label = None
    if known:
        label = "known"
        if ki and ki.get("jira_key"):
            label = f"known:{ki['jira_key']}"
    duration = run.get("duration_ms")
    try:
        duration_ms = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_ms = None
    return {
        "case_id": case_id,
        "case_name": str(case.get("name") or "")[:200],
        "run_id": str(run.get("id") or "") or None,
        "result": result,
        "duration_ms": duration_ms,
        "failure_class": str(run.get("failure_class") or "").strip().lower()[:64] or None,
        "known_issue": known,
        "known_issue_label": label,
        "skip_reason": None,
    }


def summarize_suite_run(
    plan: dict[str, Any],
    suite_run: dict[str, Any],
) -> dict[str, Any]:
    """Build a history row: time, duration, pass, fail, tag (+ known labels)."""
    outcomes = _runs_for_suite(plan, suite_run)
    pass_count = sum(1 for o in outcomes if o.get("result") == "pass")
    fail_count = sum(1 for o in outcomes if o.get("result") == "fail")
    error_count = sum(1 for o in outcomes if o.get("result") == "error")
    skipped_count = sum(1 for o in outcomes if o.get("result") == "skipped")
    known_count = sum(1 for o in outcomes if o.get("known_issue"))
    duration_sum = 0
    any_duration = False
    for o in outcomes:
        if o.get("duration_ms") is not None:
            duration_sum += int(o["duration_ms"])
            any_duration = True
    wall = _wall_duration_ms(suite_run)
    duration_ms = duration_sum if any_duration else wall
    try:
        parallel_count = int(suite_run.get("parallel_count") or 1)
    except (TypeError, ValueError):
        parallel_count = 1
    env_name = str(suite_run.get("environment_name") or "").strip()[:40] or None
    return {
        "id": str(suite_run.get("id") or ""),
        "mode": str(suite_run.get("mode") or "suite"),
        "tag": suite_run.get("tag"),
        "parallel_count": max(1, parallel_count),
        "environment_name": env_name,
        "started_at": suite_run.get("started_at"),
        "finished_at": suite_run.get("finished_at"),
        "duration_ms": duration_ms,
        "pass": pass_count,
        "fail": fail_count,
        "error": error_count,
        "skipped": skipped_count,
        "known_issues": known_count,
        "case_count": len(outcomes),
        "source_suite_run_id": suite_run.get("source_suite_run_id"),
    }


def _find_suite_run(plan: dict[str, Any], suite_run_id: str) -> dict[str, Any] | None:
    sid = (suite_run_id or "").strip()
    if not sid:
        return None
    for item in plan.get("suite_runs") or []:
        if isinstance(item, dict) and str(item.get("id") or "") == sid:
            return item
    return None


def list_suite_history(
    plan_id: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """List past suite runs for a plan in the active (or given) security level only."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return {**loaded, "cross_level": False, "runs": []}
    plan = loaded["plan"]
    rows: list[dict[str, Any]] = []
    for idx, sr in enumerate(plan.get("suite_runs") or []):
        if not isinstance(sr, dict):
            continue
        summary = summarize_suite_run(plan, sr)
        summary["_ord"] = idx
        rows.append(summary)

    def sort_key(row: dict[str, Any]) -> tuple:
        # Newest first; equal timestamps keep later-appended runs first.
        return (
            str(row.get("finished_at") or row.get("started_at") or ""),
            int(row.get("_ord") or 0),
        )

    rows.sort(key=sort_key, reverse=True)
    for row in rows:
        row.pop("_ord", None)
    return {
        "status": "ok",
        "security_level": lvl,
        "cross_level": False,
        "plan_id": plan["id"],
        "plan_name": plan.get("name"),
        "count": len(rows),
        "runs": rows,
    }


def compare_suite_runs(
    plan_id: str,
    run_a: str,
    run_b: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Compare two suite runs; return cases whose result changed. Known issues labelled."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return {
            **loaded,
            "cross_level": False,
            "changes": [],
            "unchanged": 0,
        }
    plan = loaded["plan"]
    a_id = (run_a or "").strip()
    b_id = (run_b or "").strip()
    if not a_id or not b_id:
        return {
            "status": "error",
            "error": "runs_required",
            "message": "Provide two suite run ids to compare (a and b).",
            "security_level": lvl,
            "cross_level": False,
            "changes": [],
            "unchanged": 0,
        }
    if a_id == b_id:
        return {
            "status": "error",
            "error": "same_run",
            "message": "Choose two different suite runs to compare.",
            "security_level": lvl,
            "cross_level": False,
            "changes": [],
            "unchanged": 0,
        }
    sr_a = _find_suite_run(plan, a_id)
    sr_b = _find_suite_run(plan, b_id)
    if sr_a is None or sr_b is None:
        missing = a_id if sr_a is None else b_id
        return {
            "status": "error",
            "error": "suite_run_not_found",
            "message": f"Suite run {missing!r} was not found on this plan.",
            "security_level": lvl,
            "cross_level": False,
            "changes": [],
            "unchanged": 0,
        }

    outcomes_a = {o["case_id"]: o for o in _runs_for_suite(plan, sr_a)}
    outcomes_b = {o["case_id"]: o for o in _runs_for_suite(plan, sr_b)}
    all_ids = sorted(set(outcomes_a) | set(outcomes_b))
    changes: list[dict[str, Any]] = []
    unchanged = 0
    for cid in all_ids:
        left = outcomes_a.get(cid)
        right = outcomes_b.get(cid)
        left_result = left.get("result") if left else "not_run"
        right_result = right.get("result") if right else "not_run"
        name = (left or right or {}).get("case_name") or ""
        known_a = bool(left and left.get("known_issue"))
        known_b = bool(right and right.get("known_issue"))
        known = known_a or known_b
        label = None
        if known:
            label = (right or left or {}).get("known_issue_label") or "known"
        if left_result == right_result:
            unchanged += 1
            continue
        changes.append(
            {
                "case_id": cid,
                "case_name": name,
                "result_a": left_result,
                "result_b": right_result,
                "duration_ms_a": left.get("duration_ms") if left else None,
                "duration_ms_b": right.get("duration_ms") if right else None,
                "known_issue": known,
                "known_issue_label": label,
                "known_issue_a": known_a,
                "known_issue_b": known_b,
            }
        )

    return {
        "status": "ok",
        "security_level": lvl,
        "cross_level": False,
        "plan_id": plan["id"],
        "plan_name": plan.get("name"),
        "run_a": summarize_suite_run(plan, sr_a),
        "run_b": summarize_suite_run(plan, sr_b),
        "changes": changes,
        "changed": len(changes),
        "unchanged": unchanged,
    }
