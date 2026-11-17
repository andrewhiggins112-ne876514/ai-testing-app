"""Run suite cases that carry a chosen tag (KAN-169 / C7).

Sequential only — no parallel tag runs. Untagged cases are omitted and listed
as not_selected. Suite run stores the run id and the tag used.
"""
from __future__ import annotations

from typing import Any

from plans.run_case import _execute_case
from plans.store import finish_suite_run, get_plan, start_suite_run

# First-class tags called out in C7 / FR-PLAN-2 (others allowed too).
WELL_KNOWN_TAGS = ("smoke", "regression")


def _case_quarantined(case: dict[str, Any]) -> bool:
    if case.get("quarantined") is True:
        return True
    q = case.get("quarantine")
    if isinstance(q, dict) and (
        q.get("active") or q.get("reason") or q.get("expires_at")
    ):
        return True
    return False


def _normalize_tag(tag: str | None) -> str:
    return str(tag or "").strip().lower()[:40]


def select_cases_for_tag(plan: dict[str, Any], tag: str) -> dict[str, Any]:
    """Split cases into to_run / skipped / not_selected for a tag."""
    needle = _normalize_tag(tag)
    if not needle:
        return {
            "status": "error",
            "error": "tag_required",
            "message": "Choose a tag (e.g. smoke or regression) before running.",
        }

    cases = list((plan.get("suite") or {}).get("cases") or [])
    to_run: list[str] = []
    skipped: list[dict[str, str]] = []
    not_selected: list[dict[str, str]] = []

    # Priority descending, then suite order — daily slices favour high priority.
    ordered = sorted(
        cases,
        key=lambda c: (
            -int(c.get("priority") or 0),
            int(c.get("order") or 0),
            c.get("created_at") or "",
            c["id"],
        ),
    )

    for case in ordered:
        cid = str(case.get("id") or "")
        tags = [str(t).strip().lower() for t in (case.get("tags") or [])]
        if needle not in tags:
            not_selected.append({"case_id": cid, "reason": "not_selected"})
            continue
        if case.get("archived"):
            skipped.append({"case_id": cid, "reason": "archived"})
            continue
        if not case.get("enabled", True):
            skipped.append({"case_id": cid, "reason": "disabled"})
            continue
        if _case_quarantined(case):
            skipped.append({"case_id": cid, "reason": "quarantined"})
            continue
        to_run.append(cid)

    return {
        "status": "ok",
        "tag": needle,
        "to_run": to_run,
        "skipped": skipped,
        "not_selected": not_selected,
        "well_known": needle in WELL_KNOWN_TAGS,
    }


async def run_cases_by_tag(
    plan_id: str,
    tag: str,
    *,
    level: str | None = None,
    session_id: str = "plan-run-by-tag",
) -> dict[str, Any]:
    """Run all cases with ``tag`` sequentially; store suite_run id + tag used."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    selection = select_cases_for_tag(plan, tag)
    if selection.get("status") != "ok":
        return {**selection, "security_level": lvl, "plan_id": plan_id}

    needle = str(selection["tag"])
    to_run: list[str] = list(selection.get("to_run") or [])
    skipped: list[dict[str, str]] = list(selection.get("skipped") or [])
    not_selected: list[dict[str, str]] = list(selection.get("not_selected") or [])

    # Skips shown on the suite run include both hard skips and not_selected.
    suite_skipped = list(skipped) + list(not_selected)

    started = start_suite_run(
        plan_id,
        mode="tag",
        tag=needle,
        skipped=suite_skipped,
        level=lvl,
    )
    if started.get("status") != "ok":
        return started
    suite_run = started["suite_run"]
    suite_run_id = suite_run["id"]

    case_runs: list[dict[str, str]] = []
    case_results: list[dict[str, Any]] = []

    for cid in to_run:
        payload = await _execute_case(
            plan_id,
            cid,
            level=lvl,
            session_id=session_id,
            pause_on_fail=False,
            suite_run_id=suite_run_id,
        )
        run = payload.get("run") or {}
        rid = str(run.get("id") or "")
        if rid:
            case_runs.append({"case_id": cid, "run_id": rid})
        case_results.append(
            {
                "case_id": cid,
                "run_id": rid or None,
                "result": run.get("result") or payload.get("error"),
                "message": payload.get("message"),
                "status": payload.get("status"),
            }
        )

    finished = finish_suite_run(
        plan_id,
        suite_run_id,
        case_runs=case_runs,
        skipped=suite_skipped,
        level=lvl,
    )
    plan_out = finished.get("plan") if finished.get("status") == "ok" else started.get("plan")
    ran_n = len(case_runs)
    msg = (
        f"Tag run finished: suite run {suite_run_id} — tag={needle!r}, "
        f"{ran_n} case(s) executed, {len(skipped)} skipped, "
        f"{len(not_selected)} not selected."
    )
    return {
        "status": "ok",
        "message": msg,
        "security_level": lvl,
        "plan_id": plan_id,
        "suite_run_id": suite_run_id,
        "tag": needle,
        "mode": "tag",
        "sequential": True,
        "to_run": to_run,
        "skipped": skipped,
        "not_selected": not_selected,
        "case_results": case_results,
        "suite_run": finished.get("suite_run") or suite_run,
        "plan": plan_out,
    }
