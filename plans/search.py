"""Search plans, cases, and failures in the active security level (KAN-173 / C9 / FR-PLAN-1).

Matches plan name, case name, Jira key, tag, and failure class.
Never searches across OFFICIAL/SECRET — results stay in the active level only.
"""
from __future__ import annotations

from typing import Any

from plans.store import get_plan, list_plans, plans_dir

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def clamp_limit(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return min(MAX_LIMIT, max(1, number))


def _norm_query(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _case_failure_classes(case: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for run in case.get("runs") or []:
        if not isinstance(run, dict):
            continue
        fc = str(run.get("failure_class") or "").strip().lower()
        if fc and fc not in seen:
            seen.append(fc)
    return seen


def _match_fields(
    needle: str,
    *,
    plan_name: str,
    case_name: str,
    jira_key: str,
    tags: list[str],
    failure_classes: list[str],
) -> list[str]:
    """Return which fields matched the needle (empty = no match)."""
    if not needle:
        return []
    matched: list[str] = []
    if needle in (plan_name or "").lower():
        matched.append("plan_name")
    if needle in (case_name or "").lower():
        matched.append("case_name")
    if needle in (jira_key or "").lower():
        matched.append("jira_key")
    for tag in tags:
        if needle in (tag or "").lower():
            matched.append("tag")
            break
    for fc in failure_classes:
        if needle in (fc or "").lower() or needle.replace(" ", "_") in (fc or "").lower():
            matched.append("failure_class")
            break
    return matched


def search_plans(
    query: str,
    *,
    limit: int | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Search plans/cases/failures for the active (or given) security level only."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    needle = _norm_query(query)
    capped = clamp_limit(limit if limit is not None else DEFAULT_LIMIT)

    if not needle:
        return {
            "status": "ok",
            "security_level": lvl,
            "query": "",
            "hits": [],
            "count": 0,
            "truncated": False,
            "cross_level": False,
            "message": "Enter a search term (plan name, case name, Jira key, tag, or failure class).",
        }

    listed = list_plans(level=lvl)
    hits: list[dict[str, Any]] = []
    truncated = False

    for summary in listed.get("plans") or []:
        if truncated:
            break
        plan_id = str(summary.get("id") or "").strip()
        if not plan_id:
            continue
        detail = get_plan(plan_id, level=lvl)
        if detail.get("status") != "ok" or not detail.get("plan"):
            continue
        plan = detail["plan"]
        plan_name = str(plan.get("name") or "")
        suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
        cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
        case_rows = [c for c in cases if isinstance(c, dict)]

        if not case_rows:
            # Plan-name-only match with no cases — still report the plan hit.
            matched = _match_fields(
                needle,
                plan_name=plan_name,
                case_name="",
                jira_key="",
                tags=[],
                failure_classes=[],
            )
            if matched:
                hits.append(
                    {
                        "plan_id": plan_id,
                        "plan_name": plan_name,
                        "case_id": None,
                        "case_name": None,
                        "jira_key": None,
                        "tags": [],
                        "failure_class": None,
                        "matched_fields": matched,
                    }
                )
                if len(hits) >= capped:
                    truncated = True
            continue

        for case in case_rows:
            if len(hits) >= capped:
                truncated = True
                break
            case_id = str(case.get("id") or "").strip()
            case_name = str(case.get("name") or "")
            jira_key = str(case.get("jira_key") or "").strip().upper()
            tags = [
                str(t).strip().lower()
                for t in (case.get("tags") or [])
                if str(t or "").strip()
            ]
            failure_classes = _case_failure_classes(case)
            matched = _match_fields(
                needle,
                plan_name=plan_name,
                case_name=case_name,
                jira_key=jira_key,
                tags=tags,
                failure_classes=failure_classes,
            )
            if not matched:
                continue
            latest_fc = failure_classes[-1] if failure_classes else None
            hits.append(
                {
                    "plan_id": plan_id,
                    "plan_name": plan_name,
                    "case_id": case_id or None,
                    "case_name": case_name or None,
                    "jira_key": jira_key or None,
                    "tags": tags,
                    "failure_class": latest_fc,
                    "matched_fields": matched,
                }
            )

    from plans.offline_read import annotate_search_hits

    annotated = annotate_search_hits(hits, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "query": needle,
        "hits": annotated,
        "count": len(annotated),
        "truncated": truncated,
        "cross_level": False,
        "plans_root": str(plans_dir(lvl)),
        "search_works_offline": True,
        "local_only": True,
        "jira_write": False,
    }
