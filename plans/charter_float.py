"""OS-level Charter Frame float geometry (KAN-386 / FR-MAN-1 snip-tool).

Maps relative frame (0–1 on virtual desktop) ↔ absolute window placement.
No keylog / clipboard / mic. Capture chrome hides briefly during still grab.
"""
from __future__ import annotations

from typing import Any, Optional

# Chrome around the capture body (header + dock) — logical pixels.
HEADER_H = 36
DOCK_H = 92
BORDER = 2
MIN_CAPTURE_W = 240
MIN_CAPTURE_H = 160
MIN_WINDOW_W = MIN_CAPTURE_W + 2 * BORDER
MIN_WINDOW_H = MIN_CAPTURE_H + HEADER_H + DOCK_H + 2 * BORDER

_OWN_FLOAT_TITLE = "Charter Frame"


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
    border: int = BORDER,
) -> Optional[list[int]]:
    """Absolute screen bbox of the capture body inside the float window."""
    try:
        left = int(x) + int(border)
        top = int(y) + int(border) + int(header_h)
        right = int(x) + int(width) - int(border)
        bottom = int(y) + int(height) - int(border) - int(dock_h)
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
    border: int = BORDER,
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
    height = ch + header_h + dock_h + 2 * border
    x = left - border
    y = top - border - header_h
    return {
        "x": x,
        "y": y,
        "width": max(MIN_WINDOW_W, width),
        "height": max(MIN_WINDOW_H, height),
    }


def default_window_geom(
    *,
    virtual: dict[str, int] | None = None,
    frame: dict[str, float] | None = None,
) -> dict[str, int]:
    """Place float window from relative frame on the virtual desktop."""
    virt = virtual or {"left": 0, "top": 0, "width": 1280, "height": 800}
    fr = frame or {"x": 0.18, "y": 0.16, "w": 0.64, "h": 0.58}
    ox = int(virt.get("left") or 0)
    oy = int(virt.get("top") or 0)
    vw = max(1, int(virt.get("width") or 1280))
    vh = max(1, int(virt.get("height") or 800))
    try:
        fx = float(fr.get("x", 0.18))
        fy = float(fr.get("y", 0.16))
        fw = float(fr.get("w", 0.64))
        fh = float(fr.get("h", 0.58))
    except (TypeError, ValueError):
        fx, fy, fw, fh = 0.18, 0.16, 0.64, 0.58
    left = ox + int(fx * vw)
    top = oy + int(fy * vh)
    right = left + max(MIN_CAPTURE_W, int(fw * vw))
    bottom = top + max(MIN_CAPTURE_H, int(fh * vh))
    return window_geom_from_content_bbox([left, top, right, bottom])


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


def is_float_available_payload(available: bool) -> dict[str, Any]:
    return {
        "available": bool(available),
        "title": _OWN_FLOAT_TITLE,
        "mode": "os_float",
        "keylog": False,
        "clipboard": False,
        "mic": False,
    }
