"""Seed data / fixture cases on the same in-app suite (KAN-223 / G4).

Cases name a level-scoped local fixture (file/steps). Run stores the
fixture name. Missing fixture fails as environment. No global silent
injection.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from plans.store import add_case, get_plan


def parse_seed_ref(ref: str) -> dict[str, Any]:
    """Parse source.ref: bare name → fixture; JSON → fixture + optional steps."""
    empty: dict[str, Any] = {"fixture": "", "steps": None}
    text = (ref or "").strip()
    if not text:
        return dict(empty)
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {**empty, "fixture": text[:120]}
        if isinstance(parsed, list):
            return {"fixture": "", "steps": parsed}
        if isinstance(parsed, dict):
            steps = parsed.get("steps")
            if steps is not None and not isinstance(steps, list):
                steps = None
            name = str(
                parsed.get("fixture")
                or parsed.get("seed_fixture")
                or parsed.get("name")
                or ""
            ).strip()[:120]
            return {"fixture": name, "steps": steps}
    return {**empty, "fixture": text[:120]}


def encode_seed_ref(
    *,
    fixture: str = "",
    steps: Optional[list[Any]] = None,
) -> str:
    """Encode fixture name and optional steps into source.ref (cap 300)."""
    name = (fixture or "").strip()
    if steps:
        payload: dict[str, Any] = {"fixture": name, "steps": steps}
        return json.dumps(payload, separators=(",", ":"))[:300]
    return name[:300]


def add_seed_case(
    plan_id: str,
    name: str = "",
    *,
    fixture: str = "",
    note: str = "",
    tags: list[str] | None = None,
    steps: Optional[list[Any]] = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add a seed/fixture-typed case to an existing plan suite."""
    from plugins.seed_fixture import (
        default_fixture_name,
        ensure_default_fixture,
    )

    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    ensure_default_fixture(level=level)
    fixture_name = (fixture or "").strip() or default_fixture_name()
    label = (name or "").strip() or f"Seed fixture — {fixture_name}"

    case_tags = list(tags or [])
    lowered = [t.lower() for t in case_tags]
    if "seed" not in lowered and "fixture" not in lowered:
        case_tags = ["seed", "fixture"] + case_tags

    ref = encode_seed_ref(fixture=fixture_name, steps=steps)
    return add_case(
        plan_id,
        label,
        note=note
        or (
            f"Seed/fixture case — local named fixture {fixture_name}; "
            "run stores name; missing → environment."
        ),
        tags=case_tags,
        source_kind="seed",
        source_ref=ref,
        level=level,
    )


def write_seed_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    seed: dict[str, Any],
) -> list[str]:
    """Persist seed fixture apply result as evidence (same run model)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": seed.get("plugin") or "seed_fixture",
        "fixture": seed.get("fixture"),
        "status": seed.get("status"),
        "steps": seed.get("steps") or [],
        "data": seed.get("data"),
        "error": seed.get("error"),
        "message": seed.get("message"),
        "classification": seed.get("classification"),
    }
    path = folder / "seed_fixture_result.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return [str(path)]
