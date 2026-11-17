"""Sandbox chosen as the run environment (KAN-231 / G8).

When the multi-sandbox plugin is enabled, a run may name one existing sandbox.
The run record stores that name. With no sandbox selected, the normal browser
profile is used. Sandboxes screen still manages records. Parallel stays on D1.
"""
from __future__ import annotations

from typing import Any


def list_run_sandboxes() -> dict[str, Any]:
    """Sandboxes selectable for a plan/suite run (empty when plugin disabled)."""
    from plugins.multi_sandbox import is_enabled, list_configured_sandboxes, MAX_SANDBOXES
    from plans.parallel import parallel_cap_info

    cap = parallel_cap_info()
    if not is_enabled():
        return {
            "status": "ok",
            "plugin_enabled": False,
            "sandboxes": [],
            "default_profile": True,
            "parallel_max": cap.get("parallel_max"),
            "parallel_default": cap.get("parallel_default"),
            "message": (
                "Multi-sandbox plugin is disabled. Runs use the normal browser "
                "profile. Enable the plugin on the Sandboxes screen to choose one."
            ),
        }
    boxes = list_configured_sandboxes(ensure_default=True)
    return {
        "status": "ok",
        "plugin_enabled": True,
        "sandboxes": [
            {
                "id": s.get("id"),
                "label": s.get("label") or s.get("id"),
                "url": s.get("url") or "",
                "profile": s.get("profile"),
                "status": s.get("status"),
            }
            for s in boxes
        ],
        "default_profile": True,
        "max_sandboxes": MAX_SANDBOXES,
        "parallel_max": cap.get("parallel_max"),
        "parallel_default": cap.get("parallel_default"),
        "message": (
            "Choose a sandbox for this run, or leave blank for the normal "
            "browser profile. Parallel stays capped by D1."
        ),
    }


def resolve_run_sandbox(sandbox_id: str | None = None) -> dict[str, Any]:
    """Resolve an optional sandbox id for a case/suite run.

    Empty id → default normal browser profile (sandbox=None).
    Named id requires the plugin enabled and an existing record.
    """
    from plugins.multi_sandbox import (
        is_enabled,
        list_configured_sandboxes,
        normalize_sandbox_id,
        prepare_sandboxes,
    )

    raw = (sandbox_id or "").strip()
    if not raw:
        return {
            "status": "ok",
            "sandbox": None,
            "sandbox_name": None,
            "url": None,
            "profile_dir": None,
            "default_profile": True,
            "message": "Using normal browser profile (no sandbox selected).",
        }

    sid = normalize_sandbox_id(raw)
    if not sid:
        return {
            "status": "error",
            "error": "sandbox_invalid",
            "message": (
                "Sandbox id must start with a letter and use A-Z, 0-9, _ or - "
                "(max 32)."
            ),
            "default_profile": True,
        }

    if not is_enabled():
        return {
            "status": "error",
            "error": "sandbox_plugin_disabled",
            "message": (
                "Multi-sandbox plugin is disabled. Enable it on the Sandboxes "
                "screen before naming a sandbox on a run."
            ),
            "default_profile": True,
        }

    boxes = list_configured_sandboxes(ensure_default=True)
    match = next((s for s in boxes if s.get("id") == sid), None)
    if match is None:
        return {
            "status": "error",
            "error": "sandbox_not_found",
            "message": (
                f"Sandbox '{sid}' was not found. Manage records on the "
                "Sandboxes screen."
            ),
            "sandboxes": boxes,
            "default_profile": True,
        }

    # Ensure local profile dir exists (no browser launch).
    prep = prepare_sandboxes(sandbox_id=sid)
    if prep.get("status") == "disabled":
        return {
            "status": "error",
            "error": "sandbox_plugin_disabled",
            "message": prep.get("message") or "Sandbox plugin disabled.",
            "default_profile": True,
        }

    profile_path = str(match.get("profile") or "").strip()
    if prep.get("status") == "ok":
        refreshed = next(
            (s for s in (prep.get("sandboxes") or []) if s.get("id") == sid),
            match,
        )
        profile_path = str(refreshed.get("profile") or profile_path).strip()

    if not profile_path:
        return {
            "status": "error",
            "error": "sandbox_profile_missing",
            "message": f"Sandbox '{sid}' has no local profile path.",
            "default_profile": True,
        }

    label = str(match.get("label") or sid).strip() or sid
    url = str(match.get("url") or "").strip() or None
    return {
        "status": "ok",
        "sandbox": {
            "id": sid,
            "label": label,
            "url": url or "",
            "profile": profile_path,
            "status": match.get("status"),
        },
        "sandbox_name": sid,
        "url": url,
        "profile_dir": profile_path,
        "default_profile": False,
        "message": f"Run environment: sandbox '{sid}' ({label}).",
    }
