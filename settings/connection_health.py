"""Connect-once health checks (KAN-127 / FR-CONN-1).

Probes Jira, Ollama, and the target URL. Never returns secrets or token values.
Uses the same level-scoped settings keys as App Settings (no new credential store).
"""
from __future__ import annotations

import os
import ssl
from typing import Any

import httpx

_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def _client() -> httpx.Client:
    # Match jira_plugin / scripts: OS trust store via create_default_context.
    return httpx.Client(
        timeout=_TIMEOUT,
        follow_redirects=True,
        verify=ssl.create_default_context(),
    )


def _ollama_base() -> str:
    return (os.getenv("OLLAMA_URL") or "http://localhost:11434").rstrip("/")


def _safe_detail(text: str, *, secret: str = "") -> str:
    detail = (text or "").strip()
    if secret:
        detail = detail.replace(secret, "***")
    # Never echo auth headers or obvious secret-looking blobs.
    lowered = detail.lower()
    for needle in ("authorization", "bearer ", "api_token", "password"):
        if needle in lowered:
            return "request failed"
    return detail[:160]


def _check_jira() -> dict[str, Any]:
    from settings.store import load_settings

    settings = load_settings()
    url = (settings.get("jira_url") or settings.get("jira_base_url") or "").strip().rstrip("/")
    email = (settings.get("jira_email") or os.getenv("JIRA_EMAIL") or "").strip()
    token = (settings.get("jira_api_token") or os.getenv("JIRA_API_TOKEN") or "").strip()
    if not url:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "not_configured",
            "up": False,
            "message": "Jira URL not set.",
        }
    if not (url.startswith("https://") or url.startswith("http://127.0.0.1") or url.startswith("http://localhost")):
        return {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": "Jira URL must start with https:// (or local http).",
        }
    if not token:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "not_configured",
            "up": False,
            "message": "Jira API token not set in local store.",
        }
    auth = (email, token) if email else None
    headers = {}
    if not email:
        # Some Server/DC setups use bearer; Cloud needs email+token. Prefer Basic when email present.
        headers["Authorization"] = f"Bearer {token}"
    try:
        with _client() as client:
            if auth:
                response = client.get(f"{url}/rest/api/3/myself", auth=auth)
            else:
                response = client.get(f"{url}/rest/api/3/myself", headers=headers)
    except httpx.TimeoutException:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": "Jira timed out.",
        }
    except httpx.HTTPError as exc:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": _safe_detail(str(exc), secret=token) or "Jira unreachable.",
        }
    if response.status_code == 200:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "up",
            "up": True,
            "message": "Jira reachable.",
        }
    if response.status_code in (401, 403):
        return {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": "Jira auth failed (check email/token in local store).",
        }
    if response.status_code == 429:
        return {
            "id": "jira",
            "label": "Jira",
            "state": "down",
            "up": False,
            "message": "Jira rate limited.",
        }
    return {
        "id": "jira",
        "label": "Jira",
        "state": "down",
        "up": False,
        "message": f"Jira returned HTTP {response.status_code}.",
    }


def _check_ollama() -> dict[str, Any]:
    base = _ollama_base()
    try:
        with _client() as client:
            response = client.get(f"{base}/api/tags")
    except httpx.TimeoutException:
        return {
            "id": "ollama",
            "label": "Ollama",
            "state": "down",
            "up": False,
            "message": "Ollama timed out.",
        }
    except httpx.HTTPError:
        return {
            "id": "ollama",
            "label": "Ollama",
            "state": "down",
            "up": False,
            "message": "Ollama not reachable. Start Ollama locally.",
        }
    if response.status_code == 200:
        models: list[str] = []
        try:
            payload = response.json()
            for row in payload.get("models") or []:
                name = str((row or {}).get("name") or "").strip()
                if name and name not in models:
                    models.append(name)
        except Exception:  # noqa: BLE001 — health must not crash on odd JSON
            models = []
        count = len(models)
        return {
            "id": "ollama",
            "label": "Ollama",
            "state": "up",
            "up": True,
            "message": f"Ollama reachable ({count} model{'s' if count != 1 else ''}).",
            "model_count": count,
        }
    return {
        "id": "ollama",
        "label": "Ollama",
        "state": "down",
        "up": False,
        "message": f"Ollama returned HTTP {response.status_code}.",
    }


def _check_target() -> dict[str, Any]:
    from settings.store import load_settings

    target = (load_settings().get("target_url") or "").strip()
    if not target:
        return {
            "id": "target",
            "label": "Target URL",
            "state": "not_configured",
            "up": False,
            "message": "Target URL not set.",
        }
    if not (target.startswith("https://") or target.startswith("http://")):
        return {
            "id": "target",
            "label": "Target URL",
            "state": "down",
            "up": False,
            "message": "Target URL must start with http:// or https://.",
        }
    try:
        with _client() as client:
            try:
                response = client.head(target)
            except httpx.HTTPError:
                response = client.get(target)
    except httpx.TimeoutException:
        return {
            "id": "target",
            "label": "Target URL",
            "state": "down",
            "up": False,
            "message": "Target timed out.",
        }
    except httpx.HTTPError as exc:
        return {
            "id": "target",
            "label": "Target URL",
            "state": "down",
            "up": False,
            "message": _safe_detail(str(exc)) or "Target unreachable.",
        }
    # Any HTTP response means the host answered — treat as up for connectivity.
    return {
        "id": "target",
        "label": "Target URL",
        "state": "up",
        "up": True,
        "message": f"Target reachable (HTTP {response.status_code}).",
        "http_status": response.status_code,
    }


def connection_checklist() -> dict[str, Any]:
    """Non-secret snapshot of connection keys for the connect-once checklist."""
    from settings.store import get_security_level, load_settings

    data = load_settings()
    level = get_security_level()
    email_set = bool((data.get("jira_email") or "").strip())
    token_set = bool((data.get("jira_api_token") or "").strip())
    from settings.ollama_models import get_ollama_model

    return {
        "security_level": level,
        "jira_url": (data.get("jira_url") or "").strip(),
        "jira_project": (data.get("jira_project") or "").strip(),
        "jira_credentials_configured": email_set and token_set,
        "target_url": (data.get("target_url") or "").strip(),
        "target_app_path": (data.get("target_app_path") or "").strip(),
        "api_endpoint": (data.get("api_endpoint") or "").strip(),
        "ollama_model": get_ollama_model(),
        "level_switch_requires_confirm": True,
    }


def check_jira_auth() -> dict[str, Any]:
    """Public Jira auth probe for test-connection (KAN-185). Never returns secrets."""
    return _check_jira()


def connection_health() -> dict[str, Any]:
    """Run Jira / Ollama / target probes. Never includes secrets."""
    checks = [_check_jira(), _check_ollama(), _check_target()]
    # Scrub any accidental secret leakage in the whole payload string form later via tests.
    up_count = sum(1 for c in checks if c.get("up"))
    overall = "up" if up_count == len(checks) else ("degraded" if up_count else "down")
    checklist = connection_checklist()
    summary_bits = [f"{c['label']}: {'up' if c.get('up') else c.get('state', 'down')}" for c in checks]
    return {
        "status": "ok",
        "overall": overall,
        "checks": checks,
        "checklist": checklist,
        "summary": " | ".join(summary_bits),
        "message": f"Connection health: {overall}.",
    }
