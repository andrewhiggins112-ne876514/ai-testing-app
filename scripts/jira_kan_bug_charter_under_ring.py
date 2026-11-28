"""Create/fix Bug: Recording chip present but Look 4 tray invisible (KAN-524)."""
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
    ap.add_argument("--check", metavar="KEY")
    args = ap.parse_args()
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        if args.check:
            r = client.get(
                f"{base}/rest/api/3/issue/{args.check}",
                params={"fields": "summary,status,issuetype"},
            )
            print(r.status_code, r.text[:500])
            return

        if args.create:
            types = client.get(f"{base}/rest/api/3/issuetype").json()
            bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
            body = {
                "fields": {
                    "project": {"key": "KAN"},
                    "issuetype": {"id": bug_id},
                    "summary": "Manual Recording: session chip shown but Look 4 tray missing on desktop",
                    "description": adf_text(
                        """Symptom
After Start session, Manual shows Recording + session chip (Restore / End) but the OS Charter hollow ring + icon tray is not visible on the desktop. Status says tray should be on desktop; End open session / chip End exist, but capture chrome is gone.

Expected
Look 4 shell places a visible under-ring horizontal verb bar (Still/Note/Pause/Assist/Mist/End/Cancel) with the hollow capture ring. Manual session chip remains as backup with Still / Note / Restore / End.

Actual
Side-rail tray WebView stayed taskbar-only / invisible while UI state said Recording. Session chip lacked Still/Note backup verbs.

Environment
desktop_app.py desk154, Windows pywebview + native ring, Look 4 after KAN-512…522.

Replication
1. Run desktop_app.py.
2. App → Manual; enter charter (e.g. desktop); Start session.
3. Observe Recording + chip; confirm no OS tray/ring on desktop.
4. Note Start stays disabled; End only via chip / End open session.

Relates: KAN-512, KAN-386, KAN-387, KAN-520, KAN-522."""
                    ),
                }
            }
            r = client.post(f"{base}/rest/api/3/issue", json=body)
            r.raise_for_status()
            key = r.json()["key"]
            print(json.dumps({"created": key}))
            for other in ("KAN-512", "KAN-386", "KAN-387", "KAN-520", "KAN-522"):
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
Root cause: Look 4 side-rail tray HWND class stayed unreliable on WebView2 (ghost / invisible) while Manual correctly entered Recording with a session chip. charter_float.js still targeted the vertical #cf-rail after HTML/CSS moved to a horizontal bar.

Fix (desk155): restore proven under-ring horizontal dock (MIN 480x88); rewrite charter_float HTML/CSS/JS for under-ring Look 4 bar; Manual session chip Still / Note (+ note row) as backup when tray missing; soft force-visible height uses MIN_TRAY_HWND_H.

Files: plans/charter_ring_native.py, desktop_app.py, ui/desktop/charter_float.*, ui/desktop/desktop.js|css|index.html, tests/test_charter_float.py (+ desk155 sweep)

Verify: pytest tests/test_charter_float.py — passed; restart desktop_app.py (desk155), End any stuck Recording session, Start again — under-ring bar should appear; chip Still/Note/End always available."""
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
            return
    finally:
        client.close()


if __name__ == "__main__":
    main()
