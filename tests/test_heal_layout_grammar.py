"""KAN-339 / KAN-340 — Heal FR-UI-11 (scan Sel + detail actions + bulk toolbar)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HealLayoutGrammarTests(unittest.TestCase):
    def test_heal_fr_ui11_grammar_markers_desk162(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk162", html)
        self.assertIn("desk162", desk)

        heal = html.split('id="app-section-heal"', 1)[1].split(
            'id="app-section-desktop"', 1
        )[0]

        self.assertIn('data-heal-layout-grammar="1"', heal)
        self.assertIn('data-heal-scan="1"', heal)
        self.assertIn('data-heal-detail="1"', heal)
        self.assertIn('data-heal-actions="1"', heal)
        self.assertIn('data-heal-bulk="1"', heal)
        self.assertIn('data-heal-checkbox-cell="1"', heal)
        self.assertIn('id="heal-scan-body"', heal)
        self.assertIn('id="heal-detail"', heal)
        self.assertIn('id="heal-approve"', heal)
        self.assertIn('id="heal-reject"', heal)
        self.assertIn('id="heal-bulk-approve"', heal)

        # Columns: Sel · Class · Locator · Run · When
        self.assertIn(">Sel</th>", heal)
        self.assertIn(">Class</th>", heal)
        self.assertIn(">Locator</th>", heal)
        self.assertIn(">Run</th>", heal)
        self.assertIn(">When</th>", heal)

        # Exactly one of each action control in the shell.
        self.assertEqual(html.count('id="heal-approve"'), 1)
        self.assertEqual(html.count('id="heal-reject"'), 1)
        self.assertEqual(html.count('id="heal-bulk-approve"'), 1)

        # Approve/Reject live in detail actions, not in #heal-list shell.
        heal_list = heal.split('id="heal-list"', 1)[1].split(
            'id="heal-detail"', 1
        )[0]
        self.assertNotIn("<button", heal_list.lower())
        self.assertNotIn('id="heal-approve"', heal_list)
        self.assertNotIn('id="heal-reject"', heal_list)

        actions = heal.split('data-heal-actions="1"', 1)[1].split("</div>", 1)[0]
        self.assertIn('id="heal-approve"', actions)
        self.assertIn('id="heal-reject"', actions)

        bulk = heal.split('data-heal-bulk="1"', 1)[1].split("</span>", 1)[0]
        self.assertIn('id="heal-bulk-approve"', bulk)

        # No per-row approve classes / card stack.
        self.assertNotIn("heal-approve", heal_list)
        self.assertNotIn("heal-reject", heal_list)
        self.assertNotIn("heal-card", heal)
        self.assertNotIn("heal-card", js)
        self.assertNotIn(".heal-card", css)

        # JS: scan rows, checkbox stop, detail + bulk confirm path.
        self.assertIn("function renderHealProposals", js)
        self.assertIn("function focusHealDetail", js)
        self.assertIn("function getHealCheckedIds", js)
        self.assertIn("function bulkApproveSelectedHeals", js)
        self.assertIn("function approveFocusedHeal", js)
        self.assertIn("function rejectFocusedHeal", js)
        self.assertIn('data-heal-checkbox-stop', js)
        self.assertIn("stopPropagation", js)
        self.assertIn("healBulkAwaitingConfirm", js)
        self.assertIn("Confirm approve", js)
        # Must not append Approve/Reject into scan rows.
        self.assertNotIn('className = "save-btn heal-approve"', js)
        self.assertNotIn('className = "save-btn secondary heal-reject"', js)
        self.assertNotIn('className = "heal-card"', js)

        # Soft-pass wording must not appear as a pass path.
        self.assertNotIn("Opened Heal review", js)

        # CSS grammar: 28px hit + detail pane + split.
        self.assertIn('data-heal-layout-grammar="1"', css)
        self.assertIn(".heal-scan-table", css)
        self.assertIn(".heal-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".heal-detail-pane", css)
        self.assertIn(".heal-grammar-split", css)


if __name__ == "__main__":
    unittest.main()
