"""Credential status without revealing secrets (KAN-185 / D4 / FR-SEC-5 + FR-JIRA-7).

Shows set/missing for Jira email, Jira API token, and target secret.
Test-connection uses stored secrets and returns success or a human-readable auth error.
Clear-secret requires confirm; the local audit line never includes the old value.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Secrets that may be cleared via the clear-secret flow (level-scoped).
CLEARABLE_SECRETS = (
    "jira_email",
    "jira_api_token",
    "target_secret",
)

_FIELD_LABELS = {
    "jira_email": "Jira email",
    "jira_api_token": "Jira API token",
    "target_secret": "Target secret",
}


def credentials_audit_path() -> Path:
    """LOCALAPPDATA credentials_audit.jsonl — clear-secret events only."""
    from settings.store import app_data_dir

    return app_data_dir() / "credentials_audit.jsonl"


def append_credentials_audit(entry: dict[str, Any]) -> None:
    path = credentials_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _presence(value: Any) -> str:
    return "set" if bool(str(value or "").strip()) else "missing"


def credential_field_status() -> dict[str, Any]:
    """Non-secret set/missing flags for Connection / App Settings."""
    from settings.store import get_security_level, load_settings

    data = load_settings()
    level = get_security_level()
    fields = []
    for key in CLEARABLE_SECRETS:
        state = _presence(data.get(key))
        fields.append(
            {
                "key": key,
                "label": _FIELD_LABELS.get(key, key),
                "state": state,
                "set": state == "set",
            }
        )
    email_state = _presence(data.get("jira_email"))
    token_state = _presence(data.get("jira_api_token"))
    target_state = _presence(data.get("target_secret"))
    lines = [
        f"Jira email: {email_state}",
        f"Jira API token: {token_state}",
        f"Target secret: {target_state}",
    ]
    return {
        "status": "ok",
        "security_level": level,
        "fields": fields,
        "jira_email": email_state,
        "jira_api_token": token_state,
        "target_secret": target_state,
        "summary": " | ".join(lines),
        "message": "Credential status (values never shown).",
    }


def test_connection() -> dict[str, Any]:
    """Probe Jira with stored email/token. Never returns secret values."""
    from settings.connection_health import check_jira_auth

    check = check_jira_auth()
    up = bool(check.get("up"))
    state = str(check.get("state") or ("up" if up else "down"))
    message = str(check.get("message") or "")
    # Prefer an auth-focused label when the probe is about credentials.
    if state == "not_configured":
        result = "not_configured"
    elif up:
        result = "success"
    else:
        result = "auth_error" if "auth" in message.lower() else "failed"
    return {
        "status": "ok",
        "result": result,
        "success": up,
        "check": {
            "id": check.get("id"),
            "label": check.get("label"),
            "state": state,
            "up": up,
            "message": message,
        },
        "message": message,
        "used_stored_secret": True,
    }


def clear_secret(key: str, confirm: bool = False) -> dict[str, Any]:
    """Clear one secret from the active level store. Requires confirm=True."""
    from settings.store import get_security_level, load_settings, update_setting

    normalized = str(key or "").strip()
    if normalized not in CLEARABLE_SECRETS:
        return {
            "status": "error",
            "message": f"Unknown secret key. Allowed: {', '.join(CLEARABLE_SECRETS)}.",
        }
    label = _FIELD_LABELS.get(normalized, normalized)
    data = load_settings()
    was_set = bool(str(data.get(normalized) or "").strip())
    if not confirm:
        return {
            "status": "confirmation_required",
            "key": normalized,
            "label": label,
            "was_set": was_set,
            "proposed": {normalized: "(cleared)"},
            "message": f"Confirm clear of {label} (value never shown).",
        }
    # Never put the old value in the audit or response.
    update_setting(normalized, "", confirm=True)
    level = get_security_level()
    audit = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": "clear_secret",
        "key": normalized,
        "label": label,
        "security_level": level,
        "was_set": was_set,
        # Explicitly no old_value / value fields — FR-SEC-5.
    }
    try:
        append_credentials_audit(audit)
    except OSError:
        pass
    status = credential_field_status()
    return {
        "status": "cleared",
        "key": normalized,
        "label": label,
        "was_set": was_set,
        "fields": status.get("fields"),
        "summary": status.get("summary"),
        "message": f"{label} cleared from local store.",
        "audit_has_old_value": False,
    }


def set_target_secret(value: str, confirm: bool = True) -> dict[str, Any]:
    """Store target secret (level-scoped). Response never echoes the value."""
    from settings.store import update_setting

    text = str(value or "")
    if not confirm:
        return {
            "status": "confirmation_required",
            "proposed": {"target_secret": "(hidden)" if text.strip() else ""},
        }
    update_setting("target_secret", text, confirm=True)
    status = credential_field_status()
    return {
        "status": "updated",
        "target_secret": status.get("target_secret"),
        "fields": status.get("fields"),
        "summary": status.get("summary"),
        "message": "Target secret saved to local store (value not shown).",
    }
