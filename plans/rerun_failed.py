"""Rerun only failed cases from a finished suite run (KAN-151 / B5).

Creates a new suite_run id on the same plan. Disabled and quarantined cases
are skipped with an explicit reason. Execution is sequential (no parallel).
"""
from __future__ import annotations

from typing import Any

from plans.run_case import _execute_case
from plans.store import finish_suite_run, get_plan, start_suite_run


_FAILED = frozenset({"fail", "error"})


def _case_quarantined(case: dict[str, Any]) -> bool:
    if case.get("quarantined") is True:
        return True
    q = case.get("quarantine")
    if isinstance(q, dict) and (
        q.get("active") or q.get("reason") or q.get("expires_at")
    ):
        return True
    return False


def _last_result(case: dict[str, Any]) -> str | None:
    runs = list(case.get("runs") or [])
    if not runs:
        return None
    return str(runs[-1].get("result") or "").strip().lower() or None


def _failed_case_ids_from_last_results(plan: dict[str, Any]) -> list[str]:
    """Baseline when no suite_run exists: last per-case result is fail/error."""
    out: list[str] = []
    for case in (plan.get("suite") or {}).get("cases") or []:
        if _last_result(case) in _FAILED:
            out.append(str(case["id"]))
    return out


def _failed_case_ids_from_suite_run(
    plan: dict[str, Any],
    suite_run_id: str,
) -> tuple[list[str] | None, str | None]:
    """Return failed case ids from a finished suite run, or (None, error)."""
    sid = (suite_run_id or "").strip()
    suite_runs = list(plan.get("suite_runs") or [])
    target: dict[str, Any] | None = None
    for item in suite_runs:
        if item.get("id") == sid:
            target = item
            break
    if target is None:
        return None, f"Suite run {sid!r} was not found on this plan."
    if not target.get("finished_at"):
        return None, f"Suite run {sid!r} is not finished yet."

    by_case: dict[str, dict[str, Any]] = {
        c["id"]: c for c in (plan.get("suite") or {}).get("cases") or []
    }
    failed: list[str] = []
    for entry in target.get("case_runs") or []:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("case_id") or "").strip()
        rid = str(entry.get("run_id") or "").strip()
        case = by_case.get(cid)
        if not case:
            continue
        result = None
        for run in case.get("runs") or []:
            if run.get("id") == rid:
                result = str(run.get("result") or "").strip().lower()
                break
        if result in _FAILED:
            failed.append(cid)
    return failed, None


def select_rerun_candidates(
    plan: dict[str, Any],
    *,
    source_suite_run_id: str | None = None,
) -> dict[str, Any]:
    """Pick failed cases and classify skips (disabled / quarantined / archived)."""
    src = (source_suite_run_id or "").strip() or None
    if src:
        failed_ids, err = _failed_case_ids_from_suite_run(plan, src)
        if err:
            return {"status": "error", "error": "suite_run_invalid", "message": err}
        assert failed_ids is not None
    else:
        suite_runs = [
            r for r in (plan.get("suite_runs") or []) if r.get("finished_at")
        ]
        if suite_runs:
            src = suite_runs[-1].get("id")
            failed_ids, err = _failed_case_ids_from_suite_run(plan, str(src))
            if err:
                return {"status": "error", "error": "suite_run_invalid", "message": err}
            assert failed_ids is not None
            # If the last suite run had no failures, fall back to last case results
            # so single-case failures after a green suite still rerun.
            if not failed_ids:
                failed_ids = _failed_case_ids_from_last_results(plan)
        else:
            failed_ids = _failed_case_ids_from_last_results(plan)

    by_id = {c["id"]: c for c in (plan.get("suite") or {}).get("cases") or []}
    to_run: list[str] = []
    skipped: list[dict[str, str]] = []
    for cid in failed_ids:
        case = by_id.get(cid)
        if case is None:
            skipped.append({"case_id": cid, "reason": "case_not_found"})
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

    order = {
        c["id"]: int(c.get("order") or 0)
        for c in (plan.get("suite") or {}).get("cases") or []
    }
    to_run.sort(key=lambda cid: (order.get(cid, 0), cid))
    return {
        "status": "ok",
        "source_suite_run_id": src,
        "failed_case_ids": failed_ids,
        "to_run": to_run,
        "skipped": skipped,
    }


async def rerun_failed_cases(
    plan_id: str,
    *,
    level: str | None = None,
    source_suite_run_id: str | None = None,
    session_id: str = "plan-rerun-failed",
) -> dict[str, Any]:
    """Rerun failed cases sequentially; return new suite_run id + skip reasons."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    selection = select_rerun_candidates(plan, source_suite_run_id=source_suite_run_id)
    if selection.get("status") != "ok":
        return {**selection, "security_level": lvl, "plan_id": plan_id}

    to_run: list[str] = list(selection.get("to_run") or [])
    skipped: list[dict[str, str]] = list(selection.get("skipped") or [])
    if not to_run and not selection.get("failed_case_ids"):
        return {
            "status": "error",
            "error": "no_failed_cases",
            "message": "No failed cases found to rerun. Run cases first, then retry.",
            "security_level": lvl,
            "plan_id": plan_id,
            "suite_run_id": None,
            "skipped": [],
            "case_results": [],
        }

    started = start_suite_run(
        plan_id,
        mode="rerun_failed",
        source_suite_run_id=selection.get("source_suite_run_id"),
        skipped=skipped,
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
        skipped=skipped,
        level=lvl,
    )
    plan_out = finished.get("plan") if finished.get("status") == "ok" else started.get("plan")
    ran_n = len(case_runs)
    skip_n = len(skipped)
    msg = (
        f"Rerun failed finished: suite run {suite_run_id} — "
        f"{ran_n} case(s) executed, {skip_n} skipped."
    )
    return {
        "status": "ok",
        "message": msg,
        "security_level": lvl,
        "plan_id": plan_id,
        "suite_run_id": suite_run_id,
        "source_suite_run_id": selection.get("source_suite_run_id"),
        "mode": "rerun_failed",
        "sequential": True,
        "skipped": skipped,
        "case_results": case_results,
        "suite_run": finished.get("suite_run") or suite_run,
        "plan": plan_out,
    }
