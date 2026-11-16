"""Ollama model list + agent model selection (KAN-129 / FR-CONN-1 / FR-SET-3).

Lists models local Ollama reports, persists one as the agent model, and validates
that the chosen model is present before claiming success. Does not start a second
model process — chat only requests the selected name from the local Ollama daemon.
"""
from __future__ import annotations

import os
import ssl
from typing import Any

import httpx

_DEFAULT_MODEL = "qwen2.5-coder:7b"
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def _ollama_base() -> str:
    return (os.getenv("OLLAMA_URL") or "http://localhost:11434").rstrip("/")


def default_model_name() -> str:
    env = (os.getenv("OLLAMA_MODEL") or "").strip()
    return env or _DEFAULT_MODEL


def list_ollama_models() -> dict[str, Any]:
    """Return models from local Ollama ``/api/tags``. Never starts a model."""
    base = _ollama_base()
    try:
        with httpx.Client(
            timeout=_TIMEOUT,
            follow_redirects=True,
            verify=ssl.create_default_context(),
        ) as client:
            response = client.get(f"{base}/api/tags")
    except httpx.TimeoutException:
        return {
            "status": "error",
            "error": "ollama_timeout",
            "message": "Ollama timed out while listing models.",
            "models": [],
            "ollama_url": base,
        }
    except httpx.HTTPError:
        return {
            "status": "error",
            "error": "ollama_unreachable",
            "message": "Ollama is not reachable. Start Ollama locally.",
            "models": [],
            "ollama_url": base,
        }
    if response.status_code != 200:
        return {
            "status": "error",
            "error": "ollama_http",
            "message": f"Ollama returned HTTP {response.status_code}.",
            "models": [],
            "ollama_url": base,
        }
    models: list[str] = []
    try:
        payload = response.json()
        for row in payload.get("models") or []:
            name = str((row or {}).get("name") or "").strip()
            if name and name not in models:
                models.append(name)
    except Exception:  # noqa: BLE001 — odd JSON must not crash settings
        models = []
    return {
        "status": "ok",
        "message": f"{len(models)} model{'s' if len(models) != 1 else ''} available.",
        "models": models,
        "ollama_url": base,
        "selected": get_ollama_model(),
    }


def get_ollama_model() -> str:
    """Resolved agent model: settings → env → default."""
    from settings.store import load_settings

    saved = str(load_settings().get("ollama_model") or "").strip()
    return saved or default_model_name()


def model_is_available(name: str, models: list[str] | None = None) -> bool:
    chosen = (name or "").strip()
    if not chosen:
        return False
    available = models
    if available is None:
        listed = list_ollama_models()
        if listed.get("status") != "ok":
            return False
        available = list(listed.get("models") or [])
    if chosen in available:
        return True
    # Ollama tags sometimes omit :latest — treat bare/tag variants as a match.
    bare = chosen.split(":", 1)[0]
    for item in available:
        if item == chosen or item.split(":", 1)[0] == bare:
            if ":" not in chosen and item.startswith(bare + ":"):
                return True
            if chosen.endswith(":latest") and item == bare:
                return True
            if item.endswith(":latest") and chosen == bare:
                return True
    return False


def resolve_chat_model() -> dict[str, Any]:
    """Model name for chat, or a clear missing-model error (no pretend success)."""
    name = get_ollama_model()
    listed = list_ollama_models()
    if listed.get("status") != "ok":
        return {
            "status": "error",
            "error": listed.get("error") or "ollama_unreachable",
            "message": listed.get("message") or "Ollama is not reachable.",
            "model": name,
            "models": [],
        }
    models = list(listed.get("models") or [])
    if not model_is_available(name, models):
        return {
            "status": "error",
            "error": "model_missing",
            "message": (
                f"Chosen model {name!r} is not installed in local Ollama. "
                "Pick an available model in App Settings."
            ),
            "model": name,
            "models": models,
        }
    return {
        "status": "ok",
        "model": name,
        "models": models,
        "message": f"Using model {name}.",
    }
