"""Scheduled local tagged run (KAN-239 / G12 / FR-PLAN-2).

Schedule one tagged run on this PC. Uses sequential cap (parallel=1) and the
saved connection. Missed schedule (PC off / app not running past the fire
window) is reported as not_run — never as pass. Off until the tester creates
one. No cloud-hosted schedules.
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from plans.parallel import DEFAULT_PARALLEL, MAX_PARALLEL, resolve_parallel_count
from plans.run_by_tag import _normalize_tag
from settings.store import app_data_dir, get_security_level

SCHEDULE_FORMAT = 1
FIRE_WINDOW_MINUTES = 15
HISTORY_LIMIT = 40

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_ID_RE = re.compile(r"^sch_[a-z0-9]{8,16}$")


def _local_tz():
    """System local timezone (never cloud UTC schedule hosting)."""
    try:
        return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
    except Exception:
        return ZoneInfo("UTC")


def _utcnow_iso() -> str:
    return (
        datetime.now(tz=ZoneInfo("UTC")).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def _now_local() -> datetime:
    return datetime.now(_local_tz()).replace(microsecond=0)


def _schedule_path(level: str | None = None) -> Path:
    lvl = (level or get_security_level()).strip().upper()
    return app_data_dir() / "levels" / lvl / "local_run_schedule.json"


def _new_history_id() -> str:
    return f"sch_{secrets.token_hex(5)}"


def _parse_hhmm(value: str) -> tuple[int, int] | None:
    m = _TIME_RE.match((value or "").strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _due_at_for_date(day: datetime, hh: int, mm: int) -> datetime:
    tz = _local_tz()
    return datetime(day.year, day.month, day.day, hh, mm, 0, tzinfo=tz)


def _has_saved_connection() -> bool:
    """True when level store has a usable saved connection (target or Jira URL)."""
    from settings.connection_health import connection_checklist

    checklist = connection_checklist()
    if checklist.get("jira_credentials_configured"):
        return True
    if (checklist.get("jira_url") or "").strip():
        return True
    if (checklist.get("target_url") or "").strip():
        return True
    if (checklist.get("target_app_path") or "").strip():
        return True
    return False


def _empty_state() -> dict[str, Any]:
    return {
        "format": SCHEDULE_FORMAT,
        "schedule": None,
        "history": [],
        "updated_at": _utcnow_iso(),
    }


def _normalize_history_item(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    hid = str(raw.get("id") or "").strip()
    if not _ID_RE.match(hid):
        hid = _new_history_id()
    outcome = str(raw.get("outcome") or "").strip().lower()
    if outcome not in {"ran", "not_run"}:
        return None
    # Never treat a miss as pass.
    if outcome == "not_run" and str(raw.get("result") or "").lower() == "pass":
        raw = {**raw, "result": None, "pass": None}
    return {
        "id": hid,
        "due_at": str(raw.get("due_at") or "")[:40],
        "outcome": outcome,
        "reason": str(raw.get("reason") or "")[:80],
        "suite_run_id": (str(raw.get("suite_run_id") or "").strip() or None),
        "plan_id": (str(raw.get("plan_id") or "").strip() or None),
        "tag": (str(raw.get("tag") or "").strip().lower()[:40] or None),
        "pass": raw.get("pass") if outcome == "ran" else None,
        "fail": raw.get("fail") if outcome == "ran" else None,
        "result": None if outcome == "not_run" else (str(raw.get("result") or "")[:40] or None),
        "recorded_at": str(raw.get("recorded_at") or _utcnow_iso())[:40],
        "cloud": False,
    }


def _normalize_schedule(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    plan_id = str(raw.get("plan_id") or "").strip()
    tag = _normalize_tag(raw.get("tag"))
    parsed = _parse_hhmm(str(raw.get("time_local") or ""))
    if not plan_id or not tag or not parsed:
        return None
    hh, mm = parsed
    # Scheduled runs always use sequential (D1 default); refuse storing above cap.
    resolved = resolve_parallel_count(raw.get("parallel_count", DEFAULT_PARALLEL))
    parallel_count = (
        int(resolved["parallel_count"])
        if resolved.get("status") == "ok"
        else DEFAULT_PARALLEL
    )
    if parallel_count != DEFAULT_PARALLEL:
        # G12: scheduled path is sequential only.
        parallel_count = DEFAULT_PARALLEL
    return {
        "enabled": bool(raw.get("enabled", True)),
        "plan_id": plan_id[:64],
        "tag": tag,
        "time_local": f"{hh:02d}:{mm:02d}",
        "parallel_count": parallel_count,
        "sequential": True,
        "cloud": False,
        "created_at": str(raw.get("created_at") or _utcnow_iso())[:40],
        "updated_at": str(raw.get("updated_at") or _utcnow_iso())[:40],
    }


def _load_state(level: str | None = None) -> dict[str, Any]:
    path = _schedule_path(level)
    if not path.is_file():
        return _empty_state()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    if not isinstance(raw, dict):
        return _empty_state()
    schedule = _normalize_schedule(raw.get("schedule"))
    history: list[dict[str, Any]] = []
    for item in raw.get("history") or []:
        norm = _normalize_history_item(item)
        if norm:
            history.append(norm)
    return {
        "format": SCHEDULE_FORMAT,
        "schedule": schedule,
        "history": history[-HISTORY_LIMIT:],
        "updated_at": str(raw.get("updated_at") or _utcnow_iso())[:40],
    }


def _write_state(state: dict[str, Any], level: str | None = None) -> None:
    path = _schedule_path(level)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": SCHEDULE_FORMAT,
        "schedule": state.get("schedule"),
        "history": list(state.get("history") or [])[-HISTORY_LIMIT:],
        "updated_at": _utcnow_iso(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_schedule_state(level: str | None = None) -> None:
    """Test helper — remove schedule file for the level."""
    path = _schedule_path(level)
    if path.is_file():
        path.unlink()


def schedule_info(level: str | None = None) -> dict[str, Any]:
    """Public view: schedule or off. Never invents a pass for a miss."""
    lvl = (level or get_security_level()).strip().upper()
    state = _load_state(lvl)
    schedule = state.get("schedule")
    enabled = bool(schedule and schedule.get("enabled"))
    return {
        "status": "ok",
        "security_level": lvl,
        "enabled": enabled,
        "off_until_created": not enabled,
        "cloud_hosted": False,
        "parallel_default": DEFAULT_PARALLEL,
        "parallel_max": MAX_PARALLEL,
        "sequential_only": True,
        "fire_window_minutes": FIRE_WINDOW_MINUTES,
        "has_saved_connection": _has_saved_connection(),
        "schedule": schedule if enabled else None,
        "history": list(state.get("history") or [])[-10:],
        "message": (
            f"Scheduled local run on: tag={schedule.get('tag')!r} at "
            f"{schedule.get('time_local')} (sequential)."
            if enabled and schedule
            else "No local schedule. Off until you create one. Not cloud-hosted."
        ),
    }


def set_schedule(
    plan_id: str,
    tag: str,
    time_local: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Create or replace the single local schedule (enables it)."""
    from plans.store import get_plan

    lvl = (level or get_security_level()).strip().upper()
    pid = (plan_id or "").strip()
    needle = _normalize_tag(tag)
    parsed = _parse_hhmm(time_local)
    if not pid:
        return {
            "status": "error",
            "error": "plan_required",
            "message": "Choose a plan before scheduling.",
            "security_level": lvl,
        }
    if not needle:
        return {
            "status": "error",
            "error": "tag_required",
            "message": "Choose a tag (e.g. smoke) before scheduling.",
            "security_level": lvl,
        }
    if not parsed:
        return {
            "status": "error",
            "error": "time_invalid",
            "message": "Time must be local HH:MM (24-hour).",
            "security_level": lvl,
        }
    loaded = get_plan(pid, level=lvl)
    if loaded.get("status") != "ok":
        return {**loaded, "security_level": lvl}

    hh, mm = parsed
    now_iso = _utcnow_iso()
    state = _load_state(lvl)
    previous = state.get("schedule") if isinstance(state.get("schedule"), dict) else {}
    schedule = _normalize_schedule(
        {
            "enabled": True,
            "plan_id": pid,
            "tag": needle,
            "time_local": f"{hh:02d}:{mm:02d}",
            "parallel_count": DEFAULT_PARALLEL,
            "created_at": previous.get("created_at") or now_iso,
            "updated_at": now_iso,
        }
    )
    state["schedule"] = schedule
    _write_state(state, lvl)
    info = schedule_info(lvl)
    info["message"] = (
        f"Local schedule set: plan {pid}, tag={needle!r} at "
        f"{hh:02d}:{mm:02d} (sequential). Uses saved connection. Not cloud-hosted."
    )
    return info


