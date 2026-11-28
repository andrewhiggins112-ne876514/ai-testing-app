"""Native desktop window for the AI Testing Agent (pywebview + local FastAPI).

Run:
    .\\venv\\Scripts\\python.exe desktop_app.py

KAN-386 / KAN-503: Manual snip = compact dock WebView + separate native Win32
hollow ring (never SetWindowRgn on WebView2 — that stayed opaque and crashed).
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
    float_hwnd_from_native,
    float_window_title,
    is_float_available_payload,
)
from plans import charter_ring_native as ring
from plans.charter_snap import list_snap_targets, virtual_desktop_from_monitors

HOST = "127.0.0.1"
PORT = 8765
DESK_V = "desk149"
URL = f"http://{HOST}:{PORT}/ui/desktop/index.html?v={DESK_V}"
FLOAT_URL = f"http://{HOST}:{PORT}/ui/desktop/charter_float.html?v={DESK_V}"
HEALTH = f"http://{HOST}:{PORT}/health"

_main_window: Any = None
_float_window: Any = None
_float_visible = False
_float_session_id = ""
_dock_events_hooked = False
_suppress_dock_moved = False


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


def _force_dock_native_visible(win: Any, geom: dict[str, int]) -> None:
    """Unstick taskbar-only / hidden frameless dock (Show + TOPMOST)."""
    import ctypes

    hwnd = float_hwnd_from_native(getattr(win, "native", None))
    if not hwnd:
        return
    user32 = ctypes.windll.user32
    HWND_TOPMOST = -1
    SW_RESTORE = 9
    SWP_SHOWWINDOW = 0x0040
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        int(geom["x"]),
        int(geom["y"]),
        int(geom["width"]),
        int(geom["height"]),
        SWP_SHOWWINDOW,
    )


def _sync_ring_above_dock() -> dict[str, Any]:
    """Keep capture ring glued above the dock after the user drags the dock."""
    win = _float_window
    if win is None or not _float_visible:
        return {"status": "error", "error": "float_unavailable"}
    try:
        x = int(win.x)
        y = int(win.y)
        w = int(win.width)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": "dock_geom_failed", "message": str(exc)[:120]}
    bbox = ring.get_capture_bbox()
    bw = max(ring.MIN_CAPTURE_W, int(bbox[2]) - int(bbox[0]))
    bh = max(ring.MIN_CAPTURE_H, int(bbox[3]) - int(bbox[1]))
    left = x + max(0, (w - bw) // 2)
    top = y - 12 - bh
    virtual, monitors = _snap_context()
    work = virtual or {"left": 0, "top": 0, "width": 1920, "height": 1080}
    if monitors:
        primary = next((m for m in monitors if m.get("is_primary")), None) or monitors[0]
        pb = primary.get("bbox")
        if isinstance(pb, (list, tuple)) and len(pb) == 4:
            work = {
                "left": int(pb[0]),
                "top": int(pb[1]),
                "width": int(pb[2]) - int(pb[0]),
                "height": int(pb[3]) - int(pb[1]),
            }
    ox = int(work["left"])
    oy = int(work["top"])
    aw = int(work["width"])
    ah = int(work["height"])
    left = max(ox, min(left, ox + aw - bw))
    top = max(oy, min(top, oy + ah - bh))
    return ring.set_capture_bbox([left, top, left + bw, top + bh], show=True)


def _on_dock_moved() -> None:
    global _suppress_dock_moved
    if _suppress_dock_moved or not _float_visible:
        return
    try:
        _sync_ring_above_dock()
    except Exception:  # noqa: BLE001
        pass


def _hook_dock_events() -> None:
    global _dock_events_hooked
    if _dock_events_hooked or _float_window is None:
        return
    try:
        _float_window.events.moved += _on_dock_moved
        _dock_events_hooked = True
    except Exception:  # noqa: BLE001
        pass


def _place_dock(bbox: list[int]) -> dict[str, Any]:
    global _suppress_dock_moved
    win = _float_window
    if win is None:
        return {"status": "error", "error": "float_unavailable"}
    virtual, monitors = _snap_context()
    geom = ring.dock_geom_for_bbox(bbox, virtual=virtual, monitors=monitors)
    try:
        try:
            win.restore()
        except Exception:  # noqa: BLE001
            pass
        _suppress_dock_moved = True
        try:
            # Fixed chrome size — capture size uses ± / ring, not WinForms border drag.
            win.resize(int(geom["width"]), int(geom["height"]))
            win.move(int(geom["x"]), int(geom["y"]))
            win.on_top = True
            win.show()
            _force_dock_native_visible(win, geom)
        finally:
            _suppress_dock_moved = False
        _hook_dock_events()
        return {"status": "ok", "geometry": geom}
    except Exception as exc:  # noqa: BLE001
        _suppress_dock_moved = False
        return {"status": "error", "error": "dock_place_failed", "message": str(exc)[:120]}


class DesktopApi:
    """JS bridge for main + Charter dock windows."""

    def charter_float_available(self) -> dict[str, Any]:
        payload = is_float_available_payload(_float_window is not None)
        payload["mode"] = "dock_plus_native_ring"
        payload["click_through_hole"] = True
        return payload

    def charter_float_open(self, session: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Show native hollow ring + compact dock. No WebView region punching."""
        global _float_visible, _float_session_id
        if _float_window is None:
            return {"status": "error", "error": "float_unavailable", "available": False}
        sess = session if isinstance(session, dict) else {}
        _float_session_id = str(sess.get("id") or "")
        virtual, monitors = _snap_context()
        bbox = ring.default_capture_bbox(virtual=virtual, monitors=monitors)
        try:
            ring_out = ring.set_capture_bbox(bbox, show=True)
            dock_out = _place_dock(bbox)
            if not dock_out or dock_out.get("status") != "ok":
                return {
                    "status": "error",
                    "error": "dock_place_failed",
                    "available": True,
                    "mode": "dock_plus_native_ring",
                    "session_id": _float_session_id,
                    "screen_bbox": bbox,
                    "ring": ring_out,
                    "dock": dock_out,
                }
            _float_visible = True
            return {
                "status": "ok",
                "available": True,
                "mode": "dock_plus_native_ring",
                "session_id": _float_session_id,
                "screen_bbox": bbox,
                "ring": ring_out,
                "dock": dock_out,
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
        _float_session_id = ""
        try:
            ring.hide_ring()
        except Exception:  # noqa: BLE001
            pass
        win = _float_window
        if win is not None:
            try:
                win.hide()
            except Exception:  # noqa: BLE001
                pass
        _float_visible = False
        return {"status": "ok", "available": True}

    def charter_float_screen_bbox(self) -> dict[str, Any]:
        bbox = ring.get_capture_bbox()
        virtual, _m = _snap_context()
        # Relative frame approx from bbox on virtual desktop
        from plans.charter_snap import bounds_to_frame

        frame = bounds_to_frame(bbox, virtual)
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "frame": frame,
            "geometry": ring.dock_geom_for_bbox(bbox),
        }

    def charter_float_nudge(self, dx: int = 0, dy: int = 0) -> dict[str, Any]:
        bbox = ring.nudge_bbox(ring.get_capture_bbox(), int(dx), int(dy))
        ring.set_capture_bbox(bbox, show=True)
        dock = _place_dock(bbox)
        return {"status": "ok", "screen_bbox": bbox, "dock": dock}

    def charter_float_drag_by(self, dx: int = 0, dy: int = 0) -> dict[str, Any]:
        """Drag dock by delta; ring stays glued above (header drag from float JS)."""
        global _suppress_dock_moved
        win = _float_window
        if win is None or not _float_visible:
            return {"status": "error", "error": "float_unavailable"}
        try:
            x = int(win.x) + int(dx)
            y = int(win.y) + int(dy)
            w = int(win.width)
            h = int(win.height)
            virtual, monitors = _snap_context()
            ox = int((virtual or {}).get("left") or 0)
            oy = int((virtual or {}).get("top") or 0)
            aw = int((virtual or {}).get("width") or 1920)
            ah = int((virtual or {}).get("height") or 1080)
            if monitors:
                primary = next(
                    (m for m in monitors if m.get("is_primary")), None
                ) or monitors[0]
                pb = primary.get("bbox")
                if isinstance(pb, (list, tuple)) and len(pb) == 4:
                    ox, oy = int(pb[0]), int(pb[1])
                    aw, ah = int(pb[2]) - ox, int(pb[3]) - oy
            x = max(ox, min(x, ox + aw - w))
            y = max(oy, min(y, oy + ah - h))
            geom = {"x": x, "y": y, "width": w, "height": h}
            _suppress_dock_moved = True
            try:
                win.move(x, y)
                _force_dock_native_visible(win, geom)
            finally:
                _suppress_dock_moved = False
            ring_out = _sync_ring_above_dock()
            return {
                "status": "ok",
                "geometry": geom,
                "screen_bbox": ring.get_capture_bbox(),
                "ring": ring_out,
            }
        except Exception as exc:  # noqa: BLE001
            _suppress_dock_moved = False
            return {"status": "error", "error": "drag_failed", "message": str(exc)[:120]}

    def charter_float_resize_capture(self, d_w: int = 0, d_h: int = 0) -> dict[str, Any]:
        bbox = ring.resize_bbox(ring.get_capture_bbox(), int(d_w), int(d_h))
        ring.set_capture_bbox(bbox, show=True)
        dock = _place_dock(bbox)
        return {"status": "ok", "screen_bbox": bbox, "dock": dock}

    def charter_float_set_size(self, width: int, height: int) -> dict[str, Any]:
        """Dock chrome size is fixed; capture size uses resize_capture / ± buttons."""
        win = _float_window
        if win is None:
            return {"status": "error", "error": "float_unavailable"}
        geom = ring.dock_geom_for_bbox(ring.get_capture_bbox())
        try:
            win.resize(int(geom["width"]), int(geom["height"]))
            return {"status": "ok", "geometry": geom, "locked": True}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "resize_failed", "message": str(exc)[:120]}

    def charter_float_apply_ring(self) -> dict[str, Any]:
        return ring.show_ring()

    def charter_float_prepare_still(self) -> dict[str, Any]:
        bbox = ring.get_capture_bbox()
        try:
            ring.hide_ring()
            if _float_window is not None:
                _float_window.hide()
            time.sleep(0.12)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "error": "hide_failed",
                "message": str(exc)[:120],
                "screen_bbox": bbox,
            }
        virtual, _m = _snap_context()
        from plans.charter_snap import bounds_to_frame

        return {
            "status": "ok",
            "screen_bbox": bbox,
            "frame": bounds_to_frame(bbox, virtual),
            "hidden": True,
        }

    def charter_float_restore(self) -> dict[str, Any]:
        bbox = ring.get_capture_bbox()
        try:
            ring.show_ring()
            if _float_visible or _float_session_id:
                _place_dock(bbox)
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "show_failed", "message": str(exc)[:120]}
        return {"status": "ok", "available": True, "screen_bbox": bbox}

    def charter_float_notify_main(self, event: str, session_id: str = "") -> dict[str, Any]:
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

    # Start native ring thread early (hidden).
    try:
        ring.ensure_ring_thread()
    except Exception as exc:  # noqa: BLE001
        print(f"NOTE: charter ring init deferred ({exc})", flush=True)

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
    bbox = ring.default_capture_bbox(virtual=virtual, monitors=monitors)
    dock = ring.dock_geom_for_bbox(bbox)
    _float_window = webview.create_window(
        title=float_window_title(),
        url=FLOAT_URL,
        width=int(dock["width"]),
        height=int(dock["height"]),
        x=int(dock["x"]),
        y=int(dock["y"]),
        min_size=(420, 100),
        frameless=True,
        easy_drag=False,
        on_top=True,
        shadow=True,
        resizable=False,
        hidden=True,
        background_color="#061018",
        js_api=api,
    )
    webview.start()
    try:
        ring.destroy_ring()
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
