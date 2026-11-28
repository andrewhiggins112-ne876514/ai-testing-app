"""Native desktop window for the AI Testing Agent (pywebview + local FastAPI).

Run:
    .\\venv\\Scripts\\python.exe desktop_app.py

KAN-525: Manual snip = native hollow ring + native TOOLWINDOW Look 4 *side*
tray on the ring thread. No second WebView2 tray (hide-reuse zombie class).
Never SetWindowRgn on WebView2.
"""
from __future__ import annotations

import json
import sys
import time
import threading
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import uvicorn
import webview

from plugins.playwright_env import sanitize_playwright_browsers_path
from plans.charter_float import is_float_available_payload
from plans import charter_ring_native as ring
from plans.charter_snap import list_snap_targets, virtual_desktop_from_monitors

HOST = "127.0.0.1"
PORT = 8765
DESK_V = "desk157"
URL = f"http://{HOST}:{PORT}/ui/desktop/index.html?v={DESK_V}"
HEALTH = f"http://{HOST}:{PORT}/health"
API = f"http://{HOST}:{PORT}/api"

_main_window: Any = None
_float_visible = False
_float_session_id = ""
_tray_side = "east"
_tray_collapsed = False
_paused = False


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


def _api_json(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=12.0) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": "ok"}
    except HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": "error", "error": str(exc)}
        except Exception:  # noqa: BLE001
            return {"status": "error", "error": str(exc)[:120]}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)[:120]}


def _emit_float_event(event: str, session_id: str = "") -> None:
    safe_event = str(event or "")[:32]
    safe_id = str(session_id or _float_session_id or "")[:64]
    payload = json.dumps({"type": safe_event, "session_id": safe_id})
    _notify_main(
        "window.__charterFloatEvent && window.__charterFloatEvent(" + payload + ")"
    )


def _place_chrome(bbox: list[int]) -> dict[str, Any]:
    """Show ring + fresh native side tray beside bbox."""
    virtual, monitors = _snap_context()
    ring_out = ring.set_capture_bbox(bbox, show=True)
    tray_out = ring.show_side_tray(
        side=_tray_side,
        collapsed=_tray_collapsed,
        virtual=virtual,
        monitors=monitors,
    )
    return {"ring": ring_out, "dock": tray_out, "tray": tray_out}


def _on_tray_verb(verb: str) -> None:
    """Native tray button → session actions (runs on worker thread)."""
    global _paused, _tray_collapsed, _float_visible
    sid = _float_session_id
    v = str(verb or "").strip().lower()

    if v == "toggle":
        _tray_collapsed = not _tray_collapsed
        virtual, monitors = _snap_context()
        ring.set_tray_prefs(
            collapsed=_tray_collapsed,
            side=_tray_side,
            virtual=virtual,
            monitors=monitors,
        )
        return

    if v == "pause":
        _paused = not _paused
        ring.set_toggle_flags(pause=_paused)
        return

    if not sid:
        # Try open session from API.
        open_data = _api_json("GET", "/manual-sessions/open")
        sess = (open_data or {}).get("session") or {}
        sid = str(sess.get("id") or "")
        if not sid:
            return

    if v == "still":
        if _paused:
            return
        bbox = ring.get_capture_bbox()
        if not bbox or len(bbox) != 4:
            return
        # Hard-fail if bbox unknown — no all-screens grab (KAN-525 AC).
        try:
            ring.hide_ring()
            ring.destroy_side_tray()
            time.sleep(0.1)
            out = _api_json(
                "POST",
                f"/manual-sessions/{sid}/stills",
                {"screen_bbox": bbox},
            )
            _emit_float_event("still", sid)
            if out.get("status") != "ok":
                _notify_main(
                    "window.__manualFloatFailStatus="
                    + json.dumps((out.get("message") or "Still failed")[:120])
                )
        finally:
            if _float_visible:
                _place_chrome(bbox)
        return

    if v == "note":
        # Note-sheet HWND is OOS — focus Manual chip note backup.
        _emit_float_event("note_focus", sid)
        _notify_main(
            "(function(){var i=document.querySelector('[data-manual-session-note-input]');"
            "if(i){i.focus();}})()"
        )
        return

    if v == "assist":
        st = ring.tray_state()
        nxt = not bool(st.get("assist"))
        _api_json(
            "POST",
            f"/manual-sessions/{sid}/toggles",
            {"agent_assist": nxt},
        )
        ring.set_toggle_flags(assist=nxt)
        return

    if v == "mist":
        st = ring.tray_state()
        nxt = not bool(st.get("mist"))
        _api_json(
            "POST",
            f"/manual-sessions/{sid}/toggles",
            {"armed_mist": nxt},
        )
        ring.set_toggle_flags(mist=nxt)
        return

    if v == "end":
        _api_json("POST", f"/manual-sessions/{sid}/end")
        _emit_float_event("ended", sid)
        # notify_main path also closes chrome via DesktopApi when called from JS;
        # native path closes here.
        try:
            api = DesktopApi()
            api.charter_float_close()
        except Exception:  # noqa: BLE001
            pass
        return

    if v == "cancel":
        # Native confirm (no WebView sheet).
        import ctypes

        result = ctypes.windll.user32.MessageBoxW(
            0,
            "Cancel this charter session? Nothing is written to Jira.",
            "Cancel charter",
            0x00000031,  # MB_OKCANCEL | MB_ICONWARNING
        )
        if int(result) != 1:  # IDOK
            return
        _api_json(
            "POST",
            f"/manual-sessions/{sid}/cancel",
            {"confirm": True},
        )
        _emit_float_event("cancelled", sid)
        try:
            api = DesktopApi()
            api.charter_float_close()
        except Exception:  # noqa: BLE001
            pass


