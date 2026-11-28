"""Native capture ring + Look 4 side tray (KAN-525 / KAN-528).

Hollow ring: four solid border HWNDs (no WebView, no SetWindowRgn).
Side tray: native TOOLWINDOW icon chrome on the *same* ring thread.
Create/show on Start/Resume; DestroyWindow on End — never hide-reuse a
WebView tray (that was the taskbar-ghost zombie class).

KAN-528: ring bars drag (move) + corner resize; tray drag moves hole;
tray re-docks via dock_geom_for_bbox without DestroyWindow during drag.
"""
from __future__ import annotations

import ctypes
import queue
import threading
from ctypes import wintypes
from typing import Any, Callable

from plans.charter_float import (
    DEFAULT_CAPTURE_H,
    DEFAULT_CAPTURE_W,
    MAX_CAPTURE_H,
    MAX_CAPTURE_W,
    MIN_CAPTURE_H,
    MIN_CAPTURE_W,
    default_window_geom,
    content_bbox_from_window,
    max_capture_for_work,
)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# 64-bit WPARAM/LPARAM overflow if DefWindowProc keeps default c_long argtypes.
user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    ctypes.c_uint,
    ctypes.c_size_t,
    ctypes.c_ssize_t,
]
user32.DefWindowProcW.restype = ctypes.c_ssize_t

WS_POPUP = 0x80000000
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
# Must be pointer-sized HWND — bare -1 breaks SetWindowPos on Win64 ctypes.
HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080
SW_HIDE = 0
SW_SHOWNOACTIVATE = 4
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_MOUSELEAVE = 0x02A3
WM_SETCURSOR = 0x0020
WM_CAPTURECHANGED = 0x0215
WM_APP = 0x8000
WM_RING_CMD = WM_APP + 41
DT_CENTER = 0x00000001
DT_VCENTER = 0x00000004
DT_SINGLELINE = 0x00000020
PS_SOLID = 0
TRANSPARENT = 1
IDC_ARROW = 32512
IDC_HAND = 32649
IDC_SIZEALL = 32646
IDC_SIZENWSE = 32642
IDC_SIZENESW = 32643
TME_LEAVE = 0x00000002
MK_LBUTTON = 0x0001
# Hit targets: thicker than hairline so Designer can grab the ring.
RING_BW = 8
CORNER_HIT = 28
DRAG_SLOP = 6

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    ctypes.c_uint,
    ctypes.c_size_t,
    ctypes.c_ssize_t,
]
user32.PostThreadMessageW.restype = wintypes.BOOL

# Suffix bumps when WndProc changes (RegisterClassW 1410 keeps stale proc).
_CLASS_BAR = "AiTestingCharterBar530"
_CLASS_TRAY = "AiTestingCharterTray530"
_CLASS_MSG = "AiTestingCharterMsg530"
_CLASS_TIP = "AiTestingCharterTip530"

# Look 4 Compact side rail (Accepted). Under-ring Rejected (KAN-525).
# Owner-drawn icons — no stock Win32 BUTTON chrome (Designer: cheap/outdated).
TRAY_W = 52
TRAY_COLLAPSED_W = 44
TRAY_GAP = 6
BTN_H = 44  # ≥40px hit targets
BTN_GAP = 4
MIN_TRAY_HWND_W = 40
MIN_TRAY_HWND_H = 40

# Verb order (expanded). Collapsed shows toggle only.
_VERBS_EXPANDED = (
    "toggle",
    "still",
    "note",
    "pause",
    "assist",
    "mist",
    "end",
    "cancel",
)
_VERB_TITLES = {
    "toggle": "Hide or show tray",
    "still": "Still",
    "note": "Note (use Manual chip)",
    "pause": "Pause",
    "assist": "Assist",
    "mist": "Mist",
    "end": "End",
    "cancel": "Cancel",
}
# Hover tooltips (KAN-530) — short “what it does” copy.
_VERB_TIPS = {
    "toggle": "Collapse or expand this tray",
    "still": "Capture a still inside the frame",
    "note": "Add a timestamped note (Manual chip)",
    "pause": "Pause or resume recording",
    "assist": "Toggle AI assist (local drafts only)",
    "mist": "Toggle light mist inside the frame",
    "end": "End session and open review",
    "cancel": "Cancel session — nothing written to Jira",
}
TIP_DELAY_MS = 400
TIP_TIMER_ID = 5301
WM_TIMER = 0x0113

LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, ctypes.c_uint, WPARAM, LPARAM
)

_registered = False
_hwnds: dict[str, int] = {"n": 0, "s": 0, "e": 0, "w": 0}
_bbox: list[int] = [100, 100, 820, 520]
_lock = threading.RLock()
_thread: threading.Thread | None = None
_win_tid = 0  # Win32 thread id for PostThreadMessageW (not Python ident)
_ready = threading.Event()
_brush = 0
_tray_brush = 0
_msg_hwnd = 0
_tray_hwnd = 0
_tray_side = "east"
_tray_collapsed = False
_tray_visible = False
_tray_hover = -1
_tip_hwnd = 0
_tip_text = ""
_tip_pending_verb: str | None = None
_dock_virtual: dict[str, int] | None = None
_dock_monitors: list[dict[str, Any]] | None = None
_pause_on = False
_assist_on = False
_mist_on = False
_verb_callback: Callable[[str], None] | None = None
_geom_callback: Callable[[list[int]], None] | None = None
_cmd_q: queue.Queue = queue.Queue()
_wndproc_tray_ref = None
_wndproc_msg_ref = None
_wndproc_bar_ref = None
_wndproc_tip_ref = None
_pen_cyan = 0
_pen_muted = 0
_pen_hot = 0
_brush_bg = 0
_brush_cell = 0
_brush_cell_hot = 0
_brush_on = 0
# Live drag state (ring thread only).
_drag_active = False
_drag_mode = "move"
_drag_origin = (0, 0)
_drag_bbox0: list[int] = [100, 100, 820, 520]
_drag_from_tray = False
_drag_pending_verb: str | None = None
_drag_moved = False


