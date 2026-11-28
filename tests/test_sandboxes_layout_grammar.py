"""KAN-345 / KAN-346 — Sandboxes Lab FR-UI-11 (scan + detail remove confirm)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SandboxesLayoutGrammarTests(unittest.TestCase):
    def test_sandboxes_fr_ui11_grammar_markers_desk150(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk150", html)
        self.assertIn("desk150", desk)
        self.assertIn("desktop.css?v=desk150", html)
        self.assertIn("desktop.js?v=desk150", html)

        sandboxes = html.split('id="app-section-sandboxes"', 1)[1].split(
            'id="app-drawer-toggle"', 1
        )[0]

        self.assertIn('data-sandboxes-layout-grammar="1"', sandboxes)
        self.assertIn('data-ms-scan="1"', sandboxes)
        self.assertIn('data-ms-detail="1"', sandboxes)
        self.assertIn('id="ms-scan"', sandboxes)
        self.assertIn('id="ms-scan-body"', sandboxes)
        self.assertIn('id="ms-detail"', sandboxes)
        self.assertIn('id="ms-run"', sandboxes)
        self.assertIn('id="ms-enabled"', sandboxes)
        self.assertIn('id="ms-remove"', sandboxes)
        self.assertIn('id="ms-remove-confirm"', sandboxes)
        self.assertIn('id="ms-upsert"', sandboxes)
        self.assertIn('id="ms-save"', sandboxes)
        self.assertIn('id="ms-action"', sandboxes)

        # Columns: Id · Label · URL · Ready — no checkbox column
        self.assertIn(">Id</th>", sandboxes)
        self.assertIn(">Label</th>", sandboxes)
        self.assertIn(">URL</th>", sandboxes)
        self.assertIn(">Ready</th>", sandboxes)
        scan = sandboxes.split('data-ms-scan="1"', 1)[1].split("</table>", 1)[0]
        self.assertNotIn('type="checkbox"', scan)
        self.assertNotIn("<input", scan)

        # Enable is compact toolbar check — not page-width check-row
        self.assertNotIn('class="check-row"', sandboxes)
        self.assertNotIn("check-row", sandboxes)
        toolbar = sandboxes.split('id="ms-chrome-toolbar"', 1)[1].split(
            'id="ms-primary"', 1
        )[0]
        self.assertIn('id="ms-enabled"', toolbar)
        self.assertIn('data-ms-compact-check="1"', toolbar)
        self.assertIn('id="ms-run"', toolbar)
        self.assertIn('id="ms-action"', toolbar)
        self.assertNotIn('id="ms-remove"', toolbar)
        self.assertNotIn('id="ms-upsert"', toolbar)

        # Detail holds fields + Save + Remove… / Confirm remove (disabled)
        detail = sandboxes.split('data-ms-detail="1"', 1)[1].split(
            'id="ms-advanced"', 1
        )[0]
        self.assertIn('id="ms-id"', detail)
        self.assertIn('id="ms-label"', detail)
        self.assertIn('id="ms-url"', detail)
        self.assertIn('id="ms-upsert"', detail)
        self.assertIn('id="ms-remove"', detail)
        self.assertIn('id="ms-remove-confirm"', detail)
        confirm_tag = detail.split('id="ms-remove-confirm"', 1)[1].split(">", 1)[0]
        self.assertIn("disabled", confirm_tag)
        self.assertNotIn('id="ms-enabled"', detail)

        # Advanced is Help only — no configure form / check-row
        advanced = sandboxes.split('id="ms-advanced"', 1)[1]
        self.assertIn("<summary>Advanced</summary>", advanced)
        self.assertNotIn('id="ms-enabled"', advanced)
        self.assertNotIn('id="ms-id"', advanced)
        self.assertNotIn('id="ms-remove"', advanced)

        # JS: row focus independent of remove; remove is propose-then-confirm
        self.assertIn("function focusSandboxDetail", js)
        self.assertIn("function renderSandboxList", js)
        self.assertIn("function resetMsRemoveConfirm", js)
        self.assertIn("ms-scan-row", js)
        self.assertIn("msRemoveConfirm", js)
        self.assertIn("focusSandboxDetail", js)
        self.assertIn("createElement(\"tr\")", js)
        # Row click must not call remove
        self.assertNotIn("focusSandboxDetail(s);\n        runMultiSandboxAction(\"remove\")", js)
        self.assertNotIn("Opened Sandboxes", js)

        # CSS grammar
        self.assertIn('data-sandboxes-layout-grammar="1"', css)
        self.assertIn(".ms-scan-table", css)
        self.assertIn(".ms-detail-pane", css)
        self.assertIn(".ms-grammar-split", css)
        self.assertIn(".ms-compact-check", css)
        self.assertIn(".ms-danger-zone", css)


if __name__ == "__main__":
    unittest.main()
