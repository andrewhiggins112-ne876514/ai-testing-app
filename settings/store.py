"""Local settings. Credentials stay on disk under LOCALAPPDATA, never in the repo.

OFFICIAL / SECRET isolation (FR-SEC-1):
- Shared UI prefs live in settings.json (orb, report_sections, security_level).
- Credentials and env hints live in levels/{LEVEL}/credentials.json.
- Playwright profiles live in browser_profiles/{LEVEL}/.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_SECRET_MARKERS = ("token", "password", "secret", "credential")
SECURITY_LEVELS = ("OFFICIAL", "SECRET")
_SCOPED_KEYS = (
    "jira_url",
    "jira_email",
    "jira_api_token",
    "github_token",
    "jira_project",
    "target_url",
    "target_app_path",
    "api_endpoint",
    "playwright_suite_path",
)


def settings_path() -> Path:
    override = os.getenv("AI_TESTING_SETTINGS")
    if override:
        return Path(override)
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base) / "ai_testing_app" / "settings.json"
    return Path.home() / ".ai_testing_app" / "settings.json"


def app_data_dir() -> Path:
    return settings_path().parent


def credentials_path(level: str | None = None) -> Path:
    lvl = _normalize_level(level) if level else get_security_level()
    return app_data_dir() / "levels" / lvl / "credentials.json"


def browser_profile_dir(level: str | None = None) -> Path:
    lvl = _normalize_level(level) if level else get_security_level()
    return app_data_dir() / "browser_profiles" / lvl


def _normalize_level(level: str) -> str:
    value = (level or "").strip().upper()
    if value not in SECURITY_LEVELS:
        raise ValueError(f"Invalid security level: {level!r}")
    return value


def _defaults() -> dict:
    return {
        "security_level": "OFFICIAL",
        "jira_url": "",
        "jira_email": "",
        "jira_api_token": "",
        "github_token": "",
        "orb_style": "lightning",
        "orb_calm_color": "#50cdff",
        "orb_thinking_color": "#b388ff",
        "orb_size": 360,
        "orb_shape": "sphere",
        "orb_spin_speed": 1.0,
        "orb_turbulence": 1.0,
        "orb_pulse": 1.0,
        "orb_glow": 1.0,
        "orb_presets": {},
        "orb_active_preset": "",
        # FR-REP-2: which report blocks to include on export (all on by default)
        "report_sections": {
            "summary": True,
            "stories": True,
            "bugs": True,
            "evidence": True,
        },
        # Environment hints (also proposed via document ingestion — FR-LEARN / FR-SET-2)
        "jira_project": "",
        "target_url": "",
        "target_app_path": "",
        "api_endpoint": "",
        # FR-TEST-5: path to an existing Playwright project (level-scoped)
        "playwright_suite_path": "",
        # FR-PLUG-2: desktop .exe smoke plugin (KAN-47)
        "plugin_desktop_enabled": True,
        # FR-PLUG-2: multi-sandbox orchestration stub (KAN-55) — default off
        "plugin_multi_sandbox_enabled": False,
        # FR-TEST-4: capture final screenshot on successful Playwright runs (failures always)
        "playwright_success_evidence": True,
        # FR-SEC-2: no telemetry by default (GDPR)
        "telemetry_enabled": False,
    }


def _scoped_defaults() -> dict:
    return {key: _defaults()[key] for key in _SCOPED_KEYS}


def _hidden(key: str, value: Any) -> Any:
    if any(marker in key.lower() for marker in _SECRET_MARKERS):
        return "(hidden)" if value else ""
    return value


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_shared_raw() -> dict:
    path = settings_path()
    if not path.exists():
        return {}
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def _load_credentials(level: str) -> dict:
    path = credentials_path(level)
    data = _read_json(path)
    if not isinstance(data, dict):
        return _scoped_defaults()
    merged = _scoped_defaults()
    for key in _SCOPED_KEYS:
        if key in data:
            merged[key] = data[key]
    return merged


def _save_credentials(level: str, creds: dict) -> None:
    payload = _scoped_defaults()
    for key in _SCOPED_KEYS:
        if key in creds:
            payload[key] = creds[key]
    _write_json(credentials_path(level), payload)


def _migrate_flat_credentials(shared: dict) -> dict:
    """Move legacy flat credential keys into the active level's credentials file."""
    present = [key for key in _SCOPED_KEYS if key in shared]
    if not present:
        return shared
    level = str(shared.get("security_level") or "OFFICIAL").strip().upper()
    if level not in SECURITY_LEVELS:
        level = "OFFICIAL"
    existing = _load_credentials(level)
    for key in present:
        value = shared.pop(key)
        # Prefer non-empty migrated value when target slot is empty.
        if value or not existing.get(key):
            existing[key] = value
    _save_credentials(level, existing)
    _write_json(settings_path(), shared)
    return shared


def get_security_level() -> str:
    shared = _load_shared_raw()
    level = str(shared.get("security_level") or "OFFICIAL").strip().upper()
    return level if level in SECURITY_LEVELS else "OFFICIAL"


