"""FR-MAN-1 Charter Frame (KAN-277 MVP + Track 2 through KAN-293).

Level-scoped manual / exploratory sessions under
``%LOCALAPPDATA%/ai_testing_app/plans/{LEVEL}/sessions/``.
No background capture until explicit Start. Jira writes stay preview + confirm.
Agent assist (default off) produces real local Ollama drafts at End — never note-echo AI.
Window/monitor snap (KAN-287) stores absolute screen_bbox for stills.
Page URL/title from known headed AUT + annotate-still (KAN-289); E3 on propose.
Session library + level-scoped GDPR wipe (KAN-291).
Propose/confirm harden (KAN-293): failure class + Confirm dock visibility + audited writes.
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
_REDIRECT_KINDS = (
    "comment_on_story",
    "attach_local_case_note",
    "test_step_update_preview",
)
CHARTER_MAX = 2000
NOTE_MAX = 2000
ANNOTATION_MAX = 2000

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


def _normalize_screen_bbox(raw: Any) -> list[int] | None:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        left, top, right, bottom = (int(v) for v in raw)
    except (TypeError, ValueError):
        return None
    if right - left < 12 or bottom - top < 12:
        return None
    return [left, top, right, bottom]


def _normalize_frame_mode(raw: Any) -> str:
    mode = str(raw or "free").strip().lower()
    if mode in {"free", "monitor", "window", "float"}:
        return mode
    return "free"


def _normalize_annotation(raw: Any) -> str:
    return str(raw or "").strip()[:ANNOTATION_MAX]


def _empty_page_context() -> dict[str, Any]:
    return {
        "known": False,
        "url": "",
        "title": "",
        "source": "",
        "updated_at": None,
        "keylog": False,
    }


def _normalize_page_context(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or not raw.get("known"):
        return _empty_page_context()
    return {
        "known": True,
        "url": str(raw.get("url") or "")[:2000],
        "title": str(raw.get("title") or "")[:500],
        "source": str(raw.get("source") or "")[:64],
        "updated_at": raw.get("updated_at"),
        "keylog": False,
    }


def _redact_str(text: str) -> tuple[str, int]:
    from reports.redact import redact_text

    return redact_text(str(text or ""))


def _public(session: dict[str, Any]) -> dict[str, Any]:
    """Strip nothing secret (sessions never store tokens); stable API shape."""
    bbox = _normalize_screen_bbox(session.get("screen_bbox"))
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
        "frame_mode": _normalize_frame_mode(session.get("frame_mode")),
        "screen_bbox": bbox,
        "snap_label": str(session.get("snap_label") or ""),
        "page_context": _normalize_page_context(session.get("page_context")),
        "notes": list(session.get("notes") or []),
        "stills": list(session.get("stills") or []),
        "assist_drafts": list(session.get("assist_drafts") or []),
        "assist_status": str(session.get("assist_status") or ("off" if not session.get("agent_assist") else "pending")),
        "assist_message": str(session.get("assist_message") or ""),
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
    """List sessions for the active security level only (session library)."""
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
            status = str(data.get("status") or "")
            items.append(
                {
                    "id": data.get("id"),
                    "status": status,
                    "charter": (data.get("charter") or "")[:120],
                    "created_at": data.get("created_at"),
                    "ended_at": data.get("ended_at"),
                    "plan_id": data.get("plan_id") or "",
                    "case_id": data.get("case_id") or "",
                    "jira_story_key": data.get("jira_story_key") or "",
                    "note_count": len(data.get("notes") or []),
                    "still_count": len(data.get("stills") or []),
                    "reviewable": status in {"ended", "open"},
                    "level": lvl,
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
        "library": True,
        "gdpr_wipe_category": "sessions",
    }


def inventory_manual_sessions(level: str | None = None) -> dict[str, Any]:
    """Inventory Manual session JSON + still files for one security level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    root = sessions_dir(lvl)
    if not root.exists():
        return {
            "exists": False,
            "path": str(root),
            "bytes": 0,
            "items": 0,
            "session_count": 0,
            "level": lvl,
        }
    total = 0
    items = 0
    session_count = 0
    for child in root.rglob("*"):
        if child.is_file():
            items += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
            if child.suffix == ".json" and child.name.startswith("ms"):
                session_count += 1
    return {
        "exists": True,
        "path": str(root),
        "bytes": total,
        "items": items,
        "session_count": session_count,
        "level": lvl,
    }


