"""Serve / open level-scoped run screenshots (KAN-496).

Paths must resolve under ``%LOCALAPPDATA%/ai_testing_app/{screenshots,evidence,traces}``.
Never invent a placeholder image when a file is missing.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ALLOWED_ACTIONS = frozenset({"open", "reveal", "validate"})


def _app_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    return (Path(base) / "ai_testing_app").resolve()


def allowed_shot_roots() -> list[Path]:
    root = _app_root()
    return [
        (root / "screenshots").resolve(),
        (root / "evidence").resolve(),
        (root / "traces").resolve(),
    ]


def resolve_allowed_shot(path: str) -> tuple[Optional[Path], Optional[str]]:
    """Return (resolved PNG path, error message)."""
    raw = (path or "").strip()
    if not raw:
        return None, "Screenshot path is required."
    try:
        candidate = Path(raw).expanduser().resolve()
    except OSError:
        return None, "Screenshot path could not be resolved."
    if candidate.suffix.lower() != ".png":
        return None, "Only PNG screenshots can be opened."
    if not candidate.is_file():
        return None, "Screenshot file not found."
    allowed = False
    for root in allowed_shot_roots():
        try:
            candidate.relative_to(root)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        return None, "Screenshot path is outside the local screenshots/evidence folders."
    return candidate, None


def open_evidence_shot(
    path: str,
    action: str = "open",
    *,
    launch: bool = True,
) -> Dict[str, Any]:
    """Validate and optionally open or reveal a PNG evidence shot."""
    act = (action or "open").strip().lower()
    if act not in ALLOWED_ACTIONS:
        return {
            "ok": False,
            "error": f"Unknown action '{action}'. Use open, reveal, or validate.",
            "action": act,
        }
    resolved, err = resolve_allowed_shot(path)
    if err or resolved is None:
        return {"ok": False, "error": err or "Invalid path.", "action": act}

    payload: Dict[str, Any] = {
        "ok": True,
        "action": act,
        "path": str(resolved),
        "launched": False,
    }
    if act == "validate" or not launch:
        return payload

    try:
        if act == "open":
            if sys.platform == "win32":
                os.startfile(str(resolved))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", str(resolved)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    ["xdg-open", str(resolved)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            payload["launched"] = True
            payload["message"] = "Opened screenshot."
        elif act == "reveal":
            if sys.platform == "win32":
                subprocess.Popen(
                    ["explorer", "/select,", str(resolved)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", "-R", str(resolved)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    ["xdg-open", str(resolved.parent)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            payload["launched"] = True
            payload["message"] = "Revealed screenshot in file manager."
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Could not launch: {exc}",
            "action": act,
            "path": str(resolved),
        }
    return payload
