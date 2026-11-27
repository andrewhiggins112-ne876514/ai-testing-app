"""Create/fix Bug: Start hides in-app Charter again after OS float ok (KAN-508)."""
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
                    "summary": "Manual Start: in-app Charter overlay flash then disappears again",
                    "description": adf_text(
                        """Symptom
After Start session, Charter overlay appears then immediately disappears (same as KAN-506).

Expected
In-app Charter Frame stays visible for the recording session (OS ring/dock may also show).

Actual
KAN-507 re-introduced hide of charterFrameRoot when openOsCharterFloat returned ok, recreating the flash→gone UX whenever the OS dock is weak or easy to miss.

Environment
desktop_app.py desk146→desk147, Windows pywebview.

Replication
1. Restart desktop_app (desk146).
2. Manual → charter → Start session.
3. Overlay flashes then vanishes.

Relates: KAN-386, KAN-506, KAN-507."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-506", "KAN-507"):
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
Root cause: KAN-507 showCharterFrame hid in-app chrome when floated===true (regression of KAN-506).

Fix: never hide in-app Charter when OS float reports ok; OS ring/dock stays additive. Hard comment + pytest guard. desk147.

Files: ui/desktop/desktop.js, index.html, charter_float.html, desktop_app.py, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart → Manual Start keeps overlay visible."""
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
