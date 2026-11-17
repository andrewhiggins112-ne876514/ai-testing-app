"""
Lightweight plugin registry (FR-PLUG-1 / FR-PLUG-2).

Static manifests + live enabled flags from settings. Enough for agents and
settings UI to list capabilities without rewriting core.
"""
from __future__ import annotations

from typing import Any, Optional

# id, name, description, settings toggle key, default enabled, optional live checker
_MANIFESTS: list[dict[str, Any]] = [
    {
        "id": "desktop_runner",
        "name": "Desktop .exe tests",
        "description": "Stdlib Windows .exe smoke + structured steps (not Playwright).",
        "toggle_key": "plugin_desktop_enabled",
        "default_enabled": True,
    },
    {
        "id": "multi_sandbox",
        "name": "Multi-sandbox orchestration",
        "description": (
            "Local multi-sandbox env records, status, and prepare "
            "(max 4; no cloud farms)."
        ),
        "toggle_key": "plugin_multi_sandbox_enabled",
        "default_enabled": False,
    },
    {
        "id": "playwright_runner",
        "name": "Playwright browser tests",
        "description": "Headed Playwright runner with locator self-heal.",
        "toggle_key": None,
        "default_enabled": True,
    },
    {
        "id": "playwright_suite",
        "name": "Playwright suite import",
        "description": "Import and run existing Playwright project suites (FR-TEST-5).",
        "toggle_key": None,
        "default_enabled": True,
    },
    {
        "id": "framework_switch",
        "name": "Test framework switch",
        "description": "Settings stub: Playwright default; Selenium/Cypress not implemented yet (FR-PLUG-3).",
        "toggle_key": None,
        "default_enabled": True,
    },
    {
        "id": "contract_mock",
        "name": "Contract / mock responses",
        "description": (
            "Local mock fixtures for API/messaging cases when the real queue is down "
            "(opt-in per case; KAN-221 / G3)."
        ),
        "toggle_key": None,
        "default_enabled": True,
    },
    {
        "id": "doc_ingest",
        "name": "Document ingestion",
        "description": "Parse specs into settings proposals (confirm before write).",
        "toggle_key": None,
        "default_enabled": True,
    },
    {
        "id": "jira_plugin",
        "name": "Jira",
        "description": "List / create / transition / comment (writes need confirm).",
        "toggle_key": None,
        "default_enabled": True,
    },
]


def _enabled_for(manifest: dict[str, Any], settings: dict[str, Any]) -> bool:
    key = manifest.get("toggle_key")
    if not key:
        return bool(manifest.get("default_enabled", True))
    if key in settings:
        return bool(settings[key])
    return bool(manifest.get("default_enabled", False))


def list_plugins() -> dict[str, Any]:
    """Return registered plugin manifests with current enabled flags."""
    from plugins.framework_switch import framework_status, list_frameworks
    from settings.store import load_settings

    settings = load_settings()
    plugins = []
    for m in _MANIFESTS:
        plugins.append(
            {
                "id": m["id"],
                "name": m["name"],
                "description": m["description"],
                "toggle_key": m.get("toggle_key"),
                "enabled": _enabled_for(m, settings),
                "toggleable": bool(m.get("toggle_key")),
            }
        )
    fw = framework_status()
    return {
        "plugins": plugins,
        "count": len(plugins),
        # FR-PLUG-3: active automation framework (Playwright default; others stub)
        "test_framework": fw.get("active") or "playwright",
        "frameworks": list_frameworks().get("frameworks") or [],
    }


def get_plugin(plugin_id: str) -> Optional[dict[str, Any]]:
    payload = list_plugins()
    for p in payload["plugins"]:
        if p["id"] == plugin_id:
            return p
    return None
