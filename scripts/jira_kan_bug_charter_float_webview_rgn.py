"""Create/fix Bug: WebView hollow region opaque + click crash (KAN-386)."""
from __future__ import annotations

import argparse
import json
import ssl
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jira_kan_slice_closeout import load_creds  # noqa: E402


def adf_text(text: str) -> dict:
    paras = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": block}] if block else [],
        }
        for block in text.strip().split("\n")
    ]
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
                    "summary": "Charter float middle stays opaque; click crashes app",
                    "description": adf_text(
                        """Symptom
After Start, Charter Frame middle is solid grey (not a clear hole). Clicking the middle crashes the float overlay and the desktop app.

Expected
Snip-style clear capture hole — see and click the AUT through it; dock controls remain usable; no crash.

Actual
WebView2 window stayed opaque despite SetWindowRgn; clicking the intended hole area crashed WebView/app.

Environment
Windows desktop_app.py desk142, Edge WebView2, Manual charter-only Start.

Replication
1. Run desktop_app.py (desk142).
2. Manual → Start with a charter.
3. Observe grey middle (not clear).
4. Click middle → crash.

Relates: KAN-386, KAN-387, KAN-502."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-387", "KAN-502"):
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
Root cause: SetWindowRgn on the Edge WebView2 float HWND does not yield a clear click-through hole and can crash on click.

Fix (desk143): stop punching WebView. Compact dock-only pywebview chrome + separate native Win32 hollow cyan ring (WS_EX_TRANSPARENT click-through). Move/resize via dock arrows ±. Still hides ring+dock then ImageGrab.

Files: plans/charter_ring_native.py, desktop_app.py, ui/desktop/charter_float.*, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart desktop → Start → clear desktop inside cyan ring; click AUT without crash; Note/Still from dock."""
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
    main()