def _rgb(r: int, g: int, b: int) -> int:
    return r | (g << 8) | (b << 16)


COL_BG = _rgb(8, 18, 28)
COL_CELL = _rgb(12, 28, 40)
COL_CELL_HOT = _rgb(18, 42, 58)
COL_CYAN = _rgb(80, 205, 255)
COL_MUTED = _rgb(120, 160, 180)
COL_ON = _rgb(24, 70, 90)


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


# wintypes.POINT exists on Windows ctypes; alias for clarity in icon drawing.
POINT = wintypes.POINT


def _ensure_class() -> None:
    global _registered, _brush, _tray_brush, _wndproc_tray_ref, _wndproc_msg_ref
    global _wndproc_bar_ref, _wndproc_tip_ref
    global _pen_cyan, _pen_muted, _pen_hot
    global _brush_bg, _brush_cell, _brush_cell_hot, _brush_on
    if _registered:
        return
    hinst = kernel32.GetModuleHandleW(None)
    _brush = gdi32.CreateSolidBrush(_rgb(80, 205, 255))
    _tray_brush = gdi32.CreateSolidBrush(COL_BG)
    _brush_bg = _tray_brush
    _brush_cell = gdi32.CreateSolidBrush(COL_CELL)
    _brush_cell_hot = gdi32.CreateSolidBrush(COL_CELL_HOT)
    _brush_on = gdi32.CreateSolidBrush(COL_ON)
    _pen_cyan = gdi32.CreatePen(PS_SOLID, 2, COL_CYAN)
    _pen_muted = gdi32.CreatePen(PS_SOLID, 2, COL_MUTED)
    _pen_hot = gdi32.CreatePen(PS_SOLID, 2, COL_CYAN)
    _wndproc_bar_ref = WNDPROC(_bar_wndproc)
    _wndproc_tray_ref = WNDPROC(_tray_wndproc)
    _wndproc_msg_ref = WNDPROC(_msg_wndproc)
    _wndproc_tip_ref = WNDPROC(_tip_wndproc)

    def _reg(name: str, lpfn, bg) -> None:
        wc = WNDCLASSW()
        wc.lpfnWndProc = lpfn
        wc.hInstance = hinst
        wc.hCursor = user32.LoadCursorW(None, IDC_ARROW)
        wc.hbrBackground = bg
        wc.lpszClassName = name
        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom and ctypes.GetLastError() not in (0, 1410):
            raise ctypes.WinError()

    _reg(_CLASS_BAR, ctypes.cast(_wndproc_bar_ref, ctypes.c_void_p), _brush)
    _reg(_CLASS_TRAY, ctypes.cast(_wndproc_tray_ref, ctypes.c_void_p), _tray_brush)
    _reg(_CLASS_MSG, ctypes.cast(_wndproc_msg_ref, ctypes.c_void_p), 0)
    tip_bg = gdi32.CreateSolidBrush(_rgb(12, 28, 40))
    _reg(_CLASS_TIP, ctypes.cast(_wndproc_tip_ref, ctypes.c_void_p), tip_bg)
    _registered = True


def _remember_dock_context(
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> None:
    global _dock_virtual, _dock_monitors
    if virtual is not None:
        _dock_virtual = dict(virtual)
    if monitors is not None:
        _dock_monitors = list(monitors)


def _make_bar() -> int:
    _ensure_class()
    hinst = kernel32.GetModuleHandleW(None)
    hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        _CLASS_BAR,
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
    bw = RING_BW
    _place_bar(_hwnds["n"], l - bw, t - bw, (r - l) + 2 * bw, bw, hide=hide)
    _place_bar(_hwnds["s"], l - bw, b, (r - l) + 2 * bw, bw, hide=hide)
    _place_bar(_hwnds["w"], l - bw, t, bw, b - t, hide=hide)
    _place_bar(_hwnds["e"], r, t, bw, b - t, hide=hide)
    return {"status": "ok", "bbox": list(_bbox), "hidden": hide}


def _live_place_unlocked() -> dict[str, Any]:
    """Reposition ring + existing tray during drag (no DestroyWindow)."""
    ring_out = _place_locked(hide=False)
    tray_out: dict[str, Any] = {"status": "ok", "skipped": True}
    if _tray_hwnd:
        tray_out = _place_tray_unlocked(
            virtual=_dock_virtual, monitors=_dock_monitors
        )
    return {"status": "ok", "ring": ring_out, "dock": tray_out, "bbox": list(_bbox)}


def _edge_for_hwnd(hwnd: int) -> str | None:
    h = int(hwnd)
    for key, value in _hwnds.items():
        if int(value) == h:
            return key
    return None


def bar_hit_mode(edge: str, x: int, y: int, cw: int, ch: int) -> str:
    """Hit-test a ring bar: corners resize, mid-edge moves the hole."""
    e = (edge or "").lower()
    if e == "n":
        if x <= CORNER_HIT:
            return "nw"
        if x >= max(CORNER_HIT + 1, cw - CORNER_HIT):
            return "ne"
        return "move"
    if e == "s":
        if x <= CORNER_HIT:
            return "sw"
        if x >= max(CORNER_HIT + 1, cw - CORNER_HIT):
            return "se"
        return "move"
    if e == "w":
        if y <= CORNER_HIT:
            return "nw"
        if y >= max(CORNER_HIT + 1, ch - CORNER_HIT):
            return "sw"
        return "move"
    if e == "e":
        if y <= CORNER_HIT:
            return "ne"
        if y >= max(CORNER_HIT + 1, ch - CORNER_HIT):
            return "se"
        return "move"
    return "move"


def _cursor_for_mode(mode: str) -> int:
    m = (mode or "move").lower()
    if m in ("nw", "se"):
        return IDC_SIZENWSE
    if m in ("ne", "sw"):
        return IDC_SIZENESW
    return IDC_SIZEALL


def _client_xy(lparam: int) -> tuple[int, int]:
    x = ctypes.c_short(lparam & 0xFFFF).value
    y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
    return int(x), int(y)


def _cursor_screen() -> tuple[int, int]:
    pt = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(pt)):
        return 0, 0
    return int(pt.x), int(pt.y)


