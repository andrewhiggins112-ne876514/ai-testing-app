"""Document upload privacy registry (KAN-193 / E1 / FR-SEC-2 / FR-LEARN-5).

Uploads are stored level-locally under the app data directory. Each record keeps
file name, time, security level, and consent. Bodies stay out of exports unless
the report ``documents`` section is enabled. No cloud sync.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def uploads_root(level: str | None = None) -> Path:
    from settings.store import app_data_dir, get_security_level

    lvl = (level or get_security_level()).strip().upper()
    return app_data_dir() / "uploads" / lvl


def _index_path(level: str | None = None) -> Path:
    return uploads_root(level) / "index.json"


def _bodies_dir(level: str | None = None) -> Path:
    return uploads_root(level) / "bodies"


def _read_index(level: str | None = None) -> List[Dict[str, Any]]:
    path = _index_path(level)
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("id"):
            out.append(item)
    return out


def _write_index(items: List[Dict[str, Any]], level: str | None = None) -> None:
    root = uploads_root(level)
    root.mkdir(parents=True, exist_ok=True)
    path = _index_path(level)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _public_record(item: Dict[str, Any], *, include_body: bool = False) -> Dict[str, Any]:
    body = ""
    if include_body:
        body = str(item.get("body") or "")
        if not body and item.get("body_file"):
            body = read_upload_body(str(item.get("id") or ""), level=str(item.get("security_level") or "") or None) or ""
    return {
        "id": str(item.get("id") or ""),
        "filename": str(item.get("filename") or ""),
        "uploaded_at": str(item.get("uploaded_at") or ""),
        "security_level": str(item.get("security_level") or ""),
        "consent": bool(item.get("consent")),
        "consent_at": item.get("consent_at"),
        "bytes": int(item.get("bytes") or 0),
        "has_body": bool(item.get("has_body")),
        "cloud_sync": False,
        **({"body": body} if include_body else {}),
    }


def record_upload(
    *,
    filename: str,
    text: str,
    consent: bool = False,
    level: str | None = None,
) -> Dict[str, Any]:
    """Persist an uploaded document body + metadata for the active level."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    name = (filename or "upload.txt").strip() or "upload.txt"
    # Avoid path separators in stored name.
    name = Path(name).name[:200]
    body = str(text or "")
    upload_id = str(uuid.uuid4())
    bodies = _bodies_dir(lvl)
    bodies.mkdir(parents=True, exist_ok=True)
    body_path = bodies / f"{upload_id}.txt"
    body_path.write_text(body, encoding="utf-8")
    stamp = _now_iso()
    record = {
        "id": upload_id,
        "filename": name,
        "uploaded_at": stamp,
        "security_level": lvl,
        "consent": bool(consent),
        "consent_at": stamp if consent else None,
        "bytes": len(body.encode("utf-8")),
        "has_body": True,
        "body_file": body_path.name,
        "cloud_sync": False,
    }
    items = _read_index(lvl)
    items.append(record)
    _write_index(items, lvl)
    return _public_record(record)


def set_upload_consent(
    upload_id: str,
    *,
    consent: bool = True,
    level: str | None = None,
) -> Dict[str, Any]:
    """Mark whether the user consented to keep/extracted-data storage for this upload."""
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    uid = str(upload_id or "").strip()
    if not uid:
        return {"status": "error", "message": "upload_id required"}
    items = _read_index(lvl)
    found = None
    for item in items:
        if str(item.get("id")) == uid:
            item["consent"] = bool(consent)
            item["consent_at"] = _now_iso() if consent else None
            found = item
            break
    if found is None:
        return {"status": "error", "message": "upload not found", "upload_id": uid}
    _write_index(items, lvl)
    return {"status": "ok", "upload": _public_record(found)}


def read_upload_body(upload_id: str, *, level: str | None = None) -> Optional[str]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    uid = str(upload_id or "").strip()
    if not uid or "/" in uid or "\\" in uid or ".." in uid:
        return None
    path = _bodies_dir(lvl) / f"{uid}.txt"
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def list_uploads(
    *,
    level: str | None = None,
    include_bodies: bool = False,
) -> Dict[str, Any]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    items = [_public_record(item, include_body=include_bodies) for item in _read_index(lvl)]
    return {
        "status": "ok",
        "security_level": lvl,
        "uploads": items,
        "count": len(items),
        "cloud_sync": False,
        "bodies_included": bool(include_bodies),
        "message": (
            "Local uploads only. Bodies omitted from list unless requested; "
            "exports omit bodies unless the documents report section is on."
        ),
    }


def uploads_for_export(*, level: str | None = None, include_bodies: bool = False) -> List[Dict[str, Any]]:
    """Snapshot for report sections — never syncs to cloud."""
    return list(list_uploads(level=level, include_bodies=include_bodies).get("uploads") or [])


def uploads_inventory() -> Dict[str, Any]:
    """Aggregate stats across level folders for privacy inventory."""
    from settings.store import app_data_dir

    root = app_data_dir() / "uploads"
    if not root.exists():
        return {"exists": False, "path": str(root), "bytes": 0, "items": 0}
    total = 0
    items = 0
    for child in root.rglob("*"):
        if child.is_file():
            items += 1
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return {"exists": True, "path": str(root), "bytes": total, "items": items}


def wipe_uploads() -> Dict[str, Any]:
    """Remove all level upload trees; recreate empty uploads root."""
    import shutil

    from settings.store import app_data_dir

    root = app_data_dir() / "uploads"
    resolved = root.resolve()
    app_root = app_data_dir().resolve()
    if resolved != app_root and app_root not in resolved.parents:
        raise RuntimeError(f"refusing to wipe path outside app data: {resolved}")
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        return {"path": str(root), "deleted": False, "reason": "missing", "kind": "directory"}
    shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return {"path": str(root), "deleted": True, "kind": "directory"}
