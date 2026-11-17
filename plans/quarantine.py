"""Flake score and quarantine (KAN-181 / D2 / FR-PLAN-2 + FR-PLAN-4).

Suite shows how often a case failed in the last N runs. Quarantine requires a
reason and expiry; quarantined cases are skipped and listed on the run (never
counted as pass). After expiry they return to the selectable set. Raw last
failure / runs stay visible.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from plans.store import get_plan, _write_plan, _utcnow

# Default window for flake score ("last N runs").
DEFAULT_FLAKE_WINDOW = 10

_FAILED = frozenset({"fail", "error"})


def _parse_iso(raw: Any) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def flake_score(case: dict[str, Any], *, window: int = DEFAULT_FLAKE_WINDOW) -> dict[str, Any]:
    """How often a case failed in the last N runs (fail/error)."""
    n = max(1, int(window or DEFAULT_FLAKE_WINDOW))
    runs = list(case.get("runs") or [])
    recent = runs[-n:] if runs else []
    fail_count = sum(
        1 for r in recent if str(r.get("result") or "").strip().lower() in _FAILED
    )
    total = len(recent)
    rate = (fail_count / total) if total else 0.0
    last = recent[-1] if recent else None
    last_failure = None
    for r in reversed(runs):
        if str(r.get("result") or "").strip().lower() in _FAILED:
            last_failure = {
                "id": r.get("id"),
                "result": r.get("result"),
                "failure_class": r.get("failure_class"),
                "duration_ms": r.get("duration_ms"),
                "evidence": list(r.get("evidence") or []),
                "recorded_at": r.get("recorded_at") or r.get("created_at"),
            }
            break
    return {
        "case_id": case.get("id"),
        "window": n,
        "runs_in_window": total,
        "fail_count": fail_count,
        "pass_or_other_count": total - fail_count,
        "fail_rate": round(rate, 4),
        "flake_label": f"{fail_count}/{total}" if total else "0/0",
        "last_result": (str(last.get("result")) if last else None),
        "last_failure": last_failure,
    }


def is_actively_quarantined(
    case: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> bool:
    """True only while quarantine is active and not past expiry."""
    if not isinstance(case, dict):
        return False
    q = case.get("quarantine") if isinstance(case.get("quarantine"), dict) else {}
    flagged = bool(case.get("quarantined")) or bool(q.get("active"))
    if not flagged:
        return False
    expires = _parse_iso(q.get("expires_at"))
    if expires is None:
        # Active flag without a parseable expiry — still treat as quarantined
        # until cleared (legacy rows). New sets always require expiry.
        return True
    clock = now or _now_utc()
    return clock < expires


def quarantine_status(
    case: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Public quarantine view for a case (includes expired → selectable)."""
    q = case.get("quarantine") if isinstance(case.get("quarantine"), dict) else {}
    clock = now or _now_utc()
    active = is_actively_quarantined(case, now=clock)
    expires_at = q.get("expires_at") or None
    exp_dt = _parse_iso(expires_at)
    had_quarantine = bool(case.get("quarantined")) or bool(q.get("active")) or bool(
        q.get("reason")
    )
    expired = bool(had_quarantine and exp_dt is not None and clock >= exp_dt and not active)
    return {
        "quarantined": active,
        "reason": str(q.get("reason") or "")[:500],
        "expires_at": expires_at,
        "expired": expired,
        "active": active,
    }


