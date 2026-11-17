"""First-hour home checklist widget (KAN-215 / F7 / FR-UI-6 + FR-UI-1).

Screen-drawer HUD on orb home: connection → first plan → first run.
Auto-hides when all steps are done; reopen from the drawer. Never blocks chat
or App areas (not a forced wizard).
"""
from __future__ import annotations

from typing import Any

from plans.store import get_plan, list_plans
from settings.connection_health import connection_checklist


def _connection_done(checklist: dict[str, Any]) -> bool:
    """Configured enough to count as first-hour connection (no live probe)."""
    if checklist.get("jira_credentials_configured"):
        return True
    if (checklist.get("jira_url") or "").strip():
        return True
    if (checklist.get("target_url") or "").strip():
        return True
    if (checklist.get("target_app_path") or "").strip():
        return True
    return False


def _has_finished_run(plan: dict[str, Any]) -> bool:
    for sr in plan.get("suite_runs") or []:
        if isinstance(sr, dict) and (sr.get("finished_at") or sr.get("started_at")):
            return True
    for case in plan.get("cases") or []:
        if not isinstance(case, dict):
            continue
        for run in case.get("runs") or []:
            if isinstance(run, dict) and (
                run.get("finished_at") or run.get("result") or run.get("id")
            ):
                return True
    return False


def home_checklist_summary(level: str | None = None) -> dict[str, Any]:
    """Orb-home first-hour checklist: connection, first plan, first run."""
    checklist = connection_checklist()
    listed = list_plans(level)
    plans_meta = list(listed.get("plans") or [])
    plan_count = len(plans_meta)
    first_plan_done = plan_count > 0
    first_run_done = False
    first_plan_id = ""
    if first_plan_done:
        for row in plans_meta:
            pid = str((row or {}).get("id") or "").strip()
            if not pid:
                continue
            if not first_plan_id:
                first_plan_id = pid
            loaded = get_plan(pid, level=level)
            plan = loaded.get("plan") if loaded.get("status") == "ok" else None
            if isinstance(plan, dict) and _has_finished_run(plan):
                first_run_done = True
                first_plan_id = pid
                break

    connection_done = _connection_done(checklist)
    steps = [
        {
            "id": "connection",
            "label": "Connection",
            "done": connection_done,
            "action": "open_settings",
            "hint": (
                "Connection keys saved for this level."
                if connection_done
                else "Set Jira or a target URL in Settings."
            ),
        },
        {
            "id": "first_plan",
            "label": "First plan",
            "done": first_plan_done,
            "action": "open_plans",
            "hint": (
                f"{plan_count} plan(s) on this level."
                if first_plan_done
                else "Create a plan or start a template."
            ),
            "plan_id": first_plan_id or None,
        },
        {
            "id": "first_run",
            "label": "First run",
            "done": first_run_done,
            "action": "open_plans",
            "hint": (
                "At least one run is recorded."
                if first_run_done
                else "Run a case or suite from Plans."
            ),
            "plan_id": first_plan_id or None,
        },
    ]
    done_count = sum(1 for s in steps if s["done"])
    all_done = done_count == len(steps)
    return {
        "status": "ok",
        "home_only": True,
        "blocks_app": False,
        "forced_wizard": False,
        "auto_hide_when_done": True,
        "all_done": all_done,
        "done_count": done_count,
        "step_count": len(steps),
        "steps": steps,
        "security_level": listed.get("security_level") or checklist.get("security_level"),
        "message": (
            "First-hour checklist complete — hidden unless reopened from the Screen drawer."
            if all_done
            else f"First-hour checklist: {done_count}/{len(steps)} done."
        ),
    }
