"""Manager HUD widget pack for orb home (KAN-205 / F2 / FR-UI-6 + FR-REP-1).

Optional home widgets: pass rate, known-issue count, stories with no cases,
bugs from plan. Summaries only — known issues stay fails (never shown as pass).
No separate Manager home route.
"""
from __future__ import annotations

from typing import Any

from plans.coverage import coverage_from_plan
from plans.history import summarize_suite_run
from plans.known_issue import collect_plan_known_issues, is_known_labelled
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


def _pass_rate_block(
    plan: dict[str, Any] | None,
    suite_run: dict[str, Any] | None,
) -> dict[str, Any]:
    """Pass rate from last suite — known-labelled outcomes stay out of pass."""
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
            "known_not_counted_as_pass": True,
        }
    summary = summarize_suite_run(plan, suite_run)
    passed = int(summary.get("pass") or 0)
    failed = int(summary.get("fail") or 0)
    errors = int(summary.get("error") or 0)
    known = int(summary.get("known_issues") or 0)
    denom = passed + failed + errors
    rate = round(100.0 * passed / denom, 1) if denom > 0 else None
    return {
        "plan_id": plan.get("id"),
        "plan_name": str(plan.get("name") or "")[:200],
        "suite_run_id": summary.get("id"),
        "pass": passed,
        "fail": failed,
        "error": errors,
        "known_issues": known,
        "case_count": summary.get("case_count"),
        "pass_rate_percent": rate,
        "known_not_counted_as_pass": True,
        "finished_at": summary.get("finished_at"),
        "tag": summary.get("tag"),
    }


def _known_issue_rows(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in plans:
        for item in collect_plan_known_issues(plan):
            result = str(item.get("result") or "").strip().lower()
            # Known issues must never be presented as passes.
            if result == "pass":
                result = "fail"
            rows.append(
                {
                    "plan_id": plan.get("id"),
                    "plan_name": str(plan.get("name") or "")[:200],
                    "case_id": item.get("case_id"),
                    "case_name": item.get("case_name") or "",
                    "run_id": item.get("run_id"),
                    "result": result or None,
                    "note": (item.get("note") or "")[:160],
                    "jira_key": item.get("jira_key") or "",
                    "label": "known",
                    "shown_as_pass": False,
                }
            )
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def _stories_no_case_rows(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                }
            )
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def _bugs_from_plans(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Product-bug classified fails/errors — not known issues, not passes."""
    rows: list[dict[str, Any]] = []
    for plan in plans:
        for case in (plan.get("suite") or {}).get("cases") or []:
            if not isinstance(case, dict):
                continue
            # Prefer latest run that looks like a product bug.
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
                        ).strip().upper()[:32]
                        or None,
                    }
                )
                break
            if len(rows) >= _MAX_ROWS:
                return rows
    return rows


def manager_hud_summary(level: str | None = None) -> dict[str, Any]:
    """Aggregate manager HUD pack data for the active security level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    plans = _iter_full_plans(lvl)
    last_plan, last_sr = _pick_last_suite(plans)
    pass_rate = _pass_rate_block(last_plan, last_sr)
    known_rows = _known_issue_rows(plans)
    gap_rows = _stories_no_case_rows(plans)
    bug_rows = _bugs_from_plans(plans)

    return {
        "status": "ok",
        "security_level": lvl,
        "home_only": True,
        "separate_manager_home": False,
        "plan_count": len(plans),
        "pass_rate": pass_rate,
        "known_issues": known_rows,
        "known_issue_count": len(known_rows),
        "stories_no_case": gap_rows,
        "stories_no_case_count": len(gap_rows),
        "bugs": bug_rows,
        "bugs_count": len(bug_rows),
        "known_not_shown_as_pass": True,
        "message": (
            "Manager HUD: pass rate, known issues, coverage gaps, and bugs "
            "on orb home (not a separate Manager route)."
        ),
    }


__all__ = ["manager_hud_summary"]