def clear_schedule(level: str | None = None) -> dict[str, Any]:
    """Remove the schedule — feature is off until created again."""
    lvl = (level or get_security_level()).strip().upper()
    state = _load_state(lvl)
    state["schedule"] = None
    _write_state(state, lvl)
    info = schedule_info(lvl)
    info["message"] = "Local schedule cleared. Off until you create one."
    return info


def _due_key(due: datetime) -> str:
    return due.strftime("%Y-%m-%dT%H:%M")


def _history_has_due(history: list[dict[str, Any]], due: datetime) -> bool:
    key = _due_key(due)
    for item in history:
        due_at = str(item.get("due_at") or "")
        if due_at.startswith(key) or key in due_at.replace(" ", "T"):
            return True
        # Also match date+time_local style
        if due_at[:16] == key:
            return True
    return False


def _append_history(
    state: dict[str, Any],
    *,
    due: datetime,
    outcome: str,
    reason: str,
    plan_id: str | None = None,
    tag: str | None = None,
    suite_run_id: str | None = None,
    passed: int | None = None,
    failed: int | None = None,
) -> dict[str, Any]:
    item = _normalize_history_item(
        {
            "id": _new_history_id(),
            "due_at": due.isoformat(),
            "outcome": outcome,
            "reason": reason,
            "plan_id": plan_id,
            "tag": tag,
            "suite_run_id": suite_run_id,
            "pass": passed,
            "fail": failed,
            "result": "ran" if outcome == "ran" else None,
            "recorded_at": _utcnow_iso(),
        }
    )
    assert item is not None
    history = list(state.get("history") or [])
    history.append(item)
    state["history"] = history[-HISTORY_LIMIT:]
    return item


