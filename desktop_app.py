"""Native desktop window for the AI Testing Agent (pywebview + local FastAPI).

Run:
    .\\venv\\Scripts\\python.exe desktop_app.py

KAN-386 / KAN-502: OS-level Charter Frame = snip-style hollow ring (header +
borders + dock). Capture hole has no window region so the AUT stays visible
and clickable. No evaluate_js from js_api open (deadlock).
"""
from __future__ import annotations

import sys
import time
import threading
from typing import Any, Optional
from urllib.request import urlopen
from urllib.error import URLError

import uvicorn
import webview

from plugins.playwright_env import sanitize_playwright_browsers_path
from plans.charter_float import (
    HEADER_H,
    DOCK_H,
    MIN_WINDOW_H,
    MIN_WINDOW_W,
    SIDE,
    apply_hollow_window_region,
    clamp_window_geom,
    content_bbox_from_window,
    default_window_geom,
    float_hwnd_from_native,
    float_window_title,
    is_float_available_payload,
    relative_frame_from_window,
)
from plans.charter_snap import list_snap_targets, virtual_desktop_from_monitors

HOST = "127.0.0.1"
PORT = 8765
DESK_V = "desk142"
URL = f"http://{HOST}:{PORT}/ui/desktop/index.html?v={DESK_V}"
FLOAT_URL = f"http://{HOST}:{PORT}/ui/desktop/charter_float.html?v={DESK_V}"
HEALTH = f"http://{HOST}:{PORT}/health"

_main_window: Any = None
_float_window: Any = None
_float_visible = False
_float_session_id = ""


def _serve() -> None:
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        reload=False,
    )


