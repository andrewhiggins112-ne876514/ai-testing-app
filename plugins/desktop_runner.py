"""
Desktop .exe testing plugin (FR-TEST-3).

Stdlib harness: smoke launch plus structured steps (wait for window title,
basic keyboard input). Uses Win32 via ctypes — does not fork Playwright.
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

# Structured step actions beyond smoke (KAN-87 / FR-TEST-3 depth).
SUPPORTED_ACTIONS = frozenset(
    {"launch", "wait_window", "focus_window", "type_text", "wait", "close"}
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
        "supported_actions": sorted(SUPPORTED_ACTIONS),
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


def _base_result() -> dict[str, Any]:
    return {
        "status": "fail",
        "exe_path": None,
        "pid": None,
        "returncode": None,
        "logs": "",
        "error": None,
        "plugin": "desktop_runner",
        "steps": [],
    }


# --- Win32 helpers (ctypes only; no pywinauto / Playwright) -----------------

def _user32():
    import ctypes

    return ctypes.windll.user32


def _list_windows(pid: Optional[int] = None) -> list[tuple[int, str]]:
    """Return (hwnd, title) for visible top-level windows, optionally by PID."""
    import ctypes
    from ctypes import wintypes

    user32 = _user32()
    results: list[tuple[int, str]] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _cb(hwnd, _lparam):  # type: ignore[no-untyped-def]
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value or ""
        if not title.strip():
            return True
        if pid is not None:
            out_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(out_pid))
            if int(out_pid.value) != int(pid):
                return True
        results.append((int(hwnd), title))
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return results


def _find_hwnd(title_contains: str, pid: Optional[int] = None) -> Optional[int]:
    needle = (title_contains or "").strip().lower()
    if not needle:
        return None
    for hwnd, title in _list_windows(pid=pid):
        if needle in title.lower():
            return hwnd
    # Fallback: any window matching title (app may spawn helper processes)
    if pid is not None:
        for hwnd, title in _list_windows(pid=None):
            if needle in title.lower():
                return hwnd
    return None


def _focus_hwnd(hwnd: int) -> bool:
    import ctypes

    user32 = _user32()
    kernel32 = ctypes.windll.kernel32
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    fg = user32.GetForegroundWindow()
    pid_fg = ctypes.c_ulong(0)
    pid_target = ctypes.c_ulong(0)
    tid_fg = user32.GetWindowThreadProcessId(fg, ctypes.byref(pid_fg)) if fg else 0
    tid_target = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_target))
    tid_self = kernel32.GetCurrentThreadId()
    attached = False
    if tid_fg and tid_fg != tid_self:
        attached = bool(user32.AttachThreadInput(tid_self, tid_fg, True))
    try:
        user32.BringWindowToTop(hwnd)
        return bool(user32.SetForegroundWindow(hwnd))
    finally:
        if attached:
            user32.AttachThreadInput(tid_self, tid_fg, False)


def _type_text_unicode(text: str, hwnd: Optional[int] = None) -> None:
    """Send text via PostMessage WM_CHAR, with SendInput Unicode fallback."""
    import ctypes
    from ctypes import wintypes

    user32 = _user32()
    WM_CHAR = 0x0102

    if hwnd:
        # Prefer posting to a child edit/document control when present.
        target = hwnd
        for class_name in ("Edit", "RichEditD2DPT", "RichEdit20W", "RICHEDIT50W"):
            child = user32.FindWindowExW(hwnd, None, class_name, None)
            if child:
                target = int(child)
                break
        ok = 0
        for ch in text:
            if user32.PostMessageW(target, WM_CHAR, ord(ch), 0):
                ok += 1
        if ok == len(text):
            return
        # Fall through to SendInput if PostMessage partially failed.

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    ULONG_PTR = ctypes.c_size_t

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

        _anonymous_ = ("_input",)
        _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

    n = len(text) * 2
    inputs = (INPUT * n)()
    for i, ch in enumerate(text):
        scan = ord(ch) & 0xFFFF
        inputs[i * 2].type = INPUT_KEYBOARD
        inputs[i * 2].ki = KEYBDINPUT(0, scan, KEYEVENTF_UNICODE, 0, 0)
        inputs[i * 2 + 1].type = INPUT_KEYBOARD
        inputs[i * 2 + 1].ki = KEYBDINPUT(
            0, scan, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0
        )

    sent = user32.SendInput(n, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    if sent != n:
        raise OSError(f"SendInput sent {sent}/{n} events (sizeof INPUT={ctypes.sizeof(INPUT)})")


def _kill_proc(proc: Optional[subprocess.Popen]) -> Optional[int]:
    """Terminate process tree (Win11 apps like Notepad may outlive Popen.terminate)."""
    if proc is None:
        return None
    if proc.poll() is not None:
        return proc.returncode
    pid = proc.pid
    try:
        proc.terminate()
        try:
            proc.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                pass
    except OSError:
        pass
    if proc.poll() is None and sys.platform == "win32" and pid:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass
        except (OSError, subprocess.TimeoutExpired):
            pass
    return proc.returncode


def _launch(
    path: Path,
    args: Optional[list[str]] = None,
) -> tuple[subprocess.Popen, str]:
    cmd = [str(path)] + list(args or [])
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
    return proc, f"Launched pid={proc.pid}"


def run_desktop(
    exe_path: str = "",
    timeout_s: float = 1.5,
    args: Optional[list[str]] = None,
    steps: Optional[list[Any]] = None,
) -> dict[str, Any]:
    """Run smoke launch, or a structured step list when ``steps`` is provided."""
    if steps is not None and not isinstance(steps, list):
        result = _base_result()
        result["error"] = "steps must be a list of action objects"
        return result

    if steps:
        return _run_steps(exe_path=exe_path, args=args, steps=steps, timeout_s=timeout_s)
    return _run_smoke(exe_path=exe_path, timeout_s=timeout_s, args=args)


def _run_smoke(
    exe_path: str = "",
    timeout_s: float = 1.5,
    args: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Smoke-launch a Windows desktop app. Does not use Playwright."""
    result = _base_result()

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
    proc: Optional[subprocess.Popen] = None
    stdout_data = ""
    stderr_data = ""

    try:
        proc, _ = _launch(path, args)
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


