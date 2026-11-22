"""KAN-327 / KAN-328 — Suites FR-UI-11 inherit (scan table + detail)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SuiteLayoutGrammarTests(unittest.TestCase):
    def test_suites_fr_ui11_grammar_markers_desk115(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk115", html)
        self.assertIn("desk115", desk)

        suites = html.split('id="app-section-suites"', 1)[1].split(
            'id="app-section-sandboxes"', 1
        )[0]
        self.assertIn('data-suite-layout-grammar="1"', suites)
        self.assertIn('data-suite-scan="1"', suites)
        self.assertIn('data-suite-detail="1"', suites)
        self.assertIn('data-suite-checkbox-cell="1"', suites)
        self.assertIn('id="suite-scan-body"', suites)
        self.assertIn('id="suite-detail"', suites)
        self.assertIn('id="suite-run-focused"', suites)
        self.assertIn('id="suite-copy-path"', suites)

        # Columns: Sel · Status · Title · File · Last
        self.assertIn(">Sel</th>", suites)
        self.assertIn(">Status</th>", suites)
        self.assertIn(">Title</th>", suites)
        self.assertIn(">File</th>", suites)
        self.assertIn(">Last</th>", suites)

        # No Settings-style section rail on Suites (single collection).
        self.assertNotIn("settings-section-rail", suites)
        self.assertNotIn("data-settings-section-rail", suites)
        self.assertNotIn('data-suite-section-rail', suites)

        # Import stays under Advanced, not list-row chrome.
        toolbar = suites.split('id="suite-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        self.assertNotIn('id="suite-import"', toolbar)
        advanced = suites.split('id="suite-advanced"', 1)[1]
        self.assertIn('id="suite-import"', advanced)

        # Old button-stack list items gone.
        self.assertNotIn("suite-list-item", suites)
        self.assertNotIn("suite-list-item", js)
        self.assertNotIn(".suite-list-item", css)

        # JS: checkbox stop vs row focus; Run selected uses checked set.
        self.assertIn("function renderSuiteList", js)
        self.assertIn("function focusSuiteDetail", js)
        self.assertIn("function getSuiteCheckedRows", js)
        self.assertIn('data-suite-checkbox-stop', js)
        self.assertIn("stopPropagation", js)
        self.assertIn("getSuiteCheckedRows()", js)
        self.assertIn("suite-run-focused", js)
        self.assertIn("Running selected", js)

        # CSS grammar: 28px hit cell + detail pane + split.
        self.assertIn('data-suite-layout-grammar="1"', css)
        self.assertIn(".suite-scan-table", css)
        self.assertIn(".suite-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".suite-detail-pane", css)
        self.assertIn(".suite-grammar-split", css)


if __name__ == "__main__":
    unittest.main()
