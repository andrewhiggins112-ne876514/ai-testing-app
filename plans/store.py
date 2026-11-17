"""Local plan / suite / case / run store (KAN-125 / FR-PLAN-1 / FR-PLAN-2).

Plans live under ``%LOCALAPPDATA%/ai_testing_app/plans/{LEVEL}/``.
List and get only see the active security level — OFFICIAL and SECRET never mix.
Creating plans must not rewrite settings, reports, or Playwright project files.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_ID_SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
_CASE_SOURCE_KINDS = frozenset(
    {"manual-draft", "jira", "document", "playwright", "desktop"}
)
_RUN_RESULTS = frozenset({"pass", "fail", "error", "skipped", "pending"})


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id(prefix: str = "") -> str:
    raw = uuid.uuid4().hex[:12]
    return f"{prefix}{raw}" if prefix else raw


def new_run_id() -> str:
    """Allocate a case-run id before Playwright so heals can stamp it (KAN-159)."""
    return _new_id("r")


def plans_dir(level: str | None = None) -> Path:
    from settings.store import app_data_dir, get_security_level

    lvl = (level or get_security_level()).strip().upper()
    return app_data_dir() / "plans" / lvl


def _plan_path(plan_id: str, level: str | None = None) -> Path:
    pid = (plan_id or "").strip()
    if not _ID_SAFE.match(pid):
        raise ValueError(f"invalid plan id: {plan_id!r}")
    return plans_dir(level) / f"{pid}.json"


def _normalize_known_issue_field(raw: Any) -> Optional[dict[str, Any]]:
    from plans.known_issue import normalize_known_issue

    return normalize_known_issue(raw)


def _normalize_sources(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        raw = {}
    jira_keys: list[str] = []
    for key in raw.get("jira_keys") or []:
        text = str(key or "").strip().upper()
        if text and text not in jira_keys:
            jira_keys.append(text[:32])
    documents: list[str] = []
    for name in raw.get("documents") or []:
        text = str(name or "").strip()
        if text and text not in documents:
            documents.append(text[:200])
    playwright_suites: list[str] = []
    for path in raw.get("playwright_suites") or []:
        text = str(path or "").strip()
        if text and text not in playwright_suites:
            playwright_suites.append(text[:500])
    return {
        "jira_keys": jira_keys,
        "documents": documents,
        "playwright_suites": playwright_suites,
    }


def _normalize_jira_snapshots(raw: Any) -> dict[str, dict[str, Any]]:
    """Per-issue summary/AC captured at draft time (KAN-165 / C5)."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, val in raw.items():
        k = str(key or "").strip().upper()[:32]
        if not k or not isinstance(val, dict):
            continue
        out[k] = {
            "summary": str(val.get("summary") or "")[:500],
            "acceptance_criteria": str(val.get("acceptance_criteria") or "")[:8000],
            "captured_at": str(val.get("captured_at") or "")[:64],
            "stale": bool(val.get("stale", False)),
        }
    return out


