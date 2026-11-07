#!/usr/bin/env python3
"""Compare orb mockup vs screenshot (offline, stdlib + Pillow)."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(2)


def load_rgb(path: Path, size: tuple[int, int] = (256, 256)) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return img.resize(size, Image.Resampling.LANCZOS)


def pixel_list(img: Image.Image) -> list[tuple[int, int, int]]:
    return list(img.getdata())


def average_rgb_distance(a: Image.Image, b: Image.Image) -> float:
    pa, pb = pixel_list(a), pixel_list(b)
    total = 0.0
    n = len(pa)
    for (r1, g1, b1), (r2, g2, b2) in zip(pa, pb, strict=True):
        total += math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
    return total / max(1, n)


def note_for_score(score: float) -> str:
    if score < 28:
        return "Very close — strong match on overall colour/layout."
    if score < 45:
        return "Moderate gap — check stream continuity and core bloom."
    if score < 70:
        return "Large gap — revisit density, arc visibility, or core size."
    return "Poor match — likely wrong style or major composition drift."


def main() -> int:
    parser = argparse.ArgumentParser(description="Perceptual RGB distance between two orb images.")
    parser.add_argument("mockup", type=Path, help="Reference mockup image path")
    parser.add_argument("screenshot", type=Path, help="Candidate screenshot path")
    parser.add_argument("--size", type=int, default=256, help="Resize edge (default 256)")
    args = parser.parse_args()

    for label, p in (("mockup", args.mockup), ("screenshot", args.screenshot)):
        if not p.is_file():
            print(f"{label} not found: {p}", file=sys.stderr)
            return 1

    size = (args.size, args.size)
    mock = load_rgb(args.mockup, size)
    shot = load_rgb(args.screenshot, size)
    score = average_rgb_distance(mock, shot)

    print(f"compare_orb score: {score:.2f} (lower is closer)")
    print(note_for_score(score))
    print(f"  mockup:     {args.mockup}")
    print(f"  screenshot: {args.screenshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
