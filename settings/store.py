"""Local settings. Credentials stay in this file, never in the repo."""
import json
import os
from pathlib import Path
from typing import Any

_SECRET_MARKERS = ("token", "password", "secret", "credential")

def settings_path() -> Path:
    override = os.getenv("AI_TESTING_SETTINGS")
    if override:
        return Path(override)
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base) / "ai_testing_app" / "settings.json"
    return Path.home() / ".ai_testing_app" / "settings.json"

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
    }

def _hidden(key: str, value: Any) -> Any:
    if any(marker in key.lower() for marker in _SECRET_MARKERS):
        return "(hidden)" if value else ""
    return value

def load_settings() -> dict:
    path = settings_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        merged = _defaults()
        merged.update(data)
        return merged
    return _defaults()

def write_settings(settings: dict) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def update_setting(key: str, value: Any, confirm: bool = False) -> dict:
    shown = _hidden(key, value)
    if not confirm:
        return {"status": "confirmation_required", "proposed": {key: shown}}
    settings = load_settings()
    settings[key] = value
    write_settings(settings)
    return {"status": "updated", "key": key, "value": shown}
