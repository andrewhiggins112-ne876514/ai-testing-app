"""Run suite cases that carry a chosen tag (KAN-169 / C7).

Default is sequential (parallel_count=1). Untagged cases are omitted and listed
as not_selected. Suite run stores the run id, the tag used, and parallel count
(KAN-179 / D1).
"""
from __future__ import annotations

from typing import Any

from plans.parallel import map_cases_with_parallel, resolve_parallel_count
from plans.quarantine import is_actively_quarantined
from plans.run_case import _execute_case
from plans.store import finish_suite_run, get_plan, start_suite_run

# First-class tags called out in C7 / FR-PLAN-2 (others allowed too).
WELL_KNOWN_TAGS = ("smoke", "regression")


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
        if is_actively_quarantined(case):
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
    parallel: Any = None,
    sandbox_id: str | None = None,
) -> dict[str, Any]:
    """Run all cases with ``tag``; store suite_run id + tag + parallel_count (+ sandbox)."""
    from plans.sandbox_run import resolve_run_sandbox
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    resolved = resolve_parallel_count(parallel)
    if resolved.get("status") != "ok":
        return {**resolved, "security_level": lvl, "plan_id": plan_id}

    parallel_count = int(resolved["parallel_count"])
    sequential = bool(resolved["sequential"])

    sandbox_res = resolve_run_sandbox(sandbox_id)
    if sandbox_res.get("status") != "ok":
        return {**sandbox_res, "security_level": lvl, "plan_id": plan_id}
    sandbox_name = sandbox_res.get("sandbox_name")

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
        parallel_count=parallel_count,
        sandbox=sandbox_name,
        skipped=suite_skipped,
        level=lvl,
    )
    if started.get("status") != "ok":
        return started
    suite_run = started["suite_run"]
    suite_run_id = suite_run["id"]

    async def _one(cid: str) -> dict[str, Any]:
        payload = await _execute_case(
            plan_id,
            cid,
            level=lvl,
            session_id=f"{session_id}-{cid}",
            pause_on_fail=False,
            suite_run_id=suite_run_id,
            sandbox_id=sandbox_id,
        )
        run = payload.get("run") or {}
        rid = str(run.get("id") or "")
        return {
            "case_id": cid,
            "run_id": rid or None,
            "result": run.get("result") or payload.get("error"),
            "message": payload.get("message"),
            "status": payload.get("status"),
        }

    case_results = await map_cases_with_parallel(to_run, parallel_count, _one)
    case_runs: list[dict[str, str]] = []
    for item in case_results:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("case_id") or "")
        rid = str(item.get("run_id") or "")
        if cid and rid:
            case_runs.append({"case_id": cid, "run_id": rid})

    finished = finish_suite_run(
        plan_id,
        suite_run_id,
        case_runs=case_runs,
        skipped=suite_skipped,
        level=lvl,
    )
    plan_out = finished.get("plan") if finished.get("status") == "ok" else started.get("plan")
    ran_n = len(case_runs)
    mode_label = "sequential" if sequential else f"parallel={parallel_count}"
    msg = (
        f"Tag run finished: suite run {suite_run_id} — tag={needle!r}, "
        f"{mode_label}, {ran_n} case(s) executed, {len(skipped)} skipped, "
        f"{len(not_selected)} not selected."
    )
    from plans.run_notify import attach_suite_notice

    return attach_suite_notice(
        {
            "status": "ok",
            "message": msg,
            "security_level": lvl,
            "plan_id": plan_id,
            "suite_run_id": suite_run_id,
            "tag": needle,
            "mode": "tag",
            "parallel_count": parallel_count,
            "parallel_max": resolved.get("parallel_max"),
            "sequential": sequential,
            "sandbox": sandbox_name,
            "default_profile": bool(sandbox_res.get("default_profile")),
            "to_run": to_run,
            "skipped": skipped,
            "not_selected": not_selected,
            "case_results": case_results,
            "suite_run": finished.get("suite_run") or suite_run,
            "plan": plan_out,
        },
        case_results,
        kind="tag",
    )
