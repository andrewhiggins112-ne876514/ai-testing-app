"""KAN-298 — enterprise layout tokens applied from accepted KAN-295 note (KAN-297)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EnterpriseLayoutTokensTests(unittest.TestCase):
    def test_tokens_and_wiring_desk142(self) -> None:
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        note = (ROOT / "docs" / "design" / "ENTERPRISE_LAYOUT_NOTE.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk142", html)
        self.assertIn("desk142", desk)
        self.assertIn('data-enterprise-layout-tokens="1"', html)
        self.assertIn('data-area-chrome-nonoverlap="1"', html)

        # Token definitions (type + space + chrome budget)
        for token in (
            "--type-area-title",
            "--type-body",
            "--type-ui",
            "--type-meta",
            "--type-help",
            "--space-1",
            "--space-2",
            "--space-3",
            "--space-4",
            "--space-5",
            "--chrome-max",
            "--chrome-surface-bar",
            "--chrome-toolbar",
            "--chrome-tabs",
            "--chrome-confirm",
        ):
            self.assertIn(token, css)

        root = re.search(r":root\s*\{([^}]+)\}", css, flags=re.DOTALL)
        self.assertIsNotNone(root)
        root_block = root.group(1)
        self.assertIn("--space-1: 4px", root_block)
        self.assertIn("--space-2: 8px", root_block)
        self.assertIn("--chrome-max: 120px", root_block)
        # FR-UI-3 accents remain the colour system
        self.assertIn("--cyan:", root_block)
        self.assertIn("--font:", root_block)
        self.assertIn("Segoe UI", root_block)

        # Area chrome consumes tokens (not one-off px for title/tabs/dock)
        self.assertIn("font: var(--type-area-title)", css)
        self.assertIn("letter-spacing: 0.12em", css)
        self.assertIn("font: var(--type-meta)", css)
        self.assertIn("font: var(--type-ui)", css)
        self.assertIn("font: var(--type-body)", css)
        self.assertIn("gap: var(--space-2)", css)
        self.assertIn("gap: var(--space-1)", css)
        self.assertIn("padding: var(--space-1) 0", css)
        self.assertIn("padding: var(--space-2) 0 var(--space-1)", css)
        self.assertIn("max-height: var(--chrome-surface-bar)", css)

        # No sticky-inside-scrollport regression
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)  # chrome; scan thead sticky is KAN-348

        # No cloud font CDN / Inter rebrand
        lower = css.lower()
        self.assertNotIn("fonts.googleapis", lower)
        self.assertNotIn("fonts.adobe", lower)
        self.assertNotIn("inter,", lower)

        # Note remains the accepted source; tokens story may proceed
        self.assertIn("KAN-297", note)
        self.assertIn("Accepted", note)

        # Confirm dock still outside work scrollport
        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        work_at = manual.find('data-area-work="1"')
        confirm_at = manual.find('id="manual-confirm-row"')
        self.assertGreater(confirm_at, work_at)


if __name__ == "__main__":
    unittest.main()