def _normalize_case(raw: Any, *, order: int = 0) -> Optional[dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    cid = str(raw.get("id") or "").strip()
    if not _ID_SAFE.match(cid):
        cid = _new_id("c")
    name = str(raw.get("name") or "Untitled case").strip() or "Untitled case"
    tags: list[str] = []
    for tag in raw.get("tags") or []:
        t = str(tag or "").strip().lower()
        if t and t not in tags:
            tags.append(t[:40])
    source_raw = raw.get("source") if isinstance(raw.get("source"), dict) else {}
    kind = str(source_raw.get("kind") or "manual-draft").strip().lower()
    if kind not in _CASE_SOURCE_KINDS:
        kind = "manual-draft"
    source = {
        "kind": kind,
        "ref": str(source_raw.get("ref") or "").strip()[:300],
    }
    jira_key = str(raw.get("jira_key") or "").strip().upper()[:32]
    runs_in = raw.get("runs") if isinstance(raw.get("runs"), list) else []
    runs: list[dict[str, Any]] = []
    for item in runs_in:
        run = _normalize_run(item)
        if run:
            runs.append(run)
    now = _utcnow()
    quarantine_raw = raw.get("quarantine") if isinstance(raw.get("quarantine"), dict) else {}
    quarantine = {
        "reason": str(quarantine_raw.get("reason") or "")[:500],
        "expires_at": str(quarantine_raw.get("expires_at") or "")[:64] or None,
        "active": bool(quarantine_raw.get("active", False)),
    }
    quarantined = bool(raw.get("quarantined", False)) or bool(quarantine.get("active"))
    from plans.timeouts import DEFAULT_STEP_TIMEOUT_MS, resolve_step_timeout_ms

    timeout_resolved = resolve_step_timeout_ms(
        raw.get("step_timeout_ms", DEFAULT_STEP_TIMEOUT_MS)
    )
    step_timeout_ms = (
        int(timeout_resolved["step_timeout_ms"])
        if timeout_resolved.get("status") == "ok"
        else DEFAULT_STEP_TIMEOUT_MS
    )
    return {
        "id": cid,
        "name": name[:120],
        "enabled": bool(raw.get("enabled", True)),
        "archived": bool(raw.get("archived", False)),
        "quarantined": quarantined,
        "quarantine": quarantine,
        "tags": tags,
        "priority": int(raw.get("priority") or 0),
        "step_timeout_ms": step_timeout_ms,
        "note": str(raw.get("note") or "")[:2000],
        "order": int(raw.get("order") if raw.get("order") is not None else order),
        "jira_key": jira_key,
        "source": source,
        "known_issue": _normalize_known_issue_field(raw.get("known_issue")),
        "runs": runs,
        "created_at": str(raw.get("created_at") or now),
        "updated_at": str(raw.get("updated_at") or now),
    }


def _normalize_run(raw: Any) -> Optional[dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    rid = str(raw.get("id") or "").strip()
    if not _ID_SAFE.match(rid):
        rid = _new_id("r")
    result = str(raw.get("result") or "pending").strip().lower()
    if result not in _RUN_RESULTS:
        result = "pending"
    evidence: list[str] = []
    for item in raw.get("evidence") or []:
        text = str(item or "").strip()
        if text:
            evidence.append(text[:500])
    duration = raw.get("duration_ms")
    try:
        duration_ms = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_ms = None
    failure_class = str(raw.get("failure_class") or "").strip().lower()[:64] or None
    suite_run_id = str(raw.get("suite_run_id") or "").strip()
    if suite_run_id and not _ID_SAFE.match(suite_run_id):
        suite_run_id = ""
    # D3: environment name only — never credentials (KAN-183).
    env_name = str(raw.get("environment_name") or "").strip()[:40] or None
    return {
        "id": rid,
        "result": result,
        "duration_ms": duration_ms,
        "failure_class": failure_class,
        "evidence": evidence,
        "suite_run_id": suite_run_id or None,
        "environment_name": env_name,
        "started_at": str(raw.get("started_at") or "") or None,
        "finished_at": str(raw.get("finished_at") or "") or None,
        "note": str(raw.get("note") or "")[:2000],
        "tester_note": str(raw.get("tester_note") or "")[:2000],
        "known_issue": _normalize_known_issue_field(raw.get("known_issue")),
    }


def _normalize_suite_run(raw: Any) -> Optional[dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    sid = str(raw.get("id") or "").strip()
    if not _ID_SAFE.match(sid):
        sid = _new_id("sr")
    case_runs: list[dict[str, str]] = []
    for item in raw.get("case_runs") or []:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("case_id") or "").strip()
        rid = str(item.get("run_id") or "").strip()
        if cid and rid:
            case_runs.append({"case_id": cid[:64], "run_id": rid[:64]})
    skipped: list[dict[str, str]] = []
    for item in raw.get("skipped") or []:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("case_id") or "").strip()
        reason = str(item.get("reason") or "").strip()[:80]
        if cid and reason:
            skipped.append({"case_id": cid[:64], "reason": reason})
    mode = str(raw.get("mode") or "suite").strip().lower()[:40] or "suite"
    source = str(raw.get("source_suite_run_id") or "").strip() or None
    if source and not _ID_SAFE.match(source):
        source = None
    tag = str(raw.get("tag") or "").strip().lower()[:40] or None
    # D1: store parallel count used (default sequential = 1).
    try:
        parallel_count = int(raw.get("parallel_count") if raw.get("parallel_count") is not None else 1)
    except (TypeError, ValueError):
        parallel_count = 1
    if parallel_count < 1:
        parallel_count = 1
    # D3: named environment used for this suite run (name only).
    env_name = str(raw.get("environment_name") or "").strip()[:40] or None
    # D7: persist suite duration when known (KAN-191).
    from plans.duration import coerce_duration_ms, wall_duration_ms

    duration_ms = coerce_duration_ms(raw.get("duration_ms"))
    if duration_ms is None:
        duration_ms = wall_duration_ms(raw.get("started_at"), raw.get("finished_at"))
    return {
        "id": sid,
        "mode": mode,
        "tag": tag,
        "parallel_count": parallel_count,
        "environment_name": env_name,
        "source_suite_run_id": source,
        "started_at": str(raw.get("started_at") or "") or None,
        "finished_at": str(raw.get("finished_at") or "") or None,
        "duration_ms": duration_ms,
        "case_runs": case_runs,
        "skipped": skipped,
    }


def _normalize_plan(raw: dict[str, Any], *, level: str) -> dict[str, Any]:
    pid = str(raw.get("id") or "").strip()
    if not _ID_SAFE.match(pid):
        pid = _new_id("p")
    suite_raw = raw.get("suite") if isinstance(raw.get("suite"), dict) else {}
    cases_in = suite_raw.get("cases") if isinstance(suite_raw.get("cases"), list) else []
    cases: list[dict[str, Any]] = []
    for idx, item in enumerate(cases_in):
        case = _normalize_case(item, order=idx)
        if case:
            cases.append(case)
    cases.sort(key=lambda c: (int(c.get("order") or 0), c.get("created_at") or "", c["id"]))
    suite_runs_in = raw.get("suite_runs") if isinstance(raw.get("suite_runs"), list) else []
    suite_runs: list[dict[str, Any]] = []
    for item in suite_runs_in:
        sr = _normalize_suite_run(item)
        if sr:
            suite_runs.append(sr)
    now = _utcnow()
    return {
        "id": pid,
        "name": (str(raw.get("name") or "Untitled plan").strip() or "Untitled plan")[:120],
        "intent": str(raw.get("intent") or "")[:4000],
        "security_level": level,
        "sources": _normalize_sources(raw.get("sources")),
        "jira_snapshots": _normalize_jira_snapshots(raw.get("jira_snapshots")),
        "suite": {"cases": cases},
        "suite_runs": suite_runs,
        "created_at": str(raw.get("created_at") or now),
        "updated_at": str(raw.get("updated_at") or now),
    }


def _load_plan_file(path: Path, *, level: str) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    plan = _normalize_plan(data, level=level)
    # Refuse cross-level leakage if a file somehow declares another level
    declared = str(plan.get("security_level") or level).strip().upper()
    if declared != level:
        return None
    return plan


def _write_plan(plan: dict[str, Any], *, level: str) -> dict[str, Any]:
    path = _plan_path(plan["id"], level)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def list_plans(level: str | None = None) -> dict[str, Any]:
    """List plans for the active (or given) security level only."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    root = plans_dir(lvl)
    plans: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            plan = _load_plan_file(path, level=lvl)
            if not plan:
                continue
            cases = plan.get("suite", {}).get("cases") or []
            run_count = sum(len(c.get("runs") or []) for c in cases)
            plans.append(
                {
                    "id": plan["id"],
                    "name": plan["name"],
                    "intent": plan.get("intent") or "",
                    "security_level": plan["security_level"],
                    "case_count": len(cases),
                    "run_count": run_count,
                    "sources": plan.get("sources") or {"jira_keys": [], "documents": []},
                    "created_at": plan.get("created_at"),
                    "updated_at": plan.get("updated_at"),
                }
            )
    return {
        "status": "ok",
        "security_level": lvl,
        "plans": plans,
        "count": len(plans),
    }


def get_plan(plan_id: str, level: str | None = None) -> dict[str, Any]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    pid = (plan_id or "").strip()
    if not _ID_SAFE.match(pid):
        return {
            "status": "error",
            "error": "invalid_plan_id",
            "message": "Plan id is missing or invalid.",
            "security_level": lvl,
        }
    plan = _load_plan_file(_plan_path(pid, lvl), level=lvl)
    if not plan:
        return {
            "status": "error",
            "error": "not_found",
            "message": f"Plan {pid!r} was not found for {lvl}.",
            "security_level": lvl,
        }
    return {"status": "ok", "security_level": lvl, "plan": plan}


def create_plan(
    name: str,
    intent: str = "",
    sources: dict[str, Any] | None = None,
    cases: list[dict[str, Any]] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Create a plan under the active security level. Does not touch other app data."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    now = _utcnow()
    plan = _normalize_plan(
        {
            "id": _new_id("p"),
            "name": name,
            "intent": intent,
            "sources": sources or {},
            "suite": {"cases": cases or []},
            "created_at": now,
            "updated_at": now,
        },
        level=lvl,
    )
    _write_plan(plan, level=lvl)
    return {"status": "ok", "security_level": lvl, "plan": plan}


def upsert_jira_snapshot(
    plan_id: str,
    issue_key: str,
    *,
    summary: str = "",
    acceptance_criteria: str = "",
    stale: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Record or update the draft-time summary/AC for a linked issue (KAN-165)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    key = str(issue_key or "").strip().upper()[:32]
    if not key:
        return {
            "status": "error",
            "error": "issue_key_required",
            "message": "Provide a Jira issue key for the snapshot.",
            "security_level": lvl,
        }
    now = _utcnow()
    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    snaps[key] = {
        "summary": str(summary or "")[:500],
        "acceptance_criteria": str(acceptance_criteria or "")[:8000],
        "captured_at": now,
        "stale": bool(stale),
    }
    plan["jira_snapshots"] = snaps
    sources = _normalize_sources(plan.get("sources"))
    if key not in sources["jira_keys"]:
        sources["jira_keys"].append(key)
    plan["sources"] = sources
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "snapshot": snaps[key],
        "issue_key": key,
    }


def set_jira_snapshot_stale(
    plan_id: str,
    issue_key: str,
    *,
    stale: bool,
    level: str | None = None,
) -> dict[str, Any]:
    """Flip the stale flag on an existing snapshot without changing captured text."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    key = str(issue_key or "").strip().upper()[:32]
    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    if key not in snaps:
        return {
            "status": "error",
            "error": "snapshot_missing",
            "message": f"No Jira snapshot for {key} on this plan.",
            "security_level": lvl,
        }
    snaps[key]["stale"] = bool(stale)
    plan["jira_snapshots"] = snaps
    plan["updated_at"] = _utcnow()
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "snapshot": snaps[key],
        "issue_key": key,
    }


