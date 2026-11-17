"""Traceability matrix for a plan (KAN-167 / C6 / FR-REP-1 + FR-PLAN-4).

One row per story key: case count, last result, linked bug keys, known-issue flag.
Keys with no runs are ``not_loaded`` — never treated as pass.
"""
from __future__ import annotations

import re
from typing import Any

from plans.known_issue import is_known_labelled, normalize_known_issue
from plans.store import get_plan

_JIRA_KEY_OK = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")


def _norm_filter(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _matches_filter(row: dict[str, Any], needle: str) -> bool:
    if not needle:
        return True
    bugs = " ".join(str(b) for b in (row.get("linked_bug_keys") or []))
    hay = f"{row.get('story_key') or ''} {row.get('summary') or ''} {bugs}".lower()
    return needle in hay


def _plan_cases(plan: dict[str, Any]) -> list[dict[str, Any]]:
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    return [c for c in cases if isinstance(c, dict)]


def _case_groups(plan: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for raw in _plan_cases(plan):
        key = str(raw.get("jira_key") or "").strip().upper()
        if not key:
            continue
        groups.setdefault(key, []).append(raw)
    return groups


def _run_sort_key(run: dict[str, Any]) -> str:
    return str(run.get("finished_at") or run.get("started_at") or "")


def _latest_run_for_cases(
    cases: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (case, run) for the chronologically latest run among cases."""
    best_case: dict[str, Any] | None = None
    best_run: dict[str, Any] | None = None
    best_key = ""
    for case in cases:
        runs = case.get("runs") if isinstance(case.get("runs"), list) else []
        for run in runs:
            if not isinstance(run, dict):
                continue
            key = _run_sort_key(run)
            if best_run is None or key >= best_key:
                best_key = key
                best_run = run
                best_case = case
    return best_case, best_run


def _primary_case_id(
    cases: list[dict[str, Any]],
    latest_case: dict[str, Any] | None,
) -> str | None:
    if latest_case and latest_case.get("id"):
        return str(latest_case.get("id"))
    for case in cases:
        if case.get("enabled", True) and not case.get("archived", False) and case.get("id"):
            return str(case.get("id"))
    for case in cases:
        if case.get("id"):
            return str(case.get("id"))
    return None


def _linked_bug_keys(cases: list[dict[str, Any]], story_key: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    story = (story_key or "").strip().upper()

    def add(raw: Any) -> None:
        key = str(raw or "").strip().upper()
        if not key or key == story or not _JIRA_KEY_OK.match(key):
            return
        if key in seen:
            return
        seen.add(key)
        found.append(key)

    for case in cases:
        ki = normalize_known_issue(case.get("known_issue"))
        if ki:
            add(ki.get("jira_key"))
        for run in case.get("runs") or []:
            if not isinstance(run, dict):
                continue
            rki = normalize_known_issue(run.get("known_issue"))
            if rki:
                add(rki.get("jira_key"))
    return found


def _known_flag(cases: list[dict[str, Any]]) -> bool:
    for case in cases:
        if is_known_labelled(case):
            return True
        for run in case.get("runs") or []:
            if isinstance(run, dict) and is_known_labelled(run):
                return True
    return False


def _row_for_story(
    story_key: str,
    cases: list[dict[str, Any]],
    summary: str = "",
) -> dict[str, Any]:
    latest_case, latest_run = _latest_run_for_cases(cases)
    if latest_run is None:
        last_result = "not_loaded"
    else:
        last_result = str(latest_run.get("result") or "pending").strip().lower() or "pending"
        # Never invent pass for empty/missing — keep pending/fail/error as-is.
        if last_result not in {"pass", "fail", "error", "pending", "skipped"}:
            last_result = "not_loaded"

    return {
        "story_key": story_key,
        "summary": (summary or "")[:240],
        "case_count": len(cases),
        "last_result": last_result,
        "linked_bug_keys": _linked_bug_keys(cases, story_key),
        "known_issue": _known_flag(cases),
        "primary_case_id": _primary_case_id(cases, latest_case),
    }


def traceability_from_plan(
    plan: dict[str, Any],
    *,
    filter_text: str = "",
) -> dict[str, Any]:
    """Build the C6 matrix rows from a plan. Local only — no Jira writes."""
    groups = _case_groups(plan)
    summaries: dict[str, str] = {}
    ordered_keys: list[str] = []

    sources = plan.get("sources") if isinstance(plan.get("sources"), dict) else {}
    for key in sources.get("jira_keys") or []:
        text = str(key or "").strip().upper()
        if text and text not in ordered_keys:
            ordered_keys.append(text)

    for key, cases in groups.items():
        if key not in ordered_keys:
            ordered_keys.append(key)
        if key not in summaries:
            name = str((cases[0] or {}).get("name") or "").strip()
            if name:
                summaries[key] = name[:240]

    needle = _norm_filter(filter_text)
    rows: list[dict[str, Any]] = []
    for key in ordered_keys:
        cases = groups.get(key) or []
        row = _row_for_story(key, cases, summaries.get(key) or "")
        if _matches_filter(row, needle):
            rows.append(row)

    return {
        "status": "ok",
        "plan_id": plan.get("id"),
        "filter": filter_text or "",
        "rows": rows,
        "row_count": len(rows),
        "message": f"{len(rows)} story row(s) in the traceability matrix.",
    }


def plan_traceability_matrix(
    plan_id: str,
    *,
    filter_text: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Load plan and return the filterable C6 matrix."""
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    out = traceability_from_plan(plan, filter_text=filter_text)
    out["security_level"] = loaded.get("security_level")
    out["jira_write"] = False
    return out
