"""Create focused Bugs for desk160 residuals: tip size + inert tray verbs.

Also marks KAN-528/529/530/531 Done after Designer confirm (glue/resize/tips ok).
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


# (summary, bug_body, test_summary_suffix, test_body, relate_extra)
ITEMS = [
    (
        "Charter tray hover tooltips too small to read",
        """Symptom
Designer (desk160): hover tooltips appear and copy is good, but the tip window/text is too small to read comfortably.

Expected
Tooltip text is clearly readable at a glance (larger type and/or taller tip box; still native hover-over).

Actual
Tip shows but feels cramped / hard to read.

Environment
- desktop_app.py desk160; native Look 4 tray
- Related: KAN-530/531

Replication
1. Manual → Start; hover Still / Note / End.
2. Observe tip — present but small.

Notes
Focused polish only — do not change verb wiring in this ticket.""",
        "tooltip readable size",
        """Verification for larger Charter tray hover tips.

Procedure
1. desk160+ fix; Manual → Start.
2. Hover each tray icon — tip text easy to read (larger font/box).
3. Tips still dismiss on leave / click.

Evidence
Screenshot of tip; cache-bust; pytest tip markers if added.""",
        ("KAN-530", "KAN-531"),
    ),
    (
        "Charter tray Still appears to do nothing",
        """Symptom
Designer (desk160): Still tray button click has no obvious effect (no still confirmation / Manual evidence).

Expected
Still captures inside the frame, restores ring+tray, and shows honest success or failure in Manual/session UI.

Actual
Click feels inert.

Environment
desk160 native tray; `_on_tray_verb` still path; Relates KAN-530/528/512

Replication
1. Manual → Start; click Still.
2. Check Manual session / stills — no visible result.

Notes
Focused: Still only. Check session_id wiring, API stills, float events, chrome restore.""",
        "Still capture + visible feedback",
        """Procedure
1. Start charter; click tray Still.
2. Expected: still saved; Manual shows still; chrome returns.
3. Fail path shows honest status (not silent).

Evidence
Still in session; screenshot; pytest if API path covered.""",
        ("KAN-530", "KAN-528", "KAN-512"),
    ),
    (
        "Charter tray Note appears to do nothing",
        """Symptom
Designer (desk160): Note tray button click has no obvious effect.

Expected
Note opens a usable note affordance (Manual chip note field focused and visible, or native note sheet) so the tester can type immediately.

Actual
Click feels inert (note-sheet HWND still OOS; Manual chip focus may be hidden).

Environment
desk160; Relates KAN-530/525

Replication
1. Manual → Start; click Note.
2. No note UI / focus appears.

Notes
Focused: Note only.""",
        "Note visible affordance",
        """Procedure
1. Start; click Note.
2. Expected: note input visible + focused; note saves to session.
Evidence: screenshot + session note.""",
        ("KAN-530", "KAN-525"),
    ),
    (
        "Charter tray Pause appears to do nothing",
        """Symptom
Designer (desk160): Pause click only may tint the icon; session recording behaviour / Manual UI does not clearly pause.

Expected
Pause toggles session pause via API + clear on-state on tray + Manual chip/status reflects paused; Still blocked while paused.

Actual
Feels inert / unclear.

Replication
1. Start; click Pause twice.
2. Observe Manual + Still while paused.

Notes
Focused: Pause only.""",
        "Pause API + visible state",
        """Procedure
1. Start; Pause — Manual shows paused; Still no-ops or explains.
2. Pause again — resumes.
Evidence: status + icon on-state.""",
        ("KAN-530", "KAN-512"),
    ),
    (
        "Charter tray Assist appears to do nothing",
        """Symptom
Designer (desk160): Assist click has no clear effect beyond possible icon tint.

Expected
Assist toggles session agent_assist; tray on-state; Manual reflects assist on/off; no silent Jira.

Actual
Feels inert.

