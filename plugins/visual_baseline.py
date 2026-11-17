"""Visual baseline screenshots (KAN-225 / G5 / FR-TEST-4).

Opt-in per case: store a level-scoped baseline PNG and compare later.
Mismatch fails with baseline + current paths linked. Update-baseline is
explicit only (never auto-overwrite on mismatch). One browser at a time.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import struct
import zlib
from pathlib import Path
from typing import Any

PLUGIN_NAME = "visual_baseline"
_DEFAULT_NAME = "visual_home.png"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
_BROWSER_LOCK = asyncio.Lock()


def baselines_dir(level: str | None = None) -> Path:
    """Level-scoped local visual baselines (never cloud)."""
    from settings.store import get_security_level

    lvl = (level or get_security_level() or "OFFICIAL").strip().upper() or "OFFICIAL"
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    path = Path(base) / "ai_testing_app" / "baselines" / lvl
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_baseline_name() -> str:
    return _DEFAULT_NAME


def resolve_baseline_path(name: str, *, level: str | None = None) -> Path | None:
    """Resolve a safe baseline filename under the baselines dir (no path escape)."""
    raw = (name or "").strip().replace("\\", "/")
    if not raw:
        return None
    base = Path(raw).name
    if base != raw and "/" in raw:
        if Path(raw).parent.as_posix() not in (".", ""):
            return None
        base = Path(raw).name
    if not _SAFE_NAME.match(base):
        return None
    if not base.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        base = f"{base}.png"
        if not _SAFE_NAME.match(base):
            return None
    folder = baselines_dir(level=level)
    path = (folder / base).resolve()
    try:
        path.relative_to(folder.resolve())
    except ValueError:
        return None
    return path


def _png_ihdr(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for a PNG, or None if unreadable."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    # IHDR: length(4) + type(4) + width(4) + height(4)
    if data[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return int(w), int(h)


def write_solid_png(path: Path, *, width: int = 8, height: int = 8, rgb: tuple[int, int, int] = (0, 128, 255)) -> Path:
    """Write a tiny solid-colour PNG (stdlib only — for tests / placeholders)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    r, g, b = rgb
    raw = b""
    row = b"\x00" + bytes([r, g, b]) * width
    for _ in range(height):
        raw += row
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    return path


def store_baseline(
    name: str,
    source_path: str | Path,
    *,
    level: str | None = None,
) -> dict[str, Any]:
    """Explicitly copy current image into the named baseline slot."""
    dest = resolve_baseline_path(name, level=level)
    if dest is None:
        return {
            "plugin": PLUGIN_NAME,
            "status": "fail",
            "error": f"Invalid baseline name: {(name or '')[:80]}",
            "classification": "environment",
            "baseline": None,
            "baseline_path": None,
            "current_path": str(source_path) if source_path else None,
            "matched": False,
            "updated": False,
        }
    src = Path(source_path)
    if not src.is_file():
        return {
            "plugin": PLUGIN_NAME,
            "status": "fail",
            "error": f"Current screenshot not found: {src}",
            "classification": "environment",
            "baseline": dest.name,
            "baseline_path": str(dest),
            "current_path": str(src),
            "matched": False,
            "updated": False,
        }
    try:
        shutil.copy2(src, dest)
    except OSError as exc:
        return {
            "plugin": PLUGIN_NAME,
            "status": "fail",
            "error": f"Could not store baseline: {exc}"[:300],
            "classification": "environment",
            "baseline": dest.name,
            "baseline_path": str(dest),
            "current_path": str(src),
            "matched": False,
            "updated": False,
        }
    return {
        "plugin": PLUGIN_NAME,
        "status": "pass",
        "error": None,
        "message": f"Baseline updated explicitly: {dest.name}",
        "classification": None,
        "baseline": dest.name,
        "baseline_path": str(dest),
        "current_path": str(src),
        "matched": True,
        "updated": True,
    }


