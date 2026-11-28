"""KAN-525 follow-up: Bug for missing Resume + Fix comment; polish note on 526."""
from __future__ import annotations

import json
import ssl
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jira_kan_slice_closeout import load_creds  # type: ignore


def mark_done(client: httpx.Client, base: str, key: str) -> int:
    trans = client.get(f"{base}/rest/api/3/issue/{key}/transitions").json()
    done_id = next(
        (
            t["id"]
            for t in trans.get("transitions") or []
            if t.get("name") == "Done"
        ),
        None,
    )
    if not done_id:
        return 0
    r = client.post(
        f"{base}/rest/api/3/issue/{key}/transitions",
        json={"transition": {"id": done_id}},
    )
    return r.status_code


def adf_text(text: str) -> dict:
    paras = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": block}] if block else [],
        }
        for block in text.strip().split("\n")
    ]
    return {"type": "doc", "version": 1, "content": paras}


BUG = """Symptom
Designer (desk157 human AC on KAN-525): End→Start works; hollow ring + side tray place. Resume Charter control is missing / not usable for the Resume path. Side tray verb controls look cheap/outdated (stock Win32 BUTTON letter chrome).

Expected
1. While a Manual session is open, Resume Charter stays available to re-arm Look 4 side chrome (KAN-526 path: Start → leave session open → Resume).
2. Side tray verbs match Look 4 compact icon rail (owner-drawn), not default Windows flat buttons.

Actual
Resume Charter stayed hidden whenever charterOsFloatActive was true, so the Resume AC path was unreachable in-process. Tray used BS_FLAT BUTTON children with single-letter captions.

Environment
desktop_app.py desk157; Windows; native TOOLWINDOW tray host.

Replication
1. Start desktop_app.py; Manual → Start with a short charter.
2. Observe ring + side tray (pass).
3. Look for Resume Charter while session remains open — missing/hidden.
4. End → Start works; Resume path still unavailable.

Relates: KAN-525, KAN-526."""

FIX = """Fix (desk158)

Root cause
setManualResumeUi hid Resume whenever charterOsFloatActive was true; successful Start also forced Resume hidden. That blocked KAN-526 Resume re-arm while a session stayed open.

What changed
- Resume Charter stays visible whenever an open session is pending (re-arm allowed).
- Chip Restore label → Resume (same handler).
- Native tray: remove stock Win32 BUTTONs; owner-drawn Look 4 icon cells (hover + toggle on-state) on the TOOLWINDOW rail.

Files
ui/desktop/desktop.js, ui/desktop/index.html, plans/charter_ring_native.py, desktop_app.py (desk158), tests/test_charter_float.py

Verify
pytest tests/test_charter_float.py tests/test_manual_ia.py — passed markers for Resume + owner-draw.
Human: Start → Resume Charter visible → click Resume re-places ring+tray; tray icons not letter buttons."""


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
        r = client.post(
            f"{base}/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": "KAN"},
                    "issuetype": {"name": "Bug"},
                    "summary": "Resume Charter hidden during open session; tray buttons look cheap (desk157)",
                    "description": adf_text(BUG),
                }
            },
        )
        r.raise_for_status()
        bug = r.json()["key"]
        out["bug"] = bug
        for other in ("KAN-525", "KAN-526"):
            lr = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": bug},
                    "outwardIssue": {"key": other},
                },
            )
            out[f"link_{other}"] = lr.status_code
        for key, body in (
            (bug, FIX),
            ("KAN-525", FIX),
            ("KAN-526", FIX + "\n\nRe-check Resume path + tray icon polish on desk158."),
        ):
            cr = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(body)},
            )
            out[f"comment_{key}"] = cr.status_code
            cr.raise_for_status()
        out["transition"] = mark_done(client, base, bug)
        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