Notes
Focused: Assist only.""",
        "Assist toggle + Manual sync",
        """Procedure
1. Start; click Assist — Manual/session assist on + tray on-state.
2. Click again — off.
Evidence: toggles API + UI.""",
        ("KAN-530", "KAN-512"),
    ),
    (
        "Charter tray Mist appears to do nothing",
        """Symptom
Designer (desk160): Mist click has no visible mist inside the capture hole.

Expected
Mist on → light mist visible inside the frame (FR-MAN-1 armed mist); off clears it; tray on-state matches.

Actual
No visible mist / feels inert.

Notes
Focused: Mist paint in hollow ring (native). Do not implement FR-MAN-2 circles.""",
        "Mist visible inside hole",
        """Procedure
1. Start; Mist on — mist visible in hole; off clears.
Evidence: screenshot mist on/off.""",
        ("KAN-530", "KAN-512"),
    ),
    (
        "Charter tray End appears to do nothing",
        """Symptom
Designer (desk160): End tray button may not end the session or open review / close chrome.

Expected
End ends session, closes ring+tray, Manual moves to review/end stage (same as Manual End).

Actual
Click feels inert or chrome stuck Recording.

Notes
Focused: End only.""",
        "End closes chrome + review",
        """Procedure
1. Start; End — chrome gone; Manual review/end UI.
Evidence: session ended; screenshot.""",
        ("KAN-530", "KAN-520"),
    ),
    (
        "Charter tray Cancel appears to do nothing",
        """Symptom
Designer (desk160): Cancel may not show confirm or cancel the session.

Expected
Cancel shows confirm; OK cancels (nothing to Jira), closes chrome; Cancel/dismiss aborts.

Actual
Feels inert.

Notes
Focused: Cancel only.""",
        "Cancel confirm + close",
        """Procedure
1. Start; Cancel → dismiss — session continues.
2. Cancel → OK — session cancelled; chrome gone.
Evidence: session state.""",
        ("KAN-530", "KAN-512"),
    ),
]


def transition_done(client: httpx.Client, base: str, key: str) -> int:
    tr = client.get(f"{base}/rest/api/3/issue/{key}/transitions").json()
    done_id = next(
        (
            t["id"]
            for t in tr.get("transitions") or []
            if str(t.get("name", "")).lower() in ("done", "closed")
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

        for summary, bug_body, test_suf, test_body, relates in ITEMS:
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
            for other in relates:
                client.post(
                    f"{base}/rest/api/3/issueLink",
                    json={
                        "type": {"name": "Relates"},
                        "inwardIssue": {"key": bug},
                        "outwardIssue": {"key": other},
                    },
                )
                time.sleep(0.15)
            entry = {"bug": bug, "test": test_key, "summary": summary}
            out["created"].append(entry)  # type: ignore[index]

        # Designer confirmed glue/resize/tips on desk160 — close prior bugs/tests.
        close_note = (
            "Designer desk160: button clip/glue successful; resize correct; "
            "tooltips present (size residual → new tip Bug). "
            "Inert tray verbs → separate focused Bugs. Closing this ticket."
        )
        for key in ("KAN-530", "KAN-531", "KAN-528", "KAN-529"):
            cr = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(close_note)},
            )
            out[f"comment_{key}"] = cr.status_code
            out[f"done_{key}"] = transition_done(client, base, key)
            time.sleep(0.2)

        created = out["created"]
        assert isinstance(created, list) and created
        first = created[0]
        assert isinstance(first, dict)
        tip_bug = first.get("bug")
        for key in ("KAN-530", "KAN-528"):
            client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={
                    "body": adf_text(
                        f"Residual queue starts at {tip_bug} (readable tips), "
                        f"then Still/Note/Pause/Assist/Mist/End/Cancel Bugs. "
                        f"Then KAN-510. Do not start voice / FR-MAN-2."
                    )
                },
            )

        print(json.dumps(out, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
