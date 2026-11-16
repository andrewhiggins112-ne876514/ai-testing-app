"""Layout mode ids stay aligned between Python, desktop.js, and App Settings."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from settings.area_layout import (  # noqa: E402
    AREA_LAYOUT_LABELS,
    AREA_LAYOUT_STORAGE_KEY,
    AREA_LAYOUTS,
    DEFAULT_AREA_LAYOUT,
    normalize_area_layout,
)


class AreaLayoutTests(unittest.TestCase):
    def test_known_ids_pass_through(self):
        for key in AREA_LAYOUTS:
            self.assertEqual(normalize_area_layout(key), key)
            self.assertEqual(normalize_area_layout("  " + key.upper() + "  "), key)

    def test_unknown_falls_back_to_overlay(self):
        self.assertEqual(normalize_area_layout(None), DEFAULT_AREA_LAYOUT)
        self.assertEqual(normalize_area_layout(""), DEFAULT_AREA_LAYOUT)
        self.assertEqual(normalize_area_layout("grid"), DEFAULT_AREA_LAYOUT)
        self.assertEqual(DEFAULT_AREA_LAYOUT, "overlay")

    def test_storage_key_and_labels(self):
        self.assertEqual(AREA_LAYOUT_STORAGE_KEY, "desktop-area-layout-v1")
        self.assertEqual(set(AREA_LAYOUT_LABELS), set(AREA_LAYOUTS))

    def test_desktop_shell_lists_the_same_ids(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn(AREA_LAYOUT_STORAGE_KEY, js)
        for key in AREA_LAYOUTS:
            self.assertIn(f'value="{key}"', html)
            self.assertIn(f'"{key}"', js)