def evaluate_due(
    *,
    now: datetime | None = None,
    level: str | None = None,
    fire: bool = False,
) -> dict[str, Any]:
    """Check due/missed slots. Optionally fire a sequential tagged run.

    Missed windows (PC off past FIRE_WINDOW_MINUTES) → outcome not_run (never pass).
    """
    lvl = (level or get_security_level()).strip().upper()
    state = _load_state(lvl)
    schedule = state.get("schedule")
    if not schedule or not schedule.get("enabled"):
        return {
            **schedule_info(lvl),
            "action": "off",
            "fired": False,
        }

    parsed = _parse_hhmm(str(schedule.get("time_local") or ""))
    assert parsed is not None
    hh, mm = parsed
    current = now or _now_local()
    if current.tzinfo is None:
        current = current.replace(tzinfo=_local_tz())

    history = list(state.get("history") or [])
    recorded_misses: list[dict[str, Any]] = []
    fired_payload: dict[str, Any] | None = None
    action = "waiting"

    # Only consider dues after the schedule was created (don't invent past misses).
    created_raw = str(schedule.get("created_at") or "")
    try:
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=ZoneInfo("UTC"))
        created_local = created_at.astimezone(_local_tz())
    except ValueError:
        created_local = current - timedelta(days=1)

    # Look back a few days for unrecorded dues (PC was off), after create time.
    for delta in range(3, -1, -1):
        day = current - timedelta(days=delta)
        due = _due_at_for_date(day, hh, mm)
        if due > current:
            continue
        if due < created_local:
            continue
        if _history_has_due(history, due):
            continue

        age = current - due
        within_window = age <= timedelta(minutes=FIRE_WINDOW_MINUTES)
        is_today = due.date() == current.date()

        if within_window and is_today:
            if fire:
                if not _has_saved_connection():
                    item = _append_history(
                        state,
                        due=due,
                        outcome="not_run",
                        reason="no_saved_connection",
                        plan_id=schedule.get("plan_id"),
                        tag=schedule.get("tag"),
                    )
                    history = list(state.get("history") or [])
                    recorded_misses.append(item)
                    action = "not_run"
                    continue
                # Async fire happens in tick_schedule.
                fired_payload = {
                    "pending_fire": True,
                    "plan_id": schedule["plan_id"],
                    "tag": schedule["tag"],
                    "due": due,
                    "parallel_count": DEFAULT_PARALLEL,
                }
                action = "fire"
                break
            action = "due"
            continue

        # Past the fire window (or older day) → missed, not pass.
        item = _append_history(
            state,
            due=due,
            outcome="not_run",
            reason="missed_pc_off" if age > timedelta(minutes=FIRE_WINDOW_MINUTES) else "missed",
            plan_id=schedule.get("plan_id"),
            tag=schedule.get("tag"),
        )
        history = list(state.get("history") or [])
        recorded_misses.append(item)
        action = "not_run"

    _write_state(state, lvl)
    info = schedule_info(lvl)
    info.update(
        {
            "action": action,
            "fired": False,
            "recorded_misses": recorded_misses,
            "pending_fire": fired_payload,
            "now_local": current.isoformat(),
        }
    )
    return info


