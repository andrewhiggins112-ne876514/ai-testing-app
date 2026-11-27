"""Create/fix Bug: Manual Start glitch + library closes Manual + charter locked (KAN-386)."""
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
    paras = []
    for block in text.strip().split("\n"):
        paras.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": block}] if block else [],
            }
        )
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
                    "summary": "Manual: charter hard to type; library click closes page; Start only brief glitch",
                    "description": adf_text(
                        """Symptom
Designer must close/reopen Manual repeatedly to type in the charter box. Clicking a session library row closes the Manual page. Start session only glitches Manual for ~0.5s then looks unchanged.

Expected
1. Idle Manual: charter textarea is focusable/typeable.
2. Library row reopen keeps Manual open and shows review.
3. Start keeps Manual open with clear recording status (and Charter Frame / dock), or a clear already-open message.

Actual
1. Orphan open session + data-loop-stage=recording disables .manual-primary (pointer-events:none) so charter cannot be typed.
2. reopenManualFromLibrary calls openArea(\"manual\") while Manual is already open — openArea toggles close.
3. startManualSession calls closeArea() after showCharterFrame, so Manual vanishes (looks like a no-op if float is weak).

Environment
desktop_app.py desk143→desk144, Windows pywebview, OPERATE Manual / KAN-386 float path.

Replication
1. Run desktop_app.py; App → Manual.
2. If a prior session is still open, try typing in Charter — field may be inert until End.
3. With Manual open, click a session library row — Manual closes.
4. Enter a charter; Start session — Manual flashes/closes; no clear recording UI if float is easy to miss.

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
Root cause: (1) openArea toggles closed when already on Manual — library reopen and End/Cancel paths used openArea(\"manual\"). (2) Start called closeArea() after arming the frame, so Manual vanished (half-second glitch). (3) Stuck recording stage / open session left charter textarea pointer-events:none via .manual-primary; refresh did not clear recording when no open session.

Fix: ensureAreaOpen (no toggle-close); Start keeps Manual open + clearer session_already_open status; refresh restores idle when no open session and states recording lock; desk144 cache-bust.

Files: ui/desktop/desktop.js, ui/desktop/index.html, ui/desktop/charter_float.html, desktop_app.py, tests/test_charter_float.py (+ desk144 marker sweep)

Verify: pytest tests/test_charter_float.py tests/test_manual_session_library.py; restart desktop_app.py → Manual: type charter when idle; Start stays on Manual with status; library row keeps Manual open."""
                )
            }
            client.post(f"{base}/rest/api/3/issue/{key}/comment", json=comment).raise_for_status()
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
