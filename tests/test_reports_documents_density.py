"""KAN-317 — Track3 Reports + Documents density from accepted wire (KAN-316)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class ReportsDocumentsDensityTests(unittest.TestCase):
    def test_reports_documents_density_desk113(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk113", html)
        self.assertIn("desk113", desk)
        self.assertIn('data-reports-documents-density="1"', html)
        self.assertIn("Accepted", wires)
        self.assertIn("KAN-316", wires)

        reports = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        documents = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]
        self.assertIn('data-reports-documents-density="1"', reports)
        self.assertIn('data-reports-documents-density="1"', documents)

        # Reports: toolbar → work (no intro h3/hint above chrome).
        rpt_toolbar = reports.find('id="rpt-chrome-toolbar"')
        rpt_work = reports.find('data-area-work="1"')
        self.assertGreater(rpt_work, rpt_toolbar)
        before_rpt = reports[:rpt_toolbar]
        self.assertNotIn("orb-section-label", before_rpt)
        self.assertNotIn("drawer-hint", before_rpt)

        rpt_actions = reports.split('id="rpt-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="rpt-library-refresh"',
            'id="rpt-open-settings"',
            'id="rpt-status"',
        ):
            self.assertIn(marker, rpt_actions)
        self.assertNotIn('id="rpt-export-run"', rpt_actions)
        self.assertNotIn('id="rpt-export-pack"', rpt_actions)

        # About + primary list/detail + Advanced export scroll in work.
        self.assertGreater(reports.find('data-rpt-about="1"'), rpt_work)
        self.assertGreater(reports.find('data-rpt-primary="1"'), rpt_work)
        self.assertGreater(reports.find('data-rpt-advanced="1"'), rpt_work)
        self.assertIn("Advanced (export run / pack)", reports)
        self.assertIn("Saved reports", reports)

        # Documents: toolbar → work (no intro h3 above chrome).
        doc_toolbar = documents.find('id="doc-chrome-toolbar"')
        doc_work = documents.find('data-area-work="1"')
        self.assertGreater(doc_work, doc_toolbar)
        before_doc = documents[:doc_toolbar]
        self.assertNotIn("orb-section-label", before_doc)
        self.assertNotIn("drawer-hint", before_doc)

        doc_actions = documents.split('id="doc-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="doc-parse"',
            'id="doc-uploads-refresh"',
            'id="doc-status"',
        ):
            self.assertIn(marker, doc_actions)
        self.assertNotIn('id="doc-text"', doc_actions)
        self.assertNotIn('id="doc-confirm"', doc_actions)

        self.assertGreater(documents.find('data-doc-primary="1"'), doc_work)
        self.assertGreater(documents.find('data-doc-advanced="1"'), doc_work)
        self.assertIn("Advanced &amp; help", documents)
        self.assertIn('id="doc-text"', documents.split('id="doc-primary"', 1)[1])
        self.assertIn("Confirm selected", documents)
        self.assertIn("Decline", documents)
        self.assertIn("Uploads", documents)

        # CSS budget: toolbar tokens on both areas.
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        rpt_geo = re.search(
            r"#app-section-reports\[data-reports-documents-density=\"1\"\]\s*>\s*"
            r"\.rpt-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(rpt_geo)
        self.assertIn("max-height: var(--chrome-toolbar)", rpt_geo.group(0))
        doc_geo = re.search(
            r"#app-section-documents\[data-reports-documents-density=\"1\"\]\s*>\s*"
            r"\.doc-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(doc_geo)
        self.assertIn("max-height: var(--chrome-toolbar)", doc_geo.group(0))

        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        self.assertNotIn("sticky", reports.lower())
        self.assertNotIn("sticky", documents.lower())
        self.assertNotIn("position: sticky", css)


if __name__ == "__main__":
    unittest.main()