class DesktopApi:
    """JS bridge for main window (native Charter chrome — no float WebView)."""

    def charter_float_available(self) -> dict[str, Any]:
        # Native host is always available once the ring thread can start.
        payload = is_float_available_payload(True)
        payload["mode"] = "g_tray_look4"
        payload["host"] = "native_toolwindow"
        payload["click_through_hole"] = True
        payload["tray_side"] = _tray_side
        payload["tray_collapsed"] = _tray_collapsed
        payload["placement"] = "side"
        return payload

    def charter_float_set_tray(self, prefs: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        global _tray_side, _tray_collapsed
        data = prefs if isinstance(prefs, dict) else {}
        if "side" in data:
            _tray_side = ring.normalize_tray_side(data.get("side"))
        if "collapsed" in data:
            _tray_collapsed = bool(data.get("collapsed"))
        virtual, monitors = _snap_context()
        dock = {"status": "ok"}
        if _float_visible:
            dock = ring.set_tray_prefs(
                side=_tray_side,
                collapsed=_tray_collapsed,
                virtual=virtual,
                monitors=monitors,
            )
        return {
            "status": "ok",
            "side": _tray_side,
            "collapsed": _tray_collapsed,
            "note_open": False,
            "dock": dock,
            "screen_bbox": ring.get_capture_bbox(),
            "host": "native_toolwindow",
            "placement": "side",
        }

    def charter_float_open(self, session: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Show hollow ring + Look 4 native side tray. Fresh CreateWindow every Start."""
        global _float_visible, _float_session_id, _tray_collapsed, _paused
        sess = session if isinstance(session, dict) else {}
        _float_session_id = str(sess.get("id") or "")
        _tray_collapsed = False
        _paused = False
        ring.set_toggle_flags(
            pause=False,
            assist=bool(sess.get("agent_assist")),
            mist=bool(sess.get("armed_mist")),
        )
        virtual, monitors = _snap_context()
        bbox = ring.default_capture_bbox(virtual=virtual, monitors=monitors)
        # Prefer saved screen_bbox when Resume carries one.
        saved = sess.get("screen_bbox")
        if isinstance(saved, (list, tuple)) and len(saved) == 4:
            try:
                bbox = [int(v) for v in saved]
            except (TypeError, ValueError):
                pass
        try:
            placed = _place_chrome(bbox)
            dock_out = placed.get("dock") or {}
            ring_out = placed.get("ring") or {}
            if dock_out.get("status") != "ok":
                try:
                    ring.hide_ring()
                    ring.destroy_side_tray()
                except Exception:  # noqa: BLE001
                    pass
                _float_visible = False
                return {
                    "status": "error",
                    "error": dock_out.get("error") or "dock_place_failed",
                    "available": True,
                    "mode": "g_tray_look4",
                    "host": "native_toolwindow",
                    "session_id": _float_session_id,
                    "screen_bbox": bbox,
                    "ring": ring_out,
                    "dock": dock_out,
                }
            _float_visible = True
            # Persist hole bbox + float mode so Still hard-fail path has bbox.
            if _float_session_id:
                virtual, _m = _snap_context()
                from plans.charter_snap import bounds_to_frame

                frame = bounds_to_frame(bbox, virtual)
                _api_json(
                    "POST",
                    f"/manual-sessions/{_float_session_id}/frame",
                    {
                        **(frame or {}),
                        "frame_mode": "float",
                        "screen_bbox": bbox,
                    },
                )
            return {
                "status": "ok",
                "available": True,
                "mode": "g_tray_look4",
                "host": "native_toolwindow",
                "placement": "side",
                "session_id": _float_session_id,
                "screen_bbox": bbox,
                "ring": ring_out,
                "dock": dock_out,
                "side": _tray_side,
                "collapsed": _tray_collapsed,
            }
        except Exception as exc:  # noqa: BLE001
            _float_visible = False
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
        try:
            # Destroy — never hide-reuse tray HWND (KAN-525).
            ring.destroy_side_tray()
        except Exception:  # noqa: BLE001
            pass
        _float_visible = False
        return {"status": "ok", "available": True, "host": "native_toolwindow"}

    def charter_float_screen_bbox(self) -> dict[str, Any]:
        bbox = ring.get_capture_bbox()
        virtual, _m = _snap_context()
        from plans.charter_snap import bounds_to_frame

        frame = bounds_to_frame(bbox, virtual)
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "frame": frame,
            "geometry": ring.dock_geom_for_bbox(
                bbox,
                side=_tray_side,
                collapsed=_tray_collapsed,
            ),
            "side": _tray_side,
            "collapsed": _tray_collapsed,
            "host": "native_toolwindow",
            "placement": "side",
        }

    def charter_float_nudge(self, dx: int = 0, dy: int = 0) -> dict[str, Any]:
        bbox = ring.nudge_bbox(ring.get_capture_bbox(), int(dx), int(dy))
        placed = _place_chrome(bbox) if _float_visible else {
            "ring": ring.set_capture_bbox(bbox, show=True),
            "dock": {"status": "ok"},
        }
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "dock": placed.get("dock"),
            "ring": placed.get("ring"),
        }

    def charter_float_drag_by(self, dx: int = 0, dy: int = 0) -> dict[str, Any]:
        """Drag capture hole by delta; tray stays glued to the side."""
        if not _float_visible:
            return {"status": "error", "error": "float_unavailable"}
        bbox = ring.nudge_bbox(ring.get_capture_bbox(), int(dx), int(dy))
        placed = _place_chrome(bbox)
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "dock": placed.get("dock"),
            "ring": placed.get("ring"),
        }

    def charter_float_resize_capture(self, d_w: int = 0, d_h: int = 0) -> dict[str, Any]:
        bbox = ring.resize_bbox(ring.get_capture_bbox(), int(d_w), int(d_h))
        placed = _place_chrome(bbox) if _float_visible else {
            "ring": ring.set_capture_bbox(bbox, show=True),
            "dock": {"status": "ok"},
        }
        return {
            "status": "ok",
            "screen_bbox": bbox,
            "dock": placed.get("dock"),
            "ring": placed.get("ring"),
        }

    def charter_float_set_size(self, width: int, height: int) -> dict[str, Any]:
        """Tray size is fixed by Look 4; capture size uses resize_capture."""
        del width, height
        geom = ring.dock_geom_for_bbox(
            ring.get_capture_bbox(),
            side=_tray_side,
            collapsed=_tray_collapsed,
        )
        return {"status": "ok", "geometry": geom, "locked": True, "host": "native_toolwindow"}

    def charter_float_apply_ring(self) -> dict[str, Any]:
        return ring.show_ring()

    def charter_float_prepare_still(self) -> dict[str, Any]:
        bbox = ring.get_capture_bbox()
        try:
            ring.hide_ring()
            ring.destroy_side_tray()
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
            if _float_visible or _float_session_id:
                _place_chrome(bbox)
            else:
                ring.show_ring()
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": "show_failed", "message": str(exc)[:120]}
        return {
            "status": "ok",
            "available": True,
            "screen_bbox": bbox,
            "host": "native_toolwindow",
        }

    def charter_float_notify_main(self, event: str, session_id: str = "") -> dict[str, Any]:
        safe_event = str(event or "")[:32]
        safe_id = str(session_id or _float_session_id or "")[:64]
        _emit_float_event(safe_event, safe_id)
        if safe_event in {"ended", "cancelled"}:
            self.charter_float_close()
        return {"status": "ok", "event": safe_event}


def main() -> int:
    global _main_window

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

    try:
        ring.ensure_ring_thread()
        ring.set_verb_callback(_on_tray_verb)
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
    # KAN-525: no second pywebview Charter Frame window (taskbar ghost class).
    webview.start()
    try:
        ring.destroy_ring()
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
