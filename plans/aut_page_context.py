"""Known headed AUT page URL/title for Manual evidence (KAN-289 / FR-MAN-1).

Only stores context the lab already knows (Playwright pause / explicit set).
Never scrapes arbitrary windows or keylogs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_URL_MAX = 2000
_TITLE_MAX = 500

# In-memory per security level — cleared when the headed browser closes.
_CONTEXT_BY_LEVEL: dict[str, dict[str, Any]] = {}


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _level(level: str | None = None) -> str:
    if level:
        return str(level).strip().upper() or "OFFICIAL"
    try:
        from settings.store import get_security_level

        return str(get_security_level() or "OFFICIAL").strip().upper()
    except Exception:
        return "OFFICIAL"


def reset_page_context_cache() -> None:
    """Test helper — drop all known AUT page contexts."""
    _CONTEXT_BY_LEVEL.clear()


def clear_page_context(*, level: str | None = None) -> dict[str, Any]:
    """Forget known AUT page context for a level (browser closed / left)."""
    lvl = _level(level)
    _CONTEXT_BY_LEVEL.pop(lvl, None)
    return public_page_context(level=lvl)


def set_page_context(
    url: str = "",
    title: str = "",
    *,
    source: str = "playwright",
    level: str | None = None,
) -> dict[str, Any]:
    """Publish a known headed AUT page URL + document title for this level."""
    lvl = _level(level)
    clean_url = str(url or "").strip()[:_URL_MAX]
    clean_title = str(title or "").strip()[:_TITLE_MAX]
    src = str(source or "playwright").strip()[:64] or "playwright"
    if not clean_url and not clean_title:
        return clear_page_context(level=lvl)
    _CONTEXT_BY_LEVEL[lvl] = {
        "known": True,
        "url": clean_url,
        "title": clean_title,
        "source": src,
        "updated_at": _utcnow(),
        "keylog": False,
    }
    return public_page_context(level=lvl)


def get_page_context(*, level: str | None = None) -> dict[str, Any] | None:
    """Return raw known context dict, or None when unknown."""
    lvl = _level(level)
    raw = _CONTEXT_BY_LEVEL.get(lvl)
    if not raw or not raw.get("known"):
        return None
    return dict(raw)


def public_page_context(*, level: str | None = None) -> dict[str, Any]:
    """Stable API shape — always includes known=false when empty."""
    raw = get_page_context(level=level)
    if raw is None:
        return {
            "known": False,
            "url": "",
            "title": "",
            "source": "",
            "updated_at": None,
            "keylog": False,
        }
    return {
        "known": True,
        "url": str(raw.get("url") or ""),
        "title": str(raw.get("title") or ""),
        "source": str(raw.get("source") or ""),
        "updated_at": raw.get("updated_at"),
        "keylog": False,
    }
