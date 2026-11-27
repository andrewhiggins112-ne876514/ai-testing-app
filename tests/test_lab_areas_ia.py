"""KAN-273 — Lab areas UI tidy: Documents, Heal, Desktop, Sandboxes progressive disclosure."""
from __future__ import annotations

import unittest
from pathlib import Path


class LabAreasIaDesktopUiTests(unittest.TestCase):
    def test_lab_areas_ia_markers_desk148(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        css = Path("ui/desktop/desktop.css").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk148", html)
        self.assertIn("desk148", desk)
        self.assertEqual(html.count('data-lab-areas-ia="1"'), 4)

        # Documents: sticky + ingest/list primary + privacy advanced
        self.assertIn('data-documents-ia="1"', html)
        self.assertIn('data-doc-chrome="1"', html)
        self.assertIn('id="doc-chrome-toolbar"', html)
        self.assertIn('data-doc-primary="1"', html)
        self.assertIn('data-doc-list="1"', html)
        self.assertIn('data-doc-advanced="1"', html)
        doc_toolbar = html.split('id="doc-chrome-toolbar"', 1)[1].split(
            'id="doc-primary"', 1
        )[0]
        for marker in (
            'id="doc-parse"',
            'id="doc-uploads-refresh"',
            'id="doc-status"',
        ):
            self.assertIn(marker, doc_toolbar)
        doc_advanced = html.split('id="doc-advanced"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]
        self.assertIn("<summary>", doc_advanced)
        self.assertIn("Advanced &amp; help", doc_advanced)
        self.assertIn("Privacy", doc_advanced)
        self.assertNotIn('id="doc-text"', doc_toolbar)
        self.assertIn('id="doc-text"', html.split('id="doc-primary"', 1)[1])

        # Heal: sticky filter/refresh + proposals primary + policy advanced
        self.assertIn('data-heal-ia="1"', html)
        self.assertIn('data-heal-chrome="1"', html)
        self.assertIn('data-heal-primary="1"', html)
        self.assertIn('data-heal-list="1"', html)
        self.assertIn('data-heal-advanced="1"', html)
        heal_toolbar = html.split('id="heal-chrome-toolbar"', 1)[1].split(
            'id="heal-primary"', 1
        )[0]
        for marker in (
            'id="heal-run-filter"',
            'id="heal-refresh"',
            'id="heal-status"',
        ):
            self.assertIn(marker, heal_toolbar)
        heal_advanced = html.split('id="heal-advanced"', 1)[1].split(
            'id="app-section-desktop"', 1
        )[0]
        self.assertIn("FR-HEAL-2", heal_advanced)
        self.assertNotIn('id="heal-list"', heal_toolbar)
        self.assertIn('id="heal-list"', html.split('id="heal-primary"', 1)[1])

        # Desktop: smoke sticky + FR-UI-11 scan/detail primary + help advanced
        self.assertIn('data-desktop-ia="1"', html)
        self.assertIn('data-desktop-layout-grammar="1"', html)
        self.assertIn('data-desk-chrome="1"', html)
        self.assertIn('data-desk-primary="1"', html)
        self.assertIn('data-desk-advanced="1"', html)
        desk_toolbar = html.split('id="desk-chrome-toolbar"', 1)[1].split(
            'id="desk-primary"', 1
        )[0]
        for marker in (
            'id="desk-smoke"',
            'id="desk-steps"',
            'id="desk-status"',
        ):
            self.assertIn(marker, desk_toolbar)
        self.assertNotIn('id="desk-save"', desk_toolbar)
        self.assertNotIn('id="desk-enabled"', desk_toolbar)
        desk_primary = html.split('id="desk-primary"', 1)[1].split(
            'id="desk-advanced"', 1
        )[0]
        self.assertIn('data-desk-scan="1"', desk_primary)
        self.assertIn('id="desk-enabled"', desk_primary)
        self.assertIn('id="desk-exe"', desk_primary)
        self.assertIn('id="desk-save"', desk_primary)
        desk_advanced = html.split('id="desk-advanced"', 1)[1].split(
            'id="app-section-plans"', 1
        )[0]
        self.assertNotIn('id="desk-enabled"', desk_advanced)
        self.assertNotIn('id="desk-exe"', desk_advanced)
        self.assertNotIn('id="desk-save"', desk_advanced)
        self.assertNotIn("check-row", desk_advanced)

        # Sandboxes: FR-UI-11 scan/detail + enable/orchestrate sticky + help advanced
        self.assertIn('data-sandboxes-ia="1"', html)
        self.assertIn('data-sandboxes-layout-grammar="1"', html)
        self.assertIn('data-ms-chrome="1"', html)
        self.assertIn('data-ms-primary="1"', html)
        self.assertIn('data-ms-list="1"', html)
        self.assertIn('data-ms-scan="1"', html)
        self.assertIn('data-ms-detail="1"', html)
        self.assertIn('data-ms-advanced="1"', html)
        ms_toolbar = html.split('id="ms-chrome-toolbar"', 1)[1].split(
            'id="ms-primary"', 1
        )[0]
        for marker in (
            'id="ms-enabled"',
            'id="ms-action"',
            'id="ms-run"',
            'id="ms-status"',
            'id="ms-save"',
        ):
            self.assertIn(marker, ms_toolbar)
        self.assertNotIn('id="ms-upsert"', ms_toolbar)
        self.assertNotIn('id="ms-remove"', ms_toolbar)
        self.assertNotIn("check-row", ms_toolbar)
        ms_primary = html.split('id="ms-primary"', 1)[1].split(
            'id="ms-advanced"', 1
        )[0]
        self.assertIn('data-ms-scan="1"', ms_primary)
        self.assertIn('id="ms-upsert"', ms_primary)
        self.assertIn('id="ms-remove"', ms_primary)
        self.assertIn('id="ms-remove-confirm"', ms_primary)
        self.assertIn('id="ms-id"', ms_primary)
        ms_advanced = html.split('id="ms-advanced"', 1)[1].split(
            "</div>\n        </div>\n        </div>", 1
        )[0]
        self.assertIn("<summary>Advanced</summary>", ms_advanced)
        self.assertNotIn('id="ms-enabled"', ms_advanced)
        self.assertNotIn('id="ms-upsert"', ms_advanced)
        self.assertNotIn('id="ms-remove"', ms_advanced)
        self.assertNotIn('id="ms-save"', ms_advanced)
        self.assertNotIn("check-row", ms_advanced)

        # Primary blocks sit above advanced in each area
        for primary, advanced in (
            ("doc-primary", "doc-advanced"),
            ("heal-primary", "heal-advanced"),
            ("desk-primary", "desk-advanced"),
            ("ms-primary", "ms-advanced"),
        ):
            self.assertGreater(html.find(f'id="{primary}"'), 0)
            self.assertGreater(
                html.find(f'id="{advanced}"'), html.find(f'id="{primary}"')
            )

        # FR-UI-8 — Lab tools + Documents remain reachable in App menu
        nav = html.split('id="app-drawer"', 1)[1].split('id="screen-drawer"', 1)[0]
        for section in ("documents", "heal", "desktop", "sandboxes"):
            self.assertIn(f'data-section="{section}"', nav)
        self.assertIn('data-nav-group="lab"', nav)
        self.assertIn('data-section="security"', nav)
        self.assertIn('data-section="suites"', nav)

        self.assertIn(".lab-chrome-toolbar", css)
        self.assertIn(".lab-primary", css)
        self.assertIn(".lab-advanced", css)


if __name__ == "__main__":
    unittest.main()
