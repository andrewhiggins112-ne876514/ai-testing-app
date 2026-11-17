"""Known-issue / exclusion helpers (KAN-153 / B6).

A known failure stays red (fail/error) and is labelled ``known``.
Optional note + Jira key are local only — nothing is auto-transitioned in Jira.
"""
from __future__ import annotations

import re
from typing import Any

_JIRA_KEY = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")


def normalize_known_issue(raw: Any) -> dict[str, Any] | None:
    """Return a compact known-issue payload, or None when unlinked/empty."""
    if not isinstance(raw, dict):
        return None
    note = str(raw.get("note") or "")[:2000]
    key = str(raw.get("jira_key") or "").strip().upper()[:32]
    if key and not _JIRA_KEY.match(key):
        key = ""
    linked = bool(raw.get("linked", False)) or bool(note or key)
    if not linked and not note and not key:
        return None
    return {"note": note, "jira_key": key, "linked": True}


def is_known_labelled(obj: dict[str, Any] | None) -> bool:
    """True when a case/run should show the ``known`` label."""
    if not isinstance(obj, dict):
        return False
    if str(obj.get("failure_class") or "").strip().lower() == "known_issue":
        return True
    ki = obj.get("known_issue")
    return isinstance(ki, dict) and bool(ki.get("linked"))


def collect_plan_known_issues(plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten linked known issues from a plan for report export."""
    items: list[dict[str, Any]] = []
    if not isinstance(plan, dict):
        return items
    for case in (plan.get("suite") or {}).get("cases") or []:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or "")
        cname = str(case.get("name") or "")
        case_ki = normalize_known_issue(case.get("known_issue"))
        if case_ki:
            items.append(
                {
                    "scope": "case",
                    "case_id": cid,
                    "case_name": cname,
                    "run_id": None,
                    "result": None,
                    "note": case_ki["note"],
                    "jira_key": case_ki["jira_key"],
                    "label": "known",
                }
            )
        for run in case.get("runs") or []:
            if not isinstance(run, dict):
                continue
            run_ki = normalize_known_issue(run.get("known_issue"))
            known_class = str(run.get("failure_class") or "").lower() == "known_issue"
            if not run_ki and not known_class:
                continue
            note = (run_ki or {}).get("note") or ""
            jira_key = (run_ki or {}).get("jira_key") or ""
            items.append(
                {
                    "scope": "run",
                    "case_id": cid,
                    "case_name": cname,
                    "run_id": run.get("id"),
                    "result": run.get("result"),
                    "note": note,
                    "jira_key": jira_key,
                    "label": "known",
                }
            )
    return items


def known_issues_from_result(body: Any) -> list[dict[str, Any]]:
    """Collect known-issue rows from a report result payload."""
    if not isinstance(body, dict):
        return []
    items: list[dict[str, Any]] = []
    raw_list = body.get("known_issues")
    if isinstance(raw_list, list):
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            note = str(item.get("note") or "")[:2000]
            key = str(item.get("jira_key") or item.get("key") or "").strip().upper()[:32]
            items.append(
                {
                    "scope": str(item.get("scope") or "result"),
                    "case_id": item.get("case_id"),
                    "case_name": item.get("case_name") or item.get("title") or "",
                    "run_id": item.get("run_id"),
                    "result": item.get("result"),
                    "note": note,
                    "jira_key": key if _JIRA_KEY.match(key) else "",
                    "label": "known",
                }
            )
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else None
    if plan:
        items.extend(collect_plan_known_issues(plan))
    for step in body.get("steps") or []:
        if not isinstance(step, dict):
            continue
        cls = str(step.get("classification") or step.get("failure_class") or "").lower()
        if cls != "known_issue":
            continue
        items.append(
            {
                "scope": "step",
                "case_id": None,
                "case_name": str(step.get("action") or ""),
                "run_id": None,
                "result": step.get("status"),
                "note": str(step.get("error") or step.get("note") or "")[:2000],
                "jira_key": str(step.get("jira_key") or "").strip().upper()[:32],
                "label": "known",
            }
        )
    return items
