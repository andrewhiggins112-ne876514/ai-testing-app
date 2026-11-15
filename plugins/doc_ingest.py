"""Document ingestion → settings proposals (FR-LEARN-*, FR-SET-2).

Parses uploaded/pasted specs as untrusted input. Extracts environment hints and
test ideas, presents a settings diff, and writes nothing until the user confirms.
"""
from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from settings.store import _hidden, apply_settings_diff, load_settings

_CONFIRM_WORDS = {"yes", "confirm"}
_DECLINE_WORDS = {"no", "decline", "cancel", "reject"}
_PENDING: Dict[str, Dict[str, Any]] = {}
_BY_ID: Dict[str, Dict[str, Any]] = {}
_CONFIRM_TTL = 300.0

# Keys that may be proposed from documents (never silent write).
_PROPOSABLE = frozenset({
    "jira_url",
    "jira_email",
    "jira_api_token",
    "jira_project",
    "target_url",
    "target_app_path",
    "api_endpoint",
})

_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
_EXE = re.compile(
    r"(?:[A-Za-z]:\\|\\\\)[^\s\"']+\.exe|[^\s\"']+\.exe",
    re.I,
)
_PROJECT_LABEL = re.compile(
    r"(?:jira\s+)?project(?:\s+key)?\s*[:=]\s*([A-Za-z][A-Za-z0-9_]{0,9})",
    re.I,
)
_AMQP = re.compile(r"(?:amqp|amqps|wss?)://[^\s<>\"')\]]+", re.I)
_CRED_LINE = re.compile(
    r"(?im)^\s*(?:jira[_\s-]?)?(api[_\s-]?token|token|password|secret|credential)\s*[:=]\s*(\S+)\s*$"
)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_HEADING = re.compile(r"(?m)^#{1,3}\s+(.+)$")
_GWT = re.compile(r"(?im)^\s*(?:given|when|then|and)\s+.+")
_MUST = re.compile(r"(?im)^\s*[-*]\s+.*\b(?:must|should|shall)\b.+")


def _strip_url(url: str) -> str:
    return url.rstrip(".,;:)")


def _pdf_baseline_text(data: bytes) -> str:
    """Best-effort text from simple PDFs without an extra dependency."""
    chunks: List[str] = []
    # Parenthesized string literals (common in content streams).
    for match in re.finditer(rb"\((?:\\.|[^\\)]){1,200}\)", data):
        raw = match.group(0)[1:-1]
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError:
            continue
        text = (
            text.replace("\\n", "\n")
            .replace("\\r", "")
            .replace("\\t", "\t")
            .replace("\\(", "(")
            .replace("\\)", ")")
        )
        if any(ch.isalpha() for ch in text):
            chunks.append(text)
    # UTF-16BE hex strings <FEFF...>
    for match in re.finditer(rb"<([0-9A-Fa-f\s]{8,})>", data):
        hex_body = re.sub(rb"\s+", b"", match.group(1))
        if len(hex_body) % 2:
            continue
        try:
            decoded = bytes.fromhex(hex_body.decode("ascii"))
            if decoded.startswith(b"\xfe\xff"):
                text = decoded[2:].decode("utf-16-be", errors="ignore")
            else:
                text = decoded.decode("latin-1", errors="ignore")
        except (ValueError, UnicodeError):
            continue
        if any(ch.isalpha() for ch in text):
            chunks.append(text)
    return "\n".join(chunks).strip()


