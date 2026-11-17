"""API / messaging cases on the same in-app suite (KAN-219 / G2 + KAN-221 / G3).

Cases call the saved messaging/API endpoint (Settings) and store HTTP/TCP
status plus a redacted body summary on the same run model as other cases.

G3: a case may select a local mock fixture instead; mocks are off unless
selected. Live-endpoint cases stay unchanged.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from plans.store import add_case, get_plan


def parse_api_ref(ref: str) -> dict[str, Any]:
    """Parse source.ref: empty → settings endpoint; URL → override; JSON → options."""
    empty = {
        "endpoint": "",
        "method": "GET",
        "expect_status": None,
        "body": None,
        "mock_fixture": "",
    }
    text = (ref or "").strip()
    if not text:
        return dict(empty)
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {
                **empty,
                "endpoint": text[:500],
            }
        if isinstance(parsed, dict):
            expect = parsed.get("expect_status")
            try:
                expect_i = int(expect) if expect is not None else None
            except (TypeError, ValueError):
                expect_i = None
            body = parsed.get("body")
            mock = str(
                parsed.get("mock_fixture")
                or parsed.get("mock")
                or parsed.get("fixture")
                or ""
            ).strip()[:120]
            return {
                "endpoint": str(
                    parsed.get("endpoint") or parsed.get("url") or ""
                ).strip()[:500],
                "method": str(parsed.get("method") or "GET").strip().upper() or "GET",
                "expect_status": expect_i,
                "body": None if body is None else str(body)[:2000],
                "mock_fixture": mock,
            }
    return {
        **empty,
        "endpoint": text[:500],
    }


def encode_api_ref(
    *,
    endpoint: str = "",
    method: str = "GET",
    expect_status: Optional[int] = None,
    body: str | None = None,
    mock_fixture: str = "",
) -> str:
    """Encode endpoint override / mock / options into source.ref (cap 300)."""
    path = (endpoint or "").strip()
    verb = (method or "GET").strip().upper() or "GET"
    mock = (mock_fixture or "").strip()
    needs_json = (
        verb != "GET"
        or expect_status is not None
        or body is not None
        or bool(mock)
    )
    if needs_json:
        payload: dict[str, Any] = {}
        if mock:
            payload["mock_fixture"] = mock[:80]
        if path and not mock:
            # Live override only when not on mock (mock ignores live URL).
            payload["endpoint"] = path
        if verb != "GET":
            payload["method"] = verb
        if expect_status is not None:
            payload["expect_status"] = int(expect_status)
        if body is not None and not mock:
            payload["body"] = str(body)[:500]
        return json.dumps(payload, separators=(",", ":"))[:300]
    return path[:300]


def add_api_case(
    plan_id: str,
    name: str = "",
    *,
    endpoint: str = "",
    method: str = "GET",
    expect_status: Optional[int] = None,
    note: str = "",
    tags: list[str] | None = None,
    body: str | None = None,
    mock_fixture: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Add an API/messaging-typed case to an existing plan suite."""
    from settings.store import load_settings

    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    settings = load_settings()
    saved = str(settings.get("api_endpoint") or "").strip()
    url = (endpoint or "").strip() or saved
    mock = (mock_fixture or "").strip()
    label = (name or "").strip()
    if not label:
        if mock:
            label = f"Contract mock — {mock}"
        else:
            label = (
                "API / messaging check — saved endpoint"
                if saved
                else "API / messaging check"
            )

    case_tags = list(tags or [])
    lowered = [t.lower() for t in case_tags]
    if "api" not in lowered and "messaging" not in lowered:
        case_tags = ["api", "messaging"] + case_tags
    if mock and "mock" not in lowered and "contract" not in lowered:
        case_tags = case_tags + ["mock", "contract"]

    # Empty ref → use connected settings endpoint at run time.
    # Mock cases store mock_fixture only (live endpoint unused).
    override = "" if mock else (url if url and url != saved else "")
    ref = encode_api_ref(
        endpoint=override,
        method=method,
        expect_status=expect_status,
        body=None if mock else body,
        mock_fixture=mock,
    )

    default_note = (
        f"Contract/mock case — local fixture {mock}; run record marked mock."
        if mock
        else "API/messaging case — calls the saved messaging endpoint; body redacted in log."
    )
    return add_case(
        plan_id,
        label,
        note=note or default_note,
        tags=case_tags,
        source_kind="api",
        source_ref=ref,
        level=level,
    )


def add_contract_case(
    plan_id: str,
    name: str = "",
    *,
    mock_fixture: str = "",
    expect_status: Optional[int] = None,
    note: str = "",
    tags: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add an API case that points at a local mock fixture (KAN-221 / G3)."""
    from plugins.contract_mock import (
        default_fixture_name,
        ensure_default_fixture,
    )

    ensure_default_fixture(level=level)
    fixture = (mock_fixture or "").strip() or default_fixture_name()
    return add_api_case(
        plan_id,
        name,
        mock_fixture=fixture,
        expect_status=expect_status,
        note=note,
        tags=tags,
        level=level,
    )


def write_api_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    api: dict[str, Any],
) -> list[str]:
    """Persist redacted API/mock check result as evidence (same run model)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    is_mock = bool(api.get("mock"))
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": api.get("plugin")
        or ("contract_mock" if is_mock else "api_messaging_runner"),
        "mock": is_mock,
        "fixture": api.get("fixture"),
        "status": api.get("status"),
        "transport": api.get("transport"),
        "endpoint_label": api.get("endpoint_label"),
        "method": api.get("method"),
        "http_status": api.get("http_status"),
        "expect_status": api.get("expect_status"),
        "body_summary": api.get("body_summary") or "",
        "redaction_hits": int(api.get("redaction_hits") or 0),
        "error": api.get("error"),
        "message": api.get("message"),
    }
    fname = "contract_mock_result.json" if is_mock else "api_messaging_result.json"
    path = folder / fname
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