def _run_steps(
    exe_path: str,
    args: Optional[list[str]],
    steps: list[Any],
    timeout_s: float,
) -> dict[str, Any]:
    """Execute a structured desktop step list; report per-step pass/fail."""
    result = _base_result()
    log_lines: list[str] = []

    if not is_enabled():
        result["status"] = "disabled"
        result["error"] = _DISABLED_MSG
        result["message"] = _DISABLED_MSG
        return result

    if sys.platform != "win32":
        result["error"] = "Desktop .exe testing is Windows-only."
        return result

    if not steps:
        result["error"] = "steps list is empty"
        return result

    # Validate actions before launching anything
    for raw in steps:
        if not isinstance(raw, dict):
            result["error"] = "Invalid step (not an object)"
            result["steps"] = [
                {"index": 0, "action": "?", "status": "fail", "detail": "step must be an object with action"}
            ]
            return result
        action = str(raw.get("action") or "").strip().lower()
        if action not in SUPPORTED_ACTIONS:
            detail = f"Unsupported action. Supported: {sorted(SUPPORTED_ACTIONS)}"
            result["error"] = f"Unsupported desktop step action: {action or '(empty)'}"
            result["steps"] = [
                {"index": 0, "action": action or "?", "status": "fail", "detail": detail}
            ]
            return result

    path: Optional[Path] = None
    path_err: Optional[str] = None
    proc: Optional[subprocess.Popen] = None
    focused_hwnd: Optional[int] = None
    step_results: list[dict[str, Any]] = []
    default_wait = max(0.5, float(timeout_s) if timeout_s else 5.0)

    def record(action: str, status: str, detail: str = "") -> dict[str, Any]:
        entry = {
            "index": len(step_results),
            "action": action,
            "status": status,
            "detail": detail,
        }
        step_results.append(entry)
        log_lines.append(f"[{entry['index']}] {action}: {status}" + (f" — {detail}" if detail else ""))
        return entry

    def ensure_launched(step_args: Optional[list[str]] = None) -> Optional[str]:
        nonlocal proc, path, path_err
        if proc is not None and proc.poll() is None:
            return None
        if path is None:
            path, path_err = _resolve_path(exe_path)
        if path_err or path is None:
            return path_err or "No exe path for launch"
        try:
            proc, detail = _launch(path, step_args if step_args is not None else args)
            result["exe_path"] = str(path)
            result["pid"] = proc.pid
            return None
        except OSError as exc:
            return f"Failed to launch: {exc}"

    # If no explicit launch step, auto-launch once before other actions
    actions_preview = [
        str(s.get("action") or "").strip().lower()
        for s in steps
        if isinstance(s, dict)
    ]
    auto_launch = "launch" not in actions_preview
    if auto_launch:
        err = ensure_launched()
        if err:
            result["error"] = err
            result["steps"] = step_results
            result["logs"] = _truncate("\n".join(log_lines))
            return result
        record("launch", "pass", f"auto pid={result.get('pid')}")

    try:
        for raw in steps:
            if not isinstance(raw, dict):
                record("?", "fail", "step must be an object with action")
                result["error"] = "Invalid step (not an object)"
                result["status"] = "fail"
                break

            action = str(raw.get("action") or "").strip().lower()
            if action not in SUPPORTED_ACTIONS:
                record(action or "?", "fail", f"Unsupported action. Supported: {sorted(SUPPORTED_ACTIONS)}")
                result["error"] = f"Unsupported desktop step action: {action or '(empty)'}"
                result["status"] = "fail"
                break

            if action == "launch":
                if proc is not None and proc.poll() is None:
                    record("launch", "pass", f"already running pid={proc.pid}")
                    continue
                step_args = raw.get("args")
                if isinstance(step_args, list):
                    launch_args = [str(a) for a in step_args]
                else:
                    launch_args = list(args or [])
                # Optional per-step exe_path
                step_exe = str(raw.get("exe_path") or "").strip()
                if step_exe:
                    path, path_err = _resolve_path(step_exe)
                err = ensure_launched(launch_args)
                if err:
                    record("launch", "fail", err)
                    result["error"] = err
                    result["status"] = "fail"
                    break
                record("launch", "pass", f"pid={result.get('pid')}")
                continue

            if action == "wait":
                seconds = float(raw.get("seconds") or raw.get("timeout_s") or 0.5)
                seconds = max(0.0, min(seconds, 60.0))
                time.sleep(seconds)
                record("wait", "pass", f"{seconds}s")
                continue

            if action == "wait_window":
                title = str(raw.get("title") or raw.get("value") or "").strip()
                if not title:
                    record("wait_window", "fail", "title is required")
                    result["error"] = "wait_window requires title"
                    result["status"] = "fail"
                    break
                win_timeout = float(raw.get("timeout_s") or default_wait)
                win_timeout = max(0.2, min(win_timeout, 60.0))
                deadline = time.time() + win_timeout
                hwnd = None
                pid = result.get("pid")
                while time.time() < deadline:
                    hwnd = _find_hwnd(title, pid=int(pid) if pid else None)
                    if hwnd:
                        break
                    time.sleep(0.1)
                if not hwnd:
                    record("wait_window", "fail", f"No window matching {title!r} within {win_timeout}s")
                    result["error"] = f"Window not found: {title}"
                    result["status"] = "fail"
                    break
                focused_hwnd = hwnd
                record("wait_window", "pass", f"hwnd={hwnd} title~{title!r}")
                continue

            if action == "focus_window":
                title = str(raw.get("title") or raw.get("value") or "").strip()
                hwnd = focused_hwnd
                if title:
                    pid = result.get("pid")
                    hwnd = _find_hwnd(title, pid=int(pid) if pid else None)
                if not hwnd:
                    record("focus_window", "fail", "No window to focus (set title or wait_window first)")
                    result["error"] = "focus_window: window not found"
                    result["status"] = "fail"
                    break
                _focus_hwnd(hwnd)
                focused_hwnd = hwnd
                time.sleep(0.15)
                record("focus_window", "pass", f"hwnd={hwnd}")
                continue

            if action == "type_text":
                text = raw.get("text")
                if text is None:
                    text = raw.get("value")
                if text is None:
                    record("type_text", "fail", "text is required")
                    result["error"] = "type_text requires text"
                    result["status"] = "fail"
                    break
                text = str(text)
                title = str(raw.get("title") or "").strip()
                hwnd = focused_hwnd
                if title:
                    pid = result.get("pid")
                    hwnd = _find_hwnd(title, pid=int(pid) if pid else None)
                if hwnd:
                    _focus_hwnd(hwnd)
                    focused_hwnd = hwnd
                    time.sleep(0.15)
                try:
                    _type_text_unicode(text, hwnd=hwnd)
                except OSError as exc:
                    record("type_text", "fail", str(exc))
                    result["error"] = f"type_text failed: {exc}"
                    result["status"] = "fail"
                    break
                record("type_text", "pass", f"{len(text)} chars")
                continue

            if action == "close":
                code = _kill_proc(proc)
                proc = None
                result["returncode"] = code
                record("close", "pass", f"returncode={code}")
                continue

        else:
            # Completed all steps without break
            if all(s.get("status") == "pass" for s in step_results):
                result["status"] = "pass"
            else:
                result["status"] = "fail"
                if not result.get("error"):
                    result["error"] = "One or more steps failed"

    finally:
        if proc is not None and proc.poll() is None:
            result["returncode"] = _kill_proc(proc)
            proc = None

    result["steps"] = step_results
    result["logs"] = _truncate("\n".join(log_lines))
    if result["status"] == "fail" and not result.get("error"):
        failed = next((s for s in step_results if s.get("status") == "fail"), None)
        if failed:
            result["error"] = failed.get("detail") or f"Step {failed.get('action')} failed"
    return result


def demo_notepad_steps() -> list[dict[str, Any]]:
    """Sample step list for Notepad (UI / agent convenience)."""
    return [
        {"action": "launch"},
        {"action": "wait_window", "title": "Notepad", "timeout_s": 8},
        {"action": "type_text", "text": "KAN-87 desktop steps"},
        {"action": "close"},
    ]
