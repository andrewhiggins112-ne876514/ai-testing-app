"""Native capture ring as four solid border HWNDs (no WebView, no WndProc).

KAN-503: WebView SetWindowRgn stayed opaque and crashed. Four thin TOPMOST
tool windows leave a real empty hole so the AUT is visible and clickable.
"""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Any

from plans.charter_float import (
    DEFAULT_CAPTURE_H,
    DEFAULT_CAPTURE_W,
    MIN_CAPTURE_H,
    MIN_CAPTURE_W,
    SIDE,
    clamp_window_geom,
    content_bbox_from_window,
    default_window_geom,
)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

WS_POPUP = 0x80000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
HWND_TOPMOST = -1
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080
SW_HIDE = 0
SW_SHOWNOACTIVATE = 4
WM_CLOSE = 0x0010

_CLASS = "AiTestingCharterBar"
_BORDER = 4
_registered = False
_hwnds: dict[str, int] = {"n": 0, "s": 0, "e": 0, "w": 0}
_bbox: list[int] = [100, 100, 820, 520]
_lock = threading.RLock()
_thread: threading.Thread | None = None
_ready = threading.Event()
_brush = 0


def _rgb(r: int, g: int, b: int) -> int:
    return r | (g << 8) | (b << 16)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def _ensure_class() -> None:
    global _registered, _brush
    if _registered:
        return
    hinst = kernel32.GetModuleHandleW(None)
    _brush = gdi32.CreateSolidBrush(_rgb(80, 205, 255))
    wc = WNDCLASSW()
    wc.lpfnWndProc = ctypes.cast(user32.DefWindowProcW, ctypes.c_void_p)
    wc.hInstance = hinst
    wc.hCursor = user32.LoadCursorW(None, 32512)
    wc.hbrBackground = _brush
    wc.lpszClassName = _CLASS
    atom = user32.RegisterClassW(ctypes.byref(wc))
    if not atom and ctypes.GetLastError() not in (0, 1410):
        raise ctypes.WinError()
    _registered = True


def _make_bar() -> int:
    _ensure_class()
    hinst = kernel32.GetModuleHandleW(None)
    hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        _CLASS,
        "Charter Ring",
        WS_POPUP,
        0,
        0,
        10,
        10,
        None,
        None,
        hinst,
        None,
    )
    if not hwnd:
        raise ctypes.WinError()
    return int(hwnd)


def _place_bar(hwnd: int, x: int, y: int, w: int, h: int, *, hide: bool) -> None:
    flags = SWP_NOACTIVATE | (SWP_HIDEWINDOW if hide else SWP_SHOWWINDOW)
    user32.SetWindowPos(hwnd, HWND_TOPMOST, x, y, max(1, w), max(1, h), flags)
    if not hide:
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)


def _place_locked(*, hide: bool = False) -> dict[str, Any]:
    if not all(_hwnds.values()):
        return {"status": "error", "error": "no_hwnd"}
    l, t, r, b = _bbox
    bw = _BORDER
    # North / South full width including corners; East / West fill sides only.
    _place_bar(_hwnds["n"], l - bw, t - bw, (r - l) + 2 * bw, bw, hide=hide)
    _place_bar(_hwnds["s"], l - bw, b, (r - l) + 2 * bw, bw, hide=hide)
    _place_bar(_hwnds["w"], l - bw, t, bw, b - t, hide=hide)
    _place_bar(_hwnds["e"], r, t, bw, b - t, hide=hide)
    return {"status": "ok", "bbox": list(_bbox), "hidden": hide}


def _message_loop() -> None:
    global _hwnds
    try:
        _ensure_class()
        _hwnds = {k: _make_bar() for k in ("n", "s", "e", "w")}
        _place_locked(hide=True)
    except Exception:
        _hwnds = {"n": 0, "s": 0, "e": 0, "w": 0}
    finally:
        _ready.set()
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    with _lock:
        _hwnds = {"n": 0, "s": 0, "e": 0, "w": 0}


def ensure_ring_thread() -> None:
    global _thread
    with _lock:
        if _thread and _thread.is_alive() and _ready.is_set() and all(_hwnds.values()):
            return
        if not (_thread and _thread.is_alive()):
            _ready.clear()
            _thread = threading.Thread(
                target=_message_loop, name="charter-ring", daemon=True
            )
            _thread.start()
    _ready.wait(timeout=3.0)