def count_plan_runs(plan: dict[str, Any]) -> int:
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    total = 0
    for case in cases:
        if isinstance(case, dict):
            total += len(case.get("runs") or [])
    return total


def add_case(
    plan_id: str,
    name: str,
    *,
    jira_key: str = "",
    tags: list[str] | None = None,
    priority: int = 0,
    note: str = "",
    enabled: bool = True,
    source_kind: str = "manual-draft",
    source_ref: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cases = list((plan.get("suite") or {}).get("cases") or [])
    order = len(cases)
    now = _utcnow()
    case = _normalize_case(
        {
            "id": _new_id("c"),
            "name": name,
            "enabled": enabled,
            "archived": False,
            "tags": tags or [],
            "priority": priority,
            "note": note,
            "order": order,
            "jira_key": jira_key,
            "source": {"kind": source_kind, "ref": source_ref},
            "runs": [],
            "created_at": now,
            "updated_at": now,
        },
        order=order,
    )
    assert case is not None
    cases.append(case)
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = now
    if jira_key:
        sources = _normalize_sources(plan.get("sources"))
        key = jira_key.strip().upper()
        if key and key not in sources["jira_keys"]:
            sources["jira_keys"].append(key)
        plan["sources"] = sources
    _write_plan(plan, level=lvl)
    return {"status": "ok", "security_level": lvl, "plan": plan, "case": case}


def add_run(
    plan_id: str,
    case_id: str,
    *,
    result: str = "pending",
    duration_ms: int | None = None,
    failure_class: str | None = None,
    evidence: list[str] | None = None,
    note: str = "",
    started_at: str | None = None,
    finished_at: str | None = None,
    suite_run_id: str | None = None,
    run_id: str | None = None,
    environment_name: str | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Attach a run record to a case (execution itself is later stories)."""
    from settings.environments import active_environment_name
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    cases = list((plan.get("suite") or {}).get("cases") or [])
    target: Optional[dict[str, Any]] = None
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
    now = _utcnow()
    rid = (run_id or "").strip()
    if rid and not _ID_SAFE.match(rid):
        rid = ""
    env_label = (environment_name if environment_name is not None else active_environment_name())
    run = _normalize_run(
        {
            "id": rid or _new_id("r"),
            "result": result,
            "duration_ms": duration_ms,
            "failure_class": failure_class,
            "evidence": evidence or [],
            "suite_run_id": suite_run_id,
            "environment_name": env_label,
            "started_at": started_at or now,
            "finished_at": finished_at or now,
            "note": note,
        }
    )
    assert run is not None
    target["runs"] = list(target.get("runs") or []) + [run]
    target["updated_at"] = now
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": target,
        "run": run,
    }


def start_suite_run(
    plan_id: str,
    *,
    mode: str = "suite",
    source_suite_run_id: str | None = None,
    tag: str | None = None,
    parallel_count: int = 1,
    environment_name: str | None = None,
    skipped: list[dict[str, str]] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Create a suite-level run id linked to this plan (KAN-151 / KAN-169 / KAN-179 / KAN-183)."""
    from settings.environments import active_environment_name
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    now = _utcnow()
    try:
        pcount = int(parallel_count)
    except (TypeError, ValueError):
        pcount = 1
    if pcount < 1:
        pcount = 1
    env_label = (
        environment_name if environment_name is not None else active_environment_name()
    )
    suite_run = _normalize_suite_run(
        {
            "id": _new_id("sr"),
            "mode": mode,
            "tag": (str(tag or "").strip().lower()[:40] or None),
            "parallel_count": pcount,
            "environment_name": env_label,
            "source_suite_run_id": source_suite_run_id,
            "started_at": now,
            "finished_at": None,
            "case_runs": [],
            "skipped": skipped or [],
        }
    )
    assert suite_run is not None
    plan["suite_runs"] = list(plan.get("suite_runs") or []) + [suite_run]
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "suite_run": suite_run,
    }


def finish_suite_run(
    plan_id: str,
    suite_run_id: str,
    *,
    case_runs: list[dict[str, str]] | None = None,
    skipped: list[dict[str, str]] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Mark a suite run finished and attach case-run links / skips."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    sid = (suite_run_id or "").strip()
    target: Optional[dict[str, Any]] = None
    for item in plan.get("suite_runs") or []:
        if item.get("id") == sid:
            target = item
            break
    if target is None:
        return {
            "status": "error",
            "error": "suite_run_not_found",
            "message": f"Suite run {sid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    now = _utcnow()
    if case_runs is not None:
        cleaned: list[dict[str, str]] = []
        for item in case_runs:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("case_id") or "").strip()
            rid = str(item.get("run_id") or "").strip()
            if cid and rid:
                cleaned.append({"case_id": cid[:64], "run_id": rid[:64]})
        target["case_runs"] = cleaned
    if skipped is not None:
        sk: list[dict[str, str]] = []
        for item in skipped:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("case_id") or "").strip()
            reason = str(item.get("reason") or "").strip()[:80]
            if cid and reason:
                sk.append({"case_id": cid[:64], "reason": reason})
        target["skipped"] = sk
    target["finished_at"] = now
    # D7: store duration on the suite run (local only). Prefer sum of linked
    # case durations when wall clock is 0 (timestamps are second-precision).
    from plans.duration import coerce_duration_ms, wall_duration_ms

    wall = wall_duration_ms(target.get("started_at"), now)
    case_sum = 0
    any_case_dur = False
    by_ids: dict[tuple[str, str], dict[str, Any]] = {}
    for case in (plan.get("suite") or {}).get("cases") or []:
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or "")
        for run in case.get("runs") or []:
            if isinstance(run, dict) and run.get("id"):
                by_ids[(cid, str(run["id"]))] = run
    for link in target.get("case_runs") or []:
        if not isinstance(link, dict):
            continue
        run = by_ids.get((str(link.get("case_id") or ""), str(link.get("run_id") or "")))
        if not run:
            continue
        d = coerce_duration_ms(run.get("duration_ms"))
        if d is not None:
            case_sum += d
            any_case_dur = True
    if any_case_dur and (wall is None or wall == 0 or case_sum > wall):
        target["duration_ms"] = case_sum
    else:
        target["duration_ms"] = wall if wall is not None else (case_sum if any_case_dur else None)
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "suite_run": target,
    }