def wipe_manual_sessions(level: str | None = None) -> dict[str, Any]:
    """Remove Manual session drafts + stills for one level (GDPR / FR-SEC-2).

    Does not touch other levels, credentials, or plan case JSON.
    """
    import shutil

    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    root = sessions_dir(lvl)
    before = inventory_manual_sessions(lvl)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    _OPEN_BY_LEVEL.pop(lvl, None)
    return {
        "deleted": True,
        "level": lvl,
        "path": str(root),
        "removed_items": before.get("items", 0),
        "removed_sessions": before.get("session_count", 0),
        "kind": "manual_sessions",
    }


def reopen_review(session_id: str, *, level: str | None = None) -> dict[str, Any]:
    """Reopen an ended (or open) draft for review/propose — never writes Jira."""
    result = review_session(session_id, level=level)
    if result.get("status") != "ok":
        return result
    result["reopened"] = True
    result["writes_jira"] = False
    result["message"] = (
        "Reopened local draft for review/propose. "
        "No Jira write until Propose → Confirm (FR-JIRA-5)."
    )
    return result


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
    from plans.aut_page_context import public_page_context

    # Attach known headed AUT page context at Start when the lab already has one.
    page_ctx = public_page_context(level=lvl)
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
        "frame_mode": "free",
        "screen_bbox": None,
        "snap_label": "",
        "page_context": page_ctx,
        "notes": [],
        "stills": [],
        "assist_drafts": [],
        # KAN-285 — drafts generated at End via Ollama (not note-echo).
        "assist_status": "pending" if agent_assist else "off",
        "assist_message": (
            "Assist on — local Ollama drafts will be built at End → review."
            if agent_assist
            else ""
        ),
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
        "page_context": page_ctx,
    }


