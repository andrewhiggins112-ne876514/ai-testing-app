"""Charter Frame window/monitor snap (KAN-287 / FR-MAN-1 B1 completion).

Win32 geometry via ctypes — no new dependencies. Relative frame is expressed
against the virtual-desktop union so stills can use absolute screen_bbox.
"""
from __future__ import annotations

import sys
from typing import Any, Optional

# Skip our own shell + Charter float when listing snap-to-window targets.
_OWN_TITLE_NEEDLES = ("ai testing agent", "charter frame")
_MIN_SIDE = 40


def _normalize_bbox(raw: Any) -> Optional[list[int]]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        left, top, right, bottom = (int(v) for v in raw)
    except (TypeError, ValueError):
        return None
    if right - left < _MIN_SIDE or bottom - top < _MIN_SIDE:
        return None
    return [left, top, right, bottom]


def virtual_desktop_from_monitors(monitors: list[dict[str, Any]]) -> dict[str, int]:
    """Union of monitor bboxes → virtual desktop origin + size."""
    if not monitors:
        return {"left": 0, "top": 0, "width": 1920, "height": 1080}
    lefts: list[int] = []
    tops: list[int] = []
    rights: list[int] = []
    bottoms: list[int] = []
    for mon in monitors:
        bbox = _normalize_bbox(mon.get("bbox"))
        if not bbox:
            continue
        lefts.append(bbox[0])
        tops.append(bbox[1])
        rights.append(bbox[2])
        bottoms.append(bbox[3])
    if not lefts:
        return {"left": 0, "top": 0, "width": 1920, "height": 1080}
    left = min(lefts)
    top = min(tops)
    right = max(rights)
    bottom = max(bottoms)
    return {
        "left": left,
        "top": top,
        "width": max(_MIN_SIDE, right - left),
        "height": max(_MIN_SIDE, bottom - top),
    }


def bounds_to_frame(
    bbox: Any,
    virtual: dict[str, int] | None = None,
) -> dict[str, float]:
    """Map absolute screen bbox → relative frame (0–1) on the virtual desktop."""
    rect = _normalize_bbox(bbox)
    if rect is None:
        return {"x": 0.18, "y": 0.16, "w": 0.64, "h": 0.58}
    virt = virtual or {"left": 0, "top": 0, "width": 1920, "height": 1080}
    vw = max(1, int(virt.get("width") or 1920))
    vh = max(1, int(virt.get("height") or 1080))
    ox = int(virt.get("left") or 0)
    oy = int(virt.get("top") or 0)
    x = (rect[0] - ox) / vw
    y = (rect[1] - oy) / vh
    w = (rect[2] - rect[0]) / vw
    h = (rect[3] - rect[1]) / vh
    x = max(0.0, min(1.0, x))
    y = max(0.0, min(1.0, y))
    w = max(0.12, min(1.0 - x, w))
    h = max(0.12, min(1.0 - y, h))
    return {"x": round(x, 6), "y": round(y, 6), "w": round(w, 6), "h": round(h, 6)}


def _list_monitors_win32() -> list[dict[str, Any]]:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    monitors: list[dict[str, Any]] = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )
    MONITORINFOF_PRIMARY = 0x00000001

    def _cb(hmon, _hdc, _lprc, _lparam):  # type: ignore[no-untyped-def]
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            return True
        bbox = [
            int(info.rcMonitor.left),
            int(info.rcMonitor.top),
            int(info.rcMonitor.right),
            int(info.rcMonitor.bottom),
        ]
        if _normalize_bbox(bbox) is None:
            return True
        is_primary = bool(info.dwFlags & MONITORINFOF_PRIMARY)
        idx = len(monitors) + 1
        monitors.append(
            {
                "id": f"mon{idx}",
                "label": f"Monitor {idx}" + (" (primary)" if is_primary else ""),
                "bbox": bbox,
                "is_primary": is_primary,
            }
        )
        return True

    user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(_cb), 0)
    # Stable ids: primary first, then left-to-right.
    monitors.sort(key=lambda m: (not m["is_primary"], m["bbox"][0], m["bbox"][1]))
    for i, mon in enumerate(monitors, start=1):
        mon["id"] = f"mon{i}"
        mon["label"] = f"Monitor {i}" + (" (primary)" if mon["is_primary"] else "")
    return monitors


