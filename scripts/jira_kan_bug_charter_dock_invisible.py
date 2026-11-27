"""Create/fix Bug: Charter OS dock taskbar-only; in-app overlay vanishes on Start."""
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
                    "summary": "Manual Start: in-app Charter vanishes; OS dock on taskbar but not visible",
                    "description": adf_text(
                        """Symptom
After Start session, Charter overlay appears briefly then disappears. A Charter Frame entry is on the taskbar but clicking it does not show the dock/window.

Expected
Recording controls stay usable (in-app Charter Frame and/or visible OS dock under the capture ring).

Actual
showCharterFrame hides the in-app overlay whenever charter_float_open returns ok. The compact dock WebView can remain taskbar-only / not restored on-screen, so Start looks like a flash then nothing.

Environment
desktop_app.py desk144, Windows pywebview dock_plus_native_ring, KAN-386/503/504.

Replication
1. Run desktop_app.py (desk144).
2. App → Manual; enter charter; Start session.
3. Observe overlay flash then gone; taskbar shows Charter Frame; activate does not surface usable dock.

Relates: KAN-386, KAN-387, KAN-504."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-386", "KAN-387", "KAN-504"):
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
Root cause: JS hid in-app Charter whenever OS float returned ok, even when the dock was only a taskbar ghost. dock_geom_for_bbox also clamped with full-float MIN_WINDOW_H and a fake 10000x10000 work area, so dock height/placement was wrong.

Fix: keep in-app overlay visible while recording (OS ring+dock is additive); clamp dock to primary work area with dock-sized mins; restore/show + native TOPMOST ShowWindow after place; open returns error if dock place fails. Cache-bust desk145.

Files: ui/desktop/desktop.js, desktop_app.py, plans/charter_ring_native.py, ui/desktop/index.html, tests/test_charter_float.py

Verify: pytest tests/test_charter_float.py; restart desktop_app → Manual Start keeps in-app frame; dock appears on-screen under/near ring."""
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