def _begin_drag(hwnd: int, mode: str, *, from_tray: bool = False) -> None:
    global _drag_active, _drag_mode, _drag_origin, _drag_bbox0
    global _drag_from_tray, _drag_moved
    _drag_active = True
    _drag_mode = mode or "move"
    _drag_origin = _cursor_screen()
    _drag_bbox0 = list(_bbox)
    _drag_from_tray = bool(from_tray)
    _drag_moved = False
    user32.SetCapture(hwnd)


def _update_drag() -> None:
    global _bbox, _drag_moved
    if not _drag_active:
        return
    cx, cy = _cursor_screen()
    dx = cx - _drag_origin[0]
    dy = cy - _drag_origin[1]
    if abs(dx) >= DRAG_SLOP or abs(dy) >= DRAG_SLOP:
        _drag_moved = True
    if not _drag_moved and _drag_from_tray:
        return
    _bbox = apply_drag_delta(_drag_bbox0, _drag_mode, dx, dy)
    _live_place_unlocked()


def _end_drag(*, commit: bool = True) -> None:
    global _drag_active, _drag_pending_verb, _drag_moved, _drag_from_tray
    was_active = _drag_active
    moved = _drag_moved
    pending = _drag_pending_verb
    from_tray = _drag_from_tray
    _drag_active = False
    _drag_pending_verb = None
    _drag_moved = False
    _drag_from_tray = False
    if user32.GetCapture():
        user32.ReleaseCapture()
    if was_active and commit and moved:
        _notify_geom()
    elif from_tray and pending and not moved:
        _fire_verb(pending)


def _notify_geom() -> None:
    cb = _geom_callback
    if cb is None:
        return
    bbox = list(_bbox)
    try:
        threading.Thread(
            target=cb, args=(bbox,), name="charter-geom", daemon=True
        ).start()
    except Exception:  # noqa: BLE001
        pass


def _bar_wndproc(hwnd, msg, wparam, lparam):  # noqa: ANN001
    if msg == WM_LBUTTONDOWN:
        edge = _edge_for_hwnd(int(hwnd))
        if edge:
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            x, y = _client_xy(int(lparam))
            mode = bar_hit_mode(
                edge, x, y, int(rect.right - rect.left), int(rect.bottom - rect.top)
            )
            _begin_drag(int(hwnd), mode, from_tray=False)
        return 0
    if msg == WM_MOUSEMOVE:
        if _drag_active and (int(wparam) & MK_LBUTTON):
            _update_drag()
            return 0
        edge = _edge_for_hwnd(int(hwnd))
        if edge:
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            x, y = _client_xy(int(lparam))
            mode = bar_hit_mode(
                edge, x, y, int(rect.right - rect.left), int(rect.bottom - rect.top)
            )
            user32.SetCursor(user32.LoadCursorW(None, _cursor_for_mode(mode)))
        return 0
    if msg == WM_LBUTTONUP:
        if _drag_active:
            _update_drag()
            _end_drag(commit=True)
        return 0
    if msg == WM_CAPTURECHANGED:
        if _drag_active and int(lparam) != int(hwnd):
            _end_drag(commit=True)
        return 0
    if msg == WM_SETCURSOR:
        edge = _edge_for_hwnd(int(hwnd))
        if edge:
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            user32.ScreenToClient(hwnd, ctypes.byref(pt))
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            mode = bar_hit_mode(
                edge,
                int(pt.x),
                int(pt.y),
                int(rect.right - rect.left),
                int(rect.bottom - rect.top),
            )
            user32.SetCursor(user32.LoadCursorW(None, _cursor_for_mode(mode)))
            return 1
        return 0
    if msg == WM_DESTROY:
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _hide_tip() -> None:
    global _tip_pending_verb
    _tip_pending_verb = None
    if _tray_hwnd:
        user32.KillTimer(_tray_hwnd, TIP_TIMER_ID)
    if _tip_hwnd:
        user32.ShowWindow(_tip_hwnd, SW_HIDE)


def _ensure_tip_hwnd() -> int:
    global _tip_hwnd
    if _tip_hwnd:
        return int(_tip_hwnd)
    _ensure_class()
    hinst = kernel32.GetModuleHandleW(None)
    hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        _CLASS_TIP,
        "Charter Tip",
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
    _tip_hwnd = int(hwnd or 0)
    return int(_tip_hwnd)