def set_security_level(level: str, confirm: bool = False) -> dict:
    """Switch active security level. Requires confirm=True (FR-SEC-3)."""
    try:
        normalized = _normalize_level(level)
    except ValueError:
        return {"status": "error", "message": "Invalid security level."}
    current = get_security_level()
    if normalized == current:
        return {
            "status": "unchanged",
            "security_level": current,
            "browser_profile": str(browser_profile_dir(current)),
        }
    if not confirm:
        return {
            "status": "confirmation_required",
            "proposed": {"security_level": normalized},
            "current": current,
            "browser_profile": str(browser_profile_dir(normalized)),
            "message": (
                f"Confirm switch from {current} to {normalized}? "
                "Credentials and browser profile will change."
            ),
        }
    shared = _load_shared_raw()
    shared["security_level"] = normalized
    # Ensure level dirs exist even when empty.
    credentials_path(normalized).parent.mkdir(parents=True, exist_ok=True)
    browser_profile_dir(normalized).mkdir(parents=True, exist_ok=True)
    _write_json(settings_path(), {k: v for k, v in shared.items() if k not in _SCOPED_KEYS})
    return {
        "status": "updated",
        "security_level": normalized,
        "browser_profile": str(browser_profile_dir(normalized)),
    }


def security_status() -> dict:
    """Non-secret status for UI/API (never echoes tokens)."""
    level = get_security_level()
    creds = _load_credentials(level)
    email_set = bool((creds.get("jira_email") or "").strip())
    token_set = bool((creds.get("jira_api_token") or "").strip())
    return {
        "security_level": level,
        "browser_profile": str(browser_profile_dir(level)),
        "settings_path": str(settings_path()),
        "credentials_path": str(credentials_path(level)),
        "jira_url": creds.get("jira_url") or "",
        "jira_credentials_configured": email_set and token_set,
        "jira_credentials_partial": (email_set or token_set) and not (email_set and token_set),
    }


def load_settings() -> dict:
    shared = _load_shared_raw()
    shared = _migrate_flat_credentials(dict(shared))
    merged = _defaults()
    for key, value in shared.items():
        if key not in _SCOPED_KEYS:
            merged[key] = value
    level = str(merged.get("security_level") or "OFFICIAL").strip().upper()
    if level not in SECURITY_LEVELS:
        level = "OFFICIAL"
        merged["security_level"] = level
    creds = _load_credentials(level)
    merged.update(creds)
    return merged


def write_settings(settings: dict) -> None:
    """Persist a merged settings dict, splitting shared vs level-scoped credentials."""
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dict")
    level = str(settings.get("security_level") or get_security_level()).strip().upper()
    if level not in SECURITY_LEVELS:
        level = "OFFICIAL"
    shared = {k: v for k, v in settings.items() if k not in _SCOPED_KEYS}
    shared["security_level"] = level
    # Drop any accidental scoped leftovers from disk copy.
    existing_shared = _load_shared_raw()
    for key in _SCOPED_KEYS:
        existing_shared.pop(key, None)
    existing_shared.update(shared)
    for key in _SCOPED_KEYS:
        existing_shared.pop(key, None)
    _write_json(settings_path(), existing_shared)
    creds = _load_credentials(level)
    for key in _SCOPED_KEYS:
        if key in settings:
            creds[key] = settings[key]
    _save_credentials(level, creds)


def update_setting(key: str, value: Any, confirm: bool = False) -> dict:
    shown = _hidden(key, value)
    if key == "security_level":
        return set_security_level(str(value), confirm=confirm)
    if not confirm:
        return {"status": "confirmation_required", "proposed": {key: shown}}
    if key in _SCOPED_KEYS:
        level = get_security_level()
        creds = _load_credentials(level)
        creds[key] = value
        _save_credentials(level, creds)
        return {"status": "updated", "key": key, "value": shown}
    shared = _load_shared_raw()
    for scoped in _SCOPED_KEYS:
        shared.pop(scoped, None)
    shared[key] = value
    if "security_level" not in shared:
        shared["security_level"] = "OFFICIAL"
    _write_json(settings_path(), shared)
    return {"status": "updated", "key": key, "value": shown}


def apply_settings_diff(updates: dict, confirm: bool = False) -> dict:
    """Apply multiple keys only after confirm=True (document ingestion / FR-SET-2)."""
    if not isinstance(updates, dict) or not updates:
        return {"status": "error", "message": "No settings to apply."}
    shown = {key: _hidden(key, value) for key, value in updates.items()}
    if not confirm:
        return {"status": "confirmation_required", "proposed": shown}
    if "security_level" in updates:
        level_result = set_security_level(str(updates["security_level"]), confirm=True)
        if level_result.get("status") == "error":
            return level_result
    settings = load_settings()
    for key, value in updates.items():
        if key == "security_level":
            continue
        settings[key] = value
    write_settings(settings)
    return {"status": "updated", "updated": shown}
