"""Local contract / mock API responses (KAN-221 / G3 / FR-PLUG-1).

Cases may point at a local fixture under the level-scoped mocks folder.
Mocks are off unless the case selects one — live-endpoint API cases unchanged.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from reports.redact import PLACEHOLDER, redact_text

PLUGIN_NAME = "contract_mock"
_DEFAULT_NAME = "contract_ok.json"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
_BODY_CAP = 800
_JSON_SECRET_KEY = re.compile(
    r'(?i)("(?:password|secret|api[_-]?token|authorization|credential|token)"\s*:\s*")([^"]*)(")'
)


def mocks_dir(level: str | None = None) -> Path:
    """Level-scoped local mock fixtures (never cloud)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "OFFICIAL").strip().upper() or "OFFICIAL"
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    path = Path(base) / "ai_testing_app" / "mocks" / lvl
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_fixture_name() -> str:
    return _DEFAULT_NAME


def ensure_default_fixture(level: str | None = None) -> Path:
    """Create the default contract mock file if missing."""
    folder = mocks_dir(level=level)
    path = folder / _DEFAULT_NAME
    if not path.is_file():
        payload = {
            "http_status": 200,
            "body": {
                "ok": True,
                "contract": "mock",
                "queue": "local",
                "message": "Stable local mock when the real queue is down.",
            },
            "message": "Local contract mock response.",
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def resolve_fixture_path(name: str, *, level: str | None = None) -> Path | None:
    """Resolve a safe fixture name under the mocks dir (no path escape)."""
    raw = (name or "").strip().replace("\\", "/")
    if not raw:
        return None
    # Allow bare name or name.json only — reject absolute / parent paths.
    base = Path(raw).name
    if base != raw and "/" in raw:
        # Only a single path segment allowed.
        if Path(raw).parent.as_posix() not in (".", ""):
            return None
        base = Path(raw).name
    if not _SAFE_NAME.match(base):
        return None
    if not base.lower().endswith(".json"):
        base = f"{base}.json"
        if not _SAFE_NAME.match(base):
            return None
    folder = mocks_dir(level=level)
    path = (folder / base).resolve()
    try:
        path.relative_to(folder.resolve())
    except ValueError:
        return None
    return path


def _redact_body_summary(text: str) -> tuple[str, int]:
    clipped = (text or "")[:_BODY_CAP]
    out, hits = redact_text(clipped)
    out2, n = _JSON_SECRET_KEY.subn(rf"\1{PLACEHOLDER}\3", out)
    return out2, int(hits) + int(n)


def run_mock_response(
    *,
    fixture: str,
    expect_status: Optional[int] = None,
    method: str = "GET",
    level: str | None = None,
) -> dict[str, Any]:
    """Load a local mock fixture; never hits a live endpoint."""
    verb = (method or "GET").strip().upper() or "GET"
    name = (fixture or "").strip()
    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "mock": True,
        "fixture": name or None,
        "endpoint_label": f"mock://{name or '(none)'}",
        "method": verb,
        "http_status": None,
        "body_summary": "",
        "redaction_hits": 0,
        "expect_status": expect_status,
        "transport": "mock",
        "status": "fail",
        "error": None,
        "message": None,
    }
    if not name:
        base.update(
            {
                "status": "fail",
                "error": "No mock fixture selected.",
                "message": "No mock fixture selected.",
            }
        )
        return base

    path = resolve_fixture_path(name, level=level)
    if path is None:
        base.update(
            {
                "status": "fail",
                "error": f"Invalid mock fixture name: {name[:80]}",
                "message": f"Invalid mock fixture name: {name[:80]}",
            }
        )
        return base
    if not path.is_file():
        base.update(
            {
                "status": "fail",
                "error": f"Mock fixture not found: {path.name}",
                "message": f"Mock fixture not found: {path.name}",
                "fixture": path.name,
            }
        )
        return base

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base.update(
            {
                "status": "fail",
                "error": f"Mock fixture unreadable: {exc}"[:300],
                "message": f"Mock fixture unreadable: {exc}"[:300],
                "fixture": path.name,
            }
        )
        return base

    if not isinstance(raw, dict):
        base.update(
            {
                "status": "fail",
                "error": "Mock fixture must be a JSON object.",
                "message": "Mock fixture must be a JSON object.",
                "fixture": path.name,
            }
        )
        return base

    code_raw = raw.get("http_status", raw.get("status_code", 200))
    try:
        code = int(code_raw)
    except (TypeError, ValueError):
        code = 200

    body = raw.get("body", raw.get("response"))
    if isinstance(body, (dict, list)):
        body_text = json.dumps(body, separators=(",", ":"))
    elif body is None:
        body_text = str(raw.get("body_text") or raw.get("message") or "")
    else:
        body_text = str(body)

    summary, hits = _redact_body_summary(body_text)
    expected = int(expect_status) if expect_status is not None else None
    if expected is None and raw.get("expect_status") is not None:
        try:
            expected = int(raw.get("expect_status"))
        except (TypeError, ValueError):
            expected = None

    base["fixture"] = path.name
    base["endpoint_label"] = f"mock://{path.name}"
    base["http_status"] = code
    base["body_summary"] = summary
    base["redaction_hits"] = int(hits)
    base["expect_status"] = expected

    fixture_msg = str(raw.get("message") or "").strip()
    if expected is not None:
        if code == expected:
            base["status"] = "pass"
            base["message"] = fixture_msg or f"Mock HTTP {code} (expected {expected})."
        else:
            base["status"] = "fail"
            base["error"] = f"Mock HTTP {code}, expected {expected}."
            base["message"] = base["error"]
    else:
        if 200 <= code < 400:
            base["status"] = "pass"
            base["message"] = fixture_msg or f"Mock HTTP {code}."
        else:
            base["status"] = "fail"
            base["error"] = fixture_msg or f"Mock HTTP {code}."
            base["message"] = base["error"]
    return base