def _list_windows_win32() -> list[dict[str, Any]]:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    results: list[dict[str, Any]] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    def _cb(hwnd, _lparam):  # type: ignore[no-untyped-def]
        if not user32.IsWindowVisible(hwnd):
            return True
        # Skip owned / tool windows without a title bar presence.
        if user32.GetWindow(hwnd, 4):  # GW_OWNER
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = (buf.value or "").strip()
        if not title:
            return True
        low = title.lower()
        if any(n in low for n in _OWN_TITLE_NEEDLES):
            return True
        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        bbox = [int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)]
        if _normalize_bbox(bbox) is None:
            return True
        results.append(
            {
                "id": f"hwnd{int(hwnd)}",
                "title": title[:120],
                "bbox": bbox,
                "hwnd": int(hwnd),
            }
        )
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    results.sort(key=lambda w: w["title"].lower())
    return results


def list_snap_targets() -> dict[str, Any]:
    """Monitors + visible top-level windows for Charter Frame snap pickers."""
    if sys.platform != "win32":
        # Deterministic stub for non-Windows unit hosts.
        monitors = [
            {
                "id": "mon1",
                "label": "Monitor 1 (primary)",
                "bbox": [0, 0, 1920, 1080],
                "is_primary": True,
            }
        ]
        windows: list[dict[str, Any]] = []
        virtual = virtual_desktop_from_monitors(monitors)
        return {
            "status": "ok",
            "platform": sys.platform,
            "monitors": monitors,
            "windows": windows,
            "virtual": virtual,
        }

    try:
        monitors = _list_monitors_win32()
    except Exception as exc:  # noqa: BLE001 — snap must not crash Manual
        return {
            "status": "error",
            "error": "monitor_enum_failed",
            "message": str(exc)[:200],
            "monitors": [],
            "windows": [],
            "virtual": virtual_desktop_from_monitors([]),
        }
    try:
        windows = _list_windows_win32()
    except Exception as exc:  # noqa: BLE001
        windows = []
        win_err = str(exc)[:200]
    else:
        win_err = ""

    virtual = virtual_desktop_from_monitors(monitors)
    out: dict[str, Any] = {
        "status": "ok",
        "platform": "win32",
        "monitors": monitors,
        "windows": [{"id": w["id"], "title": w["title"], "bbox": w["bbox"]} for w in windows],
        "virtual": virtual,
    }
    if win_err:
        out["windows_warning"] = win_err
    return out


def resolve_snap_target(
    mode: str,
    target_id: str,
    *,
    targets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve monitor|window target → bbox, label, relative frame."""
    mode_norm = (mode or "").strip().lower()
    tid = (target_id or "").strip()
    if mode_norm not in {"monitor", "window"}:
        return {
            "status": "error",
            "error": "invalid_mode",
            "message": "mode must be 'monitor' or 'window'.",
        }
    if not tid:
        return {
            "status": "error",
            "error": "target_required",
            "message": "target_id is required.",
        }

    payload = targets if isinstance(targets, dict) else list_snap_targets()
    virtual = payload.get("virtual") or virtual_desktop_from_monitors(
        list(payload.get("monitors") or [])
    )

    if mode_norm == "monitor":
        for mon in payload.get("monitors") or []:
            if str(mon.get("id")) == tid:
                bbox = _normalize_bbox(mon.get("bbox"))
                if bbox is None:
                    break
                return {
                    "status": "ok",
                    "mode": "monitor",
                    "target_id": tid,
                    "label": str(mon.get("label") or tid),
                    "screen_bbox": bbox,
                    "frame": bounds_to_frame(bbox, virtual),
                    "virtual": virtual,
                }
        return {
            "status": "error",
            "error": "target_not_found",
            "message": f"No monitor {tid!r}.",
        }

    for win in payload.get("windows") or []:
        if str(win.get("id")) == tid:
            bbox = _normalize_bbox(win.get("bbox"))
            if bbox is None:
                break
            title = str(win.get("title") or tid)
            return {
                "status": "ok",
                "mode": "window",
                "target_id": tid,
                "label": title,
                "screen_bbox": bbox,
                "frame": bounds_to_frame(bbox, virtual),
                "virtual": virtual,
            }
    return {
        "status": "error",
        "error": "target_not_found",
        "message": f"No window {tid!r}.",
    }
