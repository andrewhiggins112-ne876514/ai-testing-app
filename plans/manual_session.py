"""FR-MAN-1 Charter Frame MVP (KAN-277).

Level-scoped manual / exploratory sessions under
``%LOCALAPPDATA%/ai_testing_app/plans/{LEVEL}/sessions/``.
No background capture until explicit Start. Jira writes stay preview + confirm.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from plans.store import plans_dir

_ID_SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
_JIRA_KEY = re.compile(r"^[A-Z][A-Z0-9]+-\d+$", re.I)
_FAILURE_CLASSES = frozenset(
    {"product_bug", "test_defect", "environment", "known_issue", ""}
)
CHARTER_MAX = 2000
NOTE_MAX = 2000

# In-memory open-session index (also persisted). Tests may clear via reset_open_cache.
_OPEN_BY_LEVEL: dict[str, str] = {}


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id(prefix: str = "ms") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def reset_open_cache() -> None:
    """Test helper — drop in-memory open-session index."""
    _OPEN_BY_LEVEL.clear()


def sessions_dir(level: str | None = None) -> Path:
    """``plans/{LEVEL}/sessions`` — isolated per security level."""
    return plans_dir(level) / "sessions"


def _session_path(session_id: str, level: str | None = None) -> Path:
    sid = (session_id or "").strip()
    if not _ID_SAFE.match(sid):
        raise ValueError(f"invalid session id: {session_id!r}")
    return sessions_dir(level) / f"{sid}.json"


def _stills_dir(session_id: str, level: str | None = None) -> Path:
    return sessions_dir(level) / session_id


def _normalize_jira_key(raw: Any) -> str:
    text = str(raw or "").strip().upper()
    if not text:
        return ""
    if not _JIRA_KEY.match(text):
        return ""
    return text


def _normalize_charter(raw: Any) -> str:
    return str(raw or "").strip()[:CHARTER_MAX]


def _normalize_note(raw: Any) -> str:
    return str(raw or "").strip()[:NOTE_MAX]


def _default_frame() -> dict[str, float]:
    """Relative free-region rect (0–1) — snip-style default centered."""
    return {"x": 0.18, "y": 0.16, "w": 0.64, "h": 0.58}


def _normalize_frame(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return _default_frame()
    out = _default_frame()
    for key in ("x", "y", "w", "h"):
        try:
            val = float(raw.get(key))
        except (TypeError, ValueError):
            continue
        out[key] = max(0.0, min(1.0, val))
    out["w"] = max(0.12, min(1.0 - out["x"], out["w"]))
    out["h"] = max(0.12, min(1.0 - out["y"], out["h"]))
    return out


def _public(session: dict[str, Any]) -> dict[str, Any]:
    """Strip nothing secret (sessions never store tokens); stable API shape."""
    return {
        "id": session.get("id"),
        "level": session.get("level"),
        "status": session.get("status"),
        "charter": session.get("charter"),
        "plan_id": session.get("plan_id") or "",
        "case_id": session.get("case_id") or "",
        "jira_story_key": session.get("jira_story_key") or "",
        "jira_test_key": session.get("jira_test_key") or "",
        "ticket_bound": bool(session.get("ticket_bound")),
        "agent_assist": bool(session.get("agent_assist")),
        "armed_mist": bool(session.get("armed_mist")),
        "frame": dict(session.get("frame") or _default_frame()),
        "notes": list(session.get("notes") or []),
        "stills": list(session.get("stills") or []),
        "assist_drafts": list(session.get("assist_drafts") or []),
        "proposals": list(session.get("proposals") or []),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "ended_at": session.get("ended_at"),
        "background_capture": False,
        "silent_video": False,
        "keylog": False,
        "writes_jira_on_start": False,
    }


def _load(session_id: str, level: str | None = None) -> dict[str, Any] | None:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    try:
        path = _session_path(session_id, lvl)
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if str(data.get("level") or "").upper() != lvl:
        return None
    return data


def _save(session: dict[str, Any]) -> None:
    lvl = str(session.get("level") or "").strip().upper()
    sid = str(session.get("id") or "")
    path = _session_path(sid, lvl)
    path.parent.mkdir(parents=True, exist_ok=True)
    session["updated_at"] = _utcnow()
    path.write_text(json.dumps(session, indent=2), encoding="utf-8")


def _sync_open_index(level: str) -> None:
    lvl = level.strip().upper()
    open_id = None
    root = sessions_dir(lvl)
    if root.is_dir():
        for path in sorted(root.glob("ms*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("status") == "open":
                open_id = str(data.get("id") or "")
                break
    if open_id:
        _OPEN_BY_LEVEL[lvl] = open_id
    else:
        _OPEN_BY_LEVEL.pop(lvl, None)


def get_open_session(level: str | None = None) -> dict[str, Any] | None:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    sid = _OPEN_BY_LEVEL.get(lvl)
    if sid:
        session = _load(sid, lvl)
        if session and session.get("status") == "open":
            return session
    _sync_open_index(lvl)
    sid = _OPEN_BY_LEVEL.get(lvl)
    if not sid:
        return None
    return _load(sid, lvl)


def list_sessions(level: str | None = None) -> dict[str, Any]:
    """List sessions for the active security level only."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    root = sessions_dir(lvl)
    items: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.glob("ms*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            if str(data.get("level") or "").upper() != lvl:
                continue
            items.append(
                {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "charter": (data.get("charter") or "")[:120],
                    "created_at": data.get("created_at"),
                    "ended_at": data.get("ended_at"),
                    "plan_id": data.get("plan_id") or "",
                    "case_id": data.get("case_id") or "",
                    "jira_story_key": data.get("jira_story_key") or "",
                    "note_count": len(data.get("notes") or []),
                    "still_count": len(data.get("stills") or []),
                }
            )
    open_session = get_open_session(lvl)
    return {
        "status": "ok",
        "level": lvl,
        "sessions": items,
        "open_session_id": (open_session or {}).get("id"),
        "frame_visible": bool(open_session),
        "background_capture": False,
    }


def get_session(session_id: str, level: str | None = None) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r} on the active level.",
        }
    return {"status": "ok", "session": _public(session)}


