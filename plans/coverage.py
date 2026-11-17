"""Coverage gaps for a plan vs project stories (KAN-163 / C4 / FR-PLAN-3 / FR-REP-1).

Lists stories with no case and stories whose cases are all disabled.
Never creates or enables cases — review-only.
"""
from __future__ import annotations

from typing import Any

from plans.store import get_plan

DEFAULT_LIST_MAX = 50
MAX_LIST_MAX = 100
_DEFAULT_TYPES = ("Story",)


def clamp_list_max(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIST_MAX
    return min(MAX_LIST_MAX, max(1, number))


def _norm_filter(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _matches_filter(row: dict[str, Any], needle: str) -> bool:
    if not needle:
        return True
    hay = f"{row.get('key') or ''} {row.get('summary') or ''}".lower()
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


def classify_story_cases(cases: list[dict[str, Any]]) -> str:
    """Return no_case | all_disabled | covered for one story's cases."""
    if not cases:
        return "no_case"
    runnable = [
        c
        for c in cases
        if c.get("enabled", True) and not c.get("archived", False)
    ]
    if not runnable:
        return "all_disabled"
    return "covered"


def coverage_from_plan(
    plan: dict[str, Any],
    *,
    project_stories: list[dict[str, Any]] | None = None,
    filter_text: str = "",
) -> dict[str, Any]:
    """Classify stories against plan cases. Does not create cases."""
    groups = _case_groups(plan)
    summaries: dict[str, str] = {}
    ordered_keys: list[str] = []

    sources = plan.get("sources") or {}
    for key in sources.get("jira_keys") or []:
        text = str(key or "").strip().upper()
        if text and text not in ordered_keys:
            ordered_keys.append(text)

    for row in project_stories or []:
        key = str(row.get("key") or "").strip().upper()
        if not key:
            continue
        if key not in ordered_keys:
            ordered_keys.append(key)
        summary = str(row.get("summary") or "").strip()
        if summary:
            summaries[key] = summary[:240]

    for key, cases in groups.items():
        if key not in ordered_keys:
            ordered_keys.append(key)
        if key not in summaries:
            # Prefer first case name as a soft label when Jira summary unknown.
            name = str((cases[0] or {}).get("name") or "").strip()
            if name:
                summaries[key] = name[:240]

    needle = _norm_filter(filter_text)
    no_case: list[dict[str, Any]] = []
    all_disabled: list[dict[str, Any]] = []
    covered: list[dict[str, Any]] = []

    for key in ordered_keys:
        cases = groups.get(key) or []
        kind = classify_story_cases(cases)
        row = {
            "key": key,
            "summary": summaries.get(key) or "",
            "case_count": len(cases),
            "enabled_case_count": sum(
                1
                for c in cases
                if c.get("enabled", True) and not c.get("archived", False)
            ),
            "gap": kind,
        }
        if not _matches_filter(row, needle):
            continue
        if kind == "no_case":
            no_case.append(row)
        elif kind == "all_disabled":
            all_disabled.append(row)
        else:
            covered.append(row)

    return {
        "status": "ok",
        "plan_id": plan.get("id"),
        "filter": filter_text or "",
        "no_case": no_case,
        "all_disabled": all_disabled,
        "covered": covered,
        "no_case_count": len(no_case),
        "all_disabled_count": len(all_disabled),
        "covered_count": len(covered),
        "cases_created": False,
        "message": (
            f"{len(no_case)} story(ies) with no case; "
            f"{len(all_disabled)} with all cases disabled. "
            "No cases were created."
        ),
    }


async def plan_coverage_gaps(
    plan_id: str,
    *,
    filter_text: str = "",
    project: str | None = None,
    list_max: Any = DEFAULT_LIST_MAX,
    issue_types: Any = None,
    level: str | None = None,
    include_project_list: bool = True,
) -> dict[str, Any]:
    """Load plan, optionally list project stories, return filterable gap lists.

    Never writes to Jira and never creates cases.
    """
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    capped = clamp_list_max(list_max)
    project_stories: list[dict[str, Any]] = []
    list_note = None
    project_key = None

    if include_project_list:
        from plugins.jira_plugin import list_stories
        from settings.store import load_settings

        settings = load_settings()
        project_key = (
            str(project or "").strip().upper()
            or str(settings.get("jira_project") or "").strip().upper()
        )
        if project_key:
            types = issue_types if issue_types is not None else list(_DEFAULT_TYPES)
            listed = await list_stories(
                project_key,
                max=capped,
                issue_types=types,
                include_description=False,
            )
            if listed.get("status") == "ok":
                project_stories = list(listed.get("stories") or [])[:capped]
                list_note = listed.get("note")
            else:
                # Still classify from the plan alone when Jira list fails.
                list_note = listed.get("message") or "project_list_unavailable"

    out = coverage_from_plan(
        plan,
        project_stories=project_stories,
        filter_text=filter_text,
    )
    out["security_level"] = loaded.get("security_level")
    out["project"] = project_key
    out["list_max"] = capped
    out["project_stories_considered"] = len(project_stories)
    out["list_note"] = list_note
    out["jira_write"] = False
    return out
