"""KAN-369 — Scan-craft grammar splits stretch so panes can scroll (KAN-368)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SPLITS = (
    ("heal-grammar-split", "data-heal-layout-grammar"),
    ("suite-grammar-split", "data-suite-layout-grammar"),
    ("rpt-grammar-split", "data-reports-layout-grammar"),
    ("manual-grammar-split", "data-manual-layout-grammar"),
    ("ms-grammar-split", "data-sandboxes-layout-grammar"),
    ("desk-grammar-split", "data-desktop-layout-grammar"),
    ("plan-tabs-grammar-split", "data-plans-tabs-layout-grammar"),
)


class ScanCraftScrollStretchTests(unittest.TestCase):
    def test_grammar_splits_stretch_desk147(self) -> None:
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk147", html)
        self.assertIn("desk147", desk)
        self.assertIn("KAN-368", css)

        # Shared harden: no-outer-scroll splits stretch + row minmax.
        block = css.split("KAN-368", 1)[1].split(
            ".app-section[data-scan-craft=\"1\"] [data-scan-scroll=", 1
        )[0]
        self.assertIn("align-items: stretch", block)
        self.assertIn("grid-template-rows: minmax(0, 1fr)", block)

        for class_name, _attr in SPLITS:
            # Per-area split must not use align-items:start.
            pat = re.compile(
                rf"\.{re.escape(class_name)}\s*\{{([^}}]*)\}}",
                re.S,
            )
            m = pat.search(css)
            self.assertIsNotNone(m, class_name)
            body = m.group(1)
            self.assertIn("align-items: stretch", body, class_name)
            self.assertNotIn("align-items: start", body, class_name)
            self.assertIn("grid-template-rows: minmax(0, 1fr)", body, class_name)

        # Settings / Security with-detail grids.
        for needle in (
            ".settings-section-with-detail:not([hidden])",
            ".sec-section-with-detail:not([hidden])",
        ):
            idx = css.find(needle)
            self.assertGreater(idx, 0, needle)
            chunk = css[idx : idx + 280]
            self.assertIn("align-items: stretch", chunk, needle)
            self.assertNotIn("align-items: start", chunk, needle)


if __name__ == "__main__":
    unittest.main()
