"""Apply Council KAN-525 verdict: enrich 525/526 + comments 512/524 (no tokens printed)."""
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


DESC_525 = """Symptom
Designer (desk155 / KAN-524): Resume Charter or End→Start → OS Charter overlay missing on desktop; Charter Frame on taskbar; click is a no-op. Prefers Look 4 SIDE tray (not under-ring).

Council verdict (2026-11-28 Full + Studio/Creative — Designer Accepted)
Root cause (ranked): (1) hide-and-reuse zombie on second pywebview float; (2) false-visible size-only gate; (3) TOPMOST/show race; (4) two-host desync; (5) side vs under-ring geom is NOT this bug (under-ring already shipping and still fails).

Architecture (Adopt)
Native TOOLWINDOW side icon chrome on the existing hollow-ring thread. Prefer no taskbar entry. Create/show on Start/Resume; destroy/remove on End — no win.hide() recycle of a WebView tray.

Reject / do not try again
~48px WebView2 side rail; under-ring as product UX; more HWND floors / second force-visible / SW_HIDE games; SetWindowRgn; chip-as-chrome; pytest markers alone as Done; dual WebView fallback; extra process / cloud overlay.

Design Intent
Look 4 Compact side rail remains Accepted. Under-ring Rejected. Spec FR-MAN-1 CR lock 2026-11-28.

Expected (Build AC)
1. Cold Start: hollow ring + Look 4 SIDE rail on desktop; verbs clickable (≥40px hits).
2. End→Start in-process (no app restart as happy path): chrome returns every time.
3. Resume Charter: places same chrome; Manual-open alone does not auto-arm.
4. Taskbar XOR: prefer no Charter Frame button; if present, click restores usable side chrome (dead click = fail).
5. Honest fail: place/show fail ⇒ not Recording; Resume/End available; no silent ghost.
6. Manual session chip Still/Note/Restore/End = backup only — never sufficient for Done.
7. Still = hole pixels only; hard-fail if hole bbox unknown (no all-screens grab fallback).
8. Slice OOS: outward note-sheet HWND; FR-MAN-2; voice; 510/511 AC; Gradio OS float.

Actual
Overlay missing after Resume/End→Start; taskbar ghost; click no-op. KAN-516…524 insufficient.

Environment
desktop_app.py + Edge WebView2; Windows home PC; desk155; related KAN-512/518/520/522/524/510.

Replication
1. Restart desktop_app.py; End stuck Recording.
2. Manual → Start (or Resume).
3. Observe missing ring+tray; taskbar Charter Frame; click no-op.
4. End→Start — same failure.

Sequencing
Active Build = this Bug. Hard pause KAN-510/511 until KAN-525 + test KAN-526 human paths pass. Then Active → KAN-510.

Relates: KAN-512, 386/387, 510, 511, 518/520/522/524; test KAN-526."""

DESC_526 = """Intro
Verification for Bug KAN-525 after Council host fix (native Look 4 side tray). Overlay Native Chrome Gate: pytest alone ≠ Done.

Who this is for
Testers + agents on Build pick-up of KAN-525.

Test procedure
1. Restart desktop_app.py on the fixed cache-bust; End any stuck Recording.
2. Cold Start with a short charter.
   Expected: hollow ring + Look 4 SIDE rail on desktop (not under-ring; not taskbar-only).
3. End → Start again in the same process (no full app restart).
   Expected: ring + side tray reappear every time.
4. Start → leave session open → Resume Charter.
   Expected: ring + side tray place; verbs usable.
5. Taskbar: either no Charter Frame entry, OR click restores usable side chrome.
6. Confirm Manual chip Still/Note/Restore/End still work as backup — chip alone does NOT pass this ticket.
7. Optional: Still with known hole bbox succeeds; missing bbox must hard-fail (no full-desk grab).

Acceptance criteria
- Paths Start, End→Start, Resume all show on-desktop side chrome.
- No dead taskbar ghost.
- Placement = side Look 4 (under_ring pytest lock must be removed/inverted).
- Human or quiet-CU evidence with numbered steps + desktop screenshot.

Evidence blacklist (not Done)
- pytest test_charter_float.py alone
- chip works / Recording shown
- CU skipped soft-pass / opened orb home
- under-ring geom unit tests as substitute for side Accept
- first-Start only without second Start / Resume

Evidence
Screenshot of desktop with ring + side tray; cache-bust; numbered human/CU log for paths above."""

COMMENT_525 = """Council Full review Accepted (Designer 2026-11-28) — Slice-0 landed

Decision: CR + architecture host change (not another geom patch).
Adopt: native TOOLWINDOW side chrome on ring thread; Look 4 side Intent stands; under-ring Rejected.
Reject: WebView2 ~48px rail, hide-reuse zombie, chip-as-chrome, SetWindowRgn, pytest-only Done.
Pause: KAN-510/511 until this Bug + KAN-526 human paths pass.
Docs: FR-MAN-1 Spec lock, DESIGN_INTENT under-ring Rejected, WORK_LOG Active = KAN-525.
Next: Build pick-up implements this Bug; no product code in Council chat."""

COMMENT_512 = """Council KAN-525 (2026-11-28) — gap after Look 4 ship

KAN-512 remains Done (Look 4 Accepted / desk150). Reliability loop KAN-516…524 did not clear Resume/End→Start taskbar ghost; KAN-524 under-ring is Rejected as Look 4 (Spec CR lock). Host restore tracked on Bug KAN-525 / test KAN-526. Outside-window residual KAN-510 stays paused until 525 Done."""

COMMENT_524 = """Council KAN-525 (2026-11-28) — under-ring experiment superseded

KAN-524 under-ring 480×88 was a reliability experiment, not Accepted Design Intent. Designer + Council Reject under-ring / south bar as product UX (including as degraded mode). Fix path is native side TOOLWINDOW host + HWND lifecycle (KAN-525), not further under-ring geom. Pytest under_ring locks must be inverted when Build lands."""

COMMENT_510 = """Council KAN-525 (2026-11-28) — hard pause until tray host fixed

Keep this Bug paused. Outside-window capture (KAN-510) cannot be evidenced while Charter chrome is a taskbar ghost. Resume Active only after KAN-525 + KAN-526 human paths pass (side Look 4 on-desktop after Start / Resume / End→Start). Then KAN-511."""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.apply:
        ap.error("pass --apply")

    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    out: dict[str, object] = {}
    try:
        for key, desc in (("KAN-525", DESC_525), ("KAN-526", DESC_526)):
            r = client.put(
                f"{base}/rest/api/3/issue/{key}",
                json={"fields": {"description": adf_text(desc)}},
            )
            r.raise_for_status()
            out[f"desc_{key}"] = "ok"

        for key, body in (
            ("KAN-525", COMMENT_525),
            ("KAN-526", COMMENT_525 + "\n\nTest ticket: use procedure above as Done-gate."),
            ("KAN-512", COMMENT_512),
            ("KAN-524", COMMENT_524),
            ("KAN-510", COMMENT_510),
            ("KAN-511", COMMENT_510),
        ):
            r = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(body)},
            )
            r.raise_for_status()
            out[f"comment_{key}"] = "ok"

        # Relates KAN-511 / 513 / 514 if missing (best-effort)
        for other in ("KAN-511", "KAN-513", "KAN-514"):
            r = client.post(
                f"{base}/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": "KAN-525"},
                    "outwardIssue": {"key": other},
                },
            )
            out[f"link_{other}"] = r.status_code

        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