def set_capture_bbox(bbox: Any, *, show: bool = True) -> dict[str, Any]:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return {"status": "error", "error": "bad_bbox"}
    try:
        left, top, right, bottom = (int(v) for v in bbox)
    except (TypeError, ValueError):
        return {"status": "error", "error": "bad_bbox"}
    if right - left < MIN_CAPTURE_W:
        right = left + MIN_CAPTURE_W
    if bottom - top < MIN_CAPTURE_H:
        bottom = top + MIN_CAPTURE_H
    ensure_ring_thread()
    with _lock:
        global _bbox
        _bbox = [left, top, right, bottom]
        if not all(_hwnds.values()):
            return {"status": "error", "error": "no_hwnd", "bbox": list(_bbox)}
        return _place_locked(hide=not show)


def get_capture_bbox() -> list[int]:
    with _lock:
        return list(_bbox)


def hide_ring() -> dict[str, Any]:
    ensure_ring_thread()
    with _lock:
        if not all(_hwnds.values()):
            return {"status": "ok", "hidden": True, "bbox": list(_bbox)}
        for hwnd in _hwnds.values():
            user32.ShowWindow(hwnd, SW_HIDE)
        return {"status": "ok", "hidden": True, "bbox": list(_bbox)}


def show_ring() -> dict[str, Any]:
    ensure_ring_thread()
    with _lock:
        if not all(_hwnds.values()):
            return {"status": "error", "error": "no_hwnd"}
        return _place_locked(hide=False)


def destroy_ring() -> None:
    with _lock:
        hwnds = list(_hwnds.values())
    for hwnd in hwnds:
        if hwnd:
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)


def default_capture_bbox(
    *,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> list[int]:
    geom = default_window_geom(virtual=virtual, monitors=monitors)
    bbox = content_bbox_from_window(
        geom["x"], geom["y"], geom["width"], geom["height"]
    )
    if bbox:
        return bbox
    return [120, 120, 120 + DEFAULT_CAPTURE_W, 120 + DEFAULT_CAPTURE_H]


# Look 4 Compact rail (KAN-512) — side tray glued to capture hole.
TRAY_W = 48
TRAY_COLLAPSED = 36
TRAY_NOTE_EXTRA = 220
TRAY_GAP = 0  # glued to hole edge


def normalize_tray_side(side: Any) -> str:
    s = str(side or "east").strip().lower()
    return "west" if s == "west" else "east"


def dock_geom_for_bbox(
    bbox: list[int],
    *,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
    side: str = "east",
    collapsed: bool = False,
    note_open: bool = False,
) -> dict[str, Any]:
    """Look 4 side tray geom (east/west of capture hole) on primary work area.

    Expanded: ~48px icon rail matching hole height.
    Collapsed: small tray-layout toggle on the hole edge.
    Optional note sheet grows outward (does not shrink the hole).
    Auto-flips side when the preferred edge would leave the work area.
    """
    from plans.charter_float import _primary_work

    work = _primary_work(virtual, monitors)
    try:
        left, top, right, bottom = (int(v) for v in bbox)
    except (TypeError, ValueError):
        left, top, right, bottom = 120, 120, 840, 540
    ox = int(work["left"])
    oy = int(work["top"])
    aw = max(80, int(work["width"]))
    ah = max(80, int(work["height"]))
    hole_h = max(MIN_CAPTURE_H, bottom - top)

    prefer = normalize_tray_side(side)
    if collapsed:
        width = TRAY_COLLAPSED
        height = TRAY_COLLAPSED
        y = top + 8
    else:
        width = TRAY_W + (TRAY_NOTE_EXTRA if note_open else 0)
        height = max(TRAY_W * 6, min(hole_h, max(280, ah - 48)))
        y = top

    def _x_for(which: str) -> int:
        if which == "east":
            return right + TRAY_GAP
        return left - width - TRAY_GAP

    chosen = prefer
    x = _x_for(chosen)
    # Flip if preferred side clips past the work area.
    if chosen == "east" and x + width > ox + aw - 4:
        chosen = "west"
        x = _x_for(chosen)
    elif chosen == "west" and x < ox + 4:
        chosen = "east"
        x = _x_for(chosen)

    x = max(ox, min(x, ox + aw - width))
    y = max(oy, min(y, oy + ah - height))
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "side": chosen,
        "collapsed": bool(collapsed),
        "note_open": bool(note_open),
    }


def nudge_bbox(bbox: list[int], dx: int, dy: int) -> list[int]:
    l, t, r, b = bbox
    return [l + dx, t + dy, r + dx, b + dy]


def resize_bbox(bbox: list[int], d_w: int, d_h: int) -> list[int]:
    l, t, r, b = bbox
    r = max(l + MIN_CAPTURE_W, r + d_w)
    b = max(t + MIN_CAPTURE_H, b + d_h)
    return [l, t, r, b]