async def tick_schedule(
    *,
    now: datetime | None = None,
    level: str | None = None,
    fire: bool = True,
) -> dict[str, Any]:
    """Evaluate schedule; fire sequential tag run when due inside the window."""
    evaluated = evaluate_due(now=now, level=level, fire=fire)
    pending = evaluated.pop("pending_fire", None)
    if not pending:
        return evaluated

    from plans.run_by_tag import run_cases_by_tag
    from plans.run_notify import counts_from_case_results

    lvl = evaluated.get("security_level") or get_security_level()
    due: datetime = pending["due"]
    run_result = await run_cases_by_tag(
        pending["plan_id"],
        pending["tag"],
        level=lvl,
        session_id="schedule-tick",
        parallel=DEFAULT_PARALLEL,
    )

    state = _load_state(lvl)
    passed = failed = None
    suite_run_id = None
    reason = "ok"
    outcome = "ran"
    if run_result.get("status") == "ok":
        suite_run_id = run_result.get("suite_run_id")
        passed, failed = counts_from_case_results(run_result.get("case_results"))
    else:
        # Connection/plan errors still must not look like a silent pass.
        outcome = "not_run"
        reason = str(run_result.get("error") or "run_failed")[:80]

    item = _append_history(
        state,
        due=due,
        outcome=outcome,
        reason=reason,
        plan_id=pending["plan_id"],
        tag=pending["tag"],
        suite_run_id=str(suite_run_id) if suite_run_id else None,
        passed=passed,
        failed=failed,
    )
    _write_state(state, lvl)

    info = schedule_info(lvl)
    info.update(
        {
            "action": "fired" if outcome == "ran" else "not_run",
            "fired": outcome == "ran",
            "history_item": item,
            "run": {
                "status": run_result.get("status"),
                "suite_run_id": suite_run_id,
                "message": run_result.get("message"),
                "parallel_count": run_result.get("parallel_count", DEFAULT_PARALLEL),
                "sequential": run_result.get("sequential", True),
                "pass": passed,
                "fail": failed,
                "tag": pending["tag"],
                "mode": "scheduled",
            },
            "message": (
                f"Scheduled run fired: tag={pending['tag']!r}, suite {suite_run_id}."
                if outcome == "ran"
                else f"Scheduled slot recorded as not run ({reason})."
            ),
        }
    )
    return info
