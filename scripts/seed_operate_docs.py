"""Seed OPERATE Documents demo pack into OFFICIAL uploads (KAN-381).

Usage:
    .\\venv\\Scripts\\python.exe scripts\\seed_operate_docs.py
    .\\venv\\Scripts\\python.exe scripts\\seed_operate_docs.py --draft-plan

Installs synthetic functional-spec + user-guide under Documents → Uploads.
Optional --draft-plan creates/reuses plan "OPERATE documents draft" with cases
from those docs (no Jira writes).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.operate_docs import (  # noqa: E402
    GUIDE_NAME,
    SPEC_NAME,
    draft_plan_from_operate_docs,
    fixture_present,
    seed_operate_docs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed OPERATE Documents demo pack (synthetic spec + user guide)"
    )
    parser.add_argument("--level", default="OFFICIAL", help="Security level for uploads")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-upload demo files even if filenames already exist",
    )
    parser.add_argument(
        "--draft-plan",
        action="store_true",
        help="Also draft editable cases into plan 'OPERATE documents draft'",
    )
    parser.add_argument(
        "--force-new-plan",
        action="store_true",
        help="With --draft-plan, always create a new plan",
    )
    args = parser.parse_args()

    present = fixture_present()
    if not present.get("ok"):
        print(json.dumps({"status": "error", "fixture": present}, indent=2))
        return 1

    if args.draft_plan:
        out = draft_plan_from_operate_docs(
            level=args.level,
            force_new_plan=bool(args.force_new_plan),
            seed_first=True,
        )
        slim = {
            "status": out.get("status"),
            "message": out.get("message"),
            "jira_write": out.get("jira_write"),
            "security_level": args.level,
            "plan_id": out.get("plan_id"),
            "plan_name": out.get("plan_name"),
            "created_plan": out.get("created_plan"),
            "case_count": out.get("case_count"),
            "documents": out.get("documents"),
            "seed_created": (out.get("seed") or {}).get("created"),
            "both_present": (out.get("seed") or {}).get("both_present"),
            "fixture_ok": present.get("ok"),
        }
        print(json.dumps(slim, indent=2))
        if out.get("status") != "ok":
            return 1
        print(
            "\nNext: start .\\venv\\Scripts\\python.exe desktop_app.py "
            "→ Documents → Uploads (both demo docs) → Plans → "
            "OPERATE documents draft (review cases; nothing written to Jira)."
        )
        return 0

    out = seed_operate_docs(level=args.level, force=bool(args.force))
    slim = {
        "status": out.get("status"),
        "created": out.get("created"),
        "message": out.get("message"),
        "security_level": out.get("security_level"),
        "both_present": out.get("both_present"),
        "upload_names": [SPEC_NAME, GUIDE_NAME],
        "upload_count": len(out.get("uploads") or []),
        "fixture_ok": present.get("ok"),
    }
    print(json.dumps(slim, indent=2))
    if out.get("status") != "ok":
        return 1
    print(
        "\nNext: start .\\venv\\Scripts\\python.exe desktop_app.py "
        "→ Documents → Uploads → confirm both demo docs. "
        "Optional: re-run with --draft-plan to draft cases into a plan."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