def read_document(
    *,
    text: Optional[str] = None,
    path: Optional[str] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Load document bytes/text. Treats content as untrusted (FR-SEC-4)."""
    if text is not None and str(text).strip():
        name = filename or "paste.md"
        return {
            "status": "ok",
            "filename": name,
            "text": str(text),
            "format": _format_from_name(name),
        }
    if not path:
        return {"status": "error", "message": "Provide document text or a local file path."}
    file_path = Path(path)
    if not file_path.is_file():
        return {"status": "error", "message": "File not found."}
    suffix = file_path.suffix.lower()
    name = filename or file_path.name
    if suffix in {".md", ".markdown", ".txt", ".text", ".rst"}:
        raw = file_path.read_text(encoding="utf-8-sig", errors="replace")
        return {"status": "ok", "filename": name, "text": raw, "format": "markdown" if "md" in suffix else "text"}
    if suffix == ".pdf":
        data = file_path.read_bytes()
        extracted = _pdf_baseline_text(data)
        if not extracted:
            return {
                "status": "error",
                "message": "Could not extract text from this PDF (baseline extractor). Paste Markdown/text instead.",
            }
        return {"status": "ok", "filename": name, "text": extracted, "format": "pdf"}
    return {
        "status": "error",
        "message": "Unsupported format. Use Markdown, text, or a simple text PDF.",
    }


def _format_from_name(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith((".md", ".markdown")):
        return "markdown"
    return "text"


def extract_test_ideas(text: str, limit: int = 20) -> List[str]:
    ideas: List[str] = []
    seen = set()
    for pattern in (_GWT, _MUST, _HEADING):
        for match in pattern.finditer(text or ""):
            line = " ".join(match.group(0).split())
            if len(line) < 8 or line.casefold() in seen:
                continue
            seen.add(line.casefold())
            ideas.append(line[:240])
            if len(ideas) >= limit:
                return ideas
    return ideas


def extract_settings_proposals(text: str) -> Dict[str, Any]:
    """Heuristic extraction of settings keys from untrusted document text."""
    proposed: Dict[str, Any] = {}
    body = text or ""

    urls = [_strip_url(u) for u in _URL.findall(body)]
    for url in urls:
        lower = url.lower()
        if "atlassian.net" in lower or "/jira" in lower or lower.rstrip("/").endswith("jira"):
            proposed.setdefault("jira_url", url.rstrip("/"))
        elif lower.startswith(("amqp://", "amqps://", "ws://", "wss://")):
            proposed.setdefault("api_endpoint", url)
        else:
            proposed.setdefault("target_url", url)

    for match in _AMQP.finditer(body):
        proposed.setdefault("api_endpoint", _strip_url(match.group(0)))

    for match in _EXE.finditer(body):
        proposed.setdefault("target_app_path", match.group(0))

    proj = _PROJECT_LABEL.search(body)
    if proj:
        proposed["jira_project"] = proj.group(1).upper()

    for match in _CRED_LINE.finditer(body):
        label = match.group(1).lower().replace(" ", "_").replace("-", "_")
        value = match.group(2).strip().strip("\"'")
        if "token" in label or label == "api_token":
            proposed["jira_api_token"] = value
        elif label in {"password", "secret", "credential"}:
            # Map generic secrets to the Jira token slot only when labelled jira*; else skip silent guess.
            if match.group(0).lower().lstrip().startswith("jira"):
                proposed["jira_api_token"] = value

    # Prefer an email near "jira" wording.
    emails = _EMAIL.findall(body)
    if emails:
        jira_block = re.search(r"(?is)jira.{0,200}", body)
        chosen = emails[0]
        if jira_block:
            near = _EMAIL.findall(jira_block.group(0))
            if near:
                chosen = near[0]
        proposed.setdefault("jira_email", chosen)

    return {k: v for k, v in proposed.items() if k in _PROPOSABLE and str(v).strip()}


def _diff_against_store(proposed: Dict[str, Any]) -> Dict[str, Any]:
    current = load_settings()
    diff: Dict[str, Any] = {}
    for key, value in proposed.items():
        old = current.get(key, "")
        if str(old) == str(value):
            continue
        diff[key] = {
            "from": _hidden(key, old),
            "to": _hidden(key, value),
            "value": value,
        }
    return diff


def _public_diff(diff: Dict[str, Any]) -> Dict[str, Any]:
    return {k: {"from": v["from"], "to": v["to"]} for k, v in diff.items()}


def _store_pending(
    session_id: str,
    *,
    filename: str,
    format_name: str,
    diff: Dict[str, Any],
    test_ideas: List[str],
) -> Dict[str, Any]:
    proposal_id = str(uuid.uuid4())
    record = {
        "kind": "doc_ingest",
        "proposal_id": proposal_id,
        "session_id": str(session_id),
        "filename": filename,
        "format": format_name,
        "diff": diff,
        "test_ideas": test_ideas,
        "expires": time.monotonic() + _CONFIRM_TTL,
    }
    _PENDING[str(session_id)] = record
    _BY_ID[proposal_id] = record
    return {
        "status": "proposal",
        "proposal_id": proposal_id,
        "filename": filename,
        "format": format_name,
        "settings_diff": _public_diff(diff),
        "test_ideas": test_ideas,
        "note": (
            "Nothing was written. Explicit consent required (GDPR / FR-SEC-2): "
            "reply yes/confirm to store extracted settings, or decline to discard."
        ),
        "consent_required": True,
    }


def ingest_document(
    *,
    text: Optional[str] = None,
    path: Optional[str] = None,
    filename: Optional[str] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    from agent.prompt_guard import injection_meta, redact_secrets_for_model, wrap_untrusted

    loaded = read_document(text=text, path=path, filename=filename)
    if loaded.get("status") != "ok":
        return loaded
    body = loaded["text"]
    meta = injection_meta(body)
    excerpt = wrap_untrusted("document", redact_secrets_for_model(body[:2000]))
    proposed = extract_settings_proposals(body)
    ideas = extract_test_ideas(body)
    diff = _diff_against_store(proposed)
    if not diff and not ideas:
        return {
            "status": "empty",
            "filename": loaded["filename"],
            "message": "No settings hints or test ideas found in the document.",
            **meta,
            "excerpt_for_model": excerpt,
        }
    if not diff:
        return {
            "status": "ideas_only",
            "filename": loaded["filename"],
            "format": loaded["format"],
            "settings_diff": {},
            "test_ideas": ideas,
            "note": "No settings changes proposed; settings file unchanged.",
            **meta,
            "excerpt_for_model": excerpt,
        }
    result = _store_pending(
        session_id,
        filename=loaded["filename"],
        format_name=loaded["format"],
        diff=diff,
        test_ideas=ideas,
    )
    result.update(meta)
    result["excerpt_for_model"] = excerpt
    return result


def _get_record(proposal_id: Optional[str], session_id: Optional[str]) -> Optional[Dict[str, Any]]:
    record = None
    if proposal_id:
        record = _BY_ID.get(str(proposal_id))
    elif session_id is not None:
        record = _PENDING.get(str(session_id))
    if not record:
        return None
    if time.monotonic() > float(record.get("expires") or 0):
        _drop(record)
        return None
    return record


def _drop(record: Dict[str, Any]) -> None:
    pid = record.get("proposal_id")
    sid = record.get("session_id")
    if pid:
        _BY_ID.pop(str(pid), None)
    if sid is not None and _PENDING.get(str(sid)) is record:
        _PENDING.pop(str(sid), None)


def decline_proposal(
    proposal_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    record = _get_record(proposal_id, session_id)
    if not record:
        return {"status": "expired", "message": "No pending document proposal."}
    _drop(record)
    return {
        "status": "declined",
        "proposal_id": record.get("proposal_id"),
        "note": "Settings file unchanged.",
    }


def apply_proposal(
    proposal_id: Optional[str] = None,
    *,
    session_id: Optional[str] = None,
    keys: Optional[Sequence[str]] = None,
    confirm: bool = False,
) -> Dict[str, Any]:
    record = _get_record(proposal_id, session_id)
    if not record:
        return {"status": "expired", "message": "No pending document proposal. Ingest the document again."}
    diff: Dict[str, Any] = record.get("diff") or {}
    if keys is None:
        selected = list(diff.keys())
    else:
        selected = [k for k in keys if k in diff and k in _PROPOSABLE]
    if not selected:
        return {"status": "error", "message": "No approved keys to write."}
    payload = {k: diff[k]["value"] for k in selected}
    shown = {k: _hidden(k, payload[k]) for k in selected}
    if not confirm:
        return {
            "status": "confirmation_required",
            "proposal_id": record.get("proposal_id"),
            "proposed": shown,
            "note": (
                "Explicit consent required before storing extracted data. "
                "Pass confirm=true or reply yes to write these keys."
            ),
            "consent_required": True,
        }
    result = apply_settings_diff(payload, confirm=True)
    _drop(record)
    return {
        "status": "applied",
        "proposal_id": record.get("proposal_id"),
        "updated": result.get("updated") or shown,
        "skipped": [k for k in diff if k not in selected],
    }


def resolve_doc_ingest(session_id: str, user_message: str) -> Optional[Dict[str, Any]]:
    """Chat confirm/decline for the latest pending proposal on this session."""
    record = _PENDING.get(str(session_id))
    if not record or record.get("kind") != "doc_ingest":
        return None
    if time.monotonic() > float(record.get("expires") or 0):
        _drop(record)
        return {"status": "expired", "message": "That document proposal expired. Ingest again."}
    word = (user_message or "").strip().casefold()
    if word in _DECLINE_WORDS:
        return decline_proposal(session_id=session_id)
    if word not in _CONFIRM_WORDS:
        return {"status": "cancelled"}
    return apply_proposal(session_id=session_id, confirm=True)


def clear_pending() -> None:
    """Test helper."""
    _PENDING.clear()
    _BY_ID.clear()
