"""Desktop-typed cases on the same in-app suite (KAN-217 / G1 / FR-TEST-3).

Desktop .exe cases sit beside browser cases. Execution uses
``plugins.desktop_runner`` — not Playwright. Results use the same run model.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from plans.store import add_case, get_plan


def parse_desktop_ref(ref: str) -> dict[str, Any]:
    """Parse source.ref: empty → settings exe; path → exe; JSON → steps and/or exe."""
    text = (ref or "").strip()
    if not text:
        return {"exe_path": "", "steps": None}
    if text.startswith("[") or text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"exe_path": text[:500], "steps": None}
        if isinstance(parsed, list):
            return {"exe_path": "", "steps": parsed}
        if isinstance(parsed, dict):
            steps = parsed.get("steps")
            if steps is not None and not isinstance(steps, list):
                steps = None
            return {
                "exe_path": str(parsed.get("exe_path") or parsed.get("path") or "").strip()[
                    :500
                ],
                "steps": steps,
            }
    return {"exe_path": text[:500], "steps": None}


def encode_desktop_ref(
    *,
    exe_path: str = "",
    steps: Optional[list[Any]] = None,
) -> str:
    """Encode exe and/or steps into source.ref."""
    path = (exe_path or "").strip()
    if steps:
        payload: dict[str, Any] = {"steps": steps}
        if path:
            payload["exe_path"] = path
        return json.dumps(payload, separators=(",", ":"))[:300]
    return path[:300]


def add_desktop_case(
    plan_id: str,
    name: str = "",
    *,
    exe_path: str = "",
    note: str = "",
    tags: list[str] | None = None,
    steps: Optional[list[Any]] = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add a desktop-typed case to an existing plan suite."""
    from settings.store import load_settings

    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    settings = load_settings()
    path = (exe_path or "").strip() or str(settings.get("target_app_path") or "").strip()
    label = (name or "").strip()
    if not label:
        basename = Path(path).name if path else "connected exe"
        label = f"Desktop smoke — {basename}"

    case_tags = list(tags or [])
    if "desktop" not in [t.lower() for t in case_tags]:
        case_tags = ["desktop"] + case_tags

    connected = str(settings.get("target_app_path") or "").strip()
    # Empty ref → use connected settings path at run time.
    override = path if path and path != connected else ""
    ref = encode_desktop_ref(exe_path=override, steps=steps)

    return add_case(
        plan_id,
        label,
        note=note
        or "Desktop case — runs via desktop_runner against the connected exe (not Playwright).",
        tags=case_tags,
        source_kind="desktop",
        source_ref=ref,
        level=level,
    )


def write_desktop_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    desktop: dict[str, Any],
) -> list[str]:
    """Persist desktop runner logs/steps as evidence paths (same run model)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": "desktop_runner",
        "status": desktop.get("status"),
        "exe_path": desktop.get("exe_path"),
        "pid": desktop.get("pid"),
        "error": desktop.get("error"),
        "steps": desktop.get("steps") or [],
        "logs": (desktop.get("logs") or "")[:4000],
    }
    path = folder / "desktop_result.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
