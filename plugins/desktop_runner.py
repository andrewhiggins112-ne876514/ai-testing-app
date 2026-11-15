"""
Desktop .exe testing plugin (FR-TEST-3).

Stdlib smoke harness: launch a Windows app path, check it starts, return logs.
Richer UI automation (e.g. pywinauto) is a later extension — do not fork Playwright.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

_LOG_CAP = 4000
_DISABLED_MSG = (
    "Desktop testing plugin is disabled. "
    "Enable plugin_desktop_enabled in settings to run .exe smoke tests."
)


def is_enabled() -> bool:
    from settings.store import load_settings

    return bool(load_settings().get("plugin_desktop_enabled", True))


def plugin_status() -> dict[str, Any]:
    from settings.store import load_settings

    settings = load_settings()
    return {
        "plugin_desktop_enabled": bool(settings.get("plugin_desktop_enabled", True)),
        "target_app_path": (settings.get("target_app_path") or "").strip(),
    }


def set_plugin_enabled(enabled: bool) -> dict[str, Any]:
    from settings.store import update_setting

    update_setting("plugin_desktop_enabled", bool(enabled), confirm=True)
    return plugin_status()


def _truncate(text: str) -> str:
    text = text or ""
    if len(text) <= _LOG_CAP:
        return text
    return text[:_LOG_CAP] + "\n…(truncated)"


def _resolve_path(exe_path: str = "") -> tuple[Optional[Path], Optional[str]]:
    from settings.store import load_settings

    raw = (exe_path or "").strip()
    if not raw:
        raw = (load_settings().get("target_app_path") or "").strip()
    if not raw:
        return None, "No exe path. Pass exe_path or set target_app_path in settings."
    path = Path(raw).expanduser()
    if not path.is_file():
        return None, f"Path not found or not a file: {path}"
    return path.resolve(), None


def run_desktop(
    exe_path: str = "",
    timeout_s: float = 1.5,
    args: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Smoke-launch a Windows desktop app. Does not use Playwright."""
    result: dict[str, Any] = {
        "status": "fail",
        "exe_path": None,
        "pid": None,
        "returncode": None,
        "logs": "",
        "error": None,
        "plugin": "desktop_runner",
    }

    if not is_enabled():
        result["status"] = "disabled"
        result["error"] = _DISABLED_MSG
        result["message"] = _DISABLED_MSG
        return result

    if sys.platform != "win32":
        result["error"] = "Desktop .exe testing is Windows-only."
        return result

    path, err = _resolve_path(exe_path)
    if err:
        result["error"] = err
        return result

    assert path is not None
    result["exe_path"] = str(path)
    cmd = [str(path)] + list(args or [])
    proc: Optional[subprocess.Popen] = None
    stdout_data = ""
    stderr_data = ""

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(path.parent),
        )
        result["pid"] = proc.pid
        deadline = time.time() + max(0.2, float(timeout_s))
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.05)

        still_running = proc.poll() is None
        if still_running:
            try:
                proc.terminate()
                out, err_out = proc.communicate(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err_out = proc.communicate(timeout=2.0)
            stdout_data = out or ""
            stderr_data = err_out or ""
            result["returncode"] = proc.returncode
            result["status"] = "pass"
            result["logs"] = _truncate(
                f"Process started (pid={proc.pid}) and stayed alive for {timeout_s}s smoke window.\n"
                f"stdout:\n{stdout_data}\nstderr:\n{stderr_data}"
            )
            return result

        out, err_out = proc.communicate(timeout=1.0)
        stdout_data = out or ""
        stderr_data = err_out or ""
        result["returncode"] = proc.returncode
        logs = _truncate(f"stdout:\n{stdout_data}\nstderr:\n{stderr_data}")
        result["logs"] = logs
        if proc.returncode == 0:
            result["status"] = "pass"
            return result
        result["error"] = f"Process exited with code {proc.returncode} during smoke window."
        return result
    except OSError as exc:
        result["error"] = f"Failed to launch: {exc}"
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
        return result
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
