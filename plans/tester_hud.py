"""Tester HUD widget pack for orb home (KAN-203 / F1 / FR-UI-1 + FR-UI-6).

Optional home widgets: connection health, last run, failed cases, quarantined cases.
Summaries only — no secrets, no separate Tester home route.
"""
from __future__ import annotations

from typing import Any

from plans.history import summarize_suite_run
from plans.history import _runs_for_suite  # suite outcome rows (same as history)
from plans.quarantine import is_actively_quarantined, quarantine_status
from plans.store import get_plan, list_plans


_MAX_ROWS = 12


def _iter_full_plans(level: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in (list_plans(level=level).get("plans") or []):
        pid = str((row or {}).get("id") or "").strip()
        if not pid:
            continue
        loaded = get_plan(pid, level=level)
        if loaded.get("status") == "ok" and isinstance(loaded.get("plan"), dict):
            out.append(loaded["plan"])
    return out


def _connection_block(*, probe: bool = True) -> dict[str, Any]:
    """Connection health for the tester HUD — never includes secrets."""
    if probe:
        from settings.connection_health import connection_health

        health = connection_health()
        checks = []
        for c in health.get("checks") or []:
            if not isinstance(c, dict):
                continue
            checks.append(
                {
                    "id": c.get("id"),
                    "label": c.get("label"),
                    "state": c.get("state"),
                    "up": bool(c.get("up")),
                    "message": str(c.get("message") or "")[:160],
                }
            )
        return {
            "overall": health.get("overall") or "down",
            "summary": health.get("summary") or "",
            "message": health.get("message") or "",
            "checks": checks,
            "separate_tester_home": False,
        }
    from settings.connection_health import connection_checklist

    checklist = connection_checklist()
    return {
        "overall": "unknown",
        "summary": "Checklist only (probe skipped).",
        "message": "Connection checklist loaded.",
        "checks": [],
        "checklist": {
            "jira_credentials_configured": bool(
                checklist.get("jira_credentials_configured")
            ),
            "jira_url_set": bool(checklist.get("jira_url")),
            "target_url_set": bool(checklist.get("target_url")),
        },
        "separate_tester_home": False,
    }


def _suite_sort_key(sr: dict[str, Any], ord_idx: int) -> tuple:
    return (
        str(sr.get("finished_at") or sr.get("started_at") or ""),
        ord_idx,
    )


def _pick_last_suite(
    plans: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    best_plan: dict[str, Any] | None = None
    best_sr: dict[str, Any] | None = None
    best_key: tuple | None = None
    for plan in plans:
        for idx, sr in enumerate(plan.get("suite_runs") or []):
            if not isinstance(sr, dict):
                continue
            if not (sr.get("finished_at") or sr.get("started_at")):
                continue
            key = _suite_sort_key(sr, idx)
            if best_key is None or key > best_key:
                best_key = key
                best_plan = plan
                best_sr = sr
    return best_plan, best_sr


def _failed_from_suite(
    plan: dict[str, Any],
    suite_run: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for outcome in _runs_for_suite(plan, suite_run):
        result = str(outcome.get("result") or "").strip().lower()
        if result not in {"fail", "error"}:
            continue
        rows.append(
            {
                "plan_id": plan.get("id"),
                "plan_name": str(plan.get("name") or "")[:200],
                "case_id": outcome.get("case_id"),
                "case_name": outcome.get("case_name") or "",
                "run_id": outcome.get("run_id"),
                "result": result,
                "failure_class": outcome.get("failure_class"),
                "suite_run_id": suite_run.get("id"),
            }
        )
    return rows[:_MAX_ROWS]


def _quarantined_rows(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in plans:
        for case in (plan.get("suite") or {}).get("cases") or []:
            if not isinstance(case, dict):
                continue
            if not is_actively_quarantined(case):
                continue
            q = quarantine_status(case)
            rows.append(
                {
                    "plan_id": plan.get("id"),
                    "plan_name": str(plan.get("name") or "")[:200],
                    "case_id": case.get("id"),
                    "case_name": str(case.get("name") or "")[:200],
                    "reason": q.get("reason") or "",
                    "expires_at": q.get("expires_at"),
                }
            )
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def tester_hud_summary(
    level: str | None = None,
    *,
    probe_connection: bool = True,
) -> dict[str, Any]:
    """Aggregate tester HUD pack data for the active security level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    plans = _iter_full_plans(lvl)
    last_plan, last_sr = _pick_last_suite(plans)

    last_run: dict[str, Any] | None = None
    failed: list[dict[str, Any]] = []
    if last_plan is not None and last_sr is not None:
        summary = summarize_suite_run(last_plan, last_sr)
        last_run = {
            "plan_id": last_plan.get("id"),
            "plan_name": str(last_plan.get("name") or "")[:200],
            "suite_run_id": summary.get("id"),
            "finished_at": summary.get("finished_at"),
            "started_at": summary.get("started_at"),
            "pass": summary.get("pass"),
            "fail": summary.get("fail"),
            "error": summary.get("error"),
            "skipped": summary.get("skipped"),
            "case_count": summary.get("case_count"),
            "duration_ms": summary.get("duration_ms"),
            "environment_name": summary.get("environment_name"),
            "mode": summary.get("mode"),
            "tag": summary.get("tag"),
        }
        failed = _failed_from_suite(last_plan, last_sr)

    quarantine = _quarantined_rows(plans)
    connection = _connection_block(probe=probe_connection)

    return {
        "status": "ok",
        "security_level": lvl,
        "home_only": True,
        "separate_tester_home": False,
        "plan_count": len(plans),
        "connection": connection,
        "last_run": last_run,
        "failed_cases": failed,
        "failed_count": len(failed),
        "quarantined_cases": quarantine,
        "quarantined_count": len(quarantine),
        "message": (
            "Tester HUD: connection, last run, fails, and quarantine "
            "on orb home (not a separate Tester route)."
        ),
    }


__all__ = ["tester_hud_summary"]