def append_run_evidence(
    plan_id: str,
    case_id: str,
    run_id: str,
    paths: list[str],
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Attach more evidence file paths to an existing run (e.g. evidence bundle)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    rid = (run_id or "").strip()
    cases = list((plan.get("suite") or {}).get("cases") or [])
    for case in cases:
        if case.get("id") != cid:
            continue
        for run in case.get("runs") or []:
            if run.get("id") != rid:
                continue
            ev = list(run.get("evidence") or [])
            for path in paths or []:
                text = str(path or "").strip()
                if text and text not in ev:
                    ev.append(text[:500])
            run["evidence"] = ev
            case["updated_at"] = _utcnow()
            plan["suite"] = {"cases": cases}
            plan["updated_at"] = _utcnow()
            _write_plan(plan, level=lvl)
            return {
                "status": "ok",
                "security_level": lvl,
                "plan": plan,
                "case": case,
                "run": run,
            }
    return {
        "status": "error",
        "error": "run_not_found",
        "message": f"Run {rid!r} on case {cid!r} was not found.",
        "security_level": lvl,
    }


def set_run_failure_class(
    plan_id: str,
    case_id: str,
    run_id: str,
    failure_class: str | None,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Tester-selected failure class on a run (KAN-145 / FR-HEAL-4)."""
    from plans.failure_class import normalize_failure_class
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    rid = (run_id or "").strip()
    norm = normalize_failure_class(failure_class)
    cases = list((plan.get("suite") or {}).get("cases") or [])
    for case in cases:
        if case.get("id") != cid:
            continue
        for run in case.get("runs") or []:
            if run.get("id") != rid:
                continue
            run["failure_class"] = norm
            case["updated_at"] = _utcnow()
            plan["suite"] = {"cases": cases}
            plan["updated_at"] = _utcnow()
            _write_plan(plan, level=lvl)
            return {
                "status": "ok",
                "security_level": lvl,
                "plan": plan,
                "case": case,
                "run": run,
                "failure_class": norm,
                "create_bug_allowed": norm == "product_bug",
            }
    return {
        "status": "error",
        "error": "run_not_found",
        "message": f"Run {rid!r} on case {cid!r} was not found.",
        "security_level": lvl,
    }


def set_known_issue_link(
    plan_id: str,
    case_id: str,
    *,
    note: str = "",
    jira_key: str = "",
    run_id: str | None = None,
    clear: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Link (or clear) known-issue note + optional Jira key (KAN-153 / B6).

    Run result is never flipped to pass. Nothing is transitioned in Jira.
    """
    from plans.known_issue import normalize_known_issue
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    rid = (run_id or "").strip() or None

    payload = None if clear else normalize_known_issue(
        {"note": note, "jira_key": jira_key, "linked": True}
    )
    if not clear and payload is None:
        return {
            "status": "error",
            "error": "known_issue_empty",
            "message": "Provide a known-issue note and/or Jira key, or clear=true.",
            "security_level": lvl,
        }

    cases = list((plan.get("suite") or {}).get("cases") or [])
    target_case: Optional[dict[str, Any]] = None
    target_run: Optional[dict[str, Any]] = None
    for case in cases:
        if case.get("id") != cid:
            continue
        target_case = case
        if rid:
            for run in case.get("runs") or []:
                if run.get("id") == rid:
                    target_run = run
                    break
        break

    if target_case is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    if rid and target_run is None:
        return {
            "status": "error",
            "error": "run_not_found",
            "message": f"Run {rid!r} on case {cid!r} was not found.",
            "security_level": lvl,
        }

    now = _utcnow()
    prior_result = target_run.get("result") if target_run else None

    if clear:
        target_case.pop("known_issue", None)
        if target_run is not None:
            target_run.pop("known_issue", None)
    else:
        assert payload is not None
        target_case["known_issue"] = dict(payload)
        if target_run is not None:
            target_run["known_issue"] = dict(payload)
            target_run["failure_class"] = "known_issue"
            if prior_result is not None:
                target_run["result"] = prior_result

    target_case["updated_at"] = now
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)

    result_after = target_run.get("result") if target_run else None
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": target_case,
        "run": target_run,
        "known_issue": None if clear else payload,
        "label": None if clear else "known",
        "result": result_after,
        "result_unchanged": True,
        "jira_transitioned": False,
        "create_bug_allowed": False,
        "message": (
            "Known issue cleared."
            if clear
            else "Known issue linked. Run stays red underneath and is labelled known. "
            "Nothing was transitioned in Jira."
        ),
    }


