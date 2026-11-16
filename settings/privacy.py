"""GDPR helpers (FR-SEC-2): no telemetry by default, local data inventory, confirm-gated wipe.

Deletes only under the app data directory. Credentials and settings.json are never
removed by this path (out of scope for artifact wipe).
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from settings.store import app_data_dir, load_settings

# Configurable local artifacts under app data (reports / screenshots / audit / sessions / profiles / plans).
DELETABLE_CATEGORIES = (
    "reports",
    "screenshots",
    "heal_audit",
    "jira_write_audit",
    "sessions",
    "browser_profiles",
    "plans",
)

_DEFAULT_WIPE = ("reports", "screenshots", "heal_audit", "jira_write_audit", "sessions")

CONSENT_NOTE = (
    "Extracted document data is never stored without your explicit confirmation "
    "(yes/confirm). Decline leaves the settings file unchanged."
)


def _category_path(category: str) -> Path:
    root = app_data_dir()
    mapping = {
        "reports": root / "reports",
        "screenshots": root / "screenshots",
        "heal_audit": root / "heal_audit.jsonl",
        "jira_write_audit": root / "jira_write_audit.jsonl",
        "sessions": root / "sessions",
        "browser_profiles": root / "browser_profiles",
        "plans": root / "plans",
    }
    if category not in mapping:
        raise ValueError(f"Unknown category: {category!r}")
    return mapping[category]


def _ensure_under_app_data(path: Path) -> Path:
    root = app_data_dir().resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise RuntimeError(f"refusing to touch path outside app data: {resolved}")
    return resolved


def _path_stats(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "bytes": 0, "items": 0}
    if path.is_file():
        size = path.stat().st_size
        return {"exists": True, "path": str(path), "bytes": size, "items": 1}
    total = 0
    items = 0
    for child in path.rglob("*"):
        if child.is_file():
            items += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return {"exists": True, "path": str(path), "bytes": total, "items": items}


def local_data_inventory(
    categories: Optional[Sequence[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    chosen = list(categories) if categories else list(DELETABLE_CATEGORIES)
    out: Dict[str, Dict[str, Any]] = {}
    for name in chosen:
        if name not in DELETABLE_CATEGORIES:
            continue
        out[name] = _path_stats(_category_path(name))
    return out


def telemetry_enabled() -> bool:
    """FR-SEC-2: telemetry is off unless explicitly enabled (default False)."""
    settings = load_settings()
    return bool(settings.get("telemetry_enabled", False))


def privacy_status() -> Dict[str, Any]:
    return {
        "telemetry_enabled": telemetry_enabled(),
        "consent_required_for_extracted_data": True,
        "consent_note": CONSENT_NOTE,
        "app_data_dir": str(app_data_dir()),
        "categories": local_data_inventory(),
        "default_wipe_categories": list(_DEFAULT_WIPE),
        "deletable_categories": list(DELETABLE_CATEGORIES),
    }


def _normalize_categories(categories: Optional[Iterable[str]]) -> List[str]:
    if categories is None:
        return list(_DEFAULT_WIPE)
    out: List[str] = []
    for raw in categories:
        name = str(raw or "").strip().lower()
        if not name:
            continue
        if name not in DELETABLE_CATEGORIES:
            continue
        if name not in out:
            out.append(name)
    return out


def _wipe_target(path: Path) -> Dict[str, Any]:
    """Remove a file or directory tree; recreate empty dirs for known folders."""
    safe = _ensure_under_app_data(path)
    if not safe.exists():
        return {"path": str(safe), "deleted": False, "reason": "missing"}
    if safe.is_file():
        safe.unlink()
        return {"path": str(safe), "deleted": True, "kind": "file"}
    shutil.rmtree(safe)
    # Keep expected folder structure for later writers.
    if safe.name in {"reports", "screenshots", "sessions", "browser_profiles", "plans"}:
        safe.mkdir(parents=True, exist_ok=True)
    return {"path": str(safe), "deleted": True, "kind": "directory"}


def delete_local_data(
    categories: Optional[Sequence[str]] = None,
    *,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Wipe configurable local artifacts. Requires confirm=True (destructive)."""
    chosen = _normalize_categories(categories)
    if not chosen:
        return {
            "status": "error",
            "message": (
                "No valid categories. Choose from: "
                + ", ".join(DELETABLE_CATEGORIES)
            ),
        }
    inventory = local_data_inventory(chosen)
    if not confirm:
        return {
            "status": "confirmation_required",
            "proposed": {"categories": chosen},
            "inventory": inventory,
            "message": (
                "Confirm delete-local-data? This permanently removes the listed "
                "local artifacts under the app data directory. Credentials and "
                "settings.json are not included."
            ),
            "consent_note": CONSENT_NOTE,
        }

    removed: List[Dict[str, Any]] = []
    for name in chosen:
        removed.append({"category": name, **_wipe_target(_category_path(name))})

    return {
        "status": "deleted",
        "categories": chosen,
        "removed": removed,
        "inventory_after": local_data_inventory(chosen),
        "message": "Local artifacts removed for: " + ", ".join(chosen),
    }