def _show_tip_for_verb(verb: str) -> None:
    global _tip_text
    text = str(_VERB_TIPS.get(verb) or _VERB_TITLES.get(verb) or verb).strip()
    if not text:
        _hide_tip()
        return
    hwnd = _ensure_tip_hwnd()
    if not hwnd:
        return
    _tip_text = text
    # Measure roughly: 7px per char + padding.
    tw = max(120, min(360, 12 + len(text) * 7))
    th = 28
    cx, cy = _cursor_screen()
    x = cx + 16
    y = cy + 20
    user32.SetWindowPos(
        hwnd, HWND_TOPMOST, x, y, tw, th, SWP_NOACTIVATE | SWP_SHOWWINDOW
    )
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
    user32.InvalidateRect(hwnd, None, True)


def _schedule_tip(verb: str | None) -> None:
    global _tip_pending_verb
    if not _tray_hwnd:
        return
    user32.KillTimer(_tray_hwnd, TIP_TIMER_ID)
    _tip_pending_verb = verb
    if not verb or _drag_active:
        _hide_tip()
        return
    user32.SetTimer(_tray_hwnd, TIP_TIMER_ID, TIP_DELAY_MS, None)


def _tip_wndproc(hwnd, msg, wparam, lparam):  # noqa: ANN001
    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        if hdc:
            try:
                rect = wintypes.RECT()
                user32.GetClientRect(hwnd, ctypes.byref(rect))
                user32.FillRect(hdc, ctypes.byref(rect), _brush_cell)
                gdi32.SelectObject(hdc, _pen_cyan)
                gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
                gdi32.RoundRect(
                    hdc, 0, 0, max(1, rect.right - 1), max(1, rect.bottom - 1), 6, 6
                )
                gdi32.SetBkMode(hdc, TRANSPARENT)
                gdi32.SetTextColor(hdc, COL_CYAN)
                # DrawTextW
                user32.DrawTextW(
                    hdc,
                    _tip_text,
                    -1,
                    ctypes.byref(rect),
                    DT_CENTER | DT_VCENTER | DT_SINGLELINE,
                )
            finally:
                user32.EndPaint(hwnd, ctypes.byref(ps))
        return 0
    if msg == WM_ERASEBKGND:
        return 1
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _destroy_tray_unlocked() -> None:
    global _tray_hwnd, _tray_visible, _tray_hover
    _hide_tip()
    if _tray_hwnd:
        user32.DestroyWindow(_tray_hwnd)
    _tray_hwnd = 0
    _tray_visible = False
    _tray_hover = -1


def _tray_verbs() -> tuple[str, ...]:
    return ("toggle",) if _tray_collapsed else _VERBS_EXPANDED


def _tray_height(collapsed: bool) -> int:
    n = 1 if collapsed else len(_VERBS_EXPANDED)
    return n * BTN_H + (n + 1) * BTN_GAP


def _verb_at_y(y: int) -> str | None:
    verbs = _tray_verbs()
    if y < BTN_GAP:
        return None
    idx = (y - BTN_GAP) // (BTN_H + BTN_GAP)
    if idx < 0 or idx >= len(verbs):
        return None
    cell_top = BTN_GAP + idx * (BTN_H + BTN_GAP)
    if y > cell_top + BTN_H:
        return None
    return verbs[idx]


def _create_tray_unlocked() -> dict[str, Any]:
    """Fresh CreateWindow owner-drawn tray — never recycle a hidden HWND."""
    global _tray_hwnd, _tray_visible, _tray_hover
    _destroy_tray_unlocked()
    _ensure_class()
    hinst = kernel32.GetModuleHandleW(None)
    height = _tray_height(_tray_collapsed)
    width = TRAY_COLLAPSED_W if _tray_collapsed else TRAY_W
    hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        _CLASS_TRAY,
        "Charter Tray",
        WS_POPUP,
        0,
        0,
        width,
        height,
        None,
        None,
        hinst,
        None,
    )
    if not hwnd:
        return {"status": "error", "error": "tray_create_failed"}
    _tray_hwnd = int(hwnd)
    _tray_hover = -1
    _tray_visible = False
    return {"status": "ok", "hwnd": _tray_hwnd, "verbs": list(_tray_verbs())}


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


class TRACKMOUSEEVENT(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("hwndTrack", wintypes.HWND),
        ("dwHoverTime", wintypes.DWORD),
    ]


def _line(hdc, pen, x1: int, y1: int, x2: int, y2: int) -> None:
    gdi32.SelectObject(hdc, pen)
    gdi32.MoveToEx(hdc, x1, y1, None)
    gdi32.LineTo(hdc, x2, y2)