def _wait_ready(timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(HEALTH, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (URLError, OSError):
            time.sleep(0.2)
    return False


def _snap_context() -> tuple[dict[str, int], list[dict[str, Any]]]:
    try:
        targets = list_snap_targets()
        monitors = list(targets.get("monitors") or [])
        return virtual_desktop_from_monitors(monitors), monitors
    except Exception:  # noqa: BLE001
        return {"left": 0, "top": 0, "width": 1280, "height": 800}, []


def _notify_main(js: str) -> None:
    win = _main_window
    if win is None:
        return
    try:
        win.evaluate_js(js)
    except Exception:  # noqa: BLE001
        pass


def _apply_float_ring(win: Any) -> dict[str, Any]:
    """Punch hollow capture hole after show/resize."""
    try:
        w, h = int(win.width), int(win.height)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": "geom_failed", "message": str(exc)[:120]}
    hwnd = float_hwnd_from_native(getattr(win, "native", None))
    if not hwnd:
        return {"status": "error", "error": "no_hwnd"}
    return apply_hollow_window_region(
        hwnd, w, h, header_h=HEADER_H, dock_h=DOCK_H, side=SIDE
    )


class DesktopApi:
    """JS bridge for main + Charter float windows (window.pywebview.api)."""

    def charter_float_available(self) -> dict[str, Any]:
        return is_float_available_payload(_float_window is not None)

    def charter_float_open(self, session: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Show snip-sized hollow float. No evaluate_js (avoids js_api deadlock)."""
        global _float_visible, _float_session_id
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable", "available": False}
        sess = session if isinstance(session, dict) else {}
        _float_session_id = str(sess.get("id") or "")
        frame = sess.get("frame") if isinstance(sess.get("frame"), dict) else None
        virtual, monitors = _snap_context()
        geom = default_window_geom(virtual=virtual, frame=frame, monitors=monitors)
        try:
            win.resize(int(geom["width"]), int(geom["height"]))
            win.move(int(geom["x"]), int(geom["y"]))
            win.on_top = True
            win.show()
            _float_visible = True
            ring = _apply_float_ring(win)
            return {
                "status": "ok",
                "available": True,
                "mode": "os_float_hollow",
                "session_id": _float_session_id,
                "geometry": geom,
                "screen_bbox": content_bbox_from_window(
                    geom["x"], geom["y"], geom["width"], geom["height"]
                ),
                "ring": ring,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "error": "float_open_failed",
                "message": str(exc)[:200],
                "available": True,
            }

    def charter_float_close(self) -> dict[str, Any]:
        global _float_visible, _float_session_id
        win = _float_window
        _float_session_id = ""
        if win is None:
            return {"status": "ok", "available": False}
        try:
            win.hide()
        except Exception:  # noqa: BLE001
            pass
        _float_visible = False
        return {"status": "ok", "available": True}

    def charter_float_screen_bbox(self) -> dict[str, Any]:
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable"}
        try:
            x, y, w, h = int(win.x), int(win.y), int(win.width), int(win.height)
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "geom_failed", "message": str(exc)[:120]}
        virtual, _monitors = _snap_context()
        bbox = content_bbox_from_window(x, y, w, h)
        frame = relative_frame_from_window(x, y, w, h, virtual=virtual)
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "frame": frame,
            "geometry": {"x": x, "y": y, "width": w, "height": h},
        }

    def charter_float_set_size(self, width: int, height: int) -> dict[str, Any]:
        """Resize float from HTML handles; re-clamp + re-punch hollow ring."""
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable"}
        virtual, monitors = _snap_context()
        try:
            x, y = int(win.x), int(win.y)
        except Exception:
            x, y = 80, 80
        geom = clamp_window_geom(
            {"x": x, "y": y, "width": int(width), "height": int(height)},
            work=_primary_work_safe(virtual, monitors),
        )
        try:
            win.resize(int(geom["width"]), int(geom["height"]))
            win.move(int(geom["x"]), int(geom["y"]))
            ring = _apply_float_ring(win)
            bbox = content_bbox_from_window(
                geom["x"], geom["y"], geom["width"], geom["height"]
            )
            return {
                "status": "ok",
                "geometry": geom,
                "screen_bbox": bbox,
                "ring": ring,
            }
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "resize_failed", "message": str(exc)[:120]}

    def charter_float_apply_ring(self) -> dict[str, Any]:
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable"}
        return _apply_float_ring(win)

    def charter_float_prepare_still(self) -> dict[str, Any]:
        """Hide float chrome, return content bbox for ImageGrab."""
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable"}
        geom = self.charter_float_screen_bbox()
        if geom.get("status") != "ok":
            return geom
        try:
            win.hide()
            time.sleep(0.12)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "error": "hide_failed",
                "message": str(exc)[:120],
                **{k: geom[k] for k in ("screen_bbox", "frame") if k in geom},
            }
        return {
            "status": "ok",
            "screen_bbox": geom.get("screen_bbox"),
            "frame": geom.get("frame"),
            "hidden": True,
        }

    def charter_float_restore(self) -> dict[str, Any]:
        win = _float_window
        if win is None:
            return {"status": "ok", "available": False}
        try:
            if _float_visible or _float_session_id:
                win.show()
                win.on_top = True
                _apply_float_ring(win)
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "show_failed", "message": str(exc)[:120]}
        return {"status": "ok", "available": True}

    def charter_float_notify_main(self, event: str, session_id: str = "") -> dict[str, Any]:
        """Float → main shell: ended / cancelled / still / note."""
        import json

        safe_event = str(event or "")[:32]
        safe_id = str(session_id or _float_session_id or "")[:64]
        payload = json.dumps({"type": safe_event, "session_id": safe_id})
        _notify_main(
            "window.__charterFloatEvent && window.__charterFloatEvent("
            + payload
            + ")"
        )
        if safe_event in {"ended", "cancelled"}:
            self.charter_float_close()
        return {"status": "ok", "event": safe_event}


def _primary_work_safe(
    virtual: dict[str, int], monitors: list[dict[str, Any]]
) -> dict[str, int]:
    from plans.charter_float import _primary_work

    return _primary_work(virtual, monitors)


def main() -> int:
    global _main_window, _float_window

    cleaned = sanitize_playwright_browsers_path()
    if cleaned.get("cleared"):
        print(
            "NOTE: cleared invalid PLAYWRIGHT_BROWSERS_PATH "
            f"({cleaned.get('reason')}) → use default ms-playwright.",
            flush=True,
        )

    server = threading.Thread(target=_serve, name="fastapi-desktop", daemon=True)
    server.start()
    if not _wait_ready():
        print(f"ERROR: FastAPI did not become ready on {HEALTH}", flush=True)
        return 1

    api = DesktopApi()
    print(f"Opening desktop window → {URL}", flush=True)
    _main_window = webview.create_window(
        title="AI Testing Agent",
        url=URL,
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#000000",
        js_api=api,
    )
    virtual, monitors = _snap_context()
    geom = default_window_geom(virtual=virtual, monitors=monitors)
    _float_window = webview.create_window(
        title=float_window_title(),
        url=FLOAT_URL,
        width=int(geom["width"]),
        height=int(geom["height"]),
        x=int(geom["x"]),
        y=int(geom["y"]),
        min_size=(MIN_WINDOW_W, MIN_WINDOW_H),
        frameless=True,
        easy_drag=False,
        on_top=True,
        shadow=False,
        resizable=True,
        hidden=True,
        background_color="#061018",
        js_api=api,
    )
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
