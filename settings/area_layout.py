"""App area layout modes for the desktop shell (KAN-103).

The desktop UI persists the choice in localStorage under AREA_LAYOUT_STORAGE_KEY.
This module is the validation contract shared with tests. It does not read
credentials or the settings file.
"""

from __future__ import annotations

AREA_LAYOUT_STORAGE_KEY = "desktop-area-layout-v1"

# Ids match App Settings radios and docs/mockups/kan103_nav options A–E.
AREA_LAYOUTS = ("overlay", "stage", "orb_hub", "split", "floating")

AREA_LAYOUT_LABELS = {
    "overlay": "Overlay",
    "stage": "Stage",
    "orb_hub": "Orb hub",
    "split": "Split",
    "floating": "Floating",
}

DEFAULT_AREA_LAYOUT = "overlay"


def normalize_area_layout(value: str | None) -> str:
    """Return a known layout id. Unknown or blank values fall back to overlay."""
    key = (value or "").strip().lower()
    if key in AREA_LAYOUTS:
        return key
    return DEFAULT_AREA_LAYOUT