def _draw_icon(hdc, verb: str, cx: int, cy: int, *, hot: bool, on: bool) -> None:
    pen = _pen_hot if (hot or on) else _pen_cyan
    if verb == "toggle":
        # Rounded frame + side strip (Look 4 tray icon).
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5))  # NULL_BRUSH
        gdi32.RoundRect(hdc, cx - 10, cy - 9, cx + 10, cy + 9, 6, 6)
        _line(hdc, pen, cx + 3, cy - 9, cx + 3, cy + 9)
        return
    if verb == "still":
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
        gdi32.RoundRect(hdc, cx - 10, cy - 7, cx + 10, cy + 8, 4, 4)
        gdi32.Ellipse(hdc, cx - 4, cy - 3, cx + 4, cy + 5)
        _line(hdc, pen, cx - 3, cy - 7, cx - 1, cy - 10)
        _line(hdc, pen, cx - 1, cy - 10, cx + 3, cy - 10)
        _line(hdc, pen, cx + 3, cy - 10, cx + 5, cy - 7)
        return
    if verb == "note":
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
        pts = (wintypes.POINT * 5)(
            wintypes.POINT(cx - 8, cy - 10),
            wintypes.POINT(cx + 4, cy - 10),
            wintypes.POINT(cx + 8, cy - 6),
            wintypes.POINT(cx + 8, cy + 10),
            wintypes.POINT(cx - 8, cy + 10),
        )
        gdi32.Polyline(hdc, pts, 5)
        _line(hdc, pen, cx + 4, cy - 10, cx + 4, cy - 6)
        _line(hdc, pen, cx + 4, cy - 6, cx + 8, cy - 6)
        _line(hdc, pen, cx - 5, cy - 1, cx + 5, cy - 1)
        _line(hdc, pen, cx - 5, cy + 3, cx + 5, cy + 3)
        return
    if verb == "pause":
        if _pause_on:
            pts = (wintypes.POINT * 3)(
                wintypes.POINT(cx - 6, cy - 8),
                wintypes.POINT(cx - 6, cy + 8),
                wintypes.POINT(cx + 8, cy),
            )
            gdi32.SelectObject(hdc, pen)
            gdi32.SelectObject(hdc, _brush_on if on else _brush_cell)
            gdi32.Polygon(hdc, pts, 3)
        else:
            gdi32.SelectObject(hdc, _brush_cell if not on else _brush_on)
            gdi32.SelectObject(hdc, pen)
            gdi32.RoundRect(hdc, cx - 8, cy - 8, cx - 3, cy + 8, 2, 2)
            gdi32.RoundRect(hdc, cx + 3, cy - 8, cx + 8, cy + 8, 2, 2)
        return
    if verb == "assist":
        # Four-point star.
        gdi32.SelectObject(hdc, pen)
        pts = (wintypes.POINT * 8)(
            wintypes.POINT(cx, cy - 10),
            wintypes.POINT(cx + 3, cy - 3),
            wintypes.POINT(cx + 10, cy),
            wintypes.POINT(cx + 3, cy + 3),
            wintypes.POINT(cx, cy + 10),
            wintypes.POINT(cx - 3, cy + 3),
            wintypes.POINT(cx - 10, cy),
            wintypes.POINT(cx - 3, cy - 3),
        )
        gdi32.SelectObject(hdc, _brush_on if on else gdi32.GetStockObject(5))
        gdi32.Polygon(hdc, pts, 8)
        return
    if verb == "mist":
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, _brush_on if on else gdi32.GetStockObject(5))
        gdi32.Ellipse(hdc, cx - 9, cy - 4, cx + 2, cy + 7)
        gdi32.Ellipse(hdc, cx - 2, cy - 8, cx + 10, cy + 5)
        _line(hdc, pen, cx - 8, cy + 7, cx + 8, cy + 7)
        return
    if verb == "end":
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, _brush_cell)
        gdi32.RoundRect(hdc, cx - 7, cy - 7, cx + 7, cy + 7, 3, 3)
        return
    if verb == "cancel":
        gdi32.SelectObject(hdc, pen)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
        gdi32.Ellipse(hdc, cx - 9, cy - 9, cx + 9, cy + 9)
        _line(hdc, pen, cx - 5, cy - 5, cx + 5, cy + 5)
        _line(hdc, pen, cx + 5, cy - 5, cx - 5, cy + 5)


def _paint_tray(hwnd: int) -> None:
    ps = PAINTSTRUCT()
    hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
    if not hdc:
        return
    try:
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        user32.FillRect(hdc, ctypes.byref(rect), _brush_bg)
        # Outer cyan hairline.
        gdi32.SelectObject(hdc, _pen_muted)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
        gdi32.RoundRect(
            hdc, 1, 1, max(2, rect.right - 1), max(2, rect.bottom - 1), 10, 10
        )
        verbs = _tray_verbs()
        width = int(rect.right - rect.left)
        for i, verb in enumerate(verbs):
            top = BTN_GAP + i * (BTN_H + BTN_GAP)
            cell = wintypes.RECT(BTN_GAP, top, width - BTN_GAP, top + BTN_H)
            hot = i == _tray_hover
            on = (verb == "pause" and _pause_on) or (
                verb == "assist" and _assist_on
            ) or (verb == "mist" and _mist_on)
            brush = _brush_cell_hot if hot else (_brush_on if on else _brush_cell)
            user32.FillRect(hdc, ctypes.byref(cell), brush)
            gdi32.SelectObject(hdc, _pen_cyan if (hot or on) else _pen_muted)
            gdi32.SelectObject(hdc, gdi32.GetStockObject(5))
            gdi32.RoundRect(
                hdc, cell.left, cell.top, cell.right, cell.bottom, 8, 8
            )
            cx = (cell.left + cell.right) // 2
            cy = (cell.top + cell.bottom) // 2
            _draw_icon(hdc, verb, cx, cy, hot=hot, on=on)
    finally:
        user32.EndPaint(hwnd, ctypes.byref(ps))


