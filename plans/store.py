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
_CASE_SOURCE_KINDS = frozenset({"manual-draft", "jira", "document"})
_RUN_RESULTS = frozenset({"pass", "fail", "error", "skipped", "pending"})


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id(prefix: str = "") -> str:
    raw = uuid.uuid4().hex[:12]
    return f"{prefix}{raw}" if prefix else raw


def plans_dir(level: str | None = None) -> Path:
    from settings.store import app_data_dir, get_security_level

    lvl = (level or get_security_level()).strip().upper()
    return app_data_dir() / "plans" / lvl


def _plan_path(plan_id: str, level: str | None = None) -> Path:
    pid = (plan_id or "").strip()
    if not _ID_SAFE.match(pid):
        raise ValueError(f"invalid plan id: {plan_id!r}")
    return plans_dir(level) / f"{pid}.json"


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
    return {"jira_keys": jira_keys, "documents": documents}


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
    return {
        "id": cid,
        "name": name[:120],
        "enabled": bool(raw.get("enabled", True)),
        "archived": bool(raw.get("archived", False)),
        "tags": tags,
        "priority": int(raw.get("priority") or 0),
        "note": str(raw.get("note") or "")[:2000],
        "order": int(raw.get("order") if raw.get("order") is not None else order),
        "jira_key": jira_key,
        "source": source,
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
    return {
        "id": rid,
        "result": result,
        "duration_ms": duration_ms,
        "failure_class": failure_class,
        "evidence": evidence,
        "started_at": str(raw.get("started_at") or "") or None,
        "finished_at": str(raw.get("finished_at") or "") or None,
        "note": str(raw.get("note") or "")[:2000],
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
    now = _utcnow()
    return {
        "id": pid,
        "name": (str(raw.get("name") or "Untitled plan").strip() or "Untitled plan")[:120],
        "intent": str(raw.get("intent") or "")[:4000],
        "security_level": level,
        "sources": _normalize_sources(raw.get("sources")),
        "suite": {"cases": cases},
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
    level: str | None = None,
) -> dict[str, Any]:
    """Attach a run record to a case (execution itself is later stories)."""
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
    run = _normalize_run(
        {
            "id": _new_id("r"),
            "result": result,
            "duration_ms": duration_ms,
            "failure_class": failure_class,
            "evidence": evidence or [],
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
