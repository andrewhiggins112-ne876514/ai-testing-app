"""Redact secrets in evidence and exports (KAN-197 / E3 / FR-SEC-5 + FR-REP-3).

Known credential patterns and stored token values are replaced before
JSON/Markdown export and evidence-index writes. Screenshots cannot be
OCR-redacted automatically — exports warn when a screenshot path is present.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

PLACEHOLDER = "[REDACTED]"
_MIN_STORED_LEN = 8

# Label=value style secrets (keep the label, drop the value).
_LABELED = re.compile(
    r"(?i)\b((?:api[_-]?token|password|secret|authorization|credential|"
    r"jira[_\s-]?(?:api[_\s-]?)?token|target[_\s-]?secret)\s*[:=]\s*)\S+"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+=/]+")
# Common pasted Atlassian/API token shapes (long opaque strings after Token).
_TOKEN_WORD = re.compile(
    r"(?i)\b(token|api[_-]?key)\b(\s*[:=]\s*|\s+)([A-Za-z0-9_\-]{16,})"
)

_SCREENSHOT_WARN = (
    "Screenshot present: pixels are not OCR-redacted automatically. "
    "Review the image before sharing; text fields in this export were redacted."
)


def _stored_secret_values() -> list[str]:
    """Exact values from the active level store — never returned to callers as-is."""
    try:
        from settings.store import _load_credentials, get_security_level

        creds = _load_credentials(get_security_level())
    except Exception:
        return []
    values: list[str] = []
    for key in ("jira_api_token", "target_secret"):
        raw = str(creds.get(key) or "").strip()
        if len(raw) >= _MIN_STORED_LEN:
            values.append(raw)
    # Dedupe longest-first so overlapping substrings redact fully.
    values.sort(key=len, reverse=True)
    return values


def redact_text(text: str, *, extra_values: list[str] | None = None) -> tuple[str, int]:
    """Return (redacted_text, hit_count)."""
    if text is None:
        return "", 0
    original = str(text)
    if not original:
        return "", 0
    hits = 0
    out = original

    def _sub_count(pattern: re.Pattern[str], repl: str, source: str) -> tuple[str, int]:
        replaced, n = pattern.subn(repl, source)
        return replaced, n

    out, n = _sub_count(_LABELED, rf"\1{PLACEHOLDER}", out)
    hits += n
    out, n = _sub_count(_BEARER, f"Bearer {PLACEHOLDER}", out)
    hits += n
    out, n = _sub_count(_TOKEN_WORD, rf"\1\2{PLACEHOLDER}", out)
    hits += n

    secrets = list(extra_values or []) + _stored_secret_values()
    seen: set[str] = set()
    for secret in secrets:
        if not secret or secret in seen:
            continue
        seen.add(secret)
        if secret not in out:
            continue
        count = out.count(secret)
        out = out.replace(secret, PLACEHOLDER)
        hits += count
    return out, hits


def redact_value(value: Any, *, extra_values: list[str] | None = None) -> tuple[Any, int]:
    """Recursively redact strings in dict/list structures."""
    if isinstance(value, str):
        return redact_text(value, extra_values=extra_values)
    if isinstance(value, Mapping):
        total = 0
        out: dict[str, Any] = {}
        for key, item in value.items():
            # Never copy secret-looking keys through — replace whole value.
            low = str(key or "").strip().lower()
            if any(
                part in low
                for part in ("token", "password", "secret", "authorization", "credential")
            ) and not low.endswith(("_path", "_status", "_set", "_count", "_hits", "_warning")):
                if item in (None, "", [], {}):
                    out[key] = item
                else:
                    out[key] = PLACEHOLDER
                    total += 1
                continue
            cleaned, n = redact_value(item, extra_values=extra_values)
            out[key] = cleaned
            total += n
        return out, total
    if isinstance(value, list):
        total = 0
        items: list[Any] = []
        for item in value:
            cleaned, n = redact_value(item, extra_values=extra_values)
            items.append(cleaned)
            total += n
        return items, total
    if isinstance(value, tuple):
        cleaned, n = redact_value(list(value), extra_values=extra_values)
        return tuple(cleaned), n
    return value, 0


def has_screenshot_ref(payload: Any) -> bool:
    """True when export/evidence references a screenshot path or kind."""
    if isinstance(payload, str):
        lower = payload.lower()
        return lower.endswith(".png") or lower.endswith(".jpg") or "screenshot" in lower
    if isinstance(payload, Mapping):
        kind = str(payload.get("kind") or "").lower()
        if kind == "screenshot":
            return True
        if payload.get("screenshot"):
            return True
        for key in ("path", "screenshot"):
            if has_screenshot_ref(payload.get(key)):
                return True
        for item in payload.values():
            if has_screenshot_ref(item):
                return True
        return False
    if isinstance(payload, (list, tuple)):
        return any(has_screenshot_ref(item) for item in payload)
    return False


def screenshot_redaction_warning(payload: Any = None) -> str | None:
    """Warn when a screenshot cannot be redacted automatically (OCR out of scope)."""
    if payload is None or has_screenshot_ref(payload):
        return _SCREENSHOT_WARN
    return None


def redact_export_payload(
    payload: Mapping[str, Any] | None,
    *,
    extra_values: list[str] | None = None,
) -> dict[str, Any]:
    """Redact an export payload and attach hit count + screenshot warning meta."""
    body = dict(payload or {})
    cleaned, hits = redact_value(body, extra_values=extra_values)
    if not isinstance(cleaned, dict):
        cleaned = {"value": cleaned}
    warn = screenshot_redaction_warning(body)
    meta = {
        "redaction_hits": int(hits),
        "screenshot_redaction_warning": warn,
        "ocr_redaction": False,
        "patterns_applied": True,
        "stored_tokens_applied": True,
    }
    # Surface hits on summary when present (FR-REP-3 export summary).
    sections = cleaned.get("sections")
    if isinstance(sections, dict):
        summary = sections.get("summary")
        if isinstance(summary, dict):
            summary = dict(summary)
            summary["redaction_hits"] = meta["redaction_hits"]
            if warn:
                summary["screenshot_redaction_warning"] = warn
            sections = dict(sections)
            sections["summary"] = summary
            cleaned["sections"] = sections
    cleaned["redaction"] = meta
    return cleaned


def redact_evidence_index(
    bundle: Mapping[str, Any] | None,
    *,
    extra_values: list[str] | None = None,
) -> dict[str, Any]:
    """Redact an evidence bundle / index dict; attach meta (not a wipe)."""
    body = dict(bundle or {})
    cleaned, hits = redact_value(body, extra_values=extra_values)
    if not isinstance(cleaned, dict):
        cleaned = {"value": cleaned}
    warn = screenshot_redaction_warning(body)
    cleaned["redaction_hits"] = int(hits)
    if warn:
        cleaned["screenshot_redaction_warning"] = warn
    cleaned["ocr_redaction"] = False
    return cleaned


def redaction_status() -> dict[str, Any]:
    """Non-secret policy status for Security / API (never echoes token values)."""
    from settings.store import get_security_level

    try:
        from settings.store import _load_credentials

        creds = _load_credentials(get_security_level())
        stored_set = sum(
            1
            for key in ("jira_api_token", "target_secret")
            if len(str(creds.get(key) or "").strip()) >= _MIN_STORED_LEN
        )
    except Exception:
        stored_set = 0
    return {
        "status": "ok",
        "security_level": get_security_level(),
        "patterns_enabled": True,
        "stored_tokens_enabled": True,
        "stored_secrets_configured": stored_set,
        "placeholder": PLACEHOLDER,
        "ocr_redaction": False,
        "screenshot_warning": _SCREENSHOT_WARN,
        "wipes_secrets": False,
        "message": (
            "Exports and evidence index redact known secret patterns and "
            "stored token values. Screenshots are not OCR-redacted; a warning "
            "is included when a screenshot is present."
        ),
    }
