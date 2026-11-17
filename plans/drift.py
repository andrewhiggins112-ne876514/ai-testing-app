"""Acceptance text drift for linked Jira issues (KAN-165 / C5 / FR-PLAN-3 / FR-JIRA-1).

On demand: re-read linked issues, mark plan snapshots stale when summary/AC differ,
show old vs new text, and let the tester keep or refresh drafts.
Refresh never deletes cases or stored runs (no silent overwrite).
"""
from __future__ import annotations

from typing import Any

from plans.draft import _add_cases_from_issue
from plans.store import (
    count_plan_runs,
    get_plan,
    update_case,
    upsert_jira_snapshot,
    _normalize_jira_snapshots,
    _utcnow,
    _write_plan,
)


def _norm_text(value: str) -> str:
    return " ".join((value or "").replace("\r\n", "\n").split()).strip().lower()


def _texts_differ(
    old_summary: str,
    old_ac: str,
    new_summary: str,
    new_ac: str,
) -> bool:
    return _norm_text(old_summary) != _norm_text(new_summary) or _norm_text(
        old_ac
    ) != _norm_text(new_ac)


def _plan_cases(plan: dict[str, Any]) -> list[dict[str, Any]]:
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    return [c for c in cases if isinstance(c, dict)]


def _linked_keys(plan: dict[str, Any], only: list[str] | None = None) -> list[str]:
    sources = plan.get("sources") if isinstance(plan.get("sources"), dict) else {}
    keys: list[str] = []
    for raw in sources.get("jira_keys") or []:
        key = str(raw or "").strip().upper()
        if key and key not in keys:
            keys.append(key)
    for case in _plan_cases(plan):
        key = str(case.get("jira_key") or "").strip().upper()
        if key and key not in keys:
            keys.append(key)
    if only is not None:
        wanted = {str(k or "").strip().upper() for k in only if str(k or "").strip()}
        keys = [k for k in keys if k in wanted]
    return keys


def _baseline_from_cases(plan: dict[str, Any], key: str) -> tuple[str, str]:
    """Fallback old AC from jira-sourced case refs when no snapshot exists."""
    refs: list[str] = []
    for case in _plan_cases(plan):
        if str(case.get("jira_key") or "").strip().upper() != key:
            continue
        source = case.get("source") if isinstance(case.get("source"), dict) else {}
        if str(source.get("kind") or "").strip().lower() != "jira":
            continue
        ref = str(source.get("ref") or "").strip()
        if ref and ref not in refs:
            refs.append(ref[:240])
    if not refs:
        return "", ""
    return "", "\n".join(f"- {r}" for r in refs)


def _row(
    *,
    key: str,
    stale: bool,
    old_summary: str,
    old_ac: str,
    new_summary: str,
    new_ac: str,
    read_ok: bool,
    message: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "stale": bool(stale),
        "old_summary": old_summary or "",
        "old_acceptance_criteria": old_ac or "",
        "new_summary": new_summary or "",
        "new_acceptance_criteria": new_ac or "",
        "read_ok": bool(read_ok),
        "message": message or "",
    }


