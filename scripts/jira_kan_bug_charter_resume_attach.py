"""Create/fix Bug: Manual auto-arms Charter; dock not on frame; can't leave window."""
from __future__ import annotations

import argparse
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--fix", metavar="KEY")
    ap.add_argument("--mark-done", action="store_true")
    args = ap.parse_args()
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        if args.create:
            types = client.get(f"{base}/rest/api/3/issuetype").json()
            bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
            body = {
                "fields": {
                    "project": {"key": "KAN"},
                    "issuetype": {"id": bug_id},
                    "summary": "Manual: Charter auto-arms on open; controls not on frame; can't leave app window",
                    "description": adf_text(
                        """Symptom
1. Opening Manual immediately shows Charter overlay/controls without pressing Start (leftover open session auto-armed).
2. Overlay move/resize works but cannot leave the main app window.
3. Controls sit separately (bottom of window) instead of on the overlay edge; should move with the frame or outside via OS dock.

Expected
Open Manual idle unless user Start/Resume. Controls attach under the cyan frame. With OS float, dragging moves capture outside the app window.

Actual
refreshManualSessions called showCharterFrame whenever Manual was open and a session was open. In-app dock was viewport-bottom fixed. In-app frame is inherently clipped to the WebView.

Environment
desktop_app.py desk147→desk148.

Replication
1. Start a session; End not required — reopen Manual (or leave session open) → overlay appears without Start.
2. Drag cyan frame — stops at app edges.
3. Observe controls not glued to frame.

Relates: KAN-386, KAN-508."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-508"):
                client.post(
                    f"{base}/rest/api/3/issueLink",
                    json={
                        "type": {"name": "Relates"},
                        "inwardIssue": {"key": key},
                        "outwardIssue": {"key": other},
                    },
                )
            return

        if args.fix:
            key = args.fix
            comment = {
                "body": adf_text(
                    """Fix comment
Root cause: auto showCharterFrame on Manual refresh; dock CSS fixed to viewport bottom; in-app drag only updates relative coords inside the window.

Fix: Resume Charter / End open session instead of auto-arm; applyCharterFrameRect anchors dock under cyan rect; when OS float active, pointer drag nudges/resizes the outside-window ring. desk148.

Files: ui/desktop/desktop.js, desktop.css, index.html, charter_float.*, desktop_app.py, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart → Manual with open session shows Resume (no overlay); Start → controls under frame; drag OS header / Charter label moves ring outside app."""
                )
            }
            client.post(
                f"{base}/rest/api/3/issue/{key}/comment", json=comment
            ).raise_for_status()
            if args.mark_done:
                trans = client.get(f"{base}/rest/api/3/issue/{key}/transitions").json()
                done = next(
                    (
                        t["id"]
                        for t in trans.get("transitions") or []
                        if t.get("name") == "Done"
                    ),
                    None,
                )
                if done:
                    client.post(
                        f"{base}/rest/api/3/issue/{key}/transitions",
                        json={"transition": {"id": done}},
                    ).raise_for_status()
            print(json.dumps({"fixed": key, "done": bool(args.mark_done)}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
