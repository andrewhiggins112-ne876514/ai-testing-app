"""Empty-lab home status + starter template plan (KAN-135 / FR-UI-1 / FR-UI-6 / FR-PLAN-1).

When the active level has no plans, the orb home checklist offers the next actions.
The starter template creates a normal editable plan — not a second welcome canvas.
"""
from __future__ import annotations

from typing import Any

from plans.store import add_case, create_plan, get_plan, list_plans

_STARTER_CASES: tuple[dict[str, Any], ...] = (
    {
        "name": "Open the target application",
        "note": "Navigate to the connected target URL (edit if your AUT differs).",
        "tags": ["starter", "smoke"],
        "source_ref": "starter-template: open target",
    },
    {
        "name": "Confirm a key screen or control is visible",
        "note": "Rename and refine this case to match the AUT under test.",
        "tags": ["starter"],
        "source_ref": "starter-template: key screen",
    },
    {
        "name": "Negative: missing page or control is handled",
        "note": "Expect a clear fail — never treat a tool/browser error as a pass.",
        "tags": ["starter", "negative"],
        "source_ref": "starter-template: negative path",
    },
)


def lab_home_status(level: str | None = None) -> dict[str, Any]:
    """Orb-home empty-state payload: checklist when no plans exist for this level."""
    listed = list_plans(level)
    plans = list(listed.get("plans") or [])
    empty = len(plans) == 0
    checklist: list[dict[str, str]] = []
    if empty:
        checklist = [
            {
                "id": "check_connection",
                "label": "Check connection",
                "action": "connection_health",
            },
            {
                "id": "draft_from_story",
                "label": "Draft from story key",
                "action": "draft_plan",
            },
            {
                "id": "start_template",
                "label": "Start a template",
                "action": "starter_template",
            },
        ]
    return {
        "status": "ok",
        "security_level": listed.get("security_level"),
        "empty": empty,
        "plan_count": len(plans),
        "checklist": checklist,
        "message": (
            "No plan yet — check connection, draft from a story key, or start a template."
            if empty
            else f"{len(plans)} plan(s) for this level."
        ),
    }


def create_starter_plan(
    *,
    name: str = "Starter plan",
    level: str | None = None,
) -> dict[str, Any]:
    """Create a local plan with editable starter cases. No Jira writes."""
    created = create_plan(
        name=(name or "Starter plan").strip() or "Starter plan",
        intent=(
            "Starter template for a new lab. Edit case names and notes before running. "
            "Nothing was written to Jira."
        ),
        sources={"jira_keys": [], "documents": []},
        level=level,
    )
    if created.get("status") != "ok":
        return created
    plan = created["plan"]
    plan_id = plan["id"]
    cases: list[dict[str, Any]] = []
    for item in _STARTER_CASES:
        added = add_case(
            plan_id,
            item["name"],
            tags=list(item.get("tags") or []),
            note=str(item.get("note") or ""),
            enabled=True,
            source_kind="manual-draft",
            source_ref=str(item.get("source_ref") or "starter-template"),
            level=level,
        )
        if added.get("status") == "ok" and added.get("case"):
            cases.append(added["case"])

    refreshed = get_plan(plan_id, level=level)
    return {
        "status": "ok",
        "message": (
            f"Starter plan created with {len(cases)} editable case(s). "
            "Open Plans to rename, reorder, or disable before a run."
        ),
        "jira_write": False,
        "template": "starter",
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else plan,
        "case_count": len(cases),
        "home": lab_home_status(level),
    }
