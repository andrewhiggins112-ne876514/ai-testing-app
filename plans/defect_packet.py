"""Defect packet preview from a failed case run (KAN-147 / FR-JIRA-4)."""
from __future__ import annotations

from typing import Any

from plans.store import get_plan
from settings.store import get_security_level, load_settings


def _latest_run(case: dict[str, Any], run_id: str | None) -> dict[str, Any] | None:
    runs = list(case.get("runs") or [])
    if not runs:
        return None
    if run_id:
        for run in reversed(runs):
            if run.get("id") == run_id:
                return run
    return runs[-1]


def defect_packet_preview(
    plan_id: str,
    case_id: str,
    *,
    run_id: str | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    target: dict[str, Any] | None = None
    for case in (plan.get("suite") or {}).get("cases") or []:
        if case.get("id") == cid:
            target = case
            break
    if target is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} not found.",
        }
    run = _latest_run(target, run_id)
    if run is None:
        return {
            "status": "error",
            "error": "no_run",
            "message": "Run this case first to build a defect packet.",
        }
    settings = load_settings()
    env_lines = [
        f"Security level: {lvl}",
        f"Target URL: {(settings.get('target_url') or '(not set)')}",
        f"Playwright: headed",
    ]
    src = target.get("source") if isinstance(target.get("source"), dict) else {}
    replication = [
        f"Open plan {plan_id} and case {cid}.",
        f"Run case headed against the configured target URL.",
        f"Observe result: {run.get('result')}.",
    ]
    if run.get("note"):
        replication.append(f"Runner note: {run.get('note')}")
    packet = {
        "symptom": target.get("name") or "Case failed",
        "expected": src.get("ref") or target.get("note") or "Case passes against the target.",
        "actual": run.get("note") or f"Result: {run.get('result')}",
        "environment": "\n".join(env_lines),
        "replication_steps": replication,
        "evidence_paths": list(run.get("evidence") or []),
        "failure_class": run.get("failure_class"),
        "jira_key": target.get("jira_key") or "",
        "run_id": run.get("id"),
        "confirm_required": True,
    }
    return {
        "status": "ok",
        "message": "Preview only — confirm is still required to create a Jira Bug.",
        "jira_write": False,
        "packet": packet,
        "plan_id": plan_id,
        "case_id": cid,
    }

