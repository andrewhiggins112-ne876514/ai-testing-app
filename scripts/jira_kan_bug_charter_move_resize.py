"""Create Bug: native Charter overlay cannot be moved or resized (desk158)."""
from __future__ import annotations

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


BUG = """Symptom
Designer (desk158 / after KAN-525 Resume restore): Charter OS overlay (hollow cyan ring + Look 4 side tray) opens and Resume works, but the overlay cannot be moved and cannot be resized.

Expected
1. Capture hole / ring can be dragged to reposition over the AUT (snip-tool style).
2. Capture region can be resized (edges/corners or explicit controls) within FR-MAN-1 min/max bounds.
3. Side tray stays glued beside the hole after move/resize.

Actual
Overlay places on Start/Resume but has no drag or resize affordance. Native TOOLWINDOW host (KAN-525) dropped the old WebView header drag path; ring bars have no drag/resize hit targets.

Environment
- Product: desktop_app.py desk158 (native ring + owner-draw side tray)
- OS: Windows home PC
- Related: KAN-525/526 host restore; KAN-386 float drag; KAN-512 Look 4

Replication
1. Restart desktop_app.py (desk158). End any stuck session.
2. Manual → Start (short charter). Confirm ring + side tray appear.
3. Try to drag the ring or tray to move the capture hole — cannot move.
4. Try to resize the capture hole — cannot resize.
5. Resume Charter still re-arms chrome (unrelated; works).

Notes for next Build chat
Implement drag on ring chrome and/or tray, plus resize handles; keep tray docked via dock_geom_for_bbox. Prefer native Win32 hit targets on ring thread (no second WebView). Relates KAN-525/526; do not reopen under-ring.

Relates: KAN-525, KAN-526, KAN-512, KAN-386."""

TEST = """Verification for Charter move/resize Bug.

Procedure
1. desktop_app.py on the fix cache-bust; Manual → Start.
2. Drag ring (or documented handle) — hole + side tray move together.
3. Resize hole via edges/corners or controls — min capture size respected; tray re-docks.
4. Resume after move still shows chrome at last geom (or honest default).

Evidence
Screenshot after drag + after resize; note cache-bust; pytest geom helpers if added."""


def main() -> None:
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    out: dict[str, object] = {}
    try:
        types = client.get(f"{base}/rest/api/3/issuetype").json()
        bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
        test_id = next(
            (
                t["id"]
                for t in types
                if str(t.get("name", "")).lower() == "test"
            ),
            None,
        )
        r = client.post(
            f"{base}/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": "KAN"},
                    "issuetype": {"id": bug_id},
                    "summary": "Charter overlay cannot be moved or resized (native desk158)",
                    "description": adf_text(BUG),
                }
            },
        )
        r.raise_for_status()
        bug = r.json()["key"]
        out["bug"] = bug

        test_key = None
        if test_id:
            tr = client.post(
                f"{base}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": "KAN"},
                        "issuetype": {"id": test_id},
                        "summary": f"test: {bug} Charter overlay move + resize",
                        "description": adf_text(TEST),
                    }
                },
            )
            tr.raise_for_status()
            test_key = tr.json()["key"]
            out["test"] = test_key

        for other in ("KAN-525", "KAN-526", "KAN-512", "KAN-386", "KAN-510"):
            lr = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": bug},
                    "outwardIssue": {"key": other},
                },
            )
            out[f"link_{other}"] = lr.status_code
        if test_key:
            lr = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": test_key},
                    "outwardIssue": {"key": bug},
                },
            )
            out["link_test"] = lr.status_code

        note = (
            f"Designer desk158: Resume returned (KAN-525/526 path OK). "
            f"New residual Bug {bug}: overlay cannot move/resize — next Build chat. "
            f"Test {test_key or 'n/a'}."
        )
        for key in ("KAN-525", "KAN-526", bug):
            cr = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(note)},
            )
            out[f"comment_{key}"] = cr.status_code
        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
