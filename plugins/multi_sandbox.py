"""
Multi-sandbox orchestration (KAN-55 stub → KAN-95 real local records).

Persists configured sandbox environments per security level, tracks local
prepare/status, and enforces a safe max count. No cloud device farms.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_DISABLED_MSG = (
    "Multi-sandbox orchestration plugin is disabled. "
    "Enable plugin_multi_sandbox_enabled in settings to plan sandboxes."
)
_SETTING_KEY = "plugin_multi_sandbox_enabled"
_CONFIG_KEY = "multi_sandboxes"
# Home-PC safe local limit (FR-PLUG-1 follow-on; no cloud farms)
MAX_SANDBOXES = 4
_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,31}$")
_ACTIONS = frozenset({"list", "plan", "prepare", "status", "upsert", "remove"})


def is_enabled() -> bool:
    from settings.store import load_settings

    return bool(load_settings().get(_SETTING_KEY, False))


def plugin_status() -> dict[str, Any]:
    from settings.store import load_settings, security_status

    settings = load_settings()
    sec = security_status()
    sandboxes = list_configured_sandboxes(ensure_default=False)
    return {
        _SETTING_KEY: bool(settings.get(_SETTING_KEY, False)),
        "security_level": sec.get("security_level") or settings.get("security_level") or "OFFICIAL",
        "target_url": (settings.get("target_url") or "").strip(),
        "sandbox_count": len(sandboxes),
        "max_sandboxes": MAX_SANDBOXES,
        "sandboxes": sandboxes,
        "mode": "local",
    }


def set_plugin_enabled(enabled: bool) -> dict[str, Any]:
    from settings.store import update_setting

    update_setting(_SETTING_KEY, bool(enabled), confirm=True)
    if enabled:
        list_configured_sandboxes(ensure_default=True)
    return plugin_status()


def _state_path() -> Path:
    from settings.store import app_data_dir, get_security_level

    level = get_security_level()
    return app_data_dir() / "sandbox_state" / f"{level}.json"


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return {"sandboxes": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sandboxes": {}}
    if not isinstance(data, dict):
        return {"sandboxes": {}}
    boxes = data.get("sandboxes")
    if not isinstance(boxes, dict):
        boxes = {}
    return {"sandboxes": boxes}


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_id(raw: str) -> Optional[str]:
    value = (raw or "").strip()
    if not _ID_RE.match(value):
        return None
    return value.lower()


def _sanitize_record(raw: Any) -> Optional[dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    sid = _normalize_id(str(raw.get("id") or ""))
    if not sid:
        return None
    label = str(raw.get("label") or sid).strip() or sid
    url = str(raw.get("url") or "").strip()
    profile_key = str(raw.get("profile_key") or sid).strip() or sid
    profile_key = re.sub(r"[^a-zA-Z0-9_-]", "-", profile_key)[:48] or sid
    return {
        "id": sid,
        "label": label[:80],
        "url": url[:500],
        "profile_key": profile_key,
    }


def _default_seed() -> list[dict[str, Any]]:
    from settings.store import load_settings, security_status

    settings = load_settings()
    sec = security_status()
    level = (sec.get("security_level") or settings.get("security_level") or "OFFICIAL").upper()
    base_url = (settings.get("target_url") or "").strip() or "https://example.local"
    return [
        {
            "id": "primary",
            "label": "Primary AUT",
            "url": base_url,
            "profile_key": "primary",
            "credentials_scope": level,
        }
    ]


def _persist_configs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from settings.store import get_security_level, update_setting

    clean: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in records:
        item = _sanitize_record(raw)
        if not item or item["id"] in seen:
            continue
        seen.add(item["id"])
        clean.append(
            {
                "id": item["id"],
                "label": item["label"],
                "url": item["url"],
                "profile_key": item["profile_key"],
            }
        )
        if len(clean) >= MAX_SANDBOXES:
            break
    update_setting(_CONFIG_KEY, clean, confirm=True)
    level = get_security_level()
    return [_enrich_public(r, level) for r in clean]


def list_configured_sandboxes(*, ensure_default: bool = True) -> list[dict[str, Any]]:
    """Return persisted sandbox configs for the active level (not hardcoded mocks)."""
    from settings.store import get_security_level, load_settings

    settings = load_settings()
    level = get_security_level()
    raw = settings.get(_CONFIG_KEY)
    records: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw:
            clean = _sanitize_record(item)
            if clean:
                records.append(clean)
    if not records and ensure_default:
        seed = _default_seed()
        return _persist_configs(seed)
    # Cap + de-dupe without writing unless we had to trim
    trimmed = records[:MAX_SANDBOXES]
    if isinstance(raw, list) and len(raw) > MAX_SANDBOXES:
        return _persist_configs(trimmed)
    return [_enrich_public(r, level) for r in trimmed]


def _enrich_public(record: dict[str, Any], level: str) -> dict[str, Any]:
    from settings.store import browser_profile_dir

    profile_root = browser_profile_dir(level)
    profile_key = record.get("profile_key") or record["id"]
    profile_path = profile_root / f"sandbox-{profile_key}"
    state = _load_state().get("sandboxes", {}).get(record["id"], {})
    status = state.get("status") if isinstance(state, dict) else None
    if status not in {"idle", "prepared", "error"}:
        status = "idle"
        if profile_path.is_dir():
            status = "prepared"
    return {
        "id": record["id"],
        "label": record.get("label") or record["id"],
        "url": record.get("url") or "",
        "profile_key": profile_key,
        "profile": str(profile_path),
        "credentials_scope": level,
        "status": status,
        "last_error": (state.get("last_error") if isinstance(state, dict) else None),
        "updated_at": (state.get("updated_at") if isinstance(state, dict) else None),
    }


def _with_status(sandboxes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from settings.store import get_security_level

    level = get_security_level()
    return [_enrich_public(s, level) for s in sandboxes]


def upsert_sandbox(
    sandbox_id: str,
    *,
    label: str = "",
    url: str = "",
    profile_key: str = "",
) -> dict[str, Any]:
    """Add or update a configured sandbox. Enforces MAX_SANDBOXES."""
    sid = _normalize_id(sandbox_id)
    if not sid:
        return {
            "status": "error",
            "error": "sandbox_id must start with a letter and use A-Z, 0-9, _ or - (max 32).",
            "message": "Invalid sandbox id.",
            "plugin": "multi_sandbox",
        }
    if not is_enabled():
        return {
            "status": "disabled",
            "error": _DISABLED_MSG,
            "message": _DISABLED_MSG,
            "plugin": "multi_sandbox",
        }

    current = list_configured_sandboxes(ensure_default=False)
    by_id = {s["id"]: s for s in current}
    existing = by_id.get(sid)
    if existing is None and len(current) >= MAX_SANDBOXES:
        return {
            "status": "error",
            "error": f"Local sandbox limit is {MAX_SANDBOXES}. Remove one before adding.",
            "message": f"Local sandbox limit is {MAX_SANDBOXES}.",
            "max_sandboxes": MAX_SANDBOXES,
            "sandboxes": current,
            "plugin": "multi_sandbox",
        }

    record = {
        "id": sid,
        "label": (label or (existing or {}).get("label") or sid).strip() or sid,
        "url": (url if url is not None and str(url).strip() != "" else (existing or {}).get("url") or "").strip(),
        "profile_key": (
            profile_key
            or (existing or {}).get("profile_key")
            or sid
        ).strip()
        or sid,
    }
    by_id[sid] = record
    sandboxes = _persist_configs(list(by_id.values()))
    return {
        "status": "ok",
        "action": "upsert",
        "sandboxes": sandboxes,
        "sandbox": next((s for s in sandboxes if s["id"] == sid), None),
        "message": f"Saved sandbox '{sid}'.",
        "max_sandboxes": MAX_SANDBOXES,
        "plugin": "multi_sandbox",
    }


def remove_sandbox(sandbox_id: str) -> dict[str, Any]:
    sid = _normalize_id(sandbox_id)
    if not sid:
        return {
            "status": "error",
            "error": "sandbox_id is required.",
            "message": "sandbox_id is required.",
            "plugin": "multi_sandbox",
        }
    if not is_enabled():
        return {
            "status": "disabled",
            "error": _DISABLED_MSG,
            "message": _DISABLED_MSG,
            "plugin": "multi_sandbox",
        }

    current = list_configured_sandboxes(ensure_default=False)
    remaining = [s for s in current if s["id"] != sid]
    if len(remaining) == len(current):
        return {
            "status": "error",
            "error": f"Sandbox '{sid}' not found.",
            "message": f"Sandbox '{sid}' not found.",
            "sandboxes": current,
            "plugin": "multi_sandbox",
        }
    sandboxes = _persist_configs(remaining)
    state = _load_state()
    state.get("sandboxes", {}).pop(sid, None)
    _save_state(state)
    return {
        "status": "ok",
        "action": "remove",
        "sandboxes": sandboxes,
        "message": f"Removed sandbox '{sid}'.",
        "max_sandboxes": MAX_SANDBOXES,
        "plugin": "multi_sandbox",
    }


def prepare_sandboxes(sandbox_id: Optional[str] = None) -> dict[str, Any]:
    """Create local profile directories for configured sandboxes (no browser launch)."""
    from settings.store import browser_profile_dir, get_security_level

    if not is_enabled():
        return {
            "status": "disabled",
            "error": _DISABLED_MSG,
            "message": _DISABLED_MSG,
            "plugin": "multi_sandbox",
        }

    level = get_security_level()
    configured = list_configured_sandboxes(ensure_default=True)
    targets = configured
    if sandbox_id:
        sid = _normalize_id(sandbox_id)
        targets = [s for s in configured if s["id"] == sid]
        if not targets:
            return {
                "status": "error",
                "error": f"Sandbox '{sandbox_id}' not found.",
                "message": f"Sandbox '{sandbox_id}' not found.",
                "sandboxes": configured,
                "plugin": "multi_sandbox",
            }

    state = _load_state()
    boxes = state.setdefault("sandboxes", {})
    prepared: list[str] = []
    errors: list[dict[str, str]] = []
    root = browser_profile_dir(level)

    for item in targets:
        sid = item["id"]
        profile_key = item.get("profile_key") or sid
        path = root / f"sandbox-{profile_key}"
        try:
            path.mkdir(parents=True, exist_ok=True)
            boxes[sid] = {
                "status": "prepared",
                "profile_path": str(path),
                "last_error": None,
                "updated_at": _utcnow(),
            }
            prepared.append(sid)
        except OSError as exc:
            boxes[sid] = {
                "status": "error",
                "profile_path": str(path),
                "last_error": str(exc),
                "updated_at": _utcnow(),
            }
            errors.append({"id": sid, "error": str(exc)})

    _save_state(state)
    sandboxes = _with_status(configured)
    if errors and not prepared:
        return {
            "status": "fail",
            "action": "prepare",
            "sandboxes": sandboxes,
            "prepared": prepared,
            "errors": errors,
            "message": "Failed to prepare sandbox profile directories.",
            "plugin": "multi_sandbox",
        }
    msg = f"Prepared {len(prepared)} sandbox profile(s) under {root}."
    if errors:
        msg += f" {len(errors)} error(s)."
    return {
        "status": "ok",
        "action": "prepare",
        "sandboxes": sandboxes,
        "prepared": prepared,
        "errors": errors,
        "message": msg,
        "max_sandboxes": MAX_SANDBOXES,
        "plugin": "multi_sandbox",
    }


def orchestrate(
    action: str = "list",
    *,
    sandbox_id: str = "",
    label: str = "",
    url: str = "",
    profile_key: str = "",
) -> dict[str, Any]:
    """Local orchestration. Actions: list | plan | prepare | status | upsert | remove."""
    action_norm = (action or "list").strip().lower()
    if action_norm not in _ACTIONS:
        action_norm = "list"

    result: dict[str, Any] = {
        "status": "fail",
        "action": action_norm,
        "sandboxes": [],
        "plan": None,
        "error": None,
        "message": None,
        "max_sandboxes": MAX_SANDBOXES,
        "mode": "local",
        "plugin": "multi_sandbox",
    }

    if not is_enabled():
        result["status"] = "disabled"
        result["error"] = _DISABLED_MSG
        result["message"] = _DISABLED_MSG
        return result

    if action_norm == "upsert":
        return upsert_sandbox(
            sandbox_id or "",
            label=label or "",
            url=url or "",
            profile_key=profile_key or "",
        )
    if action_norm == "remove":
        return remove_sandbox(sandbox_id or "")
    if action_norm == "prepare":
        return prepare_sandboxes(sandbox_id or None)

    sandboxes = list_configured_sandboxes(ensure_default=True)
    result["sandboxes"] = sandboxes

    if action_norm in {"list", "status"}:
        prepared = sum(1 for s in sandboxes if s.get("status") == "prepared")
        result["status"] = "ok"
        result["message"] = (
            f"Listed {len(sandboxes)} configured sandbox(es) "
            f"({prepared} prepared). Max {MAX_SANDBOXES}."
        )
        return result

    # plan — real local plan from configured records
    result["plan"] = {
        "mode": "local",
        "max_sandboxes": MAX_SANDBOXES,
        "steps": [
            {
                "sandbox_id": s["id"],
                "action": "prepare_profile",
                "url": s.get("url") or "",
                "profile": s.get("profile") or "",
                "status": s.get("status") or "idle",
            }
            for s in sandboxes
        ],
        "note": (
            "Local orchestration plan from configured sandboxes. "
            "Call action=prepare to create profile directories. "
            "Cloud device farms are out of scope."
        ),
    }
    result["status"] = "ok"
    result["message"] = (
        f"Local orchestration plan ready for {len(sandboxes)} configured sandbox(es)."
    )
    return result


# Back-compat alias used by older tests / imports
def stub_sandboxes() -> list[dict[str, Any]]:
    return list_configured_sandboxes(ensure_default=True)
