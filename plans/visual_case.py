"""Visual baseline cases on the same in-app suite (KAN-225 / G5).

Opt-in source.kind=visual. Cases name a level-scoped baseline PNG and a
page URL. Compare runs link baseline + current on mismatch. Update-baseline
is an explicit API/action only — never auto on mismatch.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from plans.store import add_case, get_plan


def parse_visual_ref(ref: str) -> dict[str, Any]:
    """Parse source.ref: bare name → baseline; JSON → baseline + optional url."""
    empty: dict[str, Any] = {"baseline": "", "url": ""}
    text = (ref or "").strip()
    if not text:
        return dict(empty)
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {**empty, "baseline": text[:120]}
        if isinstance(parsed, dict):
            name = str(
                parsed.get("baseline")
                or parsed.get("visual_baseline")
                or parsed.get("name")
                or ""
            ).strip()[:120]
            url = str(parsed.get("url") or parsed.get("target_url") or "").strip()[:500]
            return {"baseline": name, "url": url}
    return {**empty, "baseline": text[:120]}


def encode_visual_ref(*, baseline: str = "", url: str = "") -> str:
    """Encode baseline name and optional URL into source.ref (cap 300)."""
    name = (baseline or "").strip()
    page = (url or "").strip()
    if page:
        payload = {"baseline": name, "url": page}
        return json.dumps(payload, separators=(",", ":"))[:300]
    return name[:300]


def add_visual_case(
    plan_id: str,
    name: str = "",
    *,
    baseline: str = "",
    url: str = "",
    note: str = "",
    tags: list[str] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Add an opt-in visual baseline case (off for all other cases)."""
    from plugins.visual_baseline import default_baseline_name
    from settings.store import load_settings

    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    baseline_name = (baseline or "").strip() or default_baseline_name()
    page = (url or "").strip() or str(load_settings().get("target_url") or "").strip()
    label = (name or "").strip() or f"Visual baseline — {baseline_name}"

    case_tags = list(tags or [])
    lowered = [t.lower() for t in case_tags]
    if "visual" not in lowered and "baseline" not in lowered:
        case_tags = ["visual", "baseline"] + case_tags

    ref = encode_visual_ref(baseline=baseline_name, url=page)
    return add_case(
        plan_id,
        label,
        note=note
        or (
            f"Visual baseline case — opt-in compare to {baseline_name}; "
            "mismatch links both images; update-baseline is explicit."
        ),
        tags=case_tags,
        source_kind="visual",
        source_ref=ref,
        level=level,
    )


def write_visual_evidence(
    *,
    run_id: str,
    plan_id: str,
    case_id: str,
    visual: dict[str, Any],
) -> list[str]:
    """Persist visual compare result; link baseline + current paths on mismatch."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    folder = Path(base) / "ai_testing_app" / "evidence" / (run_id or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    linked: list[str] = []
    for key in ("baseline_path", "current_path"):
        p = visual.get(key)
        if p and Path(str(p)).is_file():
            linked.append(str(p))
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plugin": visual.get("plugin") or "visual_baseline",
        "baseline": visual.get("baseline"),
        "baseline_path": visual.get("baseline_path"),
        "current_path": visual.get("current_path"),
        "status": visual.get("status"),
        "matched": visual.get("matched"),
        "updated": visual.get("updated"),
        "diff_pixels": visual.get("diff_pixels"),
        "size_mismatch": visual.get("size_mismatch"),
        "error": visual.get("error"),
        "message": visual.get("message"),
        "classification": visual.get("classification"),
        "linked_images": linked,
    }
    path = folder / "visual_baseline_result.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Evidence list: JSON + both images when present (AC: mismatch links both).
    evidence = [str(path)] + linked
    return evidence


def update_case_baseline(
    plan_id: str,
    case_id: str,
    *,
    current_path: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Explicit update-baseline for a visual case (no compare auto-overwrite)."""
    from plugins.visual_baseline import store_baseline
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "OFFICIAL").strip().upper()
    loaded = get_plan(plan_id, level=lvl)
    if loaded.get("status") != "ok":
        return loaded
    plan = loaded["plan"]
    cid = (case_id or "").strip()
    target: Optional[dict[str, Any]] = None
    for case in (plan.get("suite") or {}).get("cases") or []:
        if case.get("id") == cid:
            target = case
            break
    if target is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": lvl,
        }
    src = target.get("source") if isinstance(target.get("source"), dict) else {}
    if str(src.get("kind") or "") != "visual":
        return {
            "status": "error",
            "error": "not_visual_case",
            "message": "Update baseline only applies to opt-in visual cases.",
            "security_level": lvl,
        }
    parsed = parse_visual_ref(str(src.get("ref") or ""))
    name = str(parsed.get("baseline") or "").strip()
    if not name:
        return {
            "status": "error",
            "error": "no_baseline_name",
            "message": "Visual case has no baseline name.",
            "security_level": lvl,
        }
    shot = (current_path or "").strip()
    if not shot:
        return {
            "status": "error",
            "error": "no_current_screenshot",
            "message": (
                "Provide current_path, or run the case with update_baseline=true "
                "to capture then store."
            ),
            "security_level": lvl,
            "baseline": name,
        }
    stored = store_baseline(name, shot, level=lvl)
    return {
        "status": "ok" if stored.get("status") == "pass" else "error",
        "security_level": lvl,
        "plan": plan,
        "case": target,
        "visual": stored,
        "message": stored.get("message") or stored.get("error"),
        "explicit_update": True,
    }
