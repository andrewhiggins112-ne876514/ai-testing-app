"""F5 keyboard shortcuts on orb home and inside areas (KAN-211 / FR-UI-1)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KeyboardShortcutsTests(unittest.TestCase):
    def test_desktop_ui_documents_shortcuts_desk96(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk96", html)
        self.assertIn("desk96", app)
        self.assertIn("desktop.js?v=desk96", html)
        self.assertIn('id="keyboard-shortcuts-doc"', html)
        self.assertIn('id="plan-keyboard-hint"', html)
        self.assertIn("data-keyboard-shortcuts", html)
        self.assertIn("Run selected case", html)
        self.assertIn("Next failure", html)
        self.assertIn("Back to orb", html)
        self.assertIn("No shortcuts confirm Jira write or approve heal", html)
        self.assertIn("No shortcut confirms Jira write or approves heal", html)

        self.assertIn("KEYBOARD_SHORTCUTS", js)
        self.assertIn("runSelectedCaseFromKeyboard", js)
        self.assertIn("selectNextFailureFromKeyboard", js)
        self.assertIn("backToOrbFromKeyboard", js)
        self.assertIn('key === "r"', js)
        self.assertIn('key === "n"', js)
        self.assertIn('ev.key === "Escape"', js)
        self.assertIn("jira_write_confirm", js)
        self.assertIn("heal_approve", js)
        # Must not bind heal approve / jira write to keyboard shortcuts.
        self.assertNotRegex(
            js,
            r"keydown[\s\S]{0,800}heal-approve|heal.approve[\s\S]{0,200}keydown",
        )
        never = (
            js.split("KEYBOARD_SHORTCUTS", 1)[1]
            .split("};", 1)[0]
        )
        self.assertIn("jira_write_confirm", never)
        self.assertIn("heal_approve", never)


if __name__ == "__main__":
    unittest.main()
