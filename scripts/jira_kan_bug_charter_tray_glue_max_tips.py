"""Create Bug: tray detaches on side flip; max capture too small; need hover tips."""
from __future__ import annotations

import json
import ssl
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jira_kan_slice_closeout import load_creds  # type: ignore


def adf_text(text: str) -> dict:
    paras = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": block}] if block else [],
        }
        for block in text.strip().split("\n")
    ]
    return {
        "type": "doc",
        "version": 1,
        "content": paras or [{"type": "paragraph", "content": []}],
    }


BUG = """Symptom
Designer (desk159 / KAN-528 human check): drag and resize work, but (1) side tray detaches from the hollow ring when moving / switching sides and does not snap back; (2) resize max is still too small to cover a real AUT window; (3) tray icons have no hover tooltips.

Expected
1. Tray stays glued to the capture hole on east or west after every move/resize/side flip.
2. Capture can grow large enough to cover a typical app window (primary work area minus margin — not hard-capped at ~960×640).
3. Hovering each tray icon shows a short tooltip naming the action.

Actual
Tray floats detached after side changes; max size matches the small desk159 clamp; icons have no hover tips.

Environment
- desktop_app.py desk159; native ring + Look 4 tray
- Related: KAN-528/529

Replication
1. Restart desktop_app.py (desk159). Manual → Start.
2. Drag the ring toward a screen edge so the tray should flip sides — tray stays detached.
3. Resize from a corner to maximum — still too small for a window.
4. Hover tray icons — no tooltip.

Relates: KAN-528, KAN-529"""

TEST = """Verification for tray glue + larger max + hover tooltips.

Procedure
1. desktop_app.py on fix cache-bust; Manual → Start.
2. Drag ring across the screen — tray stays glued; flips east/west without floating away.
3. Resize toward a large window — hole can cover it (within work-area margin).
4. Hover each tray icon — tooltip text appears.

Evidence
Screenshot glued tray after edge move; large resize; note tooltips; pytest dock/max helpers."""


def main() -> None:
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    out: dict[str, object] = {}
    try:
        types = client.get(f"{base}/rest/api/3/issuetype").json()
        bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
        test_id = next(
            (t["id"] for t in types if str(t.get("name", "")).lower() == "test"),
            None,
        )
        r = client.post(
            f"{base}/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": "KAN"},
                    "issuetype": {"id": bug_id},
                    "summary": "Charter tray detaches on side flip; max too small; need hover tips",
                    "description": adf_text(BUG),
                }
            },
        )
        r.raise_for_status()
        bug = r.json()["key"]
        out["bug"] = bug
        test_key = None
        if test_id:
            tr = client.post(
                f"{base}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": "KAN"},
                        "issuetype": {"id": test_id},
                        "summary": f"test: {bug} tray glue + max capture + tooltips",
                        "description": adf_text(TEST),
                    }
                },
            )
            tr.raise_for_status()
            test_key = tr.json()["key"]
            out["test"] = test_key
        for other in ("KAN-528", "KAN-529"):
            lr = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": bug},
                    "outwardIssue": {"key": other},
                },
            )
            out[f"link_{other}"] = lr.status_code
        if test_key:
            lr = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": test_key},
                    "outwardIssue": {"key": bug},
                },
            )
            out["link_test"] = lr.status_code
        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