def compare_to_baseline(
    name: str,
    current_path: str | Path,
    *,
    update_baseline: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Compare current PNG to stored baseline, or store when update is explicit."""
    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "status": "fail",
        "error": None,
        "message": None,
        "classification": None,
        "baseline": None,
        "baseline_path": None,
        "current_path": str(current_path) if current_path else None,
        "matched": False,
        "updated": False,
        "diff_pixels": None,
        "size_mismatch": False,
    }
    dest = resolve_baseline_path(name, level=level)
    if dest is None:
        base.update(
            {
                "error": f"Invalid baseline name: {(name or '')[:80]}",
                "message": f"Invalid baseline name: {(name or '')[:80]}",
                "classification": "environment",
            }
        )
        return base

    src = Path(current_path) if current_path else None
    if src is None or not src.is_file():
        base.update(
            {
                "baseline": dest.name,
                "baseline_path": str(dest) if dest.is_file() else None,
                "error": "Current screenshot missing for visual compare.",
                "message": "Current screenshot missing for visual compare.",
                "classification": "environment",
            }
        )
        return base

    if update_baseline:
        stored = store_baseline(dest.name, src, level=level)
        return stored

    if not dest.is_file():
        base.update(
            {
                "baseline": dest.name,
                "baseline_path": str(dest),
                "current_path": str(src),
                "error": (
                    f"No baseline stored for {dest.name}. "
                    "Update baseline explicitly before compare."
                ),
                "message": (
                    f"No baseline stored for {dest.name}. "
                    "Update baseline explicitly before compare."
                ),
                "classification": "environment",
            }
        )
        return base

    try:
        baseline_bytes = dest.read_bytes()
        current_bytes = src.read_bytes()
    except OSError as exc:
        base.update(
            {
                "baseline": dest.name,
                "baseline_path": str(dest),
                "current_path": str(src),
                "error": f"Visual baseline unreadable: {exc}"[:300],
                "message": f"Visual baseline unreadable: {exc}"[:300],
                "classification": "environment",
            }
        )
        return base

    if baseline_bytes == current_bytes:
        base.update(
            {
                "status": "pass",
                "baseline": dest.name,
                "baseline_path": str(dest),
                "current_path": str(src),
                "matched": True,
                "message": f"Visual baseline match: {dest.name}",
                "error": None,
                "diff_pixels": 0,
            }
        )
        return base

    b_size = _png_ihdr(dest)
    c_size = _png_ihdr(src)
    size_mismatch = bool(b_size and c_size and b_size != c_size)
    # Byte-level diff count (rough); not OCR / perceptual hash.
    diff_pixels = abs(len(baseline_bytes) - len(current_bytes))
    if b_size and c_size and b_size == c_size and len(baseline_bytes) == len(current_bytes):
        diff_pixels = sum(1 for a, b in zip(baseline_bytes, current_bytes) if a != b)

    base.update(
        {
            "status": "fail",
            "baseline": dest.name,
            "baseline_path": str(dest),
            "current_path": str(src),
            "matched": False,
            "size_mismatch": size_mismatch,
            "diff_pixels": diff_pixels,
            "classification": "product_bug",
            "error": (
                f"Visual baseline mismatch: {dest.name} "
                f"(baseline + current linked in evidence)."
            ),
            "message": (
                f"Visual baseline mismatch: {dest.name} "
                f"(baseline + current linked in evidence)."
            ),
        }
    )
    return base


async def capture_page_screenshot(
    url: str,
    *,
    security_level: str | None = None,
    run_id: str = "visual",
    headless: bool = True,
) -> dict[str, Any]:
    """Capture one page screenshot with a single browser (lock-enforced)."""
    from plugins.playwright_runner import run_playwright

    target = (url or "").strip()
    if not target:
        return {
            "status": "fail",
            "error": "No URL for visual capture.",
            "classification": "environment",
            "screenshot": None,
        }

    async with _BROWSER_LOCK:
        # Empty steps → navigate once + success screenshot (one browser).
        pw = await run_playwright(
            url=target,
            mode="run",
            steps=[],
            security_level=security_level,
            request_text=f"visual baseline capture {target}",
            headless=headless,
            reject_incomplete=False,
            success_evidence=True,
        )
    shot = pw.get("screenshot")
    status = str(pw.get("status") or "").lower()
    if shot and Path(str(shot)).is_file():
        return {
            "status": "pass" if status in ("pass", "ok", "success") else status or "pass",
            "error": pw.get("error"),
            "screenshot": str(shot),
            "playwright": pw,
            "one_browser": True,
        }
    return {
        "status": "fail",
        "error": str(pw.get("error") or "Visual capture produced no screenshot.")[:300],
        "classification": "environment",
        "screenshot": str(shot) if shot else None,
        "playwright": pw,
        "one_browser": True,
    }


def apply_visual_baseline(
    *,
    baseline: str = "",
    current_path: str | Path | None = None,
    update_baseline: bool = False,
    level: str | None = None,
) -> dict[str, Any]:
    """Compare or explicitly update a named visual baseline (no silent global inject)."""
    name = (baseline or "").strip()
    if not name:
        return {
            "plugin": PLUGIN_NAME,
            "status": "fail",
            "error": "No visual baseline named (opt-in required).",
            "message": "No visual baseline named (opt-in required).",
            "classification": "environment",
            "baseline": None,
            "baseline_path": None,
            "current_path": str(current_path) if current_path else None,
            "matched": False,
            "updated": False,
        }
    if current_path is None:
        return {
            "plugin": PLUGIN_NAME,
            "status": "fail",
            "error": "Current screenshot missing for visual compare.",
            "message": "Current screenshot missing for visual compare.",
            "classification": "environment",
            "baseline": name,
            "baseline_path": None,
            "current_path": None,
            "matched": False,
            "updated": False,
        }
    return compare_to_baseline(
        name,
        current_path,
        update_baseline=bool(update_baseline),
        level=level,
    )
