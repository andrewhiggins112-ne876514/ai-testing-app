"""KAN-271 — Reports area UI tidy: sticky toolbar, primary list/detail, collapsed export."""
from __future__ import annotations

import unittest
from pathlib import Path


class ReportsIaDesktopUiTests(unittest.TestCase):
    def test_reports_ia_markers_desk99(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        css = Path("ui/desktop/desktop.css").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk99", html)
        self.assertIn("desk99", desk)
        self.assertIn('data-reports-ia="1"', html)
        self.assertIn('data-rpt-sticky="1"', html)
        self.assertIn('id="rpt-sticky-toolbar"', html)
        self.assertIn('data-rpt-primary="1"', html)
        self.assertIn('data-rpt-list="1"', html)
        self.assertIn('id="rpt-library-list"', html)
        self.assertIn('id="rpt-library-select"', html)
        self.assertIn('id="rpt-library-refresh"', html)
        self.assertIn('id="rpt-open-settings"', html)
        self.assertIn('data-rpt-detail="1"', html)
        self.assertIn('id="rpt-detail"', html)
        self.assertIn('data-rpt-advanced="1"', html)
        self.assertIn('id="rpt-advanced"', html)
        self.assertIn('id="rpt-export-run"', html)
        self.assertIn('id="rpt-export-pack"', html)

        toolbar = html.split('id="rpt-sticky-toolbar"', 1)[1].split(
            'id="rpt-primary"', 1
        )[0]
        for marker in (
            'id="rpt-library-refresh"',
            'id="rpt-open-settings"',
            'id="rpt-status"',
        ):
            self.assertIn(marker, toolbar)

        # Export stays secondary (advanced), not equal-weight in the sticky toolbar.
        self.assertNotIn('id="rpt-export-run"', toolbar)
        self.assertNotIn('id="rpt-export-pack"', toolbar)
        advanced = html.split('id="rpt-advanced"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        self.assertIn('id="rpt-export-run"', advanced)
        self.assertIn('id="rpt-export-pack"', advanced)
        self.assertIn("<summary>", advanced)

        primary_pos = html.find('id="rpt-primary"')
        advanced_pos = html.find('id="rpt-advanced"')
        self.assertGreater(primary_pos, 0)
        self.assertGreater(advanced_pos, primary_pos)

        reports_block = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        self.assertNotIn('id="rpt-summary"', reports_block)
        self.assertIn("No saved reports yet", reports_block)

        self.assertIn("renderReportLibraryList", js)
        self.assertIn("rptSelectedId", js)
        self.assertIn("/api/reports", js)
        self.assertIn("openReportSettings", js)
        self.assertIn(".rpt-sticky-toolbar", css)
        self.assertIn(".rpt-library-item", css)
        self.assertIn(".rpt-advanced", css)


if __name__ == "__main__":
    unittest.main()
