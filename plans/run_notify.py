"""Local notification when a run finishes (KAN-189 / D6 / FR-UI-1).

Long suites should not require staring at the window. Notices are local only —
no email, no cloud push — and never include secrets or page text. Testers can
turn notices off.
"""
from __future__ import annotations

import platform
import subprocess
import threading
from typing import Any

DEFAULT_ENABLED = True
SETTING_KEY = "run_finish_notify_enabled"

# In-memory last notice (tests + optional UI poll). Never holds secrets/page text.
_LAST_NOTICE: dict[str, Any] | None = None
_DELIVERED: list[dict[str, Any]] = []


def clear_notify_state() -> None:
    """Test helper — drop last notice and delivery log."""
    global _LAST_NOTICE
    _LAST_NOTICE = None
    _DELIVERED.clear()


def notify_info() -> dict[str, Any]:
    """Public defaults for UI / API."""
    enabled = is_notify_enabled()
    return {
        "status": "ok",
        "run_finish_notify_enabled": enabled,
        "run_finish_notify_default": DEFAULT_ENABLED,
        "channel": "local",
        "email": False,
        "cloud_push": False,
        "message": (
            "When a run finishes, a local notice shows pass and fail counts. "
            "No email or cloud push. Notices never include secrets or page text."
        ),
        "last_notice": dict(_LAST_NOTICE) if _LAST_NOTICE else None,
    }


def is_notify_enabled() -> bool:
    from settings.store import load_settings

    data = load_settings()
    if SETTING_KEY not in data:
        return DEFAULT_ENABLED
    return bool(data.get(SETTING_KEY))


def set_notify_enabled(enabled: bool) -> dict[str, Any]:
    from settings.store import update_setting

    update_setting(SETTING_KEY, bool(enabled), confirm=True)
    info = notify_info()
    info["message"] = (
        "Run-finish notices on." if enabled else "Run-finish notices off."
    )
    return info


def counts_from_case_results(case_results: list[Any] | None) -> tuple[int, int]:
    """Count pass vs fail/error from suite case_results rows."""
    passed = 0
    failed = 0
    for item in case_results or []:
        if not isinstance(item, dict):
            continue
        result = str(item.get("result") or "").strip().lower()
        if result == "pass":
            passed += 1
        elif result in {"fail", "error"}:
            failed += 1
    return passed, failed


def counts_from_result(result: str | None) -> tuple[int, int]:
    """Map a single case result to pass/fail counts."""
    key = str(result or "").strip().lower()
    if key == "pass":
        return 1, 0
    if key in {"fail", "error"}:
        return 0, 1
    return 0, 0


def build_notice(
    pass_count: int,
    fail_count: int,
    *,
    kind: str = "run",
) -> dict[str, Any]:
    """Safe local notice payload — counts only; no secrets or page text."""
    try:
        passed = max(0, int(pass_count))
    except (TypeError, ValueError):
        passed = 0
    try:
        failed = max(0, int(fail_count))
    except (TypeError, ValueError):
        failed = 0
    kind_key = (kind or "run").strip().lower()
    if kind_key not in {"case", "suite", "tag", "rerun", "run"}:
        kind_key = "run"
    title = "Run finished"
    body = f"{passed} passed, {failed} failed"
    return {
        "title": title,
        "body": body,
        "pass": passed,
        "fail": failed,
        "kind": kind_key,
        "channel": "local",
        "email": False,
        "cloud_push": False,
        "has_secrets": False,
        "has_page_text": False,
    }


def _windows_toast(title: str, body: str) -> bool:
    """Best-effort Windows toast via PowerShell WinRT. Never raises to callers."""
    if platform.system() != "Windows":
        return False
    # Escape for single-quoted PowerShell strings.
    t = (title or "Run finished").replace("'", "''")[:80]
    b = (body or "").replace("'", "''")[:120]
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, "
        "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
        "ContentType = WindowsRuntime] | Out-Null; "
        "$template = '<toast><visual><binding template=\"ToastGeneric\">"
        f"<text>{t}</text><text>{b}</text>"
        "</binding></visual></toast>'; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$xml.LoadXml($template); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::"
        "CreateToastNotifier('AI Testing Agent').Show($toast)"
    )
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            timeout=8,
            check=False,
        )
        return completed.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _deliver(notice: dict[str, Any]) -> dict[str, Any]:
    """Deliver locally (toast when possible). Records delivery for tests."""
    delivered = {
        **notice,
        "delivered": False,
        "delivery": "none",
    }
    if platform.system() == "Windows":
        ok = _windows_toast(str(notice.get("title") or ""), str(notice.get("body") or ""))
        delivered["delivered"] = bool(ok)
        delivered["delivery"] = "windows_toast" if ok else "windows_toast_failed"
    else:
        delivered["delivery"] = "unsupported_platform"
    _DELIVERED.append(
        {
            "title": delivered.get("title"),
            "body": delivered.get("body"),
            "pass": delivered.get("pass"),
            "fail": delivered.get("fail"),
            "delivery": delivered.get("delivery"),
        }
    )
    return delivered


def attach_standalone_case_notice(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Attach a local notice for a single-case run (skip when part of a suite)."""
    if not isinstance(payload, dict):
        return payload
    if payload.get("suite_run_id"):
        return payload
    run = payload.get("run")
    if not isinstance(run, dict):
        return payload
    result = run.get("result")
    if result is None:
        return payload
    passed, failed = counts_from_result(str(result))
    notice = notify_run_finished(passed, failed, kind="case")
    if notice:
        out = dict(payload)
        out["local_notice"] = notice
        out["pass"] = passed
        out["fail"] = failed
        return out
    return payload


def attach_suite_notice(
    payload: dict[str, Any],
    case_results: list[Any] | None,
    *,
    kind: str = "suite",
) -> dict[str, Any]:
    """Attach pass/fail local notice to a finished suite/tag/rerun payload."""
    if not isinstance(payload, dict):
        return payload
    passed, failed = counts_from_case_results(case_results)
    notice = notify_run_finished(passed, failed, kind=kind)
    out = dict(payload)
    out["pass"] = passed
    out["fail"] = failed
    if notice:
        out["local_notice"] = notice
    return out


def notify_run_finished(
    pass_count: int,
    fail_count: int,
    *,
    kind: str = "run",
    deliver: bool = True,
) -> dict[str, Any] | None:
    """Build (and optionally deliver) a local run-finished notice.

    Returns None when notices are turned off. Never sends email or cloud push.
    """
    global _LAST_NOTICE
    if not is_notify_enabled():
        return None
    notice = build_notice(pass_count, fail_count, kind=kind)
    _LAST_NOTICE = dict(notice)
    if deliver:
        try:
            # Background so a slow toast cannot stall the run response.
            threading.Thread(
                target=_deliver,
                args=(notice,),
                name="run-finish-notify",
                daemon=True,
            ).start()
        except Exception:  # noqa: BLE001 — never break a run for a toast
            pass
    return notice