def start_session(
    charter: str,
    *,
    plan_id: str = "",
    case_id: str = "",
    jira_story_key: str = "",
    jira_test_key: str = "",
    ticket_bound: bool = False,
    agent_assist: bool = False,
    armed_mist: bool = False,
    frame: Any = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Explicit Start — no Jira write, no background capture."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    text = _normalize_charter(charter)
    if not text:
        return {
            "status": "error",
            "error": "charter_required",
            "message": "Charter is required to start a manual session.",
        }

    story = _normalize_jira_key(jira_story_key)
    test_key = _normalize_jira_key(jira_test_key)
    bound = bool(ticket_bound) or bool(story)
    if bound and not story:
        return {
            "status": "error",
            "error": "story_required_when_bound",
            "message": "Jira story key is required when the session is ticket-bound.",
        }

    existing = get_open_session(lvl)
    if existing is not None:
        return {
            "status": "error",
            "error": "session_already_open",
            "message": (
                "Only one open manual session per security level. "
                "End or cancel the current session first."
            ),
            "open_session_id": existing.get("id"),
        }

    sid = _new_id("ms")
    now = _utcnow()
    session = {
        "id": sid,
        "level": lvl,
        "status": "open",
        "charter": text,
        "plan_id": str(plan_id or "").strip()[:64],
        "case_id": str(case_id or "").strip()[:64],
        "jira_story_key": story,
        "jira_test_key": test_key,
        "ticket_bound": bound,
        "agent_assist": bool(agent_assist),
        "armed_mist": bool(armed_mist),
        "frame": _normalize_frame(frame),
        "notes": [],
        "stills": [],
        "assist_drafts": [],
        "proposals": [],
        "created_at": now,
        "updated_at": now,
        "ended_at": None,
        # Never persist credentials
        "credentials": None,
    }
    _save(session)
    _OPEN_BY_LEVEL[lvl] = sid
    return {
        "status": "ok",
        "message": "Manual session started — Charter Frame armed. No Jira write.",
        "session": _public(session),
        "writes_jira": False,
        "background_capture": False,
    }


def update_session_frame(
    session_id: str,
    frame: Any,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Frame can only be resized while the session is open.",
        }
    session["frame"] = _normalize_frame(frame)
    _save(session)
    return {"status": "ok", "session": _public(session)}


def update_session_toggles(
    session_id: str,
    *,
    agent_assist: bool | None = None,
    armed_mist: bool | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Toggles can only change while the session is open.",
        }
    if agent_assist is not None:
        session["agent_assist"] = bool(agent_assist)
        if not session["agent_assist"]:
            # Assist OFF — drop unpublished AI drafts (human notes/stills kept).
            session["assist_drafts"] = []
    if armed_mist is not None:
        session["armed_mist"] = bool(armed_mist)
    _save(session)
    return {"status": "ok", "session": _public(session)}


def add_note(
    session_id: str,
    text: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Notes can only be added while the session is open.",
        }
    note_text = _normalize_note(text)
    if not note_text:
        return {
            "status": "error",
            "error": "note_required",
            "message": "Note text is required.",
        }
    note = {
        "id": _new_id("n"),
        "at": _utcnow(),
        "text": note_text,
    }
    session.setdefault("notes", []).append(note)
    if session.get("agent_assist"):
        # Local unpublished hint only — never Jira.
        session.setdefault("assist_drafts", []).append(
            {
                "id": _new_id("ad"),
                "at": _utcnow(),
                "kind": "possible_bug_hint",
                "from_note_id": note["id"],
                "text": f"Local draft from note: {note_text[:240]}",
                "published": False,
            }
        )
    _save(session)
    return {"status": "ok", "note": note, "session": _public(session)}


def attach_still(
    session_id: str,
    *,
    level: str | None = None,
    screen_bbox: Any = None,
) -> dict[str, Any]:
    """Opt-in still inside the Charter Frame region. Never continuous video."""
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Stills can only be attached while the session is open.",
        }

    lvl = str(session["level"])
    sid = str(session["id"])
    out_dir = _stills_dir(sid, lvl)
    out_dir.mkdir(parents=True, exist_ok=True)
    still_id = _new_id("st")
    filename = f"{still_id}.png"
    path = out_dir / filename

    bbox = None
    if isinstance(screen_bbox, (list, tuple)) and len(screen_bbox) == 4:
        try:
            bbox = tuple(int(v) for v in screen_bbox)
        except (TypeError, ValueError):
            bbox = None

    captured = False
    capture_error = ""
    try:
        from PIL import ImageGrab

        img = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()
        # Crop to relative frame when no absolute bbox provided.
        if bbox is None:
            frame = _normalize_frame(session.get("frame"))
            w, h = img.size
            left = int(frame["x"] * w)
            top = int(frame["y"] * h)
            right = int((frame["x"] + frame["w"]) * w)
            bottom = int((frame["y"] + frame["h"]) * h)
            img = img.crop((left, top, max(left + 1, right), max(top + 1, bottom)))
        img.save(path, format="PNG")
        captured = True
    except Exception as exc:  # noqa: BLE001 — still metadata must not crash session
        capture_error = str(exc)[:200]
        # Keep a tiny placeholder so review still lists the opt-in attempt.
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00"
            b"\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    still = {
        "id": still_id,
        "at": _utcnow(),
        "path": str(path),
        "captured": captured,
        "capture_error": capture_error,
        "frame": _normalize_frame(session.get("frame")),
        "opt_in": True,
    }
    session.setdefault("stills", []).append(still)
    _save(session)
    return {
        "status": "ok",
        "still": still,
        "session": _public(session),
        "message": (
            "Still attached (opt-in)."
            if captured
            else "Still recorded with placeholder — capture failed."
        ),
    }


