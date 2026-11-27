"""Home-PC Operate demo AUT fixture + golden-path seed (KAN-377 / OPERATE-2).

Serves synthetic pages under fixtures/operate_demo/ (mounted at /demo-aut/).
Never requires employer credentials or VPN.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "operate_demo"
INDEX_NAME = "index.html"
MOUNT_PATH = "/demo-aut"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PLAN_NAME = "OPERATE golden path"
PLAN_MARKER = "operate-demo-aut"
SMOKE_TAG = "smoke"
FAIL_DEMO_TAG = "fail-demo"
SOURCE_KIND = "operate-demo"

# Deliberate missing string so a headed run fails usefully for open-trace demos.
INTENTIONAL_FAIL_TEXT = "ELEMENT_THAT_DOES_NOT_EXIST_OPERATE377"


def fixture_index_path() -> Path:
    return FIXTURE_DIR / INDEX_NAME


def fixture_present() -> dict[str, Any]:
    index = fixture_index_path()
    ok = index.is_file()
    marker = False
    if ok:
        try:
            text = index.read_text(encoding="utf-8")
            marker = 'data-operate-demo-aut="1"' in text and "Operate Demo AUT" in text
        except OSError:
            marker = False
    return {
        "ok": bool(ok and marker),
        "dir": str(FIXTURE_DIR),
        "index": str(index),
        "exists": ok,
        "marker": marker,
        "mount_path": MOUNT_PATH,
    }


def demo_aut_url(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    h = (host or DEFAULT_HOST).strip() or DEFAULT_HOST
    p = int(port or DEFAULT_PORT)
    base = f"http://{h}:{p}{MOUNT_PATH}/"
    return base


def _find_plan_by_name(level: str, name: str) -> dict[str, Any] | None:
    from plans.store import get_plan, list_plans

    listed = list_plans(level)
    for row in listed.get("plans") or []:
        if str(row.get("name") or "").strip() == name:
            full = get_plan(str(row["id"]), level=level)
            if full.get("status") == "ok":
                return full.get("plan")
    return None


def _case_tags_smoke() -> list[str]:
    return [SMOKE_TAG, PLAN_MARKER]


def _case_tags_fail() -> list[str]:
    return [SMOKE_TAG, PLAN_MARKER, FAIL_DEMO_TAG]


def seed_operate_demo(
    *,
    level: str = "OFFICIAL",
    set_target_url: bool = True,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    force_new_plan: bool = False,
) -> dict[str, Any]:
    """Ensure fixture exists, optionally set target_url, seed OFFICIAL golden-path plan."""
    from plans.store import add_case, create_plan
    from settings.store import get_security_level, set_security_level, update_setting

    present = fixture_present()
    if not present.get("ok"):
        return {
            "status": "error",
            "message": (
                "Operate demo AUT fixture missing or incomplete under "
                f"fixtures/operate_demo/ ({present.get('index')})."
            ),
            "fixture": present,
        }

    lvl = (level or "OFFICIAL").strip().upper()
    if lvl not in {"OFFICIAL", "SECRET"}:
        return {
            "status": "error",
            "message": f"Unsupported security level for seed: {level!r}",
            "fixture": present,
        }

    url = demo_aut_url(host=host, port=port)
    target_updated = False
    previous_level = get_security_level()
    try:
        if set_target_url:
            if previous_level != lvl:
                switched = set_security_level(lvl, confirm=True)
                if switched.get("status") == "error":
                    return {
                        "status": "error",
                        "message": switched.get("message")
                        or f"Could not switch to {lvl} to set target_url.",
                        "fixture": present,
                    }
            updated = update_setting("target_url", url, confirm=True)
            if updated.get("status") != "updated":
                return {
                    "status": "error",
                    "message": updated.get("message")
                    or "Could not set target_url for the demo AUT.",
                    "fixture": present,
                    "settings": updated,
                }
            target_updated = True
    finally:
        if set_target_url and previous_level != get_security_level():
            set_security_level(previous_level, confirm=True)

    existing = None if force_new_plan else _find_plan_by_name(lvl, PLAN_NAME)
    if existing:
        cases = list((existing.get("suite") or {}).get("cases") or [])
        smoke = [
            c
            for c in cases
            if SMOKE_TAG in (c.get("tags") or []) and FAIL_DEMO_TAG not in (c.get("tags") or [])
        ]
        fail_cases = [c for c in cases if FAIL_DEMO_TAG in (c.get("tags") or [])]
        return {
            "status": "ok",
            "created": False,
            "message": (
                f"Plan already present ({existing.get('id')}) with "
                f"{len(cases)} case(s). target_url={'updated' if target_updated else 'unchanged'}."
            ),
            "security_level": lvl,
            "target_url": url if set_target_url else None,
            "target_updated": target_updated,
            "fixture": present,
            "plan": existing,
            "plan_id": existing.get("id"),
            "case_count": len(cases),
            "smoke_case_id": (smoke[0].get("id") if smoke else None),
            "fail_case_id": (fail_cases[0].get("id") if fail_cases else None),
            "demo_aut_url": url,
        }

    created = create_plan(
        PLAN_NAME,
        intent=(
            "Home-PC OPERATE golden path against the local demo AUT "
            "(fixtures/operate_demo). Synthetic only — no employer AUT."
        ),
        sources={"jira_keys": [], "documents": ["fixtures/operate_demo"]},
        level=lvl,
    )
    if created.get("status") != "ok":
        return {
            "status": "error",
            "message": created.get("message") or "Could not create OPERATE golden path plan.",
            "fixture": present,
            "create": created,
        }

    plan = created["plan"]
    plan_id = plan["id"]

    smoke = add_case(
        plan_id,
        "Smoke: open Operate demo AUT",
        tags=_case_tags_smoke(),
        note=(
            'Open the demo AUT home page. Expect text "Operate Demo AUT". '
            "Pass path for the daily loop."
        ),
        enabled=True,
        source_kind=SOURCE_KIND,
        source_ref="fixtures/operate_demo/index.html#home",
        level=lvl,
    )
    fail = add_case(
        plan_id,
        "Intentional fail: missing banner text",
        tags=_case_tags_fail(),
        note=(
            f'Open the demo AUT. Expect text "{INTENTIONAL_FAIL_TEXT}". '
            "Use this case to exercise failure evidence and Open Playwright Trace."
        ),
        enabled=True,
        source_kind=SOURCE_KIND,
        source_ref="fixtures/operate_demo/index.html#intentional-fail",
        level=lvl,
    )

    smoke_case = smoke.get("case") if smoke.get("status") == "ok" else None
    fail_case = fail.get("case") if fail.get("status") == "ok" else None
    refreshed = smoke.get("plan") if smoke.get("status") == "ok" else plan
    if fail.get("status") == "ok" and fail.get("plan"):
        refreshed = fail["plan"]

    return {
        "status": "ok",
        "created": True,
        "message": (
            f"Seeded {PLAN_NAME} on {lvl} with smoke + intentional-fail cases. "
            f"Demo AUT URL: {url}"
        ),
        "security_level": lvl,
        "target_url": url if set_target_url else None,
        "target_updated": target_updated,
        "fixture": present,
        "plan": refreshed,
        "plan_id": plan_id,
        "case_count": 2,
        "smoke_case_id": (smoke_case or {}).get("id"),
        "fail_case_id": (fail_case or {}).get("id"),
        "demo_aut_url": url,
    }
