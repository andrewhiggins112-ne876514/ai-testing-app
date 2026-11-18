"""FR-MAN-1 / KAN-285 — real local Ollama assist drafts (honest unavailable).

Never writes to Jira. Never keylogs / clipboard / mic. Used only when
Manual session agent_assist is ON — typically at End → review.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
_TIMEOUT = httpx.Timeout(45.0, connect=3.0)
_MAX_DRAFTS = 4
_DRAFT_KINDS = frozenset({"step_draft", "possible_bug_hint"})

# Test hook — replace with a stub that returns {"ok": bool, ...}.
_chat_impl: Callable[[str, str], dict[str, Any]] | None = None


def set_chat_impl(fn: Callable[[str, str], dict[str, Any]] | None) -> None:
    """Inject Ollama chat for unit tests (None restores real client)."""
    global _chat_impl
    _chat_impl = fn


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id(prefix: str = "ad") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _resolved_model() -> str:
    try:
        from settings.ollama_models import get_ollama_model

        return get_ollama_model() or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    except Exception:  # noqa: BLE001 — assist must degrade honestly
        return os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")


def ollama_reachable() -> bool:
    """Fast probe — same host as connection_health / chat."""
    try:
        from settings.degraded import degraded_status

        return bool(degraded_status().get("ollama_up"))
    except Exception:  # noqa: BLE001
        try:
            with httpx.Client(timeout=httpx.Timeout(3.0, connect=2.0)) as client:
                r = client.get(f"{_OLLAMA_URL}/api/tags")
                return r.status_code == 200
        except Exception:  # noqa: BLE001
            return False


def _strip_fences(text: str) -> str:
    body = (text or "").strip()
    if body.startswith("```"):
        lines = body.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        body = "\n".join(lines).strip()
    return body


def _extract_json_array(text: str) -> list[Any] | None:
    cleaned = _strip_fences(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get("drafts"), list):
            return parsed["drafts"]
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def _default_chat(system: str, user: str) -> dict[str, Any]:
    """Call local Ollama /api/chat (no tools). Returns ok/content or error."""
    if not ollama_reachable():
        return {
            "ok": False,
            "error": "ollama_unavailable",
            "message": (
                "Ollama is unavailable — agent assist cannot draft. "
                "Notes and stills are kept; no fake AI drafts."
            ),
        }
    payload = {
        "model": _resolved_model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(f"{_OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 — honest unavailable
        return {
            "ok": False,
            "error": "ollama_unavailable",
            "message": (
                f"Ollama assist failed ({type(exc).__name__}). "
                "No fake AI drafts — start Ollama or turn Assist off."
            ),
        }
    content = ""
    if isinstance(data, dict):
        msg = data.get("message") or {}
        if isinstance(msg, dict):
            content = str(msg.get("content") or "")
    if not content.strip():
        return {
            "ok": False,
            "error": "ollama_empty",
            "message": "Ollama returned an empty assist reply — no fake drafts.",
        }
    return {"ok": True, "content": content}


def _build_prompt(session: dict[str, Any]) -> tuple[str, str]:
    notes = list(session.get("notes") or [])
    stills = list(session.get("stills") or [])
    note_lines = [
        f"- [{n.get('id')}] {str(n.get('text') or '').strip()}"
        for n in notes
        if str(n.get("text") or "").strip()
    ]
    still_lines = [
        f"- [{s.get('id')}] still"
        + (f" captured={bool(s.get('captured'))}" if "captured" in s else "")
        for s in stills
    ]
    system = (
        "You assist a manual exploratory tester. Produce ONLY a JSON array of "
        "local unpublished draft objects (no markdown prose). Each object: "
        '{"kind":"step_draft"|"possible_bug_hint","title":"...","text":"..."}. '
        "Use session notes/stills — do not invent Jira keys or claim bugs are filed. "
        "Never ask for credentials. Max 4 drafts. Prefer concrete reproduction or "
        "next test steps from the notes."
    )
    user = (
        f"Charter: {session.get('charter') or '(none)'}\n"
        f"Story key (context only): {session.get('jira_story_key') or '(none)'}\n"
        f"Notes ({len(note_lines)}):\n"
        + ("\n".join(note_lines) if note_lines else "(none)")
        + f"\nStills ({len(still_lines)}):\n"
        + ("\n".join(still_lines) if still_lines else "(none)")
        + "\nReturn JSON array only."
    )
    return system, user


def _normalize_drafts(raw: list[Any], *, note_ids: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in _DRAFT_KINDS:
            # Map common aliases
            if kind in {"bug", "bug_hint", "possible_bug", "hint"}:
                kind = "possible_bug_hint"
            elif kind in {"step", "steps", "test_step", "step_update"}:
                kind = "step_draft"
            else:
                continue
        title = str(item.get("title") or "").strip()[:120]
        text = str(item.get("text") or item.get("body") or "").strip()[:2000]
        if not text:
            continue
        # Reject pure note-echo: identical to a single note with "Local draft from note"
        if text.lower().startswith("local draft from note:"):
            continue
        draft = {
            "id": _new_id("ad"),
            "at": _utcnow(),
            "kind": kind,
            "title": title or ("Possible bug hint" if kind == "possible_bug_hint" else "Step draft"),
            "text": text,
            "source": "ollama",
            "published": False,
            "from_note_ids": list(note_ids)[:12],
        }
        out.append(draft)
        if len(out) >= _MAX_DRAFTS:
            break
    return out


def generate_assist_drafts(session: dict[str, Any]) -> dict[str, Any]:
    """Fill session assist_drafts from local Ollama, or set honest unavailable.

    Mutates ``session`` keys: assist_drafts, assist_status, assist_message.
    Does not save; caller persists.
    """
    if not session.get("agent_assist"):
        session["assist_drafts"] = []
        session["assist_status"] = "off"
        session["assist_message"] = ""
        return {
            "status": "ok",
            "assist_status": "off",
            "assist_drafts": [],
            "message": "Agent assist is off — no AI drafts.",
        }

    notes = list(session.get("notes") or [])
    stills = list(session.get("stills") or [])
    if not notes and not stills:
        session["assist_drafts"] = []
        session["assist_status"] = "ready"
        session["assist_message"] = (
            "Assist is on, but there are no notes or stills to draft from."
        )
        return {
            "status": "ok",
            "assist_status": "ready",
            "assist_drafts": [],
            "message": session["assist_message"],
        }

    system, user = _build_prompt(session)
    chat = _chat_impl if _chat_impl is not None else _default_chat
    result = chat(system, user)
    if not result.get("ok"):
        session["assist_drafts"] = []
        session["assist_status"] = "unavailable"
        session["assist_message"] = str(
            result.get("message")
            or "Ollama is unavailable — no fake AI drafts."
        )
        return {
            "status": "ok",
            "assist_status": "unavailable",
            "assist_drafts": [],
            "error": result.get("error") or "ollama_unavailable",
            "message": session["assist_message"],
        }

    raw = _extract_json_array(str(result.get("content") or ""))
    if raw is None:
        session["assist_drafts"] = []
        session["assist_status"] = "unavailable"
        session["assist_message"] = (
            "Assist could not parse a local draft from Ollama — "
            "no fake note-echo drafts. Try again after End, or turn Assist off."
        )
        return {
            "status": "ok",
            "assist_status": "unavailable",
            "assist_drafts": [],
            "error": "parse_failed",
            "message": session["assist_message"],
        }

    note_ids = [str(n.get("id")) for n in notes if n.get("id")]
    drafts = _normalize_drafts(raw, note_ids=note_ids)
    if not drafts:
        session["assist_drafts"] = []
        session["assist_status"] = "unavailable"
        session["assist_message"] = (
            "Ollama returned no usable drafts — UI will not invent AI hints."
        )
        return {
            "status": "ok",
            "assist_status": "unavailable",
            "assist_drafts": [],
            "error": "empty_drafts",
            "message": session["assist_message"],
        }

    session["assist_drafts"] = drafts
    session["assist_status"] = "ready"
    session["assist_message"] = (
        f"{len(drafts)} local unpublished assist draft(s) from Ollama — "
        "Propose then Confirm still required for Jira."
    )
    return {
        "status": "ok",
        "assist_status": "ready",
        "assist_drafts": drafts,
        "message": session["assist_message"],
    }
