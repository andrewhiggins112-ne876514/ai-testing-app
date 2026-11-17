"""API / messaging endpoint checks (KAN-219 / G2 / FR-LEARN-3).

Calls the saved messaging/API endpoint (Settings ``api_endpoint``) and returns
status plus a redacted body summary. Does not remove the messaging settings field.
"""
from __future__ import annotations

import re
import socket
import ssl
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from reports.redact import PLACEHOLDER, redact_text

PLUGIN_NAME = "api_messaging_runner"
_BODY_CAP = 800
_DEFAULT_TIMEOUT_S = 10.0
# JSON object keys that commonly carry secrets in API/messaging payloads.
_JSON_SECRET_KEY = re.compile(
    r'(?i)("(?:password|secret|api[_-]?token|authorization|credential|token)"\s*:\s*")([^"]*)(")'
)


def _redact_body_summary(text: str) -> tuple[str, int]:
    """Redact labeled secrets and JSON secret-key values for the run log."""
    clipped = (text or "")[:_BODY_CAP]
    out, hits = redact_text(clipped)
    out2, n = _JSON_SECRET_KEY.subn(rf'\1{PLACEHOLDER}\3', out)
    return out2, int(hits) + int(n)


def _safe_endpoint_label(endpoint: str) -> str:
    """Host + path without query/fragment (query may carry tokens)."""
    try:
        parsed = urlparse((endpoint or "").strip())
    except Exception:
        return "(invalid)"
    scheme = (parsed.scheme or "").lower()
    netloc = parsed.netloc or ""
    path = parsed.path or ""
    if parsed.query or parsed.fragment:
        return f"{scheme}://{netloc}{path}?[REDACTED]"
    if scheme and netloc:
        return f"{scheme}://{netloc}{path}"
    return (endpoint or "")[:120] or "(empty)"


def _tcp_probe(host: str, port: int, timeout_s: float) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return {"ok": True, "error": None}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:300]}


def run_api_check(
    *,
    endpoint: str = "",
    method: str = "GET",
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    expect_status: Optional[int] = None,
    body: str | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Probe messaging/API endpoint; body text is redacted before return."""
    url = (endpoint or "").strip()
    timeout = max(0.5, min(float(timeout_s or _DEFAULT_TIMEOUT_S), 60.0))
    verb = (method or "GET").strip().upper() or "GET"
    label = _safe_endpoint_label(url)

    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "endpoint_label": label,
        "method": verb,
        "http_status": None,
        "body_summary": "",
        "redaction_hits": 0,
        "expect_status": expect_status,
        "transport": None,
        "status": "fail",
        "error": None,
        "message": None,
    }

    if not url:
        base.update(
            {
                "status": "fail",
                "error": "No messaging/API endpoint configured.",
                "message": "No messaging/API endpoint configured.",
                "transport": "none",
            }
        )
        return base

    try:
        parsed = urlparse(url)
    except Exception as exc:
        base.update(
            {
                "status": "fail",
                "error": f"Invalid endpoint URL: {exc}"[:300],
                "transport": "none",
            }
        )
        return base

    scheme = (parsed.scheme or "").lower()
    host = parsed.hostname or ""
    if not host:
        base.update(
            {
                "status": "fail",
                "error": "Endpoint has no host.",
                "transport": "none",
            }
        )
        return base

    # HTTP(S) — full request; redact response body for the run log.
    if scheme in ("http", "https"):
        base["transport"] = "http"
        data = None
        req_headers = dict(headers or {})
        if body is not None and verb in ("POST", "PUT", "PATCH"):
            data = str(body).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")
        try:
            req = Request(url, data=data, headers=req_headers, method=verb)
            ctx = ssl.create_default_context() if scheme == "https" else None
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read(4096)
                code = int(getattr(resp, "status", None) or resp.getcode() or 0)
                charset = "utf-8"
                try:
                    charset = resp.headers.get_content_charset() or "utf-8"
                except Exception:
                    pass
                text = raw.decode(charset, errors="replace")
        except Exception as exc:
            # urllib raises HTTPError for 4xx/5xx — treat as status response.
            http_err = getattr(exc, "code", None)
            if http_err is not None:
                code = int(http_err)
                try:
                    raw = exc.read(4096)  # type: ignore[attr-defined]
                    text = raw.decode("utf-8", errors="replace") if raw else ""
                except Exception:
                    text = str(exc)[:400]
            else:
                base.update(
                    {
                        "status": "fail",
                        "error": str(exc)[:300],
                        "message": str(exc)[:300],
                    }
                )
                return base

        summary, hits = _redact_body_summary(text)
        base["http_status"] = code
        base["body_summary"] = summary
        base["redaction_hits"] = int(hits)
        expected = int(expect_status) if expect_status is not None else None
        if expected is not None:
            if code == expected:
                base["status"] = "pass"
                base["message"] = f"HTTP {code} (expected {expected})."
            else:
                base["status"] = "fail"
                base["error"] = f"HTTP {code}, expected {expected}."
                base["message"] = base["error"]
        else:
            if 200 <= code < 400:
                base["status"] = "pass"
                base["message"] = f"HTTP {code}."
            else:
                base["status"] = "fail"
                base["error"] = f"HTTP {code}."
                base["message"] = base["error"]
        return base

    # amqp / amqps / ws / wss — TCP reachability only (no protocol handshake).
    if scheme in ("amqp", "amqps", "ws", "wss"):
        base["transport"] = "tcp"
        default_ports = {"amqp": 5672, "amqps": 5671, "ws": 80, "wss": 443}
        port = int(parsed.port or default_ports.get(scheme, 0) or 0)
        if not port:
            base.update(
                {
                    "status": "fail",
                    "error": f"No port for scheme {scheme}.",
                    "message": f"No port for scheme {scheme}.",
                }
            )
            return base
        probe = _tcp_probe(host, port, timeout)
        if probe["ok"]:
            base["status"] = "pass"
            base["message"] = f"TCP connect ok ({scheme}://{host}:{port})."
            base["body_summary"] = f"tcp_ok host={host} port={port}"
        else:
            err = probe.get("error") or "TCP connect failed."
            base["status"] = "fail"
            base["error"] = err
            base["message"] = err
            base["body_summary"] = f"tcp_fail host={host} port={port}"
        return base

    base.update(
        {
            "status": "fail",
            "error": f"Unsupported endpoint scheme: {scheme or '(none)'}.",
            "message": f"Unsupported endpoint scheme: {scheme or '(none)'}.",
            "transport": "unsupported",
        }
    )
    return base
