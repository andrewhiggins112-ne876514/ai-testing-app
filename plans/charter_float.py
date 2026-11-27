"""OS-level Charter Frame float geometry (KAN-386 / FR-MAN-1 snip-tool).

Hollow ring: header + side borders + dock stay hittable; capture hole has no
window region so the AUT stays visible and clickable (snipping-tool style).
No keylog / clipboard / mic.
"""
from __future__ import annotations

from typing import Any, Optional

# Chrome around the capture hole (logical pixels).
HEADER_H = 40
DOCK_H = 100
SIDE = 10  # left/right border thickness (also top/bottom of hole inset)
MIN_CAPTURE_W = 280
MIN_CAPTURE_H = 180
MIN_WINDOW_W = MIN_CAPTURE_W + 2 * SIDE
MIN_WINDOW_H = MIN_CAPTURE_H + HEADER_H + DOCK_H
# Snip defaults — never span the whole virtual desktop.
DEFAULT_CAPTURE_W = 720
DEFAULT_CAPTURE_H = 420
MAX_CAPTURE_W = 960
MAX_CAPTURE_H = 640

_OWN_FLOAT_TITLE = "Charter Frame"

# Back-compat aliases used by older call sites / tests.
BORDER = SIDE


def float_window_title() -> str:
    return _OWN_FLOAT_TITLE


def content_bbox_from_window(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    header_h: int = HEADER_H,
    dock_h: int = DOCK_H,
    border: int = SIDE,
) -> Optional[list[int]]:
    """Absolute screen bbox of the hollow capture hole."""
    try:
        left = int(x) + int(border)
        top = int(y) + int(header_h)
        right = int(x) + int(width) - int(border)
        bottom = int(y) + int(height) - int(dock_h)
    except (TypeError, ValueError):
        return None
    if right - left < 12 or bottom - top < 12:
        return None
    return [left, top, right, bottom]


def window_geom_from_content_bbox(
    bbox: Any,
    *,
    header_h: int = HEADER_H,
    dock_h: int = DOCK_H,
    border: int = SIDE,
) -> dict[str, int]:
    """Expand a capture bbox to outer float-window x/y/width/height."""
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return default_window_geom()
    try:
        left, top, right, bottom = (int(v) for v in bbox)
    except (TypeError, ValueError):
        return default_window_geom()
    cw = max(MIN_CAPTURE_W, right - left)
    ch = max(MIN_CAPTURE_H, bottom - top)
    width = cw + 2 * border
    height = ch + header_h + dock_h
    x = left - border
    y = top - header_h
    return {
        "x": x,
        "y": y,
        "width": max(MIN_WINDOW_W, width),
        "height": max(MIN_WINDOW_H, height),
    }


def _primary_work(virtual: dict[str, int] | None, monitors: list[dict[str, Any]] | None) -> dict[str, int]:
    """Prefer primary monitor bbox; fall back to virtual desktop."""
    if monitors:
        primary = next((m for m in monitors if m.get("is_primary")), None) or monitors[0]
        bbox = primary.get("bbox")
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            try:
                left, top, right, bottom = (int(v) for v in bbox)
                return {
                    "left": left,
                    "top": top,
                    "width": max(1, right - left),
                    "height": max(1, bottom - top),
                }
            except (TypeError, ValueError):
                pass
    virt = virtual or {"left": 0, "top": 0, "width": 1280, "height": 800}
    return {
        "left": int(virt.get("left") or 0),
        "top": int(virt.get("top") or 0),
        "width": max(1, int(virt.get("width") or 1280)),
        "height": max(1, int(virt.get("height") or 800)),
    }


def clamp_window_geom(
    geom: dict[str, int],
    *,
    work: dict[str, int] | None = None,
) -> dict[str, int]:
    """Keep the float fully inside a work area and within max snip size."""
    area = work or {"left": 0, "top": 0, "width": 1280, "height": 800}
    ox = int(area["left"])
    oy = int(area["top"])
    aw = max(MIN_WINDOW_W, int(area["width"]))
    ah = max(MIN_WINDOW_H, int(area["height"]))
    max_w = min(aw - 16, MAX_CAPTURE_W + 2 * SIDE)
    max_h = min(ah - 16, MAX_CAPTURE_H + HEADER_H + DOCK_H)
    width = max(MIN_WINDOW_W, min(int(geom.get("width") or MIN_WINDOW_W), max_w))
    height = max(MIN_WINDOW_H, min(int(geom.get("height") or MIN_WINDOW_H), max_h))
    x = int(geom.get("x") or ox)
    y = int(geom.get("y") or oy)
    x = max(ox, min(x, ox + aw - width))
    y = max(oy, min(y, oy + ah - height))
    return {"x": x, "y": y, "width": width, "height": height}


