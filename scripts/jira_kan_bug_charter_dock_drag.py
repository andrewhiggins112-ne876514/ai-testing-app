"""Create/fix Bug: Charter chrome on home; dock/controls not movable (KAN-507)."""
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
                    "summary": "Manual Charter: chrome on app open; dock/controls not movable; sideways-only resize",
                    "description": adf_text(
                        """Symptom
1. Opening the desktop app shows Charter controls without starting a session.
2. After Start, in-app controls + cyan dock appear but neither can be moved.
3. Dock appears resizable only sideways and only a limited amount.

Expected
Home/orb has no Charter chrome. Start shows one movable snip UI: drag dock header moves ring+dock; ± resizes capture; dock chrome size stays fixed.

Actual
refreshManualSessions armed showCharterFrame on every load (including home) when an open session existed. Dual chrome (in-app + OS) left fixed bottom controls and a non-dragging dock (easy_drag=False without JS drag API). Accidental WinForms-ish sideways resize confused capture sizing.

Environment
desktop_app.py desk145→desk146, Windows pywebview dock_plus_native_ring.

Replication
1. Leave a Manual session open; restart desktop_app — controls appear on home.
2. Start a session — see in-app dock + cyan OS dock; try to drag either.
3. Try to resize the cyan dock from edges.

Relates: KAN-386, KAN-506."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-506"):
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
Root cause: auto-arm on refreshManualSessions without Manual open; dual immovable chrome; dock had no drag_by path; capture vs dock resize confused.

Fix: arm Charter only when Manual area open; hide in-app when OS float ok; charter_float_drag_by + header pointer drag moves dock with ring glued above; dock chrome size locked (± is capture only). desk146.

Files: desktop_app.py, ui/desktop/desktop.js, charter_float.js/html/css, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart desktop — home clean; Manual Start → drag header moves ring+dock; ± changes capture."""
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
