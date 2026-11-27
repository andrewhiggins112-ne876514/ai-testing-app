"""Create/fix Bug: Charter float opaque oversized non-snip (KAN-386)."""
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
                    "summary": "Charter float is opaque, oversized, not snip-style click-through",
                    "description": adf_text(
                        """Symptom
After Manual Start, Charter Frame float opens larger than the screen, cannot be resized, blocks the desktop with an opaque panel, and most dock buttons appear broken. Tester cannot see or interact with the AUT behind the frame.

Expected
Snipping-tool / Computer-Use style hollow ring: resizable capture hole shows the desktop/AUT and passes clicks through; header+dock chrome stay usable for Note / Still / Annotate / End; size fits primary monitor.

Actual
Solid opaque WebView covering most of the screen; relative frame used virtual-desktop size; no hollow region; resize unavailable; controls unreliable.

Environment
Windows desktop_app.py desk141, pywebview Edge WebView2, Manual charter-only Start.

Replication
1. Restart desktop_app.py.
2. App → Manual; charter e.g. "the desktop"; Link to Jira off; Assist off.
3. Start session.
4. Observe oversized opaque float; try to click desktop behind; try resize and dock buttons.

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
Root cause: float used opaque full-bleed WebView sized from relative frame on the whole virtual desktop (multi-monitor → oversized). No OS hole, so AUT was covered and unusable.

Fix (desk142): snip-sized geom clamped to primary monitor; Win32 SetWindowRgn hollow ring (header/sides/dock stay hittable; capture hole click-through); HTML edge/corner resize via charter_float_set_size; dock ensureSession + clearer chip errors. Files: plans/charter_float.py, desktop_app.py, ui/desktop/charter_float.*, tests/test_charter_float.py.

Verify: pytest tests/test_charter_float.py; restart desktop → Start → see desktop through hole, click AUT, resize edges, Note/Still/End."""
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
