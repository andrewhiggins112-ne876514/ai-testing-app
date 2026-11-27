"""Create/fix Bug: Manual Start hangs when opening OS Charter float (KAN-386)."""
from __future__ import annotations

import argparse
import json
import ssl
from pathlib import Path

import httpx

from jira_kan_slice_closeout import load_creds  # type: ignore


def adf_text(text: str) -> dict:
    paras = []
    for block in text.strip().split("\n"):
        paras.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": block}] if block else [],
            }
        )
    return {"type": "doc", "version": 1, "content": paras or [{"type": "paragraph", "content": []}]}


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
                    "summary": "Manual Start session hangs — OS Charter float bridge deadlock",
                    "description": adf_text(
                        """Symptom
Clicking Manual → Start session appears to do nothing (status stuck on Starting Charter Frame… or area closes with no visible frame).

Expected
Charter Frame opens (OS float and/or in-app overlay) and recording controls are usable.

Actual
startManualSession awaits pywebview.api.charter_float_open; DesktopApi.charter_float_open calls evaluate_js on the float window while the main window JS is blocked waiting for the API promise — classic pywebview deadlock. Session may already be open server-side.

Environment
desktop_app.py desk140, Windows pywebview 6.2.1 Edge WebView2, KAN-386.

Replication
1. Run desktop_app.py (desk140).
2. App → Manual; enter a charter; leave Link to Jira and Assist off.
3. Click Start session.
4. Observe: no usable Charter Frame; UI appears stuck / no float.

Relates: KAN-386, KAN-387."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-387"):
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
Root cause: DesktopApi.charter_float_open called evaluate_js on the float window from inside a main-window js_api call, deadlocking Start. Also no timeout/fallback if the float bridge stalled.

Fix: remove evaluate_js from open path; float page loads open session via GET /api/manual-sessions/open; JS Promise.race timeout falls back to in-app Charter Frame; always show in-app overlay first then hide if float reports ok. Cache-bust desk141.

Files: desktop_app.py, ui/desktop/desktop.js, ui/desktop/charter_float.js, ui/desktop/index.html, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart desktop_app.py → Manual Start shows frame (float and/or in-app)."""
                )
            }
            client.post(f"{base}/rest/api/3/issue/{key}/comment", json=comment).raise_for_status()
            if args.mark_done:
                trans = client.get(f"{base}/rest/api/3/issue/{key}/transitions").json()
                done = next(
                    (t["id"] for t in trans.get("transitions") or [] if t.get("name") == "Done"),
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
    # Allow importing sibling script helpers
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
