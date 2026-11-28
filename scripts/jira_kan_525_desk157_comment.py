"""Comment on KAN-525/526: desk157 SetWindowPos fix (no Done)."""
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
    return {"type": "doc", "version": 1, "content": paras}


BODY = """Fix follow-up desk157 (Designer AC: Recording chip, no OS chrome)

Root cause
HWND_TOPMOST = -1 passed to ctypes SetWindowPos on Win64 did not move/size the native bars/tray. Ring HWNDs stayed ~5x5/10x10 at 0,0 (hidden); no Charter Tray. Manual still showed Recording / session chip after a prior false-visible path.

Fix
Pointer-sized HWND_TOPMOST + SetWindowPos argtypes; PostThreadMessageW wake for CreateWindow; ring place is cross-thread SetWindowPos. Cache-bust desk157.

Verify (agent)
EnumWindows after show_side_tray: tray visible at expected side geom (e.g. 846,180 48x388) + four cyan bars. pytest tests/test_charter_float.py — 9 passed.

Human AC (KAN-526) — re-run on desk157
1. Fully restart desktop_app.py (desk157). End any stuck session.
2. Cold Start / End→Start / Resume — expect hollow ring + SIDE verb strip on desktop.
"""


def main() -> None:
    base, auth = load_creds()
    client = httpx.Client(
        timeout=60.0,
        verify=ssl.create_default_context(),
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    out = {}
    try:
        for key in ("KAN-525", "KAN-526"):
            r = client.post(
                f"{base}/rest/api/3/issue/{key}/comment",
                json={"body": adf_text(BODY)},
            )
            out[key] = r.status_code
            r.raise_for_status()
        print(json.dumps(out))
    finally:
        client.close()


if __name__ == "__main__":
    main()
