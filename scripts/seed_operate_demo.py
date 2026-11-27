"""Seed home-PC OPERATE demo AUT + golden-path plan (KAN-377).

Usage (with desktop app running or not — seed writes local plans/settings):
    .\\venv\\Scripts\\python.exe scripts\\seed_operate_demo.py

Sets OFFICIAL target_url to http://127.0.0.1:8765/demo-aut/ and creates
plan "OPERATE golden path" with a smoke pass case + intentional fail case.
Idempotent if the plan already exists.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.operate_demo import (  # noqa: E402
    DEFAULT_HOST,
    DEFAULT_PORT,
    demo_aut_url,
    fixture_present,
    seed_operate_demo,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed OPERATE demo AUT + golden-path plan")
    parser.add_argument("--level", default="OFFICIAL", help="Security level for the plan")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--no-target-url",
        action="store_true",
        help="Do not write Settings target_url",
    )
    parser.add_argument(
        "--force-new-plan",
        action="store_true",
        help="Always create a new plan even if one named OPERATE golden path exists",
    )
    args = parser.parse_args()

    present = fixture_present()
    if not present.get("ok"):
        print(json.dumps({"status": "error", "fixture": present}, indent=2))
        return 1

    out = seed_operate_demo(
        level=args.level,
        set_target_url=not args.no_target_url,
        host=args.host,
        port=args.port,
        force_new_plan=bool(args.force_new_plan),
    )
    # Avoid dumping full plan JSON noise — keep ids + URL.
    slim = {
        "status": out.get("status"),
        "created": out.get("created"),
        "message": out.get("message"),
        "security_level": out.get("security_level"),
        "demo_aut_url": out.get("demo_aut_url") or demo_aut_url(host=args.host, port=args.port),
        "target_updated": out.get("target_updated"),
        "plan_id": out.get("plan_id"),
        "smoke_case_id": out.get("smoke_case_id"),
        "fail_case_id": out.get("fail_case_id"),
        "case_count": out.get("case_count"),
        "fixture_ok": present.get("ok"),
    }
    if out.get("status") != "ok":
        slim["error_detail"] = {
            k: out.get(k) for k in ("message", "settings", "create") if out.get(k)
        }
        print(json.dumps(slim, indent=2))
        return 1
    print(json.dumps(slim, indent=2))
    print(
        "\nNext: start .\\venv\\Scripts\\python.exe desktop_app.py "
        "→ Plans → OPERATE golden path → run the smoke case "
        "(or the intentional-fail case for open-trace)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
