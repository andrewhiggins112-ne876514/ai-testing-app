"""Bridge Designer Accept: Charter G+tray Look 4 → KAN-512 / 510 / 511 (no tokens printed)."""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKOFF = 0.4

STORY_512 = """h2. Designer Accept — Charter G+tray Look 4 (2026-11-28)

*Decision:* Accepted. Spec CR landed on FR-MAN-1. Active Build stays *KAN-388* — implement this *next* after current Active finishes (do not steal Active now).

*Route:* Option G + side tray. Look *4 Compact rail*.
* Manual steps back to a session chip (Restore); only overlay open.
* One hollow OS capture shell (click-through hole; thin cyan compact stroke).
* Icon tray glued to a remembered side (default east; edge flip).
* Tray hide/show via tray-layout icon (rounded rect + right strip — IDE secondary-sidebar glyph). Collapsed = hollow frame + toggle only.
* Pause = own icon. Assist / Mist on the tray (default off).
* Still = hole pixels only. No keylog / clipboard / mic / continuous video.
* Prefer Win32 hollow ring + thin tray chrome over a second fat WebView as primary.
* Honest place-fail (no silent in-app rect fallback on desktop shell).

*Mockups (source of truth):*
* {{docs/mockups/charter_outside_window/looks/look4-picker.html}}
* {{docs/mockups/charter_outside_window/looks/look4-expanded.html}}
* {{docs/mockups/charter_outside_window/looks/look4-collapsed.html}}
* Research: {{docs/mockups/charter_outside_window/RESEARCH_G_TRAY.md}}
* Design Intent: Accepted appendix in {{docs/mockups/DESIGN_INTENT.md}}

*Build AC (Slice when Active moves here):*
# Armed desktop session: hollow OS shell over another app (e.g. IDE chat); Manual = chip only (no second cyan rect).
# Tray expanded: Still, Note, Pause (own), Assist, Mist, End, Cancel — icon-only compact rail (~36–40px).
# Tray collapsed via tray-layout icon; restore via same icon; remember side + collapsed state.
# Drag moves whole shell outside main client; hole click-through; Still proves foreign-app region.
# Place fail → honest error, no silent in-app fallback.
# Theme/orb/home/App nav untouched. Gradio: no OS float.

*Related:* outside-window residual *KAN-510*/513; focus hang *KAN-511*/514 — fix in/after this redesign Build (Designer: bugs after redesign OK).
*OOS:* FR-MAN-2, voice, dual interactive chrome, fat WebView primary dock.
"""

BUG_510 = """h2. Council+Studio direction (2026-11-28)

Outside-window capture remains in scope under Accepted *KAN-512* G+tray Look 4 (hollow OS shell over other apps; Manual chip only).

*Do not* invent chrome ahead of *KAN-512* Build. Active stays *KAN-388*; Charter Build is *next* after that.

*AC when building:* Still over a non-app window must store hole-only PNG of that region; shell must leave the main client area; tray may be collapsed.

Mock: {{docs/mockups/charter_outside_window/looks/look4-picker.html}}
"""

BUG_511 = """h2. Council+Studio direction (2026-11-28)

Focus-return Not Responding stays a reliability gate for the Charter redesign Build (*KAN-512* path). Prefer Win32 hollow ring + thin tray; avoid second WebView2 as primary (KAN-501 / pywebview hang class).

*Done-gate:* human-hands focus recipe (Cursor ≥10s → taskbar return → no NR; Manual/Still usable). Pytest alone ≠ Done.

Active stays *KAN-388*. Fix with/after G+tray implementation (Designer: bugs after redesign OK).
"""


def load_creds() -> tuple[str, tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    levels = path.parent / "levels"
    level = str(data.get("security_level") or "OFFICIAL").upper()
    cred_path = levels / level / "credentials.json"
    if cred_path.exists():
        creds = json.loads(cred_path.read_text(encoding="utf-8-sig"))
        data = {**data, **creds}
    return (
        (data.get("jira_url") or "https://ai-testing-lab.atlassian.net").rstrip("/"),
        (data["jira_email"], data["jira_api_token"]),
    )


def req(method: str, url: str, auth: tuple[str, str], body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    r = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    r.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:800]
        raise SystemExit(f"HTTP {e.code} {url}: {err}") from e


def add_comment(base: str, auth: tuple[str, str], key: str, text: str) -> None:
    req("POST", f"{base}/rest/api/2/issue/{key}/comment", auth, {"body": text})
    time.sleep(BACKOFF)


def patch_description(base: str, auth: tuple[str, str], key: str, text: str) -> None:
    # api/2 accepts wiki markup string for description
    req("PUT", f"{base}/rest/api/2/issue/{key}", auth, {"fields": {"description": text}})
    time.sleep(BACKOFF)


DESC_512 = """h1. Summary
Accepted UX for outside-window Charter Frame on the desktop shell (FR-MAN-1 CR 2026-11-28).

h2. Requirements
* Option G + side tray, Look 4 Compact rail (Designer Accepted 2026-11-28).
* Manual → session chip; hollow OS shell + collapsible icon tray; Pause own icon; Assist/Mist on tray; remember last side + collapsed state.
* Tray toggle = IDE secondary-sidebar glyph (rounded rect + right strip).
* Spec: docs/FUNCTIONAL_SPEC.md FR-MAN-1. Mockups: docs/mockups/charter_outside_window/looks/look4-picker.html

h2. Acceptance Criteria
# Hollow OS shell over another app; Manual chip only (no second cyan rect) while armed on desktop shell.
# Compact tray (~36–40px): Still, Note, Pause (own), Assist, Mist, End, Cancel; hide/show via tray icon; remember side + collapsed.
# Drag outside main client; hole click-through; Still = hole-only PNG of foreign region.
# Place fail honest; no silent in-app fallback on desktop shell; theme/orb/home untouched.
# Build *after* Active KAN-388 finishes (queued next) — do not steal Active.

h2. Out of Scope
FR-MAN-2, voice, keylog/clipboard/mic, continuous video, Gradio OS float, fat WebView as primary chrome.

h2. Relates
Epic KAN-383; float KAN-386; bugs KAN-510 / KAN-511 (tests KAN-513 / KAN-514).
"""


def main() -> int:
    base, auth = load_creds()
    patch_description(base, auth, "KAN-512", DESC_512)
    print("patched KAN-512 description")
    add_comment(base, auth, "KAN-512", STORY_512)
    print("commented KAN-512")
    add_comment(base, auth, "KAN-510", BUG_510)
    print("commented KAN-510")
    add_comment(base, auth, "KAN-511", BUG_511)
    print("commented KAN-511")
    add_comment(base, auth, "KAN-513", BUG_510)
    print("commented KAN-513")
    add_comment(base, auth, "KAN-514", BUG_511)
    print("commented KAN-514")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
