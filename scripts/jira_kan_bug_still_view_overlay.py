"""Close KAN-534/535 after Designer capture confirm; raise overlay + view Bugs.

Standing authorization (bugs found during slice). Relates to KAN-534/535.
"""
from __future__ import annotations

import json
import ssl
import sys
import time
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


def transition_done(client: httpx.Client, base: str, key: str) -> int:
    tr = client.get(f"{base}/rest/api/3/issue/{key}/transitions")
    tr.raise_for_status()
    for t in tr.json().get("transitions") or []:
        name = str(t.get("name") or "").lower()
        if name in {"done", "closed", "complete", "completed"}:
            r = client.post(
                f"{base}/rest/api/3/issue/{key}/transitions",
                json={"transition": {"id": t["id"]}},
            )
            return r.status_code
    return 0


def main() -> None:
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    out: dict[str, object] = {"created": []}
    try:
        types = client.get(f"{base}/rest/api/3/issuetype").json()
        bug_id = next(t["id"] for t in types if t.get("name") == "Bug")
        test_id = next(
            (t["id"] for t in types if str(t.get("name", "")).lower() == "test"),
            None,
        )

        close_note = (
            "Designer desk162: Still capture works — Manual shows the still was saved "
            "(count/status). Closing capture Bug. Residuals ticketed: on-overlay confirm "
            "+ open/view still image (no gallery/link today). Then Note verbs / KAN-510."
        )
        for key in ("KAN-534", "KAN-535"):
            cr = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(close_note)},
            )
            out[f"comment_{key}"] = cr.status_code
            out[f"done_{key}"] = transition_done(client, base, key)
            time.sleep(0.2)

        items = [
            (
                "Charter Still has no on-overlay saved confirmation",
                """Symptom
Designer (desk162): tray Still saves (visible later in Manual) but while looking at the OS overlay/tray there is no indication the still saved.

Expected
Immediate visible confirm near the tray/ring (brief status tip or flash) so the tester does not have to switch to Manual to know Still worked. Failures also show on-overlay.

Actual
No on-overlay feedback; only Manual status/count updates.

Environment
desk162; native Look 4 tray; Relates KAN-534/535

Replication
1. Manual → Start; focus on overlay/AUT.
2. Click tray Still.
3. Observe tray/ring — no saved confirmation while overlay is foreground.

Notes
Do not require opening Manual to know Still succeeded.""",
                "On-overlay Still saved / fail tip",
                """Procedure
1. Start charter; click Still while overlay is foreground.
2. Pass: brief on-overlay tip/flash “Still saved” (or honest fail); Manual still updates.
3. Screenshot optional.

Evidence
desk cache-bust; pytest tip/flash markers if added.""",
            ),
            (
                "Manual has no way to open or view a captured still",
                """Symptom
Designer (desk162): Still count/status shows in Manual after tray Still, but there is no review link, Open control, or image preview for the still. Review text lists still ids only.

Expected
Tester can open/view the captured PNG from Manual (open session or after End review) — clickable still list and/or preview image. Not a full gallery; at least last still + review list openable.

Actual
“N stills” / “open from review; not a gallery” copy with no open path; review pre lists ids without images.

Environment
desk162; FR-MAN-1 opt-in stills; Relates KAN-534/535

Replication
1. Manual → Start → Still → see count in Manual.
2. Try to view the image — no Open/link/preview.
3. End → review — still ids only, no image.

Notes
Serve level-scoped still via API FileResponse; do not rely on raw filesystem paths in UI.""",
                "Open/view captured Manual still",
                """Procedure
1. Capture a still; in Manual click Open last still / still row — image shows.
2. End → review — stills openable/previewable.
3. pytest covers GET still file + UI markers.

Evidence
Screenshot of preview; pytest pass count.""",
            ),
        ]

        created_keys: list[str] = []
        for summary, bug_body, test_suf, test_body in items:
            r = client.post(
                f"{base}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": "KAN"},
                        "issuetype": {"id": bug_id},
                        "summary": summary,
                        "description": adf_text(bug_body),
                    }
                },
            )
            r.raise_for_status()
            bug = r.json()["key"]
            created_keys.append(bug)
            time.sleep(0.25)
            test_key = None
            if test_id:
                tr = client.post(
                    f"{base}/rest/api/3/issue",
                    json={
                        "fields": {
                            "project": {"key": "KAN"},
                            "issuetype": {"id": test_id},
                            "summary": f"test: {bug} {test_suf}",
                            "description": adf_text(test_body),
                        }
                    },
                )
                tr.raise_for_status()
                test_key = tr.json()["key"]
                time.sleep(0.25)
                client.post(
                    f"{base}/rest/api/3/issueLink",
                    json={
                        "type": {"name": "Relates"},
                        "inwardIssue": {"key": test_key},
                        "outwardIssue": {"key": bug},
                    },
                )
            for other in ("KAN-534", "KAN-535", "KAN-512"):
                client.post(
                    f"{base}/rest/api/3/issueLink",
                    json={
                        "type": {"name": "Relates"},
                        "inwardIssue": {"key": bug},
                        "outwardIssue": {"key": other},
                    },
                )
                time.sleep(0.15)
            out["created"].append({"bug": bug, "test": test_key, "summary": summary})

        # Point Active toward view-still first (more blocking), then overlay tip.
        view_bug = created_keys[1] if len(created_keys) > 1 else created_keys[0]
        for key in ("KAN-534", "KAN-535"):
            client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={
                    "body": adf_text(
                        f"Next Active: {view_bug} (open/view still), then "
                        f"{created_keys[0]} (on-overlay tip). Note verbs after. "
                        "Do not start voice / FR-MAN-2."
                    )
                },
            )
            time.sleep(0.15)

        print(json.dumps(out, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
