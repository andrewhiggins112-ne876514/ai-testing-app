"""KAN-343 / KAN-344 — Desktop Lab FR-UI-11 (single-target scan + detail)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopLayoutGrammarTests(unittest.TestCase):
    def test_desktop_fr_ui11_grammar_markers_desk146(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk146", html)
        self.assertIn("desk146", desk)
        self.assertIn("desktop.css?v=desk146", html)
        self.assertIn("desktop.js?v=desk146", html)

        desktop = html.split('id="app-section-desktop"', 1)[1].split(
            'id="app-section-plans"', 1
        )[0]

        self.assertIn('data-desktop-layout-grammar="1"', desktop)
        self.assertIn('data-desk-scan="1"', desktop)
        self.assertIn('data-desk-detail="1"', desktop)
        self.assertIn('data-desk-checkbox-cell="1"', desktop)
        self.assertIn('id="desk-scan"', desktop)
        self.assertIn('id="desk-detail"', desktop)
        self.assertIn('id="desk-enabled"', desktop)
        self.assertIn('id="desk-smoke"', desktop)
        self.assertIn('id="desk-steps"', desktop)
        self.assertIn('id="desk-save"', desktop)
        self.assertIn('id="desk-exe"', desktop)
        self.assertIn('id="desk-path"', desktop)
        self.assertIn('id="desk-last-smoke"', desktop)

        # Columns: Enabled · Status · Path · Last smoke
        self.assertIn(">Enabled</th>", desktop)
        self.assertIn(">Status</th>", desktop)
        self.assertIn(">Path</th>", desktop)
        self.assertIn(">Last smoke</th>", desktop)

        # Enabled lives in the 28px hit cell — not a page-width check-row.
        self.assertNotIn('class="check-row"', desktop)
        self.assertNotIn("check-row", desktop)
        hit = desktop.split('data-desk-checkbox-cell="1"', 1)[1].split("</td>", 1)[0]
        self.assertIn('id="desk-enabled"', hit)
        self.assertIn('data-desk-checkbox-stop="1"', hit)
        self.assertIn('class="desk-hit"', desktop)

        # Detail holds path override + save; toolbar keeps run actions.
        detail = desktop.split('data-desk-detail="1"', 1)[1].split(
            'id="desk-advanced"', 1
        )[0]
        self.assertIn('id="desk-exe"', detail)
        self.assertIn('id="desk-save"', detail)
        self.assertNotIn('id="desk-enabled"', detail)
        toolbar = desktop.split('id="desk-chrome-toolbar"', 1)[1].split(
            'id="desk-primary"', 1
        )[0]
        self.assertIn('id="desk-smoke"', toolbar)
        self.assertIn('id="desk-steps"', toolbar)
        self.assertNotIn('id="desk-save"', toolbar)
        self.assertNotIn('id="desk-enabled"', toolbar)

        # Empty path is an em dash cell, not a hero card.
        self.assertIn('id="desk-path" class="desk-path-cell">—</td>', desktop)
        self.assertNotIn("Smoke status", desktop)

        # JS: checkbox stop + row focus independent of enable toggle.
        self.assertIn("function focusDesktopDetail", js)
        self.assertIn("function applyDesktopPlugin", js)
        self.assertIn("function recordDeskLastSmoke", js)
        self.assertIn('data-desk-checkbox-stop', js)
        self.assertIn("stopPropagation", js)
        self.assertIn("focusDesktopDetail", js)
        self.assertIn("desk-scan-row", js)
        # Must not bind enable toggle to the whole row click path.
        self.assertNotIn("deskEnabled.checked = !deskEnabled.checked", js)
        self.assertNotIn("Opened Desktop", js)

        # CSS grammar: 28px hit + detail pane + split.
        self.assertIn('data-desktop-layout-grammar="1"', css)
        self.assertIn(".desk-scan-table", css)
        self.assertIn(".desk-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".desk-detail-pane", css)
        self.assertIn(".desk-grammar-split", css)


if __name__ == "__main__":
    unittest.main()