def update_session_frame(
    session_id: str,
    frame: Any,
    *,
    frame_mode: str | None = None,
    screen_bbox: Any = None,
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
    mode = _normalize_frame_mode(frame_mode if frame_mode is not None else "free")
    # OS float (KAN-386): keep absolute screen_bbox for still capture.
    if mode == "float":
        session["frame_mode"] = "float"
        bbox = _normalize_screen_bbox(screen_bbox)
        if bbox is not None:
            session["screen_bbox"] = bbox
        session["snap_label"] = session.get("snap_label") or "OS float"
    # Manual in-app drag/resize returns to free-region (clears absolute snap bbox).
    elif mode == "free" or frame_mode is None:
        session["frame_mode"] = "free"
        session["screen_bbox"] = None
        session["snap_label"] = ""
    else:
        session["frame_mode"] = mode
    _save(session)
    return {"status": "ok", "session": _public(session)}


def snap_session_frame(
    session_id: str,
    mode: str,
    target_id: str,
    *,
    level: str | None = None,
    targets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Snap Charter Frame to a monitor or window (KAN-287)."""
    from plans.charter_snap import resolve_snap_target

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
            "message": "Snap is only available while the session is open.",
        }

    resolved = resolve_snap_target(mode, target_id, targets=targets)
    if resolved.get("status") != "ok":
        return resolved

    session["frame"] = _normalize_frame(resolved.get("frame"))
    session["frame_mode"] = _normalize_frame_mode(resolved.get("mode"))
    session["screen_bbox"] = _normalize_screen_bbox(resolved.get("screen_bbox"))
    session["snap_label"] = str(resolved.get("label") or "")[:120]
    _save(session)
    return {
        "status": "ok",
        "message": f"Snapped to {session['snap_label'] or session['frame_mode']}.",
        "session": _public(session),
        "snap": {
            "mode": session["frame_mode"],
            "target_id": str(resolved.get("target_id") or ""),
            "label": session["snap_label"],
            "screen_bbox": session["screen_bbox"],
            "frame": dict(session["frame"]),
        },
        # Toggles / click-through contract unchanged by snap.
        "agent_assist": bool(session.get("agent_assist")),
        "armed_mist": bool(session.get("armed_mist")),
    }


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
            session["assist_status"] = "off"
            session["assist_message"] = ""
        else:
            session["assist_status"] = "pending"
            session["assist_message"] = (
                "Assist on — local Ollama drafts will be built at End → review."
            )
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
    # KAN-285: do not echo notes as AI drafts. Real Ollama drafts run at End.
    if session.get("agent_assist") and session.get("assist_status") not in {
        "ready",
        "unavailable",
    }:
        session["assist_status"] = "pending"
        session["assist_message"] = (
            "Assist on — drafts build at End → review (not note-echo)."
        )
    _save(session)
    return {"status": "ok", "note": note, "session": _public(session)}


def refresh_page_context(
    session_id: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Pull known headed AUT URL/title onto the open session (no keylog)."""
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
            "message": "Page context can only be refreshed while the session is open.",
        }
    from plans.aut_page_context import public_page_context

    page_ctx = public_page_context(level=str(session.get("level") or ""))
    session["page_context"] = page_ctx
    _save(session)
    return {
        "status": "ok",
        "page_context": page_ctx,
        "session": _public(session),
        "message": (
            "Page context attached from known headed AUT."
            if page_ctx.get("known")
            else "No headed AUT page context known — notes/stills still work."
        ),
        "keylog": False,
    }


def attach_still(
    session_id: str,
    *,
    level: str | None = None,
    screen_bbox: Any = None,
    annotation: str = "",
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

    # Prefer explicit request bbox, then snapped session screen_bbox.
    bbox = _normalize_screen_bbox(screen_bbox)
    if bbox is None:
        bbox = _normalize_screen_bbox(session.get("screen_bbox"))

    # KAN-525: OS float stills must use the hole bbox — never full-desk grab.
    frame_mode = _normalize_frame_mode(session.get("frame_mode"))
    if bbox is None and frame_mode == "float":
        return {
            "status": "error",
            "error": "bbox_required",
            "message": "Still needs the capture hole bbox (no full-desk grab fallback).",
        }

    captured = False
    capture_error = ""
    try:
        from PIL import ImageGrab

        if bbox is not None:
            img = ImageGrab.grab(bbox=tuple(bbox), all_screens=True)
        else:
            # In-app free frame only: crop relative region from a single grab.
            try:
                img = ImageGrab.grab(all_screens=True)
            except TypeError:
                img = ImageGrab.grab()
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
        "screen_bbox": bbox,
        "frame_mode": _normalize_frame_mode(session.get("frame_mode")),
        "opt_in": True,
        "annotation": _normalize_annotation(annotation),
        "annotated": bool(_normalize_annotation(annotation)),
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


def still_file_path(
    session_id: str,
    still_id: str,
    *,
    level: str | None = None,
) -> Path | None:
    """Resolve a level-scoped still PNG for FileResponse (KAN-550).

    Prefers the canonical ``{still_id}.png`` under the session stills dir.
    Never returns a path outside that directory.
    """
    session = _load(session_id, level)
    if session is None:
        return None
    wanted = str(still_id or "").strip()
    if not wanted or not _ID_SAFE.match(wanted):
        return None
    stills = list(session.get("stills") or [])
    if not any(str(s.get("id") or "") == wanted for s in stills):
        return None
    sid = str(session["id"])
    lvl = str(session["level"])
    root = _stills_dir(sid, lvl).resolve()
    canonical = (root / f"{wanted}.png").resolve()
    try:
        canonical.relative_to(root)
    except ValueError:
        return None
    if canonical.is_file():
        return canonical
    # Legacy / odd save: accept stored path only if it stays under root.
    for s in stills:
        if str(s.get("id") or "") != wanted:
            continue
        raw = str(s.get("path") or "").strip()
        if not raw:
            break
        try:
            resolved = Path(raw).resolve()
            resolved.relative_to(root)
        except (OSError, ValueError):
            break
        if resolved.is_file():
            return resolved
        break
    return None


def annotate_still(
    session_id: str,
    still_id: str,
    annotation: str,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Human annotate-still — text stored locally with the opt-in still."""
    session = _load(session_id, level)
    if session is None:
        return {
            "status": "error",
            "error": "session_not_found",
            "message": f"No manual session {session_id!r}.",
        }
    if session.get("status") not in {"open", "ended"}:
        return {
            "status": "error",
            "error": "not_annotatable",
            "message": "Annotate is only available for open or ended sessions.",
        }
    text = _normalize_annotation(annotation)
    if not text:
        return {
            "status": "error",
            "error": "annotation_required",
            "message": "Annotation text is required.",
        }
    wanted = str(still_id or "").strip()
    found = None
    for still in session.get("stills") or []:
        if str(still.get("id")) == wanted:
            still["annotation"] = text
            still["annotated"] = True
            still["annotated_at"] = _utcnow()
            found = still
            break
    if found is None:
        return {
            "status": "error",
            "error": "still_not_found",
            "message": f"No still {still_id!r} on this session.",
        }
    _save(session)
    return {
        "status": "ok",
        "still": found,
        "session": _public(session),
        "message": "Annotation stored with still (local only).",
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
    assist_result: dict[str, Any] = {"assist_status": "off"}
    if session.get("agent_assist"):
        from plans.manual_assist import generate_assist_drafts

        assist_result = generate_assist_drafts(session)
    else:
        session["assist_drafts"] = []
        session["assist_status"] = "off"
        session["assist_message"] = ""
    _save(session)
    lvl = str(session["level"])
    if _OPEN_BY_LEVEL.get(lvl) == session_id:
        _OPEN_BY_LEVEL.pop(lvl, None)
    msg = "Session ended — review the draft. Propose then confirm for Jira."
    if session.get("agent_assist"):
        extra = str(assist_result.get("message") or session.get("assist_message") or "")
        if extra:
            msg = f"{msg} {extra}"
    return {
        "status": "ok",
        "message": msg,
        "session": _public(session),
        "review": _review_payload(session),
        "assist": {
            "status": session.get("assist_status"),
            "message": session.get("assist_message") or "",
            "draft_count": len(session.get("assist_drafts") or []),
        },
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
        "assist_status": str(
            session.get("assist_status")
            or ("off" if not session.get("agent_assist") else "pending")
        ),
        "assist_message": str(session.get("assist_message") or ""),
        "agent_assist": bool(session.get("agent_assist")),
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


def _build_defect_packet(
    session: dict[str, Any],
    *,
    note_lines: list[str],
    annotation_lines: list[str],
    evidence_paths: list[str],
    page_ctx_public: dict[str, Any],
    failure_class: str,
    explicit_bug_pick: bool,
    redaction_hits: int,
) -> dict[str, Any]:
    """FR-JIRA-4 defect packet shape for Manual Propose Bug (KAN-293)."""
    page_url = str(page_ctx_public.get("url") or "")
    page_title = str(page_ctx_public.get("title") or "")
    env_bits = [f"Security level: {session.get('level')}"]
    if page_ctx_public.get("known"):
        env_bits.append(f"AUT URL: {page_url or '(none)'}")
        env_bits.append(f"AUT title: {page_title or '(none)'}")
    replication = [
        f"Start manual session with charter: {session.get('charter')}",
    ]
    if page_ctx_public.get("known"):
        replication.append(f"AUT page: {page_title or page_url}")
    if note_lines:
        replication.extend(f"Note: {t}" for t in note_lines[:8])
    else:
        replication.append("Reproduce from session notes.")
    replication.extend(f"Still annotation: {a}" for a in annotation_lines[:4])
    return {
        "symptom": (session.get("charter") or "Manual session finding")[:200],
        "expected": "Behaviour matches charter / acceptance criteria.",
        "actual": "\n".join(note_lines)[:2000] or "(no notes selected)",
        "environment": " | ".join(env_bits),
        "replication_steps": replication,
        "evidence_paths": evidence_paths,
        "failure_class": "product_bug" if explicit_bug_pick else failure_class,
        "selected_failure_class": failure_class,
        "explicit_bug_pick": bool(explicit_bug_pick),
        "classification": "product_bug",
        "jira_key": session.get("jira_story_key") or "",
        "confirm_required": True,
        "page_context": page_ctx_public,
        "redaction_hits": redaction_hits,
    }


def propose(
    session_id: str,
    kind: str,
    *,
    note_ids: list[str] | None = None,
    still_ids: list[str] | None = None,
    failure_class: str = "product_bug",
    explicit_bug: bool = False,
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
    fc = (failure_class or "product_bug").strip().lower().replace(" ", "_")
    if fc not in _FAILURE_CLASSES or not fc:
        fc = "product_bug"
    explicit = bool(explicit_bug)

    proposal_id = _new_id("pr")
    payload: dict[str, Any] = {
        "id": proposal_id,
        "kind": kind_key,
        "created_at": _utcnow(),
        "state": "pending_review",
        "confirm_required": kind_key in {"create_bug", "comment_on_story"},
        "jira_written": False,
        "issue_key": None,
        "failure_class": fc,
        "explicit_bug_pick": explicit,
    }

    # E3 — redact secrets in notes / page context / still annotations before propose.
    redaction_hits = 0
    note_lines: list[str] = []
    for n in notes:
        cleaned, hits = _redact_str(str(n.get("text") or ""))
        redaction_hits += hits
        note_lines.append(cleaned)

    page_ctx = _normalize_page_context(session.get("page_context"))
    page_url, u_hits = _redact_str(page_ctx.get("url") or "")
    page_title, t_hits = _redact_str(page_ctx.get("title") or "")
    redaction_hits += u_hits + t_hits
    page_ctx_public = {
        "known": bool(page_ctx.get("known")),
        "url": page_url,
        "title": page_title,
        "source": page_ctx.get("source") or "",
        "keylog": False,
    }
    payload["page_context"] = page_ctx_public

    annotation_lines: list[str] = []
    for s in stills:
        ann = str(s.get("annotation") or "").strip()
        if not ann:
            continue
        cleaned, hits = _redact_str(ann)
        redaction_hits += hits
        annotation_lines.append(cleaned)

    evidence_paths = [str(s.get("path") or "") for s in stills if s.get("path")]
    payload["redaction_hits"] = redaction_hits
    payload["e3_redaction"] = True

    if kind_key == "create_bug":
        if fc != "product_bug" and not explicit:
            return {
                "status": "error",
                "error": "product_bug_only",
                "failure_class": fc,
                "redirect_kinds": list(_REDIRECT_KINDS),
                "message": (
                    f"Create Bug is blocked for failure class {fc!r} (FR-HEAL-4). "
                    "Choose Comment, local case note, or step preview — "
                    "or tick File as Bug to file explicitly."
                ),
            }
        packet = _build_defect_packet(
            session,
            note_lines=note_lines,
            annotation_lines=annotation_lines,
            evidence_paths=evidence_paths,
            page_ctx_public=page_ctx_public,
            failure_class=fc,
            explicit_bug_pick=explicit and fc != "product_bug",
            redaction_hits=redaction_hits,
        )
        payload["packet"] = packet
        payload["explicit_bug_pick"] = bool(packet.get("explicit_bug_pick"))
        payload["message"] = (
            "Preview only — Confirm writes a Jira Bug (FR-JIRA-5); Cancel writes nothing."
        )

    elif kind_key == "comment_on_story":
        story = session.get("jira_story_key") or ""
        if not story:
            return {
                "status": "error",
                "error": "story_required",
                "message": "Comment on story needs a linked Jira story key.",
            }
        body_parts = [
            f"Manual session {session.get('id')} — {session.get('charter')}",
            f"Failure class: {fc}",
            "",
        ]
        if page_ctx_public.get("known"):
            body_parts.append(f"AUT: {page_title} — {page_url}".strip(" —"))
            body_parts.append("")
        body_parts.extend(note_lines)
        if annotation_lines:
            body_parts.append("")
            body_parts.extend(f"Still annotation: {a}" for a in annotation_lines)
        body = "\n".join(body_parts)[:4000]
        payload["comment"] = {"issue_key": story, "body": body}
        payload["message"] = (
            "Preview only — Confirm posts the Jira comment (FR-JIRA-5); Cancel writes nothing."
        )

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
            "failure_class": fc,
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
            "failure_class": fc,
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
        "redaction_hits": redaction_hits,
    }


def _jira_session_key(session_id: str) -> str:
    return f"manual:{session_id}"


async def _execute_jira_create_bug(
    session_id: str, packet: dict[str, Any]
) -> dict[str, Any]:
    from plugins.jira_plugin import create_bug, resolve_create

    jira_sid = _jira_session_key(session_id)
    preview = await create_bug(
        summary=str(packet.get("symptom") or "")[:255] or None,
        symptom=str(packet.get("symptom") or "") or None,
        expected=str(packet.get("expected") or "") or None,
        actual=str(packet.get("actual") or "") or None,
        environment=str(packet.get("environment") or "") or None,
        replication_steps=list(packet.get("replication_steps") or []),
        evidence_paths=list(packet.get("evidence_paths") or []),
        classification="product_bug",
        relates_to=str(packet.get("jira_key") or "") or None,
        session_id=jira_sid,
    )
    if preview.get("status") != "confirmation_required":
        return preview
    return await resolve_create(jira_sid, "confirm") or {
        "status": "error",
        "message": "Confirm resolve returned nothing.",
    }


async def _execute_jira_comment(
    session_id: str, comment: dict[str, Any]
) -> dict[str, Any]:
    from plugins.jira_plugin import add_comment, resolve_create

    jira_sid = _jira_session_key(session_id)
    preview = await add_comment(
        issue_key=str(comment.get("issue_key") or ""),
        body=str(comment.get("body") or ""),
        session_id=jira_sid,
    )
    if preview.get("status") != "confirmation_required":
        return preview
    return await resolve_create(jira_sid, "confirm") or {
        "status": "error",
        "message": "Confirm resolve returned nothing.",
    }


async def confirm_proposal(
    session_id: str,
    proposal_id: str,
    *,
    confirm: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Two-step confirm for Jira side effects; Cancel writes nothing.

    Confirm on create_bug / comment_on_story performs the FR-JIRA-5 write via
    create_bug/add_comment + resolve (Manual Confirm is the human gate) and
    appends jira_write_audit on success (KAN-293).
    """
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
            "writes_jira": bool(target.get("jira_written")),
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
        packet = target.get("packet") or {}
        outcome = await _execute_jira_create_bug(session_id, packet)
        if outcome.get("status") not in {"created", "ok"}:
            target["state"] = "pending_review"
            target["ready_for_jira"] = True
            target["jira_written"] = False
            target["last_write_error"] = outcome.get("message") or outcome.get("error")
            _save(session)
            return {
                "status": "error",
                "error": outcome.get("error") or "jira_write_failed",
                "message": outcome.get("message")
                or "Jira Bug write failed — proposal left pending; nothing audited as success.",
                "proposal": target,
                "writes_jira": False,
                "jira_outcome": outcome,
                "session": _public(session),
            }
        issue_key = str(outcome.get("key") or outcome.get("issue_key") or "")
        target["state"] = "submitted"
        target["jira_written"] = True
        target["ready_for_jira"] = False
        target["issue_key"] = issue_key
        target["submitted_at"] = _utcnow()
        _save(session)
        return {
            "status": "ok",
            "message": f"Jira Bug created ({issue_key or 'key pending'}) — write audited.",
            "proposal": target,
            "writes_jira": True,
            "issue_key": issue_key,
            "jira_outcome": outcome,
            "session": _public(session),
        }

    if kind == "comment_on_story":
        comment = target.get("comment") or {}
        outcome = await _execute_jira_comment(session_id, comment)
        if outcome.get("status") not in {"commented", "ok", "created"}:
            target["state"] = "pending_review"
            target["ready_for_jira"] = True
            target["jira_written"] = False
            target["last_write_error"] = outcome.get("message") or outcome.get("error")
            _save(session)
            return {
                "status": "error",
                "error": outcome.get("error") or "jira_write_failed",
                "message": outcome.get("message")
                or "Jira comment failed — proposal left pending; nothing audited as success.",
                "proposal": target,
                "writes_jira": False,
                "jira_outcome": outcome,
                "session": _public(session),
            }
        issue_key = str(
            outcome.get("issue_key") or comment.get("issue_key") or ""
        )
        target["state"] = "submitted"
        target["jira_written"] = True
        target["ready_for_jira"] = False
        target["issue_key"] = issue_key
        target["submitted_at"] = _utcnow()
        _save(session)
        return {
            "status": "ok",
            "message": f"Jira comment posted on {issue_key or 'issue'} — write audited.",
            "proposal": target,
            "writes_jira": True,
            "issue_key": issue_key,
            "jira_outcome": outcome,
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
        # KAN-285 — honest local Ollama assist (no note-echo AI)
        "honest_assist_drafts": True,
        "assist_drafts_at_end": True,
        "assist_never_silent_jira": True,
        # KAN-287 — window/monitor snap (free-region kept)
        "window_monitor_snap": True,
        "frame_snap_modes": ["free", "monitor", "window"],
        # KAN-293 — propose/confirm harden
        "propose_harden": True,
        "failure_class_gates_create_bug": True,
        "explicit_bug_pick": True,
        "confirm_dock_outside_scroll": True,
        "confirm_writes_jira_with_audit": True,
        "failure_classes": [
            "product_bug",
            "test_defect",
            "environment",
            "known_issue",
        ],
    }
