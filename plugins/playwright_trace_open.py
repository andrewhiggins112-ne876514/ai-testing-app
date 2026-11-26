"""Open / reveal a local Playwright trace.zip (KAN-375 OPERATE-1).

Paths must resolve under ``%LOCALAPPDATA%/ai_testing_app/{traces,evidence}``.
Never embeds Trace Viewer; launches ``playwright show-trace`` or Explorer.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ALLOWED_ACTIONS = frozenset({"show_trace", "reveal", "validate"})


def _app_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    return (Path(base) / "ai_testing_app").resolve()


def allowed_trace_roots() -> list[Path]:
    root = _app_root()
    return [(root / "traces").resolve(), (root / "evidence").resolve()]


def resolve_allowed_trace(path: str) -> tuple[Optional[Path], Optional[str]]:
    """Return (resolved zip path, error message)."""
    raw = (path or "").strip()
    if not raw:
        return None, "Trace path is required."
    try:
        candidate = Path(raw).expanduser().resolve()
    except OSError:
        return None, "Trace path could not be resolved."
    if candidate.suffix.lower() != ".zip":
        return None, "Only .zip Playwright traces can be opened."
    if not candidate.is_file():
        return None, "Trace file not found."
    allowed = False
    for root in allowed_trace_roots():
        try:
            candidate.relative_to(root)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        return None, "Trace path is outside the local traces/evidence folders."
    return candidate, None


def open_playwright_trace(
    path: str,
    action: str = "show_trace",
    *,
    launch: bool = True,
) -> Dict[str, Any]:
    """Validate and optionally launch show-trace or Reveal in Explorer."""
    act = (action or "show_trace").strip().lower()
    if act not in ALLOWED_ACTIONS:
        return {
            "ok": False,
            "error": f"Unknown action '{action}'. Use show_trace, reveal, or validate.",
            "action": act,
        }
    resolved, err = resolve_allowed_trace(path)
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
        if act == "show_trace":
            subprocess.Popen(
                [sys.executable, "-m", "playwright", "show-trace", str(resolved)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
            payload["launched"] = True
            payload["message"] = "Opened Playwright Trace Viewer."
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
                parent = str(resolved.parent)
                subprocess.Popen(
                    ["xdg-open", parent],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )
            payload["launched"] = True
            payload["message"] = "Revealed trace in file manager."
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Could not launch: {exc}",
            "action": act,
            "path": str(resolved),
        }
    return payload
