"""KAN-335 / KAN-336 — Documents FR-UI-11 (Keep cell + uploads scan)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentsLayoutGrammarTests(unittest.TestCase):
    def test_documents_fr_ui11_scan_detail_markers_desk141(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk141", html)
        self.assertIn("desk141", desk)

        documents = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]

        self.assertIn('data-documents-layout-grammar="1"', documents)
        self.assertIn('data-doc-diff-scan="1"', documents)
        self.assertIn('data-doc-uploads-scan="1"', documents)
        self.assertIn('data-doc-diff-detail="1"', documents)
        self.assertIn('data-doc-upload-detail="1"', documents)
        self.assertIn('data-doc-section-tabs="1"', documents)
        self.assertIn('id="doc-tab-propose"', documents)
        self.assertIn('id="doc-tab-uploads"', documents)
        self.assertIn('id="doc-diff"', documents)
        self.assertIn('id="doc-uploads-body"', documents)
        self.assertIn('id="doc-confirm"', documents)
        self.assertIn('id="doc-decline"', documents)
        self.assertIn('id="doc-text"', documents)

        self.assertIn(">Keep</th>", documents)
        self.assertIn(">Key</th>", documents)
        self.assertIn(">From</th>", documents)
        self.assertIn(">To</th>", documents)
        self.assertIn(">Name</th>", documents)
        self.assertIn(">Time</th>", documents)
        self.assertIn(">Level</th>", documents)
        self.assertIn(">Consent</th>", documents)

        # Confirm / Decline live outside the diff table element.
        diff_table = documents.split('id="doc-diff-scan"', 1)[1].split("</table>", 1)[0]
        self.assertNotIn('id="doc-confirm"', diff_table)
        self.assertNotIn('id="doc-decline"', diff_table)
        detail = documents.split('id="doc-diff-detail"', 1)[1].split(
            'id="doc-panel-uploads"', 1
        )[0]
        self.assertIn('id="doc-confirm"', detail)
        self.assertIn('id="doc-decline"', detail)

        # Ban whole-row check-row grammar in Documents.
        self.assertNotIn('class="check-row"', documents)
        self.assertNotIn("doc-diff-row", documents)
        self.assertNotIn('id="doc-uploads-list"', documents)

        # JS: Keep cell stopPropagation; no check-row render path.
        self.assertIn("function renderDocProposal", js)
        self.assertIn("function loadDocUploads", js)
        self.assertIn("function focusDocDiffKey", js)
        self.assertIn('data-doc-keep-stop', js)
        self.assertIn("stopPropagation", js)
        self.assertIn('createElement("tr")', js)
        self.assertIn("doc-scan-row", js)
        self.assertNotIn('check-row doc-diff-row', js)
        self.assertNotIn("doc-uploads-list", js)

        # CSS grammar: 28px hit + split + tabs.
        self.assertIn('data-documents-layout-grammar="1"', css)
        self.assertIn(".doc-scan-table", css)
        self.assertIn(".doc-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".doc-detail-pane", css)
        self.assertIn(".doc-grammar-split", css)
        self.assertIn(".doc-section-tabs", css)


if __name__ == "__main__":
    unittest.main()
