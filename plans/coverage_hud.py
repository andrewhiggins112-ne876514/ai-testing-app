"""Coverage HUD widget pack for orb home (KAN-209 / F4 / FR-UI-6 + FR-PLAN-4).

Optional home widgets for an open story: AC lines covered / partial / missing.
Choosing a line opens Plan/Suite on the linked case. Does not edit Jira.
No separate PO / Coverage home route.
"""
from __future__ import annotations

from typing import Any

from plans.draft import _split_ac_bullets
from plans.store import get_plan, list_plans

_MAX_ROWS = 24


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


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


def _plan_updated_key(plan: dict[str, Any]) -> str:
    return str(
        plan.get("updated_at")
        or plan.get("created_at")
        or plan.get("id")
        or ""
    )


def _story_candidates(plan: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    sources = plan.get("sources") if isinstance(plan.get("sources"), dict) else {}
    for raw in sources.get("jira_keys") or []:
        key = str(raw or "").strip().upper()
        if key and key not in keys:
            keys.append(key)
    snaps = plan.get("jira_snapshots") if isinstance(plan.get("jira_snapshots"), dict) else {}
    for raw in snaps.keys():
        key = str(raw or "").strip().upper()
        if key and key not in keys:
            keys.append(key)
    return keys


def _snapshot_for(plan: dict[str, Any], story_key: str) -> dict[str, Any]:
    snaps = plan.get("jira_snapshots") if isinstance(plan.get("jira_snapshots"), dict) else {}
    snap = snaps.get(story_key) or snaps.get(story_key.lower()) or {}
    return snap if isinstance(snap, dict) else {}


def _pick_open_story(
    plans: list[dict[str, Any]],
    *,
    story_key: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    want = str(story_key or "").strip().upper() or None
    ranked = sorted(plans, key=_plan_updated_key, reverse=True)

    if want:
        for plan in ranked:
            if want in _story_candidates(plan):
                return plan, want
        # Explicit key with no plan yet — still return empty shell.
        return None, want

    for plan in ranked:
        for key in _story_candidates(plan):
            return plan, key
    return None, None


def _plan_cases(plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not plan:
        return []
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    return [c for c in cases if isinstance(c, dict)]


def _latest_result(case: dict[str, Any]) -> str | None:
    runs = case.get("runs") if isinstance(case.get("runs"), list) else []
    for run in reversed(runs):
        if not isinstance(run, dict):
            continue
        result = str(run.get("result") or "").strip().lower()
        if result:
            return result
    return None


def _case_matches_line(case: dict[str, Any], story_key: str, line: str) -> bool:
    key = str(case.get("jira_key") or "").strip().upper()
    if key != story_key:
        return False
    needle = _norm(line)[:160]
    if not needle:
        return False
    src = case.get("source") if isinstance(case.get("source"), dict) else {}
    ref = _norm(str(src.get("ref") or ""))
    name = _norm(str(case.get("name") or ""))
    if ref and (needle == ref or needle in ref or ref in needle):
        return True
    if name and (needle in name or name in needle):
        return True
    return False


def _classify_line(
    *,
    plan: dict[str, Any] | None,
    story_key: str,
    line: str,
) -> dict[str, Any]:
    matches = [
        c
        for c in _plan_cases(plan)
        if _case_matches_line(c, story_key, line)
        and not c.get("archived", False)
    ]
    primary = matches[0] if matches else None
    results = [_latest_result(c) for c in matches]
    if not matches:
        status = "missing"
    elif any(r == "pass" for r in results) and not any(
        r in {"fail", "error"} for r in results
    ):
        status = "covered"
    else:
        status = "partial"

    return {
        "line": line[:240],
        "status": status,
        "plan_id": (plan or {}).get("id") if plan else None,
        "plan_name": str((plan or {}).get("name") or "")[:200] if plan else None,
        "story_key": story_key,
        "case_id": (primary or {}).get("id") if primary else None,
        "case_name": str((primary or {}).get("name") or "")[:200] if primary else None,
        "case_count": len(matches),
        "latest_result": results[0] if results else None,
        "opens_plans": True,
        "jira_write": False,
    }


def _ac_lines_for_story(
    plan: dict[str, Any] | None,
    story_key: str,
) -> list[dict[str, Any]]:
    snap = _snapshot_for(plan, story_key) if plan else {}
    acceptance = str(snap.get("acceptance_criteria") or "").strip()
    bullets = _split_ac_bullets(acceptance)
    if not bullets and plan:
        # Fall back to unique source_ref lines for this story's cases.
        seen: set[str] = set()
        for case in _plan_cases(plan):
            if str(case.get("jira_key") or "").strip().upper() != story_key:
                continue
            src = case.get("source") if isinstance(case.get("source"), dict) else {}
            ref = str(src.get("ref") or "").strip()
            if len(ref) < 3:
                continue
            key = _norm(ref)
            if key in seen:
                continue
            seen.add(key)
            bullets.append(ref[:240])
            if len(bullets) >= _MAX_ROWS:
                break
    rows = [
        _classify_line(plan=plan, story_key=story_key, line=line)
        for line in bullets[:_MAX_ROWS]
    ]
    return rows


def coverage_hud_summary(
    level: str | None = None,
    *,
    story_key: str | None = None,
) -> dict[str, Any]:
    """Aggregate Coverage HUD pack data for the active security level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    plans = _iter_full_plans(lvl)
    plan, open_key = _pick_open_story(plans, story_key=story_key)

    lines: list[dict[str, Any]] = []
    summary = ""
    if open_key:
        if plan:
            snap = _snapshot_for(plan, open_key)
            summary = str(snap.get("summary") or "")[:240]
        lines = _ac_lines_for_story(plan, open_key)

    covered = [r for r in lines if r["status"] == "covered"]
    partial = [r for r in lines if r["status"] == "partial"]
    missing = [r for r in lines if r["status"] == "missing"]

    open_story = {
        "story_key": open_key,
        "summary": summary or None,
        "plan_id": (plan or {}).get("id") if plan else None,
        "plan_name": str((plan or {}).get("name") or "")[:200] if plan else None,
        "ac_total": len(lines),
        "covered_count": len(covered),
        "partial_count": len(partial),
        "missing_count": len(missing),
        "opens_plans": True,
        "jira_write": False,
    }

    return {
        "status": "ok",
        "security_level": lvl,
        "home_only": True,
        "separate_coverage_home": False,
        "separate_po_home": False,
        "jira_write": False,
        "plan_count": len(plans),
        "open_story": open_story,
        "ac_lines": lines,
        "covered": covered,
        "partial": partial,
        "missing": missing,
        "covered_count": len(covered),
        "partial_count": len(partial),
        "missing_count": len(missing),
        "message": (
            "Coverage HUD: open-story AC lines covered/partial/missing on orb "
            "home — choosing a line opens Plan/Suite; does not edit Jira "
            "(not a separate PO home)."
        ),
    }


__all__ = ["coverage_hud_summary"]
