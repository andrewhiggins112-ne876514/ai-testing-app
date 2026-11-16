"""Evidence bundle for failed browser cases (KAN-143 / FR-PLAN-4 / FR-TEST-4)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _bundle_dir(run_id: str) -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_failure_bundle(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    playwright: dict[str, Any],
) -> dict[str, Any]:
    """Persist screenshot ref, step log, and console-like messages — no secrets."""
    folder = _bundle_dir(run_id)
    screenshot = playwright.get("screenshot")
    steps = playwright.get("steps") or []
    console_lines: list[str] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        err = step.get("error")
        if err:
            console_lines.append(f"[step {step.get('action')}] {err}")
    bundle = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "screenshot": screenshot,
        "trace": None,
        "console_messages": console_lines[:50],
        "steps": steps,
        "playwright_status": playwright.get("status"),
        "error": playwright.get("error"),
    }
    trace_placeholder = folder / "trace.notice.txt"
    trace_placeholder.write_text(
        "Playwright trace capture for plan runs is reserved for a future runner hook.\n",
        encoding="utf-8",
    )
    bundle["trace"] = str(trace_placeholder)
    manifest = folder / "bundle.json"
    manifest.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    paths = [str(manifest)]
    if screenshot:
        paths.append(str(screenshot))
    paths.append(str(trace_placeholder))
    return {"bundle_path": str(manifest), "paths": paths, "bundle": bundle}