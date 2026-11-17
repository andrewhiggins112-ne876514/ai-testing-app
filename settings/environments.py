"""Named target environments under the active security level (KAN-183 / D3).

Local / test / staging are separate named targets. Credentials stay in the
level store and are never copied into a plan. Switching environment does not
switch security level. Runs record the environment name used.
"""
from __future__ import annotations

import re
import secrets
from typing import Any

from settings.store import (
    SECURITY_LEVELS,
    get_security_level,
    load_settings,
    update_setting,
)

MAX_NAMED_ENVIRONMENTS = 8
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.\-]{0,39}$")
_ID_RE = re.compile(r"^env_[a-z0-9]{8,16}$")


def _http_url_ok(value: str) -> bool:
    return value.startswith("https://") or value.startswith("http://")


def _messaging_url_ok(value: str) -> bool:
    lower = value.lower()
    return lower.startswith(
        ("https://", "http://", "amqp://", "amqps://", "ws://", "wss://")
    )


def _new_env_id() -> str:
    return f"env_{secrets.token_hex(5)}"


def _public_env(raw: dict[str, Any]) -> dict[str, Any]:
    """Strip anything that could look like a secret; targets only."""
    return {
        "id": str(raw.get("id") or ""),
        "name": str(raw.get("name") or ""),
        "target_url": str(raw.get("target_url") or "").strip(),
        "target_app_path": str(raw.get("target_app_path") or "").strip(),
        "api_endpoint": str(raw.get("api_endpoint") or "").strip(),
    }


def _normalize_env(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    eid = str(raw.get("id") or "").strip()
    if not _ID_RE.match(eid):
        eid = _new_env_id()
    name = str(raw.get("name") or "").strip()
    if not name or not _NAME_RE.match(name):
        return None
    url = str(raw.get("target_url") or "").strip()
    if url and not _http_url_ok(url):
        return None
    messaging = str(raw.get("api_endpoint") or "").strip()
    if messaging and not _messaging_url_ok(messaging):
        return None
    return {
        "id": eid,
        "name": name[:40],
        "target_url": url[:500],
        "target_app_path": str(raw.get("target_app_path") or "").strip()[:500],
        "api_endpoint": messaging[:500],
    }


def _seed_from_flat(data: dict[str, Any]) -> list[dict[str, Any]]:
    """If flat target fields exist but no named list, create a Default env."""
    url = str(data.get("target_url") or "").strip()
    exe = str(data.get("target_app_path") or "").strip()
    api = str(data.get("api_endpoint") or "").strip()
    if not (url or exe or api):
        return []
    seeded = _normalize_env(
        {
            "id": _new_env_id(),
            "name": "Default",
            "target_url": url,
            "target_app_path": exe,
            "api_endpoint": api,
        }
    )
    return [seeded] if seeded else []


def _load_raw_list(data: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], str]:
    settings = data if data is not None else load_settings()
    raw_list = settings.get("named_environments")
    envs: list[dict[str, Any]] = []
    if isinstance(raw_list, list):
        for item in raw_list:
            norm = _normalize_env(item)
            if norm:
                envs.append(norm)
    if not envs:
        envs = _seed_from_flat(settings)
    active = str(settings.get("active_environment_id") or "").strip()
    if envs and (not active or not any(e["id"] == active for e in envs)):
        active = envs[0]["id"]
    if not envs:
        active = ""
    return envs, active


def _persist(envs: list[dict[str, Any]], active_id: str) -> None:
    """Write named list + active id; mirror active targets into flat keys."""
    update_setting("named_environments", envs, confirm=True)
    update_setting("active_environment_id", active_id or "", confirm=True)
    active = next((e for e in envs if e["id"] == active_id), None)
    if active:
        update_setting("target_url", active.get("target_url") or "", confirm=True)
        update_setting(
            "target_app_path", active.get("target_app_path") or "", confirm=True
        )
        update_setting("api_endpoint", active.get("api_endpoint") or "", confirm=True)


