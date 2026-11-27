"""KAN-333 / KAN-334 — Reports library FR-UI-11 (scan table + detail)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReportsLayoutGrammarTests(unittest.TestCase):
    def test_reports_fr_ui11_scan_detail_markers_desk136(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk136", html)
        self.assertIn("desk136", desk)

        reports = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]

        self.assertIn('data-reports-layout-grammar="1"', reports)
        self.assertIn('data-rpt-scan="1"', reports)
        self.assertIn('data-rpt-detail="1"', reports)
        self.assertIn('id="rpt-scan-body"', reports)
        self.assertIn('id="rpt-markdown"', reports)
        self.assertIn('id="rpt-open-settings"', reports)
        self.assertIn(">When</th>", reports)
        self.assertIn(">Title</th>", reports)
        self.assertIn(">Level</th>", reports)
        self.assertIn(">Kind</th>", reports)

        # Duplicate openers removed.
        self.assertNotIn('id="rpt-library-select"', reports)
        self.assertNotIn('id="rpt-library-list"', reports)
        self.assertNotIn("rpt-library-item", js)
        self.assertNotIn(".rpt-library-item", css)

        # No multi-select / section editor in Reports.
        self.assertNotIn('type="checkbox"', reports)
        self.assertNotIn('id="rpt-summary"', reports)
        self.assertNotIn("settings-section-rail", reports)
        self.assertNotIn("data-settings-section-rail", reports)

        self.assertIn("function renderReportLibraryList", js)
        self.assertIn("createElement(\"tr\")", js)
        self.assertIn("rpt-scan-row", js)
        self.assertIn("rpt-scan-body", js)
        self.assertIn("loadReportDetail", js)
        self.assertIn("openReportSettings", js)

        self.assertIn('data-reports-layout-grammar="1"', css)
        self.assertIn(".rpt-scan-table", css)
        self.assertIn(".rpt-detail-pane", css)
        self.assertIn(".rpt-grammar-split", css)


if __name__ == "__main__":
    unittest.main()
