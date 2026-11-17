"""
Dynamic test-framework switching stub (KAN-79 / FR-PLUG-3).

Playwright is the default and only ready runner. Selenium / Cypress can be
selected in settings but runs return a clear not-implemented message — no crash.
"""
from __future__ import annotations

from typing import Any, Optional

SETTING_KEY = "test_framework"
DEFAULT_FRAMEWORK = "playwright"

_FRAMEWORKS: dict[str, dict[str, Any]] = {
    "playwright": {
        "id": "playwright",
        "name": "Playwright",
        "status": "ready",
        "description": "Default browser automation runner (headed Playwright).",
    },
    "selenium": {
        "id": "selenium",
        "name": "Selenium",
        "status": "not_implemented",
        "description": "Stub only — coming later (FR-PLUG-3).",
    },
    "cypress": {
        "id": "cypress",
        "name": "Cypress",
        "status": "not_implemented",
        "description": "Stub only — coming later (FR-PLUG-3).",
    },
}


def normalize_framework(value: str | None) -> str:
    key = (value or "").strip().lower()
    if key in _FRAMEWORKS:
        return key
    return DEFAULT_FRAMEWORK


def get_framework() -> str:
    from settings.store import load_settings

    return normalize_framework(load_settings().get(SETTING_KEY))


def list_frameworks() -> dict[str, Any]:
    active = get_framework()
    items = []
    for fid, meta in _FRAMEWORKS.items():
        items.append(
            {
                **meta,
                "active": fid == active,
                "implemented": meta["status"] == "ready",
            }
        )
    return {
        "frameworks": items,
        "active": active,
        "default": DEFAULT_FRAMEWORK,
        "setting_key": SETTING_KEY,
    }


def framework_status() -> dict[str, Any]:
    active = get_framework()
    meta = _FRAMEWORKS[active]
    payload = list_frameworks()
    return {
        SETTING_KEY: active,
        "active": active,
        "name": meta["name"],
        "status": meta["status"],
        "implemented": meta["status"] == "ready",
        "frameworks": payload["frameworks"],
        "default": DEFAULT_FRAMEWORK,
        "setting_key": SETTING_KEY,
        "message": (
            f"Active test framework: {meta['name']} ({meta['status']})."
            if meta["status"] == "ready"
            else (
                f"Active test framework: {meta['name']} — not implemented yet. "
                "Switch back to Playwright to run tests."
            )
        ),
    }


def set_framework(framework: str) -> dict[str, Any]:
    from settings.store import update_setting

    key = (framework or "").strip().lower()
    if key not in _FRAMEWORKS:
        payload = framework_status()
        payload.update(
            {
                "status": "error",
                "message": (
                    f"Unknown framework {framework!r}. "
                    f"Choose one of: {', '.join(_FRAMEWORKS)}."
                ),
            }
        )
        return payload

    update_setting(SETTING_KEY, key, confirm=True)
    payload = framework_status()
    payload.update({"status": "updated", "message": f"Test framework set to {key}."})
    return payload


def not_implemented_result(framework: str | None = None, action: str = "run") -> dict[str, Any]:
    """Clear failure payload when a stub framework is asked to run."""
    fw = normalize_framework(framework or get_framework())
    meta = _FRAMEWORKS[fw]
    action_norm = (action or "run").strip() or "run"
    return {
        "status": "not_implemented",
        "ok": False,
        "framework": fw,
        "action": action_norm,
        "plugin": "framework_switch",
        "message": (
            f"{meta['name']} is not implemented yet (FR-PLUG-3 stub). "
            "Set test_framework to playwright to run browser tests."
        ),
    }


def reject_if_unsupported(action: str = "run") -> Optional[dict[str, Any]]:
    """Return a not-implemented payload when active framework is not Playwright."""
    active = get_framework()
    if active == DEFAULT_FRAMEWORK:
        return None
    return not_implemented_result(active, action=action)


def attempt_run(framework: str | None = None, action: str = "run") -> dict[str, Any]:
    """
    Stub entry for 'run with selected framework'.
    Playwright → ok stub (real runners stay on playwright_* tools).
    Others → not_implemented (AC for KAN-79 / KAN-233 G9).
    """
    fw = normalize_framework(framework or get_framework())
    if fw != DEFAULT_FRAMEWORK:
        payload = not_implemented_result(fw, action=action)
        payload["implemented"] = False
        return payload
    return {
        "status": "ok",
        "ok": True,
        "framework": fw,
        "action": (action or "run").strip() or "run",
        "plugin": "framework_switch",
        "implemented": True,
        "message": (
            "Playwright is the active framework. "
            "Use run_playwright or run_playwright_suite to execute tests."
        ),
    }


def plan_run_result(framework: str | None = None, action: str = "run") -> dict[str, Any]:
    """
    Plan/suite mapping for a selected framework (KAN-233 / G9).

    Selenium/Cypress → not_implemented, never passed.
    Playwright → ready (pass on the framework-selection case only).
    """
    raw = attempt_run(framework=framework, action=action)
    fw = str(raw.get("framework") or normalize_framework(framework))
    if raw.get("status") == "not_implemented" or not raw.get("ok", False):
        return {
            **raw,
            "result": "error",
            "failure_class": "tool",
            "passed": False,
            "framework": fw,
            "implemented": False,
        }
    return {
        **raw,
        "result": "pass",
        "failure_class": None,
        "passed": True,
        "framework": fw,
        "implemented": True,
    }