def _place_tray_unlocked(
    *,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    global _tray_side, _tray_visible
    if not _tray_hwnd:
        return {"status": "error", "error": "no_tray"}
    virt = virtual if virtual is not None else _dock_virtual
    mons = monitors if monitors is not None else _dock_monitors
    _remember_dock_context(virt, mons)
    geom = dock_geom_for_bbox(
        list(_bbox),
        virtual=virt,
        monitors=mons,
        side=_tray_side,
        collapsed=_tray_collapsed,
    )
    _tray_side = normalize_tray_side(geom.get("side") or _tray_side)
    user32.SetWindowPos(
        _tray_hwnd,
        HWND_TOPMOST,
        int(geom["x"]),
        int(geom["y"]),
        int(geom["width"]),
        int(geom["height"]),
        SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )
    user32.ShowWindow(_tray_hwnd, SW_SHOWNOACTIVATE)
    _tray_visible = True
    # Soft visibility: GetWindowRect must report ≥40×40 on-screen.
    rect = wintypes.RECT()
    if not user32.GetWindowRect(_tray_hwnd, ctypes.byref(rect)):
        return {"status": "error", "error": "tray_rect_failed", "geometry": geom}
    rw = int(rect.right) - int(rect.left)
    rh = int(rect.bottom) - int(rect.top)
    if rw < MIN_TRAY_HWND_W or rh < MIN_TRAY_HWND_H:
        return {
            "status": "error",
            "error": "tray_not_visible",
            "geometry": geom,
            "rect": [rect.left, rect.top, rect.right, rect.bottom],
        }
    return {
        "status": "ok",
        "geometry": geom,
        "side": _tray_side,
        "collapsed": _tray_collapsed,
        "hwnd": _tray_hwnd,
        "host": "native_toolwindow",
        "glued": True,
    }


def _fire_verb(verb: str) -> None:
    cb = _verb_callback
    if cb is None:
        return
    try:
        threading.Thread(
            target=cb, args=(verb,), name="charter-verb", daemon=True
        ).start()
    except Exception:  # noqa: BLE001
        pass


def _tray_wndproc(hwnd, msg, wparam, lparam):  # noqa: ANN001
    global _tray_hover, _drag_pending_verb
    if msg == WM_ERASEBKGND:
        return 1
    if msg == WM_PAINT:
        _paint_tray(int(hwnd))
        return 0
    if msg == WM_TIMER:
        if int(wparam) == TIP_TIMER_ID and _tip_pending_verb and not _drag_active:
            _show_tip_for_verb(_tip_pending_verb)
        return 0
    if msg == WM_LBUTTONDOWN:
        _hide_tip()
        _x, y = _client_xy(int(lparam))
        _drag_pending_verb = _verb_at_y(y)
        # Tray drag moves the capture hole; click-without-drag still fires verb.
        _begin_drag(int(hwnd), "move", from_tray=True)
        return 0
    if msg == WM_MOUSEMOVE:
        if _drag_active and (int(wparam) & MK_LBUTTON):
            _hide_tip()
            _update_drag()
            return 0
        y = _client_xy(int(lparam))[1]
        verbs = _tray_verbs()
        idx = -1
        verb = _verb_at_y(y)
        if verb is not None:
            idx = verbs.index(verb)
        if idx != _tray_hover:
            _tray_hover = idx
            user32.InvalidateRect(hwnd, None, False)
            _schedule_tip(verb)
        tme = TRACKMOUSEEVENT(
            ctypes.sizeof(TRACKMOUSEEVENT), TME_LEAVE, hwnd, 0
        )
        user32.TrackMouseEvent(ctypes.byref(tme))
        return 0
    if msg == WM_MOUSELEAVE:
        if _tray_hover != -1:
            _tray_hover = -1
            user32.InvalidateRect(hwnd, None, False)
        _hide_tip()
        return 0
    if msg == WM_LBUTTONUP:
        if _drag_active:
            _update_drag()
            _end_drag(commit=True)
            return 0
        y = _client_xy(int(lparam))[1]
        verb = _verb_at_y(y)
        if verb:
            _fire_verb(verb)
        return 0
    if msg == WM_CAPTURECHANGED:
        if _drag_active and int(lparam) != int(hwnd):
            _end_drag(commit=True)
        return 0
    if msg == WM_SETCURSOR:
        # Move cursor when dragging / over chrome; hand over verb cells.
        if _drag_active and _drag_moved:
            user32.SetCursor(user32.LoadCursorW(None, IDC_SIZEALL))
        else:
            user32.SetCursor(user32.LoadCursorW(None, IDC_HAND))
        return 1
    if msg == WM_DESTROY:
        _hide_tip()
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _drain_cmds() -> None:
    while True:
        try:
            fn = _cmd_q.get_nowait()
        except queue.Empty:
            break
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass


def _msg_wndproc(hwnd, msg, wparam, lparam):  # noqa: ANN001
    if msg == WM_RING_CMD:
        _drain_cmds()
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _post_ring_cmd(fn: Callable[[], None]) -> None:
    """Queue work and wake the ring thread (PostThreadMessage — reliable)."""
    _cmd_q.put(fn)
    tid = int(_win_tid or 0)
    if tid:
        # Thread messages have hwnd=NULL; GetMessage loop handles WM_RING_CMD.
        user32.PostThreadMessageW(tid, WM_RING_CMD, 0, 0)
    hwnd = int(_msg_hwnd or 0)
    if hwnd:
        user32.PostMessageW(hwnd, WM_RING_CMD, 0, 0)


def _run_on_ring(fn: Callable[[], Any], timeout: float = 5.0) -> Any:
    """Run fn on the ring thread; return its result."""
    if _thread is not None and threading.current_thread() is _thread:
        return fn()
    box: dict[str, Any] = {}
    done = threading.Event()

    def wrapper() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # noqa: BLE001
            box["error"] = exc
        finally:
            done.set()

    _post_ring_cmd(wrapper)
    if not done.wait(timeout):
        return {"status": "error", "error": "ring_cmd_timeout"}
    if "error" in box:
        return {
            "status": "error",
            "error": "ring_cmd_failed",
            "message": str(box["error"])[:120],
        }
    return box.get("value")


def _message_loop() -> None:
    global _hwnds, _msg_hwnd, _win_tid
    _win_tid = int(kernel32.GetCurrentThreadId())
    try:
        _ensure_class()
        hinst = kernel32.GetModuleHandleW(None)
        # Hidden popup as wake target (HWND_MESSAGE parent is flaky via ctypes).
        _msg_hwnd = int(
            user32.CreateWindowExW(
                WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
                _CLASS_MSG,
                "CharterMsg",
                WS_POPUP,
                0,
                0,
                1,
                1,
                None,
                None,
                hinst,
                None,
            )
            or 0
        )
        if _msg_hwnd:
            user32.ShowWindow(_msg_hwnd, SW_HIDE)
        _hwnds = {k: _make_bar() for k in ("n", "s", "e", "w")}
        _place_locked(hide=True)
    except Exception:
        _hwnds = {"n": 0, "s": 0, "e": 0, "w": 0}
        _msg_hwnd = 0
    finally:
        _ready.set()
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_RING_CMD:
            _drain_cmds()
            continue
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
        # Drain any cmds that arrived via hwnd PostMessage during dispatch.
        if not _cmd_q.empty():
            _drain_cmds()
    with _lock:
        _destroy_tray_unlocked()
        _hwnds = {"n": 0, "s": 0, "e": 0, "w": 0}
        _msg_hwnd = 0
        _win_tid = 0


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


def set_verb_callback(cb: Callable[[str], None] | None) -> None:
    global _verb_callback
    _verb_callback = cb


def set_geom_callback(cb: Callable[[list[int]], None] | None) -> None:
    """Fired after a completed native drag/resize (mouseup)."""
    global _geom_callback
    _geom_callback = cb


def set_capture_bbox(bbox: Any, *, show: bool = True) -> dict[str, Any]:
    """Place ring bars. SetWindowPos is safe cross-thread once HWNDs exist."""
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
    global _bbox
    with _lock:
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
    ensure_ring_thread()

    def _do() -> None:
        global _tip_hwnd
        with _lock:
            _destroy_tray_unlocked()
            if _tip_hwnd:
                user32.DestroyWindow(_tip_hwnd)
            _tip_hwnd = 0
            hwnds = list(_hwnds.values())
        for hwnd in hwnds:
            if hwnd:
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        if _msg_hwnd:
            user32.PostMessageW(_msg_hwnd, WM_CLOSE, 0, 0)

    _post_ring_cmd(_do)


def show_side_tray(
    *,
    side: str = "east",
    collapsed: bool = False,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create (fresh) + place Look 4 side tray. Destroys any prior tray first."""
    global _tray_side, _tray_collapsed
    ensure_ring_thread()
    _tray_side = normalize_tray_side(side)
    _tray_collapsed = bool(collapsed)
    _remember_dock_context(virtual, monitors)

    # CreateWindow/DestroyWindow must run on the ring thread.
    def _create() -> dict[str, Any]:
        with _lock:
            return _create_tray_unlocked()

    created = _run_on_ring(_create, timeout=5.0)
    if not isinstance(created, dict) or created.get("status") != "ok":
        return created if isinstance(created, dict) else {
            "status": "error",
            "error": "tray_show_failed",
        }
    with _lock:
        return _place_tray_unlocked(virtual=virtual, monitors=monitors)


def destroy_side_tray() -> dict[str, Any]:
    """DestroyWindow tray chrome (End path). No hide-reuse."""
    ensure_ring_thread()

    def _do() -> dict[str, Any]:
        with _lock:
            _destroy_tray_unlocked()
        return {"status": "ok", "destroyed": True}

    return _run_on_ring(_do) or {"status": "ok", "destroyed": True}


def place_side_tray(
    *,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Re-place existing tray beside current bbox (or create if missing)."""
    ensure_ring_thread()
    with _lock:
        if _tray_hwnd:
            return _place_tray_unlocked(virtual=virtual, monitors=monitors)

    def _create() -> dict[str, Any]:
        with _lock:
            return _create_tray_unlocked()

    created = _run_on_ring(_create, timeout=5.0)
    if not isinstance(created, dict) or created.get("status") != "ok":
        return created if isinstance(created, dict) else {
            "status": "error",
            "error": "tray_place_failed",
        }
    with _lock:
        return _place_tray_unlocked(virtual=virtual, monitors=monitors)


def set_tray_prefs(
    *,
    side: str | None = None,
    collapsed: bool | None = None,
    virtual: dict[str, int] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    global _tray_side, _tray_collapsed
    ensure_ring_thread()
    if side is not None:
        _tray_side = normalize_tray_side(side)
    if collapsed is not None:
        _tray_collapsed = bool(collapsed)

    def _create() -> dict[str, Any]:
        with _lock:
            return _create_tray_unlocked()

    created = _run_on_ring(_create, timeout=5.0)
    if not isinstance(created, dict) or created.get("status") != "ok":
        return created if isinstance(created, dict) else {
            "status": "error",
            "error": "tray_prefs_failed",
        }
    with _lock:
        return _place_tray_unlocked(virtual=virtual, monitors=monitors)


def tray_state() -> dict[str, Any]:
    with _lock:
        return {
            "visible": _tray_visible,
            "hwnd": _tray_hwnd,
            "side": _tray_side,
            "collapsed": _tray_collapsed,
            "pause": _pause_on,
            "assist": _assist_on,
            "mist": _mist_on,
            "host": "native_toolwindow",
        }


def set_toggle_flags(
    *,
    pause: bool | None = None,
    assist: bool | None = None,
    mist: bool | None = None,
) -> dict[str, Any]:
    global _pause_on, _assist_on, _mist_on
    with _lock:
        if pause is not None:
            _pause_on = bool(pause)
        if assist is not None:
            _assist_on = bool(assist)
        if mist is not None:
            _mist_on = bool(mist)
        if _tray_hwnd:
            user32.InvalidateRect(_tray_hwnd, None, False)
        return tray_state()


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
    note_open: bool = False,  # noqa: ARG001 — OOS note-sheet HWND (KAN-525)
) -> dict[str, Any]:
    """Look 4 Compact *side* rail geometry (KAN-525). Under-ring Rejected.

    KAN-530: always glue x to the hole edge — never clamp tray to a distant
    work-area edge (that was the detached-floating-tray bug).
    """
    from plans.charter_float import _primary_work

    work = _primary_work(virtual, monitors)
    try:
        left, top, right, bottom = (int(v) for v in bbox)
    except (TypeError, ValueError):
        left, top, right, bottom = 120, 120, 840, 540
    ox = int(work["left"])
    oy = int(work["top"])
    aw = max(160, int(work["width"]))
    ah = max(160, int(work["height"]))

    prefer = normalize_tray_side(side)
    width = TRAY_COLLAPSED_W if collapsed else TRAY_W
    height = _tray_height(bool(collapsed))
    height = min(height, max(BTN_H + 2 * BTN_GAP, ah - 16))
    y = top
    if y + height > oy + ah - 8:
        y = max(oy + 8, oy + ah - height - 8)
    y = max(oy + 4, min(y, oy + ah - height - 4))

    east_x = right + TRAY_GAP
    west_x = left - TRAY_GAP - width
    east_fits = east_x + width <= ox + aw - 4
    west_fits = west_x >= ox + 4

    if prefer == "east":
        if east_fits:
            side_n, x = "east", east_x
        elif west_fits:
            side_n, x = "west", west_x
        else:
            # Both clipped — stay glued to preferred edge (may overhang).
            side_n, x = "east", east_x
    else:
        if west_fits:
            side_n, x = "west", west_x
        elif east_fits:
            side_n, x = "east", east_x
        else:
            side_n, x = "west", west_x

    return {
        "x": int(x),
        "y": int(y),
        "width": width,
        "height": height,
        "side": side_n,
        "collapsed": bool(collapsed),
        "note_open": False,
        "placement": "side",
        "host": "native_toolwindow",
    }


def nudge_bbox(bbox: list[int], dx: int, dy: int) -> list[int]:
    l, t, r, b = bbox
    return [l + dx, t + dy, r + dx, b + dy]


def resize_bbox(bbox: list[int], d_w: int, d_h: int) -> list[int]:
    l, t, r, b = bbox
    max_w, max_h = max_capture_for_work(_dock_virtual, _dock_monitors)
    r = max(l + MIN_CAPTURE_W, min(l + max_w, r + d_w))
    b = max(t + MIN_CAPTURE_H, min(t + max_h, b + d_h))
    return [l, t, r, b]


def apply_drag_delta(bbox: list[int], mode: str, dx: int, dy: int) -> list[int]:
    """Apply screen-delta move/resize for a ring drag mode (KAN-528 / KAN-530)."""
    try:
        l, t, r, b = (int(v) for v in bbox)
    except (TypeError, ValueError):
        return list(bbox) if isinstance(bbox, list) else [100, 100, 820, 520]
    m = str(mode or "move").strip().lower()
    if m == "move":
        return [l + int(dx), t + int(dy), r + int(dx), b + int(dy)]
    dx_i, dy_i = int(dx), int(dy)
    if "w" in m:
        l = l + dx_i
    if "e" in m:
        r = r + dx_i
    if "n" in m:
        t = t + dy_i
    if "s" in m:
        b = b + dy_i
    # Min size — keep the anchored edges fixed when possible.
    if r - l < MIN_CAPTURE_W:
        if "w" in m and "e" not in m:
            l = r - MIN_CAPTURE_W
        else:
            r = l + MIN_CAPTURE_W
    if b - t < MIN_CAPTURE_H:
        if "n" in m and "s" not in m:
            t = b - MIN_CAPTURE_H
        else:
            b = t + MIN_CAPTURE_H
    max_w, max_h = max_capture_for_work(_dock_virtual, _dock_monitors)
    max_w = max(MIN_CAPTURE_W, min(MAX_CAPTURE_W, max_w))
    max_h = max(MIN_CAPTURE_H, min(MAX_CAPTURE_H, max_h))
    if r - l > max_w:
        if "w" in m and "e" not in m:
            l = r - max_w
        else:
            r = l + max_w
    if b - t > max_h:
        if "n" in m and "s" not in m:
            t = b - max_h
        else:
            b = t + max_h
    return [l, t, r, b]