def end_session(session_id: str, *, level: str | None = None) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Session is not open.",
        }
    session["status"] = "ended"
    session["ended_at"] = _utcnow()
    _save(session)
    lvl = str(session["level"])
    if _OPEN_BY_LEVEL.get(lvl) == session_id:
        _OPEN_BY_LEVEL.pop(lvl, None)
    return {
        "status": "ok",
        "message": "Session ended — review the draft. Propose then confirm for Jira.",
        "session": _public(session),
        "review": _review_payload(session),
    }


def cancel_session(
    session_id: str,
    *,
    confirm: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") != "open":
        return {
            "status": "error",
            "error": "session_not_open",
            "message": "Only an open session can be cancelled.",
        }
    if not confirm:
        return {
            "status": "error",
            "error": "confirm_required",
            "message": "Cancel discards the uncommitted session — pass confirm=true.",
            "confirm_required": True,
        }
    session["status"] = "cancelled"
    session["ended_at"] = _utcnow()
    _save(session)
    lvl = str(session["level"])
    if _OPEN_BY_LEVEL.get(lvl) == session_id:
        _OPEN_BY_LEVEL.pop(lvl, None)
    return {
        "status": "ok",
        "message": (
            "Session cancelled — local draft marked cancelled (product rules); "
            "nothing written to Jira."
        ),
        "session": _public(session),
        "writes_jira": False,
        "discarded": True,
    }


def _review_payload(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": session.get("id"),
        "charter": session.get("charter"),
        "notes": list(session.get("notes") or []),
        "stills": list(session.get("stills") or []),
        "assist_drafts": list(session.get("assist_drafts") or []),
        "propose_options": [
            "create_bug",
            "comment_on_story",
            "attach_local_case_note",
            "test_step_update_preview",
        ],
        "confirm_required_for_jira": True,
    }


def review_session(session_id: str, *, level: str | None = None) -> dict[str, Any]:
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") not in {"ended", "open"}:
        return {
            "status": "error",
            "error": "not_reviewable",
            "message": "Cancelled sessions are not opened for propose.",
        }
    return {
        "status": "ok",
        "session": _public(session),
        "review": _review_payload(session),
    }


def _selected_notes(session: dict[str, Any], note_ids: list[str] | None) -> list[dict]:
    notes = list(session.get("notes") or [])
    if not note_ids:
        return notes
    wanted = {str(n) for n in note_ids}
    return [n for n in notes if str(n.get("id")) in wanted]


def _selected_stills(session: dict[str, Any], still_ids: list[str] | None) -> list[dict]:
    stills = list(session.get("stills") or [])
    if not still_ids:
        return stills
    wanted = {str(s) for s in still_ids}
    return [s for s in stills if str(s.get("id")) in wanted]


def propose(
    session_id: str,
    kind: str,
    *,
    note_ids: list[str] | None = None,
    still_ids: list[str] | None = None,
    failure_class: str = "product_bug",
    level: str | None = None,
) -> dict[str, Any]:
    """Build a local proposal preview. Does not write to Jira."""
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") not in {"ended", "open"}:
        return {
            "status": "error",
            "error": "not_reviewable",
            "message": "End the session before proposing ticket updates.",
        }

    kind_key = (kind or "").strip().lower()
    allowed = {
        "create_bug",
        "comment_on_story",
        "attach_local_case_note",
        "test_step_update_preview",
    }
    if kind_key not in allowed:
        return {
            "status": "error",
            "error": "invalid_propose_kind",
            "message": f"Unknown propose kind {kind!r}.",
        }

    notes = _selected_notes(session, note_ids)
    stills = _selected_stills(session, still_ids)
    fc = (failure_class or "product_bug").strip().lower()
    if fc not in _FAILURE_CLASSES:
        fc = "product_bug"

    proposal_id = _new_id("pr")
    payload: dict[str, Any] = {
        "id": proposal_id,
        "kind": kind_key,
        "created_at": _utcnow(),
        "state": "pending_review",
        "confirm_required": kind_key in {"create_bug", "comment_on_story"},
        "jira_written": False,
        "issue_key": None,
    }

    note_lines = [str(n.get("text") or "") for n in notes]
    evidence_paths = [str(s.get("path") or "") for s in stills if s.get("path")]

    if kind_key == "create_bug":
        if fc != "product_bug":
            return {
                "status": "error",
                "error": "product_bug_only",
                "message": "Create Bug is only offered when failure class is product_bug.",
            }
        packet = {
            "symptom": (session.get("charter") or "Manual session finding")[:200],
            "expected": "Behaviour matches charter / acceptance criteria.",
            "actual": "\n".join(note_lines)[:2000] or "(no notes selected)",
            "environment": f"Security level: {session.get('level')}",
            "replication_steps": [
                f"Start manual session with charter: {session.get('charter')}",
                *([f"Note: {t}" for t in note_lines[:8]] or ["Reproduce from session notes."]),
            ],
            "evidence_paths": evidence_paths,
            "failure_class": fc,
            "jira_key": session.get("jira_story_key") or "",
            "confirm_required": True,
        }
        payload["packet"] = packet
        payload["message"] = "Preview only — confirm required to create a Jira Bug."

    elif kind_key == "comment_on_story":
        story = session.get("jira_story_key") or ""
        if not story:
            return {
                "status": "error",
                "error": "story_required",
                "message": "Comment on story needs a linked Jira story key.",
            }
        body = "\n".join(
            [
                f"Manual session {session.get('id')} — {session.get('charter')}",
                "",
                *note_lines,
            ]
        )[:4000]
        payload["comment"] = {"issue_key": story, "body": body}
        payload["message"] = "Preview only — confirm required to comment on Jira."

    elif kind_key == "attach_local_case_note":
        plan_id = session.get("plan_id") or ""
        case_id = session.get("case_id") or ""
        if not plan_id or not case_id:
            return {
                "status": "error",
                "error": "plan_case_required",
                "message": "Local case note needs linked plan id and case id.",
            }
        payload["local_note"] = {
            "plan_id": plan_id,
            "case_id": case_id,
            "text": "\n".join(note_lines)[:NOTE_MAX],
        }
        payload["confirm_required"] = False
        payload["message"] = "Local case note ready — apply writes B7 note only (no Jira)."

    else:  # test_step_update_preview
        payload["step_update"] = {
            "plan_id": session.get("plan_id") or "",
            "case_id": session.get("case_id") or "",
            "jira_test_key": session.get("jira_test_key") or "",
            "preview_steps": note_lines[:20],
            "pending_review": True,
            "auto_commit": False,
            "weakens_assertions": False,
        }
        payload["confirm_required"] = False
        payload["message"] = (
            "Test-step update preview only — local pending_review; never auto-commit."
        )

    session.setdefault("proposals", []).append(payload)
    _save(session)
    return {
        "status": "ok",
        "proposal": payload,
        "session": _public(session),
        "writes_jira": False,
    }


def confirm_proposal(
    session_id: str,
    proposal_id: str,
    *,
    confirm: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Two-step confirm for Jira side effects; Cancel writes nothing."""
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }

    proposals = list(session.get("proposals") or [])
    target: dict[str, Any] | None = None
    for item in proposals:
        if str(item.get("id")) == str(proposal_id):
            target = item
            break
    if target is None:
        return {
            "status": "error",
            "error": "proposal_not_found",
            "message": f"No proposal {proposal_id!r}.",
        }

    if target.get("state") == "submitted":
        return {
            "status": "ok",
            "message": "Proposal already submitted.",
            "proposal": target,
            "session": _public(session),
        }

    if not confirm:
        target["state"] = "cancelled"
        _save(session)
        return {
            "status": "ok",
            "message": "Proposal cancelled — nothing written to Jira.",
            "proposal": target,
            "writes_jira": False,
            "session": _public(session),
        }

    kind = target.get("kind")
    if kind == "attach_local_case_note":
        local = target.get("local_note") or {}
        from plans.store import set_plan_notes

        result = set_plan_notes(
            str(local.get("plan_id") or ""),
            str(local.get("case_id") or ""),
            case_note=str(local.get("text") or ""),
        )
        if result.get("status") != "ok":
            return result
        target["state"] = "submitted"
        target["jira_written"] = False
        _save(session)
        return {
            "status": "ok",
            "message": "Local case note saved (no Jira).",
            "proposal": target,
            "writes_jira": False,
            "session": _public(session),
        }

    if kind == "test_step_update_preview":
        target["state"] = "submitted"
        target["jira_written"] = False
        _save(session)
        return {
            "status": "ok",
            "message": "Step-update preview acknowledged — still pending_review locally.",
            "proposal": target,
            "writes_jira": False,
            "session": _public(session),
        }

    if kind == "create_bug":
        # Preview confirm path: mark submitted only after plugin create_bug with confirm.
        # Callers that pass confirm=true expect the gate; actual Jira create stays async
        # via agent/plugin. Here we record intent + packet for the UI and require the
        # existing create_bug tool with its own confirm for the live write.
        packet = target.get("packet") or {}
        target["state"] = "confirmed_local"
        target["confirm_required"] = True
        target["jira_written"] = False
        target["ready_for_jira"] = True
        target["packet"] = packet
        _save(session)
        return {
            "status": "ok",
            "message": (
                "Bug proposal confirmed locally. Use create_bug with confirm=true "
                "and this packet to write to Jira (FR-JIRA-5). Nothing written yet."
            ),
            "proposal": target,
            "writes_jira": False,
            "confirm_required": True,
            "packet": packet,
            "session": _public(session),
        }

    if kind == "comment_on_story":
        comment = target.get("comment") or {}
        target["state"] = "confirmed_local"
        target["ready_for_jira"] = True
        target["jira_written"] = False
        _save(session)
        return {
            "status": "ok",
            "message": (
                "Comment proposal confirmed locally. Post via Jira comment with "
                "confirm=true — nothing written yet."
            ),
            "proposal": target,
            "writes_jira": False,
            "confirm_required": True,
            "comment": comment,
            "session": _public(session),
        }

    return {
        "status": "error",
        "error": "unsupported_kind",
        "message": f"Cannot confirm kind {kind!r}.",
    }


def defaults_info() -> dict[str, Any]:
    """Public defaults for Manual UI (assist/mist off)."""
    open_session = get_open_session()
    return {
        "status": "ok",
        "agent_assist_default": False,
        "armed_mist_default": False,
        "background_capture": False,
        "silent_video": False,
        "keylog": False,
        "click_through_default": True,
        "frame_style": "snip_free_region",
        "open_session_id": (open_session or {}).get("id"),
        "open_session": _public(open_session) if open_session else None,
        "fr_man_2": "parked",
        # KAN-283 — trustworthy headed loop contract
        "trustworthy_loop": True,
        "loop_stages": ["idle", "recording", "review"],
        "cancel_writes_jira": False,
        "confirm_uses_fr_jira_5": True,
        "in_app_cancel_confirm": True,
    }