def set_plan_notes(
    plan_id: str,
    case_id: str,
    *,
    case_note: str | None = None,
    run_note: str | None = None,
    run_id: str | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Set local exploratory notes on a case and/or a run (KAN-155 / B7).

    Case note → ``case.note``. Run note → ``run.tester_note`` (does not overwrite
    system/error ``run.note``). Level-scoped with the plan. No session recorder.
    """
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    rid = (run_id or "").strip() or None

    if case_note is None and run_note is None:
        return {
            "status": "error",
            "error": "notes_empty",
            "message": "Provide case_note and/or run_note.",
            "security_level": lvl,
        }

    want_run_note = run_note is not None
    run_note_text = str(run_note)[:2000] if want_run_note else ""

    cases = list((plan.get("suite") or {}).get("cases") or [])
    target_case: Optional[dict[str, Any]] = None
    target_run: Optional[dict[str, Any]] = None
    for case in cases:
        if case.get("id") != cid:
            continue
        target_case = case
        if rid:
            for run in case.get("runs") or []:
                if run.get("id") == rid:
                    target_run = run
                    break
        elif want_run_note:
            runs = case.get("runs") or []
            if runs:
                target_run = runs[-1]
                rid = str(target_run.get("id") or "") or None
        break

    if target_case is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    if want_run_note and target_run is None:
        # Allow case-only save when UI sends empty run_note with no runs yet.
        if rid or run_note_text.strip():
            return {
                "status": "error",
                "error": "run_not_found",
                "message": (
                    f"Run {rid!r} on case {cid!r} was not found."
                    if rid
                    else f"Case {cid!r} has no runs to attach a run note."
                ),
                "security_level": lvl,
            }
        want_run_note = False

    now = _utcnow()
    if case_note is not None:
        target_case["note"] = str(case_note)[:2000]
    if want_run_note and target_run is not None:
        target_run["tester_note"] = run_note_text

    target_case["updated_at"] = now
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {
        "status": "ok",
        "security_level": lvl,
        "plan": plan,
        "case": target_case,
        "run": target_run,
        "case_note": target_case.get("note") or "",
        "tester_note": (target_run.get("tester_note") if target_run else "") or "",
        "run_id": rid,
        "message": "Notes saved locally (level-scoped with the plan).",
    }


def update_case(
    plan_id: str,
    case_id: str,
    *,
    name: str | None = None,
    note: str | None = None,
    enabled: bool | None = None,
    archived: bool | None = None,
    order: int | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    step_timeout_ms: int | None = None,
    level: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Edit a case before any run (KAN-133 / FR-PLAN-1/2). Local only.

    Archive (KAN-177 / C11) sets archived=True without deleting runs or evidence.
    Step timeout (KAN-187 / D5) is editable before run; default matches runner.
    Successful edits append a local side-effects audit line (KAN-195 / E2).
    """
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    cases = list((plan.get("suite") or {}).get("cases") or [])
    target: Optional[dict[str, Any]] = None
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
    now = _utcnow()
    fields_changed: list[str] = []
    if name is not None:
        text = str(name).strip() or "Untitled case"
        target["name"] = text[:120]
        fields_changed.append("name")
    if note is not None:
        target["note"] = str(note)[:2000]
        fields_changed.append("note")
    if enabled is not None:
        target["enabled"] = bool(enabled)
        fields_changed.append("enabled")
    if archived is not None:
        # Soft archive only — never clears runs/evidence (KAN-177).
        target["archived"] = bool(archived)
        fields_changed.append("archived")
    if order is not None:
        try:
            target["order"] = int(order)
            fields_changed.append("order")
        except (TypeError, ValueError):
            pass
    if priority is not None:
        try:
            target["priority"] = int(priority)
            fields_changed.append("priority")
        except (TypeError, ValueError):
            pass
    if tags is not None:
        cleaned: list[str] = []
        for tag in tags:
            t = str(tag or "").strip().lower()
            if t and t not in cleaned:
                cleaned.append(t[:40])
        target["tags"] = cleaned
        fields_changed.append("tags")
    if step_timeout_ms is not None:
        from plans.timeouts import resolve_step_timeout_ms

        resolved = resolve_step_timeout_ms(step_timeout_ms)
        if resolved.get("status") != "ok":
            return {
                **resolved,
                "security_level": lvl,
                "plan_id": plan_id,
                "case_id": cid,
            }
        target["step_timeout_ms"] = int(resolved["step_timeout_ms"])
        fields_changed.append("step_timeout_ms")
    target["updated_at"] = now
    cases.sort(key=lambda c: (int(c.get("order") or 0), c.get("created_at") or "", c["id"]))
    plan["suite"] = {"cases": cases}
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    if fields_changed:
        try:
            from settings.local_audit import audit_plan_case_edit

            audit_plan_case_edit(
                plan_id=str(plan.get("id") or plan_id),
                case_id=cid,
                level=lvl,
                session_id=session_id,
                fields_changed=fields_changed,
            )
        except OSError:
            pass
    return {"status": "ok", "security_level": lvl, "plan": plan, "case": target}


def reorder_cases(
    plan_id: str,
    case_ids: list[str],
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Reorder cases by id list. Unknown ids keep their relative place at the end."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cases = list((plan.get("suite") or {}).get("cases") or [])
    by_id = {c["id"]: c for c in cases}
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in case_ids or []:
        cid = str(raw or "").strip()
        if cid in by_id and cid not in seen:
            ordered.append(by_id[cid])
            seen.add(cid)
    for case in cases:
        if case["id"] not in seen:
            ordered.append(case)
    now = _utcnow()
    for idx, case in enumerate(ordered):
        case["order"] = idx
        case["updated_at"] = now
    plan["suite"] = {"cases": ordered}
    plan["updated_at"] = now
    _write_plan(plan, level=lvl)
    return {"status": "ok", "security_level": lvl, "plan": plan}


def cases_for_run(plan: dict[str, Any] | str, *, level: str | None = None) -> dict[str, Any]:
    """Cases that later runs should execute — skips disabled, archived, quarantine (KAN-133 / D2)."""
    from settings.store import get_security_level
    from plans.quarantine import is_actively_quarantined

    lvl = (level or get_security_level()).strip().upper()
    if isinstance(plan, str):
        loaded = get_plan(plan, level=lvl)
        if loaded.get("status") != "ok":
            return loaded
        plan_obj = loaded["plan"]
    else:
        plan_obj = plan
    cases = list((plan_obj.get("suite") or {}).get("cases") or [])
    runnable: list[dict[str, Any]] = []
    skipped: list[str] = []
    skipped_reasons: list[dict[str, str]] = []
    for c in cases:
        cid = str(c.get("id") or "")
        if c.get("archived", False):
            skipped.append(cid)
            skipped_reasons.append({"case_id": cid, "reason": "archived"})
            continue
        if not c.get("enabled", True):
            skipped.append(cid)
            skipped_reasons.append({"case_id": cid, "reason": "disabled"})
            continue
        if is_actively_quarantined(c):
            skipped.append(cid)
            skipped_reasons.append({"case_id": cid, "reason": "quarantined"})
            continue
        runnable.append(c)
    runnable.sort(key=lambda c: (int(c.get("order") or 0), c.get("created_at") or "", c["id"]))
    return {
        "status": "ok",
        "security_level": lvl,
        "plan_id": plan_obj.get("id"),
        "cases": runnable,
        "count": len(runnable),
        "skipped_case_ids": skipped,
        "skipped_count": len(skipped),
        "skipped": skipped_reasons,
    }


def record_document_source(
    plan_id: str,
    document_name: str,
    *,
    jira_key: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Attach a document name (and optional Jira key) to plan sources without rewriting cases."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    sources = _normalize_sources(plan.get("sources"))
    doc = (document_name or "").strip()[:200]
    if doc and doc not in sources["documents"]:
        sources["documents"].append(doc)
    key = (jira_key or "").strip().upper()[:32]
    if key and key not in sources["jira_keys"]:
        sources["jira_keys"].append(key)
    plan["sources"] = sources
    plan["updated_at"] = _utcnow()
    _write_plan(plan, level=lvl)
    return {"status": "ok", "security_level": lvl, "plan": plan}


def record_playwright_source(
    plan_id: str,
    suite_path: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Record an imported Playwright project path on the plan (never deletes external files)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    sources = _normalize_sources(plan.get("sources"))
    path = (suite_path or "").strip()[:500]
    if path and path not in sources["playwright_suites"]:
        sources["playwright_suites"].append(path)
    plan["sources"] = sources
    plan["updated_at"] = _utcnow()
    _write_plan(plan, level=lvl)
    return {"status": "ok", "security_level": lvl, "plan": plan}
