"""
Multi-sandbox orchestration stub (KAN-55 / MULTI-1).

Registry entry + settings toggle. Mock orchestration only — no parallel
Playwright grid or Kubernetes. Future slices can grow real runners here.
"""
from __future__ import annotations

from typing import Any

_DISABLED_MSG = (
    "Multi-sandbox orchestration plugin is disabled. "
    "Enable plugin_multi_sandbox_enabled in settings to plan sandboxes."
)
_SETTING_KEY = "plugin_multi_sandbox_enabled"


def is_enabled() -> bool:
    from settings.store import load_settings

    return bool(load_settings().get(_SETTING_KEY, False))


def plugin_status() -> dict[str, Any]:
    from settings.store import load_settings, security_status

    settings = load_settings()
    sec = security_status()
    return {
        _SETTING_KEY: bool(settings.get(_SETTING_KEY, False)),
        "security_level": sec.get("security_level") or settings.get("security_level") or "OFFICIAL",
        "target_url": (settings.get("target_url") or "").strip(),
        "sandbox_count": len(stub_sandboxes()),
    }


def set_plugin_enabled(enabled: bool) -> dict[str, Any]:
    from settings.store import update_setting

    update_setting(_SETTING_KEY, bool(enabled), confirm=True)
    return plugin_status()


def stub_sandboxes() -> list[dict[str, Any]]:
    """Placeholder sandbox slots (URLs / profiles / credential scopes). No secrets."""
    from settings.store import load_settings, security_status

    settings = load_settings()
    sec = security_status()
    level = (sec.get("security_level") or settings.get("security_level") or "OFFICIAL").upper()
    base_url = (settings.get("target_url") or "").strip() or "https://example.local"
    profile = sec.get("browser_profile") or f"browser_profiles/{level}"

    return [
        {
            "id": "primary",
            "label": "Primary AUT",
            "url": base_url,
            "profile": profile,
            "credentials_scope": level,
        },
        {
            "id": "secondary",
            "label": "Secondary AUT (stub)",
            "url": base_url.rstrip("/") + "/sandbox-b",
            "profile": f"{profile}-b",
            "credentials_scope": level,
        },
    ]


def orchestrate(action: str = "list") -> dict[str, Any]:
    """Mock orchestration. action: list | plan."""
    action_norm = (action or "list").strip().lower()
    if action_norm not in {"list", "plan"}:
        action_norm = "list"

    result: dict[str, Any] = {
        "status": "fail",
        "action": action_norm,
        "sandboxes": [],
        "plan": None,
        "error": None,
        "message": None,
        "plugin": "multi_sandbox",
    }

    if not is_enabled():
        result["status"] = "disabled"
        result["error"] = _DISABLED_MSG
        result["message"] = _DISABLED_MSG
        return result

    sandboxes = stub_sandboxes()
    result["sandboxes"] = sandboxes

    if action_norm == "list":
        result["status"] = "ok"
        result["message"] = f"Listed {len(sandboxes)} stub sandbox(es). No environments launched."
        return result

    # plan — mock only
    result["plan"] = {
        "mode": "mock",
        "steps": [
            {"sandbox_id": s["id"], "action": "prepare", "url": s["url"]}
            for s in sandboxes
        ],
        "note": "Stub plan only — parallel runners not implemented (out of scope for KAN-55).",
    }
    result["status"] = "ok"
    result["message"] = "Mock orchestration plan ready. No sandboxes were started."
    return result
