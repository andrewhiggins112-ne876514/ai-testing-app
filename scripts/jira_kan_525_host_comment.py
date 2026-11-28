"""Post KAN-525/526 implementation comments (no Done — human AC gate)."""
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


COMMENT_525 = """Agent implementation (desk156) — host fix landed; awaiting KAN-526 human AC

What the agent implemented
- Native Look 4 SIDE TOOLWINDOW tray on the hollow-ring Win32 thread (same message loop).
- Create/show on Start/Resume; DestroyWindow on End — no WebView tray hide-reuse zombie.
- Removed second pywebview Charter Frame window (taskbar ghost class).
- Verbs: Still / Note / Pause / Assist / Mist / End / Cancel (≥44px hits). Note focuses Manual chip (note-sheet HWND OOS).
- Still hard-fails without hole bbox (no full-desk grab for float mode).
- dock_geom placement=side (under_ring pytest lock inverted).

Files
plans/charter_ring_native.py, desktop_app.py, ui/desktop/desktop.js, ui/desktop/index.html, plans/manual_session.py, tests/test_charter_float.py (+ desk156 sweep)

Verify (agent)
pytest tests/test_charter_float.py tests/test_manual_ia.py tests/test_manual_trustworthy_loop.py — 16 passed
Smoke: show_side_tray → destroy → recreate OK

Status
Bug stays open until KAN-526 human paths pass (Cold Start / End→Start / Resume). Do not treat pytest alone as Done."""

COMMENT_526 = """Agent prep for human AC (desk156) — Overlay Native Chrome Gate

App: .\\venv\\Scripts\\python.exe desktop_app.py (cache-bust desk156). End any stuck Recording first.

Numbered human script
1. Cold Start — Manual → short charter → Start.
   Pass: cyan hollow ring + SIDE verb tray on desktop (not under-ring; not taskbar-only).
2. End (tray End or chip End) → Start again in the same process (no app restart).
   Pass: ring + side tray reappear every time.
3. Leave session open → End chrome only if needed → Resume Charter.
   Pass: ring + side tray place; verbs clickable.
4. Taskbar: prefer no Charter Frame button; if one appears, click must restore usable side chrome (dead click = fail).
5. Chip Still/Note/Restore/End still work as backup — chip alone does NOT pass this ticket.

Evidence needed
Desktop screenshot with ring + side tray; note desk156; numbered log for paths 1–3.
pytest alone / under-ring geom / opened orb home = not Done.

Agent unit evidence (not sufficient alone)
pytest tests/test_charter_float.py … — 16 passed; placement=side; host=native_toolwindow."""


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
        for key, body in (("KAN-525", COMMENT_525), ("KAN-526", COMMENT_526)):
            r = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(body)},
            )
            out[key] = r.status_code
            r.raise_for_status()
        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
