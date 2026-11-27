"""KAN-341 / KAN-342 — Manual FR-UI-11 (session scan + compact checks)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ManualLayoutGrammarTests(unittest.TestCase):
    def test_manual_fr_ui11_grammar_markers_desk140(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk140", html)
        self.assertIn("desk140", desk)
        self.assertIn("desktop.css?v=desk140", html)
        self.assertIn("desktop.js?v=desk140", html)

        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]

        self.assertIn('data-manual-layout-grammar="1"', manual)
        self.assertIn('data-manual-session-scan="1"', manual)
        self.assertIn('data-manual-detail="1"', manual)
        self.assertIn('data-manual-compact-check="1"', manual)
        self.assertIn('id="manual-start"', manual)
        self.assertIn('id="manual-confirm-row"', manual)
        self.assertIn('id="manual-session-list"', manual)

        # Columns: When · Charter · Link · Stage
        self.assertIn(">When</th>", manual)
        self.assertIn(">Charter</th>", manual)
        self.assertIn(">Link</th>", manual)
        self.assertIn(">Stage</th>", manual)

        # Compact checks on ticket / assist / mist; no page-width check-row in Manual.
        self.assertNotIn('class="check-row"', manual)
        self.assertNotIn("check-row", manual)
        compact_count = manual.count('data-manual-compact-check="1"')
        self.assertGreaterEqual(compact_count, 3)
        self.assertIn('id="manual-ticket-bound"', manual)
        self.assertIn('id="manual-assist"', manual)
        self.assertIn('id="manual-mist"', manual)

        # Confirm dock is a sibling after area-work (not nested inside it).
        work_at = manual.find('data-area-work="1"')
        confirm_at = manual.find('id="manual-confirm-row"')
        advanced_at = manual.find('id="manual-advanced"')
        self.assertGreater(work_at, -1)
        self.assertGreater(advanced_at, work_at)
        self.assertGreater(confirm_at, advanced_at)
        review = manual.split('id="manual-review"', 1)[1].split(
            'id="manual-advanced"', 1
        )[0]
        self.assertNotIn('id="manual-confirm-row"', review)
        work_inner = manual.split('data-area-work="1"', 1)[1].split(
            'id="manual-advanced"', 1
        )[0]
        self.assertNotIn('id="manual-confirm-row"', work_inner)

        # Charter Frame ids survive (outside Manual section).
        self.assertIn('id="charter-frame-root"', html)
        self.assertIn('id="charter-frame-dock"', html)
        self.assertIn('id="charter-end"', html)
        self.assertIn('id="charter-note-add"', html)
        self.assertIn('id="charter-still-add"', html)

        # JS builds tr scan rows; row click focuses / reopens — not li toggle only.
        self.assertIn("function refreshManualSessions", js)
        self.assertIn("function focusManualSessionRow", js)
        self.assertIn("function reopenManualFromLibrary", js)
        self.assertIn("manual-scan-row", js)
        self.assertIn("<tr class=\"manual-scan-row", js)
        self.assertIn("closest(\"tr.manual-scan-row\")", js)
        self.assertNotIn("li.manual-session-row", js)
        self.assertNotIn("manual-library-reopen", js)

        # Soft-pass wording must not appear as a pass path.
        self.assertNotIn("Opened Manual", js)

        # CSS grammar.
        self.assertIn('data-manual-layout-grammar="1"', css)
        self.assertIn(".manual-scan-table", css)
        self.assertIn(".manual-detail-pane", css)
        self.assertIn(".manual-grammar-split", css)
        self.assertIn(".manual-compact-check", css)


if __name__ == "__main__":
    unittest.main()
