"""Export a chosen plan case run with report section toggles (KAN-159 / C2).

Section include/exclude stays on the saved report profile (FR-REP-2).
Heal proposals for the same run_id surface in Heal review (FR-HEAL-2).
"""
from __future__ import annotations

from typing import Any, Mapping

from plans.store import get_plan, list_plans
from plugins.heal_policy import list_pending_heals
from reports.exporter import export_run
from reports.sections import load_report_sections, normalize_sections


def list_exportable_runs(*, level: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List recent case runs for the active level (newest first)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    listed = list_plans(level=lvl)
    summaries = list(listed.get("plans") or [])
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        pid = str(summary.get("id") or "").strip()
        if not pid:
            continue
        loaded = get_plan(pid, level=lvl)
        if loaded.get("status") != "ok":
            continue
        plan = loaded.get("plan") if isinstance(loaded.get("plan"), dict) else {}
        pname = str(plan.get("name") or summary.get("name") or pid)
        for case in (plan.get("suite") or {}).get("cases") or []:
            if not isinstance(case, dict):
                continue
            cid = str(case.get("id") or "")
            cname = str(case.get("name") or cid)
            for run in case.get("runs") or []:
                if not isinstance(run, dict):
                    continue
                rid = str(run.get("id") or "").strip()
                if not rid:
                    continue
                rows.append(
                    {
                        "plan_id": pid,
                        "plan_name": pname,
                        "case_id": cid,
                        "case_name": cname,
                        "run_id": rid,
                        "result": run.get("result"),
                        "finished_at": run.get("finished_at") or run.get("started_at"),
                        "duration_ms": run.get("duration_ms"),
                        "suite_run_id": run.get("suite_run_id"),
                        "jira_key": case.get("jira_key") or "",
                        "label": (
                            f"{pname} · {cname} · {rid} · "
                            f"{run.get('result') or 'pending'}"
                        ),
                    }
                )
    rows.sort(
        key=lambda r: str(r.get("finished_at") or ""),
        reverse=True,
    )
    capped = rows[: max(1, min(int(limit or 50), 200))]
    return {
        "status": "ok",
        "security_level": lvl,
        "runs": capped,
        "count": len(capped),
    }


def _find_case_run(
    plan: dict[str, Any],
    case_id: str,
    run_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    cid = (case_id or "").strip()
    rid = (run_id or "").strip()
    for case in (plan.get("suite") or {}).get("cases") or []:
        if not isinstance(case, dict) or case.get("id") != cid:
            continue
        for run in case.get("runs") or []:
            if isinstance(run, dict) and run.get("id") == rid:
                return case, run
        return case, None
    return None, None


def build_result_for_run(
    plan_id: str,
    case_id: str,
    run_id: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Build a report ``result`` body for one plan case run."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    case, run = _find_case_run(plan, case_id, run_id)
    if case is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {case_id!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    if run is None:
        return {
            "status": "error",
            "error": "run_not_found",
            "message": f"Run {run_id!r} was not found on case {case_id!r}.",
            "security_level": lvl,
        }

    jira_key = str(case.get("jira_key") or "").strip().upper()
    result_status = str(run.get("result") or "pending")
    evidence_links: list[dict[str, str]] = []
    screenshot = None
    for item in run.get("evidence") or []:
        path = str(item or "").strip()
        if not path:
            continue
        kind = "screenshot" if path.lower().endswith(".png") else "path"
        evidence_links.append({"kind": kind, "path": path})
        if kind == "screenshot" and not screenshot:
            screenshot = path

    steps: list[dict[str, Any]] = [
        {
            "action": case.get("name") or case_id,
            "status": "pass" if result_status == "pass" else "fail",
            "classification": run.get("failure_class"),
            "error": run.get("note") or None,
            "story_key": jira_key or None,
        }
    ]

    notes: list[dict[str, Any]] = []
    case_note = str(case.get("note") or "").strip()
    if case_note:
        notes.append(
            {
                "scope": "case",
                "case_id": case.get("id"),
                "case_name": case.get("name"),
                "run_id": None,
                "text": case_note,
            }
        )
    tester_note = str(run.get("tester_note") or "").strip()
    if tester_note:
        notes.append(
            {
                "scope": "run",
                "case_id": case.get("id"),
                "case_name": case.get("name"),
                "run_id": run.get("id"),
                "text": tester_note,
            }
        )

    known_issues: list[dict[str, Any]] = []
    from plans.known_issue import is_known_labelled, normalize_known_issue

    for scope_obj, scope, rid in (
        (case, "case", None),
        (run, "run", run.get("id")),
    ):
        ki = normalize_known_issue(scope_obj.get("known_issue"))
        if not ki and not (scope == "run" and is_known_labelled(run)):
            continue
        known_issues.append(
            {
                "scope": scope,
                "case_id": case.get("id"),
                "case_name": case.get("name"),
                "run_id": rid,
                "result": run.get("result") if scope == "run" else None,
                "note": (ki or {}).get("note") or "",
                "jira_key": (ki or {}).get("jira_key") or "",
                "label": "known",
            }
        )

    bugs: list[dict[str, Any]] = []
    fc = str(run.get("failure_class") or "").strip().lower()
    if result_status in {"fail", "error"} and fc == "product_bug":
        bugs.append(
            {
                "summary": case.get("name") or case_id,
                "error": run.get("note") or "",
                "classification": "product_bug",
                "story_key": jira_key or None,
                "area": "plan",
            }
        )

    heals = list_pending_heals(run_id=str(run.get("id") or ""))
    from plans.traceability import traceability_from_plan

    matrix = traceability_from_plan(plan)
    body = {
        "title": f"{plan.get('name') or plan_id} / {case.get('name') or case_id}",
        "status": "pass" if result_status == "pass" else "fail",
        "error": run.get("note") or None,
        "steps": steps,
        "stories": [jira_key] if jira_key else [],
        "jira_keys": [jira_key] if jira_key else [],
        "bugs": bugs,
        "evidence": evidence_links,
        "screenshot": screenshot,
        "notes": notes,
        "known_issues": known_issues,
        "traceability": list(matrix.get("rows") or []),
        "run_id": run.get("id"),
        "plan_id": plan.get("id"),
        "case_id": case.get("id"),
        "suite_run_id": run.get("suite_run_id"),
        "duration_ms": run.get("duration_ms"),
        "failure_class": run.get("failure_class"),
        "functional_area": "plan",
        "heal_pending_count": heals.get("count") or 0,
    }
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": case,
        "run": run,
        "result": body,
        "request_text": (
            f"Plan {plan.get('name') or plan_id} case {case.get('name') or case_id}"
            + (f" {jira_key}" if jira_key else "")
        ),
    }


def export_plan_run(
    plan_id: str,
    case_id: str,
    run_id: str,
    *,
    sections: Mapping[str, Any] | None = None,
    level: str | None = None,
    session_id: str = "plan-export",
) -> dict[str, Any]:
    """Export JSON/Markdown for a chosen run using the section picker profile."""
    built = build_result_for_run(plan_id, case_id, run_id, level=level)
    if built.get("status") != "ok":
        return built

    enabled = (
        normalize_sections(sections)
        if sections is not None
        else load_report_sections()
    )
    result_body = built["result"]
    exported = export_run(
        result_body,
        built.get("request_text") or "",
        session_id,
        sections=enabled,
    )
    heals = list_pending_heals(run_id=str(run_id or "").strip())
    return {
        "status": "ok",
        "security_level": built.get("security_level"),
        "plan_id": plan_id,
        "case_id": case_id,
        "run_id": run_id,
        "sections": enabled,
        "result": exported,
        "heal_pending": heals.get("pending") or [],
        "heal_pending_count": heals.get("count") or 0,
        "message": (
            f"Exported run {run_id} with selected report sections. "
            f"{heals.get('count') or 0} pending heal(s) for this run "
            "(approve/reject in Heal review; no auto-commit)."
        ),
    }
