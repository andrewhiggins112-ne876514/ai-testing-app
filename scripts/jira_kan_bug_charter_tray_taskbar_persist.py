"""Create Bug: Charter tray still taskbar-only after Resume/End→Start (council)."""
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
    args = ap.parse_args()
    if not args.create:
        ap.error("pass --create")
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        types = client.get(f"{base}/rest/api/3/issuetype").json()
        bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
        test_id = next(
            (
                t["id"]
                for t in types
                if str(t.get("name", "")).lower() == "test"
                or t.get("name") == "Test"
            ),
            None,
        )
        body = {
            "fields": {
                "project": {"key": "KAN"},
                "issuetype": {"id": bug_id},
                "summary": "Charter tray still taskbar-only after Resume/End→Start (desk155); side tray preferred",
                "description": adf_text(
                    """Symptom
Designer (2026-11-28, desk155 / KAN-524 under-ring restore): after Resume Charter or End open session then Start session again, the OS Charter overlay (hollow ring + Look 4 verb tray) still does not appear on the desktop. A Charter Frame entry is visible on the Windows taskbar; clicking that taskbar entry does nothing (window does not surface). Manual can still show Recording / session chip.

Expected
1. After Start or Resume, hollow capture ring + Look 4 verb tray are visibly placed on the desktop (not taskbar-only).
2. Activating the taskbar Charter Frame entry must restore / bring the tray (and ring chrome) to a usable on-screen position.
3. Designer preference (CR input for council): tray/bar on the SIDE of the capture ring (Look 4 Compact rail), not along the bottom / under-ring. Bottom placement was a temporary reliability experiment and is not the desired UX.

Actual
Overlay missing on desktop after End→Start / Resume→Start. Taskbar shows Charter Frame; click is a no-op. Prior fixes KAN-516…524 (recording unlock, HWND floor, no SW_HIDE, soft visibility, under-ring 480×88) did not clear this human-reported path.

Environment
- Product: desktop_app.py (pywebview + Edge WebView2), cache-bust desk155
- OS: Windows 10/11 home PC (DESKTOP-NAL5HLJ)
- Mode: Manual / FR-MAN-1 Look 4 (KAN-512); native ring + float dock
- Related history: KAN-518/520/522/524 taskbar ghost / invisible tray

Replication
1. Fully restart desktop_app.py (desk155).
2. App → Manual. If a stuck Recording session exists, End it.
3. Enter a charter → Start session (or Resume Charter on an open session).
4. Observe: Manual may show Recording / session chip; hollow ring + tray not visible on desktop.
5. Find Charter Frame on the Windows taskbar → click it.
6. Observe: nothing surfaces; overlay still unusable.
7. End → Start again (or Resume → Start path) — same failure.

Council hold
Do NOT patch in Build until Advisory Council reviews architecture options (side tray vs under-ring, HWND restore, alternate chrome host). Bug raised for council solution — Designer requested review, not another silent dock tweak.

Relates: KAN-512 (G+tray Look 4), KAN-386/387 (float), KAN-510 (outside-window residual), KAN-518/520/522/524 (prior tray reliability bugs)."""
                ),
            }
        }
        r = client.post(f"{base}/rest/api/3/issue", json=body)
        r.raise_for_status()
        key = r.json()["key"]
        relates = (
            "KAN-512",
            "KAN-386",
            "KAN-387",
            "KAN-510",
            "KAN-518",
            "KAN-520",
            "KAN-522",
            "KAN-524",
        )
        for other in relates:
            client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": key},
                    "outwardIssue": {"key": other},
                },
            )
        test_key = None
        if test_id:
            tr = client.post(
                f"{base}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": "KAN"},
                        "issuetype": {"id": test_id},
                        "summary": f"test: {key} Charter tray visible after Resume/End→Start (side preferred)",
                        "description": adf_text(
                            f"""Intro
Verification for Bug {key} — Charter OS tray must be on-desktop after Resume/End→Start; taskbar activate must restore; side tray preferred per Designer.

Who this is for
Testers + agents after council-approved fix lands in Build.

Test procedure
1. Restart desktop_app.py on the fixed cache-bust.
2. Manual → End any open session → Start with a short charter.
   Expected: hollow ring + Look 4 side tray visible on desktop (not taskbar-only).
3. End session → Start again.
   Expected: tray/ring reappear on desktop every time.
4. If a taskbar Charter Frame entry exists, click it.
   Expected: tray restores on-screen (usable verbs).
5. Confirm Manual session chip Still/Note/End still work as backup.

Acceptance criteria
- No taskbar-only ghost after Start/Resume/End→Start.
- Taskbar activate restores chrome.
- Placement matches council-accepted side-tray Look 4 (unless council explicitly accepts alternate).

Evidence
Screenshot of desktop with ring+tray; note cache-bust; optional CU/human-hands confirm."""
                        ),
                    }
                },
            )
            tr.raise_for_status()
            test_key = tr.json()["key"]
            client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": test_key},
                    "outwardIssue": {"key": key},
                },
            )
        # Comment: hold for council
        client.post(
            f"{base}/rest/api/3/issue/{key}/comment",
            json={
                "body": adf_text(
                    """Agent note — raised for Advisory Council (no Build patch this turn)
Designer confirmed desk155 still reproduces: Resume/End→Start → overlay missing; taskbar Charter Frame click no-op. Preference: side tray, not bottom/under-ring. Prior reliability bugs (KAN-516…524) insufficient. Hold Build coding until council verdict on chrome host / restore strategy / Look 4 side placement."""
                )
            },
        )
        print(json.dumps({"created": key, "test": test_key}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
