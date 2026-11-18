"""Pause-on-fail sessions for headed plan runs (KAN-149 / B4).

When pause_on_fail is on, a failed step keeps the browser open until the
tester continues (next steps) or stops (record failed run). Off by default.
"""
from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PauseSession:
    id: str
    plan_id: str
    case_id: str
    level: str
    state: str = "running"  # running | paused | done
    message: str = ""
    partial_playwright: dict[str, Any] | None = None
    result_payload: dict[str, Any] | None = None
    decision_future: asyncio.Future | None = field(default=None, repr=False)
    state_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    created_at: float = field(default_factory=time.monotonic)


_SESSIONS: dict[str, PauseSession] = {}


def clear_sessions() -> None:
    """Test helper — drop in-memory pause sessions."""
    _SESSIONS.clear()


def create_session(plan_id: str, case_id: str, *, level: str) -> PauseSession:
    sid = "pause-" + secrets.token_hex(8)
    session = PauseSession(
        id=sid,
        plan_id=plan_id,
        case_id=case_id,
        level=(level or "OFFICIAL").strip().upper(),
        message="Running with pause on fail…",
    )
    _SESSIONS[sid] = session
    return session


def get_session(pause_id: str) -> PauseSession | None:
    return _SESSIONS.get((pause_id or "").strip())


def _notify(session: PauseSession) -> None:
    session.state_event.set()


def public_session(session: PauseSession) -> dict[str, Any]:
    out: dict[str, Any] = {
        "status": session.state if session.state != "done" else "ok",
        "pause_state": session.state,
        "pause_id": session.id,
        "plan_id": session.plan_id,
        "case_id": session.case_id,
        "security_level": session.level,
        "message": session.message,
        "pause_on_fail": True,
    }
    if session.state == "paused":
        out["status"] = "paused"
        pw = session.partial_playwright or {}
        out["playwright"] = {
            "status": pw.get("status"),
            "error": pw.get("error"),
            "screenshot": pw.get("screenshot"),
            "url": pw.get("url"),
            "title": pw.get("title"),
        }
        # Surface known headed AUT page context for Manual (KAN-289).
        out["page_context"] = {
            "known": bool(pw.get("url") or pw.get("title")),
            "url": str(pw.get("url") or ""),
            "title": str(pw.get("title") or ""),
            "source": "playwright_pause",
            "keylog": False,
        }
    if session.state == "done" and session.result_payload:
        merged = dict(session.result_payload)
        merged["pause_id"] = session.id
        merged["pause_state"] = "done"
        merged["pause_on_fail"] = True
        return merged
    return out


async def wait_until_paused_or_done(
    session: PauseSession,
    *,
    timeout_s: float = 600.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while True:
        if session.state in {"paused", "done"}:
            return public_session(session)
        session.state_event.clear()
        if session.state in {"paused", "done"}:
            return public_session(session)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            session.state = "done"
            session.message = "Timed out waiting for pause or completion."
            session.result_payload = {
                "status": "error",
                "error": "pause_timeout",
                "message": session.message,
                "pause_id": session.id,
            }
            _notify(session)
            return public_session(session)
        try:
            await asyncio.wait_for(session.state_event.wait(), timeout=min(1.0, remaining))
        except asyncio.TimeoutError:
            continue


async def make_pause_waiter(session: PauseSession):
    """Return an awaitable pause_decision callback bound to this session."""

    async def pause_decision(partial: dict[str, Any]) -> str:
        session.partial_playwright = dict(partial or {})
        session.state = "paused"
        session.message = (
            "Paused on fail — headed browser left open. Continue or Stop."
        )
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        session.decision_future = fut
        _notify(session)
        decision = await fut
        session.decision_future = None
        session.state = "running"
        session.message = (
            "Continuing after pause…"
            if decision == "continue"
            else "Stopping after pause…"
        )
        return "continue" if decision == "continue" else "stop"

    return pause_decision


async def signal_decision(pause_id: str, decision: str) -> dict[str, Any]:
    session = get_session(pause_id)
    if session is None:
        return {
            "status": "error",
            "error": "pause_not_found",
            "message": f"No pause session {pause_id!r}.",
        }
    if session.state != "paused" or session.decision_future is None:
        if session.state == "done":
            return public_session(session)
        return {
            "status": "error",
            "error": "not_paused",
            "message": "Run is not waiting on a pause decision.",
            "pause_id": session.id,
            "pause_state": session.state,
        }
    choice = "continue" if decision == "continue" else "stop"
    if not session.decision_future.done():
        session.decision_future.set_result(choice)
    deadline = time.monotonic() + 600.0
    if choice == "stop":
        while session.state != "done" and time.monotonic() < deadline:
            session.state_event.clear()
            if session.state == "done":
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                await asyncio.wait_for(
                    session.state_event.wait(), timeout=min(1.0, remaining)
                )
            except asyncio.TimeoutError:
                continue
        return public_session(session)
    while session.state == "running" and time.monotonic() < deadline:
        session.state_event.clear()
        if session.state != "running":
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            await asyncio.wait_for(session.state_event.wait(), timeout=min(1.0, remaining))
        except asyncio.TimeoutError:
            continue
    return public_session(session)