async def check_acceptance_drift(
    plan_id: str,
    *,
    keys: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Re-read linked issues and mark snapshots stale when summary/AC differ."""
    from plugins.jira_plugin import read_issue
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    target_keys = _linked_keys(plan, keys)
    if not target_keys:
        return {
            "status": "ok",
            "security_level": lvl,
            "plan_id": plan.get("id"),
            "stale": False,
            "stale_count": 0,
            "checked": [],
            "stale_items": [],
            "jira_write": False,
            "message": "No linked Jira keys on this plan.",
        }

    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    checked: list[dict[str, Any]] = []
    stale_items: list[dict[str, Any]] = []
    now = _utcnow()

    for key in target_keys:
        issue = await read_issue(key)
        if issue.get("status") != "ok":
            row = _row(
                key=key,
                stale=False,
                old_summary="",
                old_ac="",
                new_summary="",
                new_ac="",
                read_ok=False,
                message=issue.get("message") or f"Could not read {key}.",
            )
            checked.append(row)
            continue

        new_summary = str(issue.get("summary") or "").strip()
        new_ac = str(issue.get("acceptance_criteria") or "").strip()
        snap = snaps.get(key)
        if snap:
            old_summary = str(snap.get("summary") or "")
            old_ac = str(snap.get("acceptance_criteria") or "")
        else:
            old_summary, old_ac = _baseline_from_cases(plan, key)
            # First capture with no prior text: baseline only, not stale.
            if not old_summary and not old_ac:
                snaps[key] = {
                    "summary": new_summary[:500],
                    "acceptance_criteria": new_ac[:8000],
                    "captured_at": now,
                    "stale": False,
                }
                checked.append(
                    _row(
                        key=key,
                        stale=False,
                        old_summary=new_summary,
                        old_ac=new_ac,
                        new_summary=new_summary,
                        new_ac=new_ac,
                        read_ok=True,
                        message="Baseline snapshot recorded (no prior draft text).",
                    )
                )
                continue

        differs = _texts_differ(old_summary, old_ac, new_summary, new_ac)
        if key not in snaps:
            snaps[key] = {
                "summary": old_summary[:500],
                "acceptance_criteria": old_ac[:8000],
                "captured_at": now,
                "stale": differs,
            }
        else:
            snaps[key]["stale"] = differs
        row = _row(
            key=key,
            stale=differs,
            old_summary=old_summary,
            old_ac=old_ac,
            new_summary=new_summary,
            new_ac=new_ac,
            read_ok=True,
            message="Summary/AC differ." if differs else "In sync.",
        )
        checked.append(row)
        if differs:
            stale_items.append(row)

    plan["jira_snapshots"] = snaps
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)

    return {
        "status": "ok",
        "security_level": lvl,
        "plan_id": plan.get("id"),
        "plan": plan,
        "stale": bool(stale_items),
        "stale_count": len(stale_items),
        "checked": checked,
        "stale_items": stale_items,
        "jira_write": False,
        "message": (
            f"{len(stale_items)} linked issue(s) stale (summary/AC differ)."
            if stale_items
            else "No acceptance text drift detected."
        ),
    }


async def keep_acceptance_drafts(
    plan_id: str,
    *,
    keys: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Keep current draft cases; re-baseline snapshots to live Jira text; clear stale."""
    from plugins.jira_plugin import read_issue
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    target_keys = _linked_keys(plan, keys)
    if not target_keys:
        return {
            "status": "error",
            "error": "no_keys",
            "message": "No linked Jira keys to keep.",
            "security_level": lvl,
            "jira_write": False,
        }

    kept: list[str] = []
    skipped: list[dict[str, Any]] = []
    for key in target_keys:
        issue = await read_issue(key)
        if issue.get("status") != "ok":
            skipped.append(
                {
                    "key": key,
                    "message": issue.get("message") or f"Could not read {key}.",
                }
            )
            continue
        upsert_jira_snapshot(
            plan_id,
            key,
            summary=str(issue.get("summary") or ""),
            acceptance_criteria=str(issue.get("acceptance_criteria") or ""),
            stale=False,
            level=lvl,
        )
        kept.append(key)

    refreshed = get_plan(plan_id, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan_id": plan_id,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else None,
        "action": "keep",
        "keys": kept,
        "skipped": skipped,
        "cases_changed": False,
        "runs_deleted": False,
        "jira_write": False,
        "message": (
            f"Kept existing drafts for {len(kept)} issue(s); "
            "snapshots re-baselined. No cases overwritten."
        ),
    }


async def refresh_acceptance_drafts(
    plan_id: str,
    *,
    keys: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Refresh jira draft cases from live AC. Never deletes cases or runs."""
    from plugins.jira_plugin import read_issue
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    runs_before = count_plan_runs(plan)
    target_keys = _linked_keys(plan, keys)
    if not target_keys:
        return {
            "status": "error",
            "error": "no_keys",
            "message": "No linked Jira keys to refresh.",
            "security_level": lvl,
            "jira_write": False,
            "runs_before": runs_before,
            "runs_after": runs_before,
            "runs_deleted": False,
        }

    refreshed_keys: list[str] = []
    disabled_case_ids: list[str] = []
    added_cases: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for key in target_keys:
        issue = await read_issue(key)
        if issue.get("status") != "ok":
            skipped.append(
                {
                    "key": key,
                    "message": issue.get("message") or f"Could not read {key}.",
                }
            )
            continue

        summary = str(issue.get("summary") or key).strip()
        acceptance = str(issue.get("acceptance_criteria") or "").strip()
        description = str(issue.get("description") or "").strip()

        # Disable prior jira-sourced cases for this key — keep ids + runs.
        for case in _plan_cases(get_plan(plan_id, level=lvl).get("plan") or plan):
            if str(case.get("jira_key") or "").strip().upper() != key:
                continue
            source = case.get("source") if isinstance(case.get("source"), dict) else {}
            if str(source.get("kind") or "").strip().lower() != "jira":
                continue
            if not case.get("enabled", True):
                continue
            note = str(case.get("note") or "")
            marker = "Superseded by acceptance refresh (KAN-165)."
            if marker not in note:
                note = (note + ("\n" if note else "") + marker)[:2000]
            updated = update_case(
                plan_id,
                case["id"],
                enabled=False,
                note=note,
                level=lvl,
            )
            if updated.get("status") == "ok":
                disabled_case_ids.append(case["id"])

        new_cases = _add_cases_from_issue(
            plan_id,
            key=key,
            summary=summary,
            acceptance=acceptance,
            description=description,
            level=lvl,
        )
        added_cases.extend(new_cases)
        upsert_jira_snapshot(
            plan_id,
            key,
            summary=summary,
            acceptance_criteria=acceptance,
            stale=False,
            level=lvl,
        )
        refreshed_keys.append(key)

    after = get_plan(plan_id, level=lvl)
    plan_after = after.get("plan") if after.get("status") == "ok" else None
    runs_after = count_plan_runs(plan_after or {})
    return {
        "status": "ok",
        "security_level": lvl,
        "plan_id": plan_id,
        "plan": plan_after,
        "action": "refresh",
        "keys": refreshed_keys,
        "skipped": skipped,
        "disabled_case_ids": disabled_case_ids,
        "added_case_count": len(added_cases),
        "cases_changed": True,
        "runs_before": runs_before,
        "runs_after": runs_after,
        "runs_deleted": False,
        "jira_write": False,
        "silent_overwrite": False,
        "message": (
            f"Refreshed drafts for {len(refreshed_keys)} issue(s): "
            f"disabled {len(disabled_case_ids)} prior case(s), "
            f"added {len(added_cases)} new case(s). "
            f"Stored runs preserved ({runs_after} after, {runs_before} before)."
        ),
    }
