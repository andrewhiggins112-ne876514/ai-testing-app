"""Local exploratory notes on a case and on a run (KAN-155 / B7).

Case notes use ``case.note``. Run exploratory notes use ``run.tester_note``
so the system/error ``run.note`` from Playwright is not overwritten.
Notes are level-scoped with the plan. They appear in report export when the
evidence section is on. No session recorder (H1 is out of scope).
"""
from __future__ import annotations

from typing import Any


def normalize_tester_note(raw: Any) -> str:
    """Compact tester note text (max 2000 chars)."""
    return str(raw or "")[:2000]


def collect_plan_notes(plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten case + run exploratory notes from a plan for evidence export."""
    items: list[dict[str, Any]] = []
    if not isinstance(plan, dict):
        return items
    for case in (plan.get("suite") or {}).get("cases") or []:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or "")
        cname = str(case.get("name") or "")
        case_note = normalize_tester_note(case.get("note"))
        if case_note.strip():
            items.append(
                {
                    "scope": "case",
                    "case_id": cid,
                    "case_name": cname,
                    "run_id": None,
                    "text": case_note,
                }
            )
        for run in case.get("runs") or []:
            if not isinstance(run, dict):
                continue
            run_note = normalize_tester_note(run.get("tester_note"))
            if not run_note.strip():
                continue
            items.append(
                {
                    "scope": "run",
                    "case_id": cid,
                    "case_name": cname,
                    "run_id": run.get("id"),
                    "text": run_note,
                }
            )
    return items


def notes_from_result(body: Any) -> list[dict[str, Any]]:
    """Collect exploratory notes from a report result payload."""
    if not isinstance(body, dict):
        return []
    items: list[dict[str, Any]] = []
    raw_list = body.get("notes")
    if isinstance(raw_list, list):
        for item in raw_list:
            if isinstance(item, dict):
                text = normalize_tester_note(item.get("text") or item.get("note"))
                if not text.strip():
                    continue
                items.append(
                    {
                        "scope": str(item.get("scope") or "result"),
                        "case_id": item.get("case_id"),
                        "case_name": item.get("case_name") or item.get("title") or "",
                        "run_id": item.get("run_id"),
                        "text": text,
                    }
                )
            elif isinstance(item, str) and item.strip():
                items.append(
                    {
                        "scope": "result",
                        "case_id": None,
                        "case_name": "",
                        "run_id": None,
                        "text": normalize_tester_note(item),
                    }
                )
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else None
    if plan:
        items.extend(collect_plan_notes(plan))
    # Single-case / single-run shorthand fields
    case_note = normalize_tester_note(body.get("case_note"))
    if case_note.strip():
        items.append(
            {
                "scope": "case",
                "case_id": body.get("case_id"),
                "case_name": str(body.get("case_name") or body.get("title") or ""),
                "run_id": None,
                "text": case_note,
            }
        )
    run_note = normalize_tester_note(body.get("tester_note") or body.get("run_note"))
    if run_note.strip():
        items.append(
            {
                "scope": "run",
                "case_id": body.get("case_id"),
                "case_name": str(body.get("case_name") or body.get("title") or ""),
                "run_id": body.get("run_id"),
                "text": run_note,
            }
        )
    return items
