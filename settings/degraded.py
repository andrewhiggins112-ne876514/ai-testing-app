"""Degraded-mode hints when Jira, Ollama, or target is down (KAN-139 / FR-CONN-1)."""
from __future__ import annotations

from typing import Any

from settings.connection_health import connection_health


def degraded_status() -> dict[str, Any]:
    """Non-secret dependency snapshot for UI, draft, and chat."""
    health = connection_health()
    checks = {c.get("id"): c for c in health.get("checks") or [] if isinstance(c, dict)}
    jira = checks.get("jira") or {}
    ollama = checks.get("ollama") or {}
    target = checks.get("target") or {}
    messages: dict[str, str] = {}
    if not ollama.get("up"):
        messages["ollama"] = (
            ollama.get("message") or "Ollama is unavailable — chat and draft may not work."
        )
    if not jira.get("up"):
        messages["jira"] = (
            jira.get("message") or "Jira is unavailable — new reads fail; saved plans still open."
        )
    if not target.get("up"):
        messages["target"] = (
            target.get("message") or "Target is down — runs fail as environment, not as pass."
        )
    return {
        "status": "ok",
        "security_level": health.get("security_level"),
        "ollama_up": bool(ollama.get("up")),
        "jira_up": bool(jira.get("up")),
        "target_up": bool(target.get("up")),
        "messages": messages,
        "checks": health.get("checks") or [],
        "plans_available": True,
    }


def ollama_chat_blocked() -> dict[str, Any] | None:
    """Return a chat-style payload when Ollama is down; plans/chat stay readable."""
    snap = degraded_status()
    if snap.get("ollama_up"):
        return None
    msg = snap.get("messages", {}).get(
        "ollama",
        "Ollama is unavailable. Saved plans still open; start Ollama to chat or draft.",
    )
    return {"ok": False, "error": "ollama_unavailable", "reply": msg, "degraded": snap}