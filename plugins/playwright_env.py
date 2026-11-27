"""Sanitize Playwright browser path for product runs (KAN-495).

Cursor agent shells often set PLAYWRIGHT_BROWSERS_PATH to a sandbox cache that
does not contain Chromium. The product must use the normal user install under
%LOCALAPPDATA%\\ms-playwright (or an explicit valid override).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _looks_like_cursor_sandbox(path: str) -> bool:
    norm = path.replace("\\", "/").lower()
    return "cursor-sandbox-cache" in norm


def _chromium_exe_present(root: Path) -> bool:
    if not root.is_dir():
        return False
    patterns = (
        "chromium-*/chrome-win64/chrome.exe",
        "chromium-*/chrome-win/chrome.exe",
        "chromium-*/chrome-linux/chrome",
        "chromium-*/chrome-mac/Chromium.app",
        "chromium-*/chrome-mac-arm64/Chromium.app",
    )
    for pattern in patterns:
        if any(root.glob(pattern)):
            return True
    return False


def sanitize_playwright_browsers_path() -> dict[str, Any]:
    """Drop invalid / Cursor-sandbox PLAYWRIGHT_BROWSERS_PATH so Playwright uses defaults.

    Safe to call at desktop_app startup and before each runner launch.
    """
    raw = (os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "").strip()
    if not raw:
        return {
            "changed": False,
            "cleared": False,
            "reason": "unset",
            "previous": None,
            "current": None,
        }

    previous = raw
    root = Path(raw)
    reason = ""
    if _looks_like_cursor_sandbox(raw):
        reason = "cursor_sandbox_cache"
    elif not _chromium_exe_present(root):
        reason = "chromium_missing"
    else:
        return {
            "changed": False,
            "cleared": False,
            "reason": "valid_override",
            "previous": previous,
            "current": previous,
        }

    os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
    return {
        "changed": True,
        "cleared": True,
        "reason": reason,
        "previous": previous,
        "current": None,
    }


def is_missing_browser_error(text: str) -> bool:
    err = (text or "").lower()
    return (
        "executable doesn't exist" in err
        or "playwright install" in err
        or "browserType.launch".lower() in err and "doesn't exist" in err
    )
