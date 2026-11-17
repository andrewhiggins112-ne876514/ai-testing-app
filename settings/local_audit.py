"""Local side-effects audit (KAN-195 / E2 / FR-SEC-2).

Confirm-gated or destructive local actions (plan edits, quarantines, privacy
wipes) append one JSONL line: time, action, plan/case id, level, session.
Never stores tokens or document bodies. Jira write audit stays separate.
No cloud / SIEM shipping.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Keys that must never appear in an audit line (tokens / document bodies).
_FORBIDDEN_KEYS = frozenset(
    {
        "token",
        "api_token",
        "jira_api_token",
        "password",
        "secret",
        "target_secret",
        "old_value",
        "value",
        "body",
        "document_body",
        "text",
        "content",
        "extracted",
    }
)


def local_audit_path() -> Path:
    """LOCALAPPDATA local_side_effects_audit.jsonl."""
    from settings.store import app_data_dir

    return app_data_dir() / "local_side_effects_audit.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _scrub(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Drop forbidden keys and nested blobs that look like secrets/bodies."""
    clean: Dict[str, Any] = {}
    for key, value in entry.items():
        low = str(key or "").strip().lower()
        if low in _FORBIDDEN_KEYS or any(part in low for part in ("token", "password", "secret")):
            continue
        if low in {"body", "document_body", "extracted_text"}:
            continue
        if isinstance(value, dict):
            clean[key] = _scrub(value)
        elif isinstance(value, list):
            # Keep short id/category lists only — never long document text.
            cleaned_list: List[Any] = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_list.append(_scrub(item))
                elif isinstance(item, str) and len(item) > 200:
                    continue
                else:
                    cleaned_list.append(item)
            clean[key] = cleaned_list
        elif isinstance(value, str) and len(value) > 500:
            # Cap free-text fields (e.g. quarantine reason already truncated upstream).
            clean[key] = value[:500]
        else:
            clean[key] = value
    return clean


def append_local_audit(
    action: str,
    *,
    plan_id: str | None = None,
    case_id: str | None = None,
    level: str | None = None,
    session_id: str | None = None,
    status: str = "ok",
    detail: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Append one local audit line. Never stores tokens or document bodies."""
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "").strip().upper()
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "action": str(action or "").strip()[:80],
        "plan_id": str(plan_id or "")[:120] or None,
        "case_id": str(case_id or "")[:120] or None,
        "security_level": lvl,
        "session_id": str(session_id or "desktop")[:120],
        "status": str(status or "ok")[:40],
        "cloud_siem": False,
    }
    if detail:
        entry["detail"] = _scrub(dict(detail))
    entry = _scrub(entry)
    path = local_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
    return entry


def list_local_audit(*, limit: int = 100) -> Dict[str, Any]:
    """Recent local side-effect lines for Security UI. No secrets/bodies."""
    from plugins.jira_plugin import jira_write_log_path

    n = max(1, min(int(limit or 100), 500))
    path = local_audit_path()
    entries: List[Dict[str, Any]] = []
    if path.is_file():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                entries.append(_scrub(parsed))
    # Newest first for the Security panel.
    entries.reverse()
    trimmed = entries[:n]
    jira_path = jira_write_log_path()
    return {
        "status": "ok",
        "path": str(path),
        "count": len(trimmed),
        "total_lines": len(entries),
        "entries": trimmed,
        "jira_write_audit_remains": True,
        "jira_write_audit_path": str(jira_path),
        "jira_write_audit_exists": jira_path.is_file(),
        "cloud_siem": False,
        "message": (
            "Local side-effects audit (plan edits, quarantines, wipes). "
            "No tokens or document bodies. Jira write audit remains separate."
        ),
    }


def audit_plan_case_edit(
    *,
    plan_id: str,
    case_id: str,
    level: str | None = None,
    session_id: str | None = None,
    fields_changed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Record a successful plan case edit (ids + field names only)."""
    return append_local_audit(
        "plan_case_edit",
        plan_id=plan_id,
        case_id=case_id,
        level=level,
        session_id=session_id,
        detail={"fields_changed": list(fields_changed or [])},
    )


def audit_quarantine(
    action: str,
    *,
    plan_id: str,
    case_id: str,
    level: str | None = None,
    session_id: str | None = None,
    reason: str | None = None,
    expires_at: str | None = None,
) -> Dict[str, Any]:
    """Record quarantine set/clear. Reason capped; never stores secrets."""
    detail: Dict[str, Any] = {}
    if reason is not None:
        detail["reason"] = str(reason)[:500]
    if expires_at is not None:
        detail["expires_at"] = str(expires_at)[:64]
    return append_local_audit(
        action,
        plan_id=plan_id,
        case_id=case_id,
        level=level,
        session_id=session_id,
        detail=detail or None,
    )


def audit_local_wipe(
    *,
    categories: List[str],
    level: str | None = None,
    session_id: str | None = None,
) -> Dict[str, Any]:
    """Record a confirmed privacy wipe (category names only)."""
    return append_local_audit(
        "local_data_wipe",
        plan_id=None,
        case_id=None,
        level=level,
        session_id=session_id,
        detail={"categories": [str(c) for c in categories]},
    )