def list_environments(*, level: str | None = None) -> dict[str, Any]:
    """List named environments for the active (or given) security level."""
    from settings.store import get_security_level as _gsl

    lvl = (level or _gsl()).strip().upper()
    if lvl not in SECURITY_LEVELS:
        lvl = "OFFICIAL"
    # Always load via current level settings; caller should set level first.
    # Switching env never changes security_level — we report it for clarity.
    current = get_security_level()
    envs, active = _load_raw_list()
    # Persist seed if we just created Default from flat fields.
    stored = load_settings().get("named_environments")
    if envs and not (isinstance(stored, list) and stored):
        _persist(envs, active)
    return {
        "status": "ok",
        "security_level": current,
        "requested_level": lvl,
        "level_unchanged": True,
        "active_environment_id": active or None,
        "active_environment_name": next(
            (e["name"] for e in envs if e["id"] == active), None
        ),
        "environments": [_public_env(e) for e in envs],
        "max": MAX_NAMED_ENVIRONMENTS,
        "credentials_in_plan": False,
        "message": (
            f"{len(envs)} named environment(s) under {current}. "
            "Credentials stay in the level store; switching env does not "
            "change security level."
        ),
    }


def get_active_environment() -> dict[str, Any]:
    """Active named environment (or empty defaults). Never includes secrets."""
    envs, active = _load_raw_list()
    for env in envs:
        if env["id"] == active:
            pub = _public_env(env)
            pub["status"] = "ok"
            pub["security_level"] = get_security_level()
            return pub
    return {
        "status": "ok",
        "id": None,
        "name": None,
        "target_url": str(load_settings().get("target_url") or "").strip(),
        "target_app_path": str(load_settings().get("target_app_path") or "").strip(),
        "api_endpoint": str(load_settings().get("api_endpoint") or "").strip(),
        "security_level": get_security_level(),
    }


def active_environment_name() -> str | None:
    """Name stamped onto runs; None if no named env is configured."""
    active = get_active_environment()
    name = str(active.get("name") or "").strip()
    return name or None


def upsert_environment(
    *,
    name: str,
    target_url: str = "",
    target_app_path: str = "",
    api_endpoint: str = "",
    env_id: str | None = None,
    activate: bool = False,
) -> dict[str, Any]:
    """Create or update a named target under the active level."""
    level_before = get_security_level()
    envs, active = _load_raw_list()
    clean_name = (name or "").strip()
    if not clean_name or not _NAME_RE.match(clean_name):
        return {
            "status": "error",
            "error": "environment_name_invalid",
            "message": (
                "Environment name must be 1–40 characters: letters, digits, "
                "spaces, underscore, dot, or hyphen."
            ),
            "security_level": level_before,
        }
    url = (target_url or "").strip()
    if url and not _http_url_ok(url):
        return {
            "status": "error",
            "error": "target_url_invalid",
            "message": "Target URL must start with http:// or https://.",
            "security_level": level_before,
        }
    messaging = (api_endpoint or "").strip()
    if messaging and not _messaging_url_ok(messaging):
        return {
            "status": "error",
            "error": "api_endpoint_invalid",
            "message": (
                "Messaging endpoint must start with http(s)://, amqp(s)://, or ws(s)://."
            ),
            "security_level": level_before,
        }
    exe = (target_app_path or "").strip()
    eid = (env_id or "").strip()
    existing_idx = next((i for i, e in enumerate(envs) if e["id"] == eid), None)
    if existing_idx is None and eid:
        return {
            "status": "error",
            "error": "environment_not_found",
            "message": f"Environment {eid!r} was not found under {level_before}.",
            "security_level": level_before,
        }
    if existing_idx is None and len(envs) >= MAX_NAMED_ENVIRONMENTS:
        return {
            "status": "error",
            "error": "environment_limit",
            "message": (
                f"At most {MAX_NAMED_ENVIRONMENTS} named environments under "
                f"one security level."
            ),
            "security_level": level_before,
            "max": MAX_NAMED_ENVIRONMENTS,
        }
    # Unique names (case-insensitive) within the level.
    lower = clean_name.lower()
    for i, e in enumerate(envs):
        if e["name"].lower() == lower and i != existing_idx:
            return {
                "status": "error",
                "error": "environment_name_taken",
                "message": f"An environment named {clean_name!r} already exists.",
                "security_level": level_before,
            }
    payload = _normalize_env(
        {
            "id": eid or _new_env_id(),
            "name": clean_name,
            "target_url": url,
            "target_app_path": exe,
            "api_endpoint": messaging,
        }
    )
    assert payload is not None
    if existing_idx is None:
        envs.append(payload)
        if activate or not active:
            active = payload["id"]
    else:
        envs[existing_idx] = payload
        if activate:
            active = payload["id"]
    _persist(envs, active)
    level_after = get_security_level()
    return {
        "status": "ok",
        "security_level": level_after,
        "level_unchanged": level_before == level_after,
        "environment": _public_env(payload),
        "active_environment_id": active,
        "environments": [_public_env(e) for e in envs],
        "credentials_copied_to_plan": False,
        "message": f"Saved environment {payload['name']!r}.",
    }


