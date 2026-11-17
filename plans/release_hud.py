"""Release HUD widget pack for orb home (KAN-207 / F3 / FR-UI-6 + FR-REP-2).

Optional home widgets: environment name, last run, uncovered stories,
open product bugs. Summaries deep-link into Reports readiness — ticks stay
on the Reports surface. No separate Release home route.
"""
from __future__ import annotations

from typing import Any

from plans.coverage import coverage_from_plan
from plans.history import summarize_suite_run
from plans.known_issue import is_known_labelled
from plans.store import get_plan, list_plans
from settings.environments import get_active_environment, list_environments


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


def _environment_block() -> dict[str, Any]:
    """Active named environment — name only for go/no-go; no secrets."""
    active = get_active_environment()
    listed = list_environments()
    name = str(active.get("name") or listed.get("active_environment_name") or "").strip()
    return {
        "name": name or None,
        "id": active.get("id") or listed.get("active_environment_id"),
        "target_url_set": bool(str(active.get("target_url") or "").strip()),
        "target_app_path_set": bool(str(active.get("target_app_path") or "").strip()),
        "api_endpoint_set": bool(str(active.get("api_endpoint") or "").strip()),
        "security_level": active.get("security_level") or listed.get("security_level"),
        "environment_count": len(listed.get("environments") or []),
        "readiness_links_to": "reports",
    }


def _last_run_block(
    plan: dict[str, Any] | None,
    suite_run: dict[str, Any] | None,
) -> dict[str, Any]:
    if plan is None or suite_run is None:
        return {
            "plan_id": None,
            "plan_name": None,
            "suite_run_id": None,
            "pass": 0,
            "fail": 0,
            "error": 0,
            "known_issues": 0,
            "case_count": 0,
            "pass_rate_percent": None,
            "environment_name": None,
            "finished_at": None,
            "readiness_links_to": "reports",
        }
    summary = summarize_suite_run(plan, suite_run)
    passed = int(summary.get("pass") or 0)
    failed = int(summary.get("fail") or 0)
    errors = int(summary.get("error") or 0)
    denom = passed + failed + errors
    rate = round(100.0 * passed / denom, 1) if denom > 0 else None
    env_name = (
        str(suite_run.get("environment_name") or "").strip()
        or None
    )
    return {
        "plan_id": plan.get("id"),
        "plan_name": str(plan.get("name") or "")[:200],
        "suite_run_id": summary.get("id"),
        "pass": passed,
        "fail": failed,
        "error": errors,
        "known_issues": int(summary.get("known_issues") or 0),
        "case_count": summary.get("case_count"),
        "pass_rate_percent": rate,
        "environment_name": env_name,
        "finished_at": summary.get("finished_at"),
        "tag": summary.get("tag"),
        "readiness_links_to": "reports",
    }


def _uncovered_story_rows(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for plan in plans:
        cov = coverage_from_plan(plan)
        for gap in cov.get("no_case") or []:
            if not isinstance(gap, dict):
                continue
            key = str(gap.get("key") or "").strip().upper()
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "plan_id": plan.get("id"),
                    "plan_name": str(plan.get("name") or "")[:200],
                    "story_key": key,
                    "summary": str(gap.get("summary") or "")[:240],
                    "gap": "no_case",
                    "readiness_links_to": "reports",
                }
            )
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def _open_product_bugs(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in plans:
        for case in (plan.get("suite") or {}).get("cases") or []:
            if not isinstance(case, dict):
                continue
            for run in reversed(list(case.get("runs") or [])):
                if not isinstance(run, dict):
                    continue
                result = str(run.get("result") or "").strip().lower()
                fc = str(run.get("failure_class") or "").strip().lower()
                if result not in {"fail", "error"}:
                    continue
                if is_known_labelled(run) or is_known_labelled(case) or fc == "known_issue":
                    continue
                if fc != "product_bug":
                    continue
                rows.append(
                    {
                        "plan_id": plan.get("id"),
                        "plan_name": str(plan.get("name") or "")[:200],
                        "case_id": case.get("id"),
                        "case_name": str(case.get("name") or "")[:200],
                        "run_id": run.get("id"),
                        "result": result,
                        "failure_class": "product_bug",
                        "jira_key": str(
                            case.get("jira_key") or run.get("bug_key") or ""
                        )
                        .strip()
                        .upper()[:32]
                        or None,
                        "readiness_links_to": "reports",
                    }
                )
                break
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def release_hud_summary(level: str | None = None) -> dict[str, Any]:
    """Aggregate release HUD pack data for the active security level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    plans = _iter_full_plans(lvl)
    last_plan, last_sr = _pick_last_suite(plans)
    env = _environment_block()
    last_run = _last_run_block(last_plan, last_sr)
    uncovered = _uncovered_story_rows(plans)
    bugs = _open_product_bugs(plans)

    return {
        "status": "ok",
        "security_level": lvl,
        "home_only": True,
        "separate_release_home": False,
        "readiness_ticks_on_reports": True,
        "plan_count": len(plans),
        "environment": env,
        "last_run": last_run,
        "uncovered_stories": uncovered,
        "uncovered_stories_count": len(uncovered),
        "open_product_bugs": bugs,
        "open_product_bugs_count": len(bugs),
        "message": (
            "Release HUD: environment, last run, uncovered stories, and open "
            "product bugs on orb home — readiness detail stays in Reports "
            "(not a separate Release route)."
        ),
    }


__all__ = ["release_hud_summary"]
