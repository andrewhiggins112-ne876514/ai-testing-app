"""Local seed data / fixtures (KAN-223 / G4 / FR-PLUG-1).

Cases that assume a user or row name a level-scoped fixture file (or
inline steps). Fixtures are never injected globally — only when a case
names one. Missing fixture fails as environment.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

PLUGIN_NAME = "seed_fixture"
_DEFAULT_NAME = "seed_user.json"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


def fixtures_dir(level: str | None = None) -> Path:
    """Level-scoped local seed fixtures (never cloud)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "OFFICIAL").strip().upper() or "OFFICIAL"
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    path = Path(base) / "ai_testing_app" / "fixtures" / lvl
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_fixture_name() -> str:
    return _DEFAULT_NAME


def ensure_default_fixture(level: str | None = None) -> Path:
    """Create the default seed-user fixture if missing."""
    folder = fixtures_dir(level=level)
    path = folder / _DEFAULT_NAME
    if not path.is_file():
        payload = {
            "name": "seed_user",
            "description": "Named seed user/row for cases that assume fixture data.",
            "data": {
                "user": {
                    "id": "seed-1",
                    "email": "seed.user@example.local",
                    "role": "tester",
                },
                "row": {"id": 1, "status": "ready"},
            },
            "steps": [
                {"action": "ensure_user", "user_id": "seed-1"},
                {"action": "ensure_row", "row_id": 1},
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def resolve_fixture_path(name: str, *, level: str | None = None) -> Path | None:
    """Resolve a safe fixture name under the fixtures dir (no path escape)."""
    raw = (name or "").strip().replace("\\", "/")
    if not raw:
        return None
    base = Path(raw).name
    if base != raw and "/" in raw:
        if Path(raw).parent.as_posix() not in (".", ""):
            return None
        base = Path(raw).name
    if not _SAFE_NAME.match(base):
        return None
    if not base.lower().endswith(".json"):
        base = f"{base}.json"
        if not _SAFE_NAME.match(base):
            return None
    folder = fixtures_dir(level=level)
    path = (folder / base).resolve()
    try:
        path.relative_to(folder.resolve())
    except ValueError:
        return None
    return path


def apply_seed_fixture(
    *,
    fixture: str = "",
    steps: Optional[list[Any]] = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Load a named local seed fixture (or validate inline steps).

    Does not silently inject fixtures into other cases — caller must name one.
    """
    name = (fixture or "").strip()
    inline = list(steps) if isinstance(steps, list) else None
    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "fixture": name or None,
        "steps": [],
        "data": None,
        "status": "fail",
        "error": None,
        "message": None,
        "classification": None,
    }

    # Named file path takes precedence; inline steps alone need a name too.
    if not name and not inline:
        base.update(
            {
                "status": "fail",
                "error": "No seed fixture named.",
                "message": "No seed fixture named.",
                "classification": "environment",
            }
        )
        return base

    if name:
        path = resolve_fixture_path(name, level=level)
        if path is None:
            base.update(
                {
                    "status": "fail",
                    "error": f"Invalid seed fixture name: {name[:80]}",
                    "message": f"Invalid seed fixture name: {name[:80]}",
                    "classification": "environment",
                }
            )
            return base
        if not path.is_file():
            base.update(
                {
                    "status": "fail",
                    "error": f"Seed fixture not found: {path.name}",
                    "message": f"Seed fixture not found: {path.name}",
                    "fixture": path.name,
                    "classification": "environment",
                }
            )
            return base
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            base.update(
                {
                    "status": "fail",
                    "error": f"Seed fixture unreadable: {exc}"[:300],
                    "message": f"Seed fixture unreadable: {exc}"[:300],
                    "fixture": path.name,
                    "classification": "environment",
                }
            )
            return base
        if not isinstance(raw, dict):
            base.update(
                {
                    "status": "fail",
                    "error": "Seed fixture must be a JSON object.",
                    "message": "Seed fixture must be a JSON object.",
                    "fixture": path.name,
                    "classification": "environment",
                }
            )
            return base
        file_steps = raw.get("steps")
        if not isinstance(file_steps, list):
            file_steps = []
        # Case-level inline steps override file steps when provided.
        used_steps = inline if inline is not None else file_steps
        base.update(
            {
                "status": "pass",
                "fixture": path.name,
                "steps": used_steps,
                "data": raw.get("data"),
                "message": (
                    f"Seed fixture {path.name} ready "
                    f"({len(used_steps)} step(s))."
                ),
                "error": None,
                "classification": None,
            }
        )
        return base

    # Inline steps only — still require an explicit name on the case (no silent inject).
    base.update(
        {
            "status": "fail",
            "error": "Seed fixture name required (no silent injection).",
            "message": "Seed fixture name required (no silent injection).",
            "steps": inline or [],
            "classification": "environment",
        }
    )
    return base
