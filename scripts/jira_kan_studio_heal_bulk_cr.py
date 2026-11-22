"""Studio CR 2026-11-22: lock History A/B radios; add Heal bulk approve to KAN-339/340.

Never prints tokens. Does not change WORK_LOG Active.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Reuse bridge helpers + updated Heal pair text
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jira_kan_fr_ui11_rest_bridge import (  # noqa: E402
    Jira,
    PAIRS,
    adf_from_lines,
    lines,
    load_creds,
)


def put_fields(jira: Jira, key: str, fields: dict) -> None:
    r = jira._req("PUT", f"/rest/api/3/issue/{key}", json={"fields": fields})
    if r.status_code >= 300:
        jira.failures.append(f"put {key}: {r.status_code} {r.text[:200]}")
    else:
        print(f"updated {key}")


def main() -> None:
    heal = next(p for p in PAIRS if "Heal" in p["story_summary"] or p["order"] == "5")
    base, auth = load_creds()
    jira = Jira(base, auth)
    try:
        put_fields(
            jira,
            "KAN-339",
            {
                "summary": heal["story_summary"],
                "description": adf_from_lines(lines(heal["story"])),
            },
        )
        put_fields(
            jira,
            "KAN-340",
            {
                "summary": heal["test_summary"],
                "description": adf_from_lines(lines(heal["test"])),
            },
        )
        jira.comment(
            "KAN-331",
            [
                "Studio Designer CR 2026-11-22 — open question 1 accepted.",
                "History compare uses dedicated A/B radio cells (~28px hit cells). Row click focuses the run; radios drive Compare A and B.",
                "Mockup: docs/mockups/secondary_areas_rest/01-themed-plans-tabs.html (History panel).",
                "No product UI in this Studio chat. Active Build remains KAN-329.",
            ],
        )
        jira.comment(
            "KAN-339",
            [
                "Studio Designer CR 2026-11-22 — open question 2: bulk approve yes.",
                "Heal now: detail Approve/Reject for focused proposal + toolbar Approve selected (N) after dedicated Sel checkboxes + confirm.",
                "Checkbox never means approve. Row never approves. Bulk reject out of scope.",
                "Description and summary rewritten to match. Mockup: docs/mockups/secondary_areas_rest/01e-themed-heal.html",
                "Spec FR-UI-11 Heal paragraph updated. Linked test KAN-340 rewritten for Sel + data-heal-bulk markers.",
                "Active Build remains KAN-329.",
            ],
        )
        jira.comment(
            "KAN-340",
            [
                "Studio Designer CR 2026-11-22 — test tightened for Heal bulk approve.",
                "Markers: data-heal-scan Sel column, data-heal-actions, data-heal-bulk / heal-bulk-approve.",
                "Fail if Approve/Reject sit on the row. Fail if checkbox click approves. Soft-pass 'opened Heal' fails.",
                "Story KAN-339 description matches.",
            ],
        )
        print(json.dumps({"failures": jira.failures}, indent=2))
    finally:
        jira.close()


if __name__ == "__main__":
    main()