def default_window_geom(
    *,
    virtual: dict[str, int] | None = None,
    frame: dict[str, float] | None = None,
    monitors: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Snip-sized float centered on the primary monitor (not full virtual desktop)."""
    work = _primary_work(virtual, monitors)
    # Ignore huge relative frames from old sessions — always start snip-sized.
    cw = min(DEFAULT_CAPTURE_W, max(MIN_CAPTURE_W, int(work["width"] * 0.45)))
    ch = min(DEFAULT_CAPTURE_H, max(MIN_CAPTURE_H, int(work["height"] * 0.45)))
    if isinstance(frame, dict):
        # Allow a previously saved float bbox only when already absolute-ish via screen use;
        # relative frame on multi-monitor virtual desktop caused oversized windows.
        try:
            fw = float(frame.get("w", 0))
            fh = float(frame.get("h", 0))
            if 0.05 <= fw <= 0.55 and 0.05 <= fh <= 0.55:
                cw = max(MIN_CAPTURE_W, min(MAX_CAPTURE_W, int(fw * work["width"])))
                ch = max(MIN_CAPTURE_H, min(MAX_CAPTURE_H, int(fh * work["height"])))
        except (TypeError, ValueError):
            pass
    left = work["left"] + max(0, (work["width"] - cw) // 2)
    top = work["top"] + max(0, (work["height"] - ch) // 2)
    geom = window_geom_from_content_bbox([left, top, left + cw, top + ch])
    return clamp_window_geom(geom, work=work)


def relative_frame_from_window(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    virtual: dict[str, int] | None = None,
) -> dict[str, float]:
    """Map float window → relative frame on virtual desktop (via content bbox)."""
    from plans.charter_snap import bounds_to_frame

    bbox = content_bbox_from_window(x, y, width, height)
    return bounds_to_frame(bbox, virtual)


def hollow_region_rects(
    width: int,
    height: int,
    *,
    header_h: int = HEADER_H,
    dock_h: int = DOCK_H,
    side: int = SIDE,
) -> dict[str, list[int]]:
    """Client-relative outer + hole rects for SetWindowRgn (RGN_DIFF)."""
    w = max(MIN_WINDOW_W, int(width))
    h = max(MIN_WINDOW_H, int(height))
    hole_left = int(side)
    hole_top = int(header_h)
    hole_right = w - int(side)
    hole_bottom = h - int(dock_h)
    if hole_right - hole_left < 12:
        hole_right = hole_left + 12
    if hole_bottom - hole_top < 12:
        hole_bottom = hole_top + 12
    return {
        "outer": [0, 0, w, h],
        "hole": [hole_left, hole_top, hole_right, hole_bottom],
    }


def apply_hollow_window_region(
    hwnd: int,
    width: int,
    height: int,
    *,
    header_h: int = HEADER_H,
    dock_h: int = DOCK_H,
    side: int = SIDE,
) -> dict[str, Any]:
    """Punch a click-through hole so the AUT is visible and usable (Win32)."""
    if not hwnd:
        return {"status": "error", "error": "no_hwnd"}
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    rects = hollow_region_rects(
        width, height, header_h=header_h, dock_h=dock_h, side=side
    )
    ol, ot, oright, obottom = rects["outer"]
    hl, ht, hr, hb = rects["hole"]
    CreateRectRgn = user32.CreateRectRgn
    CombineRgn = user32.CombineRgn
    SetWindowRgn = user32.SetWindowRgn
    DeleteObject = ctypes.windll.gdi32.DeleteObject
    RGN_DIFF = 4

    outer = CreateRectRgn(ol, ot, oright, obottom)
    hole = CreateRectRgn(hl, ht, hr, hb)
    if not outer or not hole:
        if outer:
            DeleteObject(outer)
        if hole:
            DeleteObject(hole)
        return {"status": "error", "error": "rgn_create_failed"}
    CombineRgn(outer, outer, hole, RGN_DIFF)
    DeleteObject(hole)
    # SetWindowRgn takes ownership of the region handle.
    ok = bool(SetWindowRgn(wintypes.HWND(int(hwnd)), outer, True))
    return {
        "status": "ok" if ok else "error",
        "error": None if ok else "set_window_rgn_failed",
        "hwnd": int(hwnd),
        "rects": rects,
    }


def float_hwnd_from_native(native: Any) -> int:
    """Best-effort HWND from pywebview window.native (WinForms Form)."""
    if native is None:
        return 0
    try:
        handle = getattr(native, "Handle", None)
        if handle is None:
            return 0
        to_int = getattr(handle, "ToInt32", None) or getattr(handle, "ToInt64", None)
        if callable(to_int):
            return int(to_int())
        return int(handle)
    except Exception:  # noqa: BLE001
        return 0


def is_float_available_payload(available: bool) -> dict[str, Any]:
    return {
        "available": bool(available),
        "title": _OWN_FLOAT_TITLE,
        "mode": "os_float_hollow",
        "keylog": False,
        "clipboard": False,
        "mic": False,
        "click_through_hole": True,
    }