def suite_flake_report(
    plan: dict[str, Any],
    *,
    window: int = DEFAULT_FLAKE_WINDOW,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Per-case flake scores + quarantine status for a suite."""
    clock = now or _now_utc()
    n = max(1, int(window or DEFAULT_FLAKE_WINDOW))
    cases_out: list[dict[str, Any]] = []
    for case in (plan.get("suite") or {}).get("cases") or []:
        flake = flake_score(case, window=n)
        qstat = quarantine_status(case, now=clock)
        cases_out.append(
            {
                **flake,
                "name": case.get("name"),
                "quarantine": qstat,
                "quarantined": qstat["quarantined"],
            }
        )
    return {
        "status": "ok",
        "plan_id": plan.get("id"),
        "window": n,
        "cases": cases_out,
        "quarantined_count": sum(1 for c in cases_out if c["quarantined"]),
        "message": (
            f"Flake scores over last {n} runs per case. "
            "Quarantine is skip-only — never counted as pass."
        ),
    }


def set_quarantine(
    plan_id: str,
    case_id: str,
    *,
    reason: str,
    expires_at: str,
    level: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Quarantine a case — requires reason and expiry. Keeps runs/last failure."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    why = str(reason or "").strip()
    if not why:
        return {
            "status": "error",
            "error": "quarantine_reason_required",
            "message": "Quarantine requires a reason.",
            "security_level": lvl,
        }
    exp = _parse_iso(expires_at)
    if exp is None:
        return {
            "status": "error",
            "error": "quarantine_expiry_required",
            "message": "Quarantine requires a valid expiry (ISO datetime).",
            "security_level": lvl,
        }
    clock = now or _now_utc()
    if exp <= clock:
        return {
            "status": "error",
            "error": "quarantine_expiry_past",
            "message": "Quarantine expiry must be in the future.",
            "security_level": lvl,
        }

    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    target: dict[str, Any] | None = None
    cases = list((plan.get("suite") or {}).get("cases") or [])
    for case in cases:
        if case.get("id") == cid:
            target = case
            break
    if target is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }

    stamp = _utcnow()
    target["quarantine"] = {
        "reason": why[:500],
        "expires_at": exp.replace(microsecond=0).isoformat(),
        "active": True,
        "set_at": stamp,
    }
    target["quarantined"] = True
    target["updated_at"] = stamp
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = stamp
    _write_plan(plan, level=lvl)
    flake = flake_score(target)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": target,
        "quarantine": quarantine_status(target, now=clock),
        "flake": flake,
        "last_failure": flake.get("last_failure"),
        "counted_as_pass": False,
        "message": (
            "Case quarantined until expiry. It will be skipped on suite runs "
            "(not counted as pass). Last failure remains visible."
        ),
    }


def clear_quarantine(
    plan_id: str,
    case_id: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Manually return a case to the selectable set before expiry."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    target: dict[str, Any] | None = None
    cases = list((plan.get("suite") or {}).get("cases") or [])
    for case in cases:
        if case.get("id") == cid:
            target = case
            break
    if target is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }

    stamp = _utcnow()
    prev = target.get("quarantine") if isinstance(target.get("quarantine"), dict) else {}
    target["quarantine"] = {
        "reason": str(prev.get("reason") or "")[:500],
        "expires_at": prev.get("expires_at") or None,
        "active": False,
        "cleared_at": stamp,
        "set_at": prev.get("set_at"),
    }
    target["quarantined"] = False
    target["updated_at"] = stamp
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = stamp
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": target,
        "quarantine": quarantine_status(target),
        "message": "Quarantine cleared — case is selectable again.",
    }


def expire_stale_quarantines(
    plan: dict[str, Any],
    *,
    level: str | None = None,
    now: datetime | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Flip expired quarantines off so cases return to the selectable set."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    clock = now or _now_utc()
    cases = list((plan.get("suite") or {}).get("cases") or [])
    expired_ids: list[str] = []
    changed = False
    for case in cases:
        q = case.get("quarantine") if isinstance(case.get("quarantine"), dict) else {}
        was_flagged = bool(case.get("quarantined")) or bool(q.get("active"))
        if not was_flagged:
            continue
        if is_actively_quarantined(case, now=clock):
            continue
        # Was flagged but no longer active → mark cleared by expiry
        case["quarantined"] = False
        case["quarantine"] = {
            "reason": str(q.get("reason") or "")[:500],
            "expires_at": q.get("expires_at") or None,
            "active": False,
            "expired_at": _utcnow(),
            "set_at": q.get("set_at"),
        }
        case["updated_at"] = _utcnow()
        expired_ids.append(str(case.get("id")))
        changed = True
    if changed and persist and plan.get("id"):
        plan["suite"] = {"cases": cases}
        plan["updated_at"] = _utcnow()
        _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "expired_case_ids": expired_ids,
        "count": len(expired_ids),
        "plan": plan,
    }


def default_expiry_iso(*, days: int = 7) -> str:
    """Helper for UI default expiry (7 days ahead)."""
    return (_now_utc() + timedelta(days=max(1, int(days)))).isoformat()