def activate_environment(env_id: str) -> dict[str, Any]:
    """Switch active named target. Does not change security level."""
    level_before = get_security_level()
    eid = (env_id or "").strip()
    envs, _active = _load_raw_list()
    match = next((e for e in envs if e["id"] == eid), None)
    if match is None:
        return {
            "status": "error",
            "error": "environment_not_found",
            "message": f"Environment {eid!r} was not found under {level_before}.",
            "security_level": level_before,
            "level_unchanged": True,
        }
    _persist(envs, eid)
    level_after = get_security_level()
    return {
        "status": "ok",
        "security_level": level_after,
        "level_unchanged": level_before == level_after,
        "active_environment_id": eid,
        "active_environment_name": match["name"],
        "environment": _public_env(match),
        "credentials_copied_to_plan": False,
        "message": (
            f"Active environment is now {match['name']!r}. "
            f"Security level remains {level_after}."
        ),
    }


def delete_environment(env_id: str) -> dict[str, Any]:
    """Remove a named environment. Credentials file is untouched for secrets."""
    level_before = get_security_level()
    eid = (env_id or "").strip()
    envs, active = _load_raw_list()
    kept = [e for e in envs if e["id"] != eid]
    if len(kept) == len(envs):
        return {
            "status": "error",
            "error": "environment_not_found",
            "message": f"Environment {eid!r} was not found under {level_before}.",
            "security_level": level_before,
        }
    if active == eid:
        active = kept[0]["id"] if kept else ""
    _persist(kept, active)
    return {
        "status": "ok",
        "security_level": get_security_level(),
        "level_unchanged": True,
        "active_environment_id": active or None,
        "environments": [_public_env(e) for e in kept],
        "message": "Environment removed. Secrets were not moved into any plan.",
    }


def sync_active_from_flat_targets() -> None:
    """Keep the active named env in sync when flat target fields are saved."""
    envs, active = _load_raw_list()
    data = load_settings()
    url = str(data.get("target_url") or "").strip()
    exe = str(data.get("target_app_path") or "").strip()
    api = str(data.get("api_endpoint") or "").strip()
    if not envs:
        if not (url or exe or api):
            return
        seeded = _normalize_env(
            {
                "id": _new_env_id(),
                "name": "Default",
                "target_url": url,
                "target_app_path": exe,
                "api_endpoint": api,
            }
        )
        if seeded:
            _persist([seeded], seeded["id"])
        return
    for i, env in enumerate(envs):
        if env["id"] == active:
            envs[i] = {
                **env,
                "target_url": url,
                "target_app_path": exe,
                "api_endpoint": api,
            }
            # Persist list + active only (flat keys already correct).
            update_setting("named_environments", envs, confirm=True)
            update_setting("active_environment_id", active, confirm=True)
            return
