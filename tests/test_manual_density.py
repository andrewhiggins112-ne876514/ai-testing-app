"""KAN-315 — Track3 Manual density + Confirm dock from accepted wire (KAN-314)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class ManualDensityGeometryTests(unittest.TestCase):
    def test_manual_density_confirm_dock_desk135(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk135", html)
        self.assertIn("desk135", desk)
        self.assertIn('data-manual-density="1"', html)
        self.assertIn("Accepted", wires)
        self.assertIn("KAN-314", wires)

        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        self.assertIn('data-manual-density="1"', manual)

        # Chrome stack: toolbar → work → Confirm dock (no intro h3/hint above chrome).
        toolbar_at = manual.find('id="manual-chrome-toolbar"')
        work_at = manual.find('data-area-work="1"')
        confirm_at = manual.find('id="manual-confirm-row"')
        self.assertGreater(work_at, toolbar_at)
        self.assertGreater(confirm_at, work_at)
        before_chrome = manual[:toolbar_at]
        self.assertNotIn("orb-section-label", before_chrome)
        self.assertNotIn("drawer-hint", before_chrome)

        # Loop + status live in the single toolbar band (no second status strip).
        actions = manual.split('id="manual-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        self.assertIn('id="manual-loop-stage-label"', actions)
        self.assertIn('id="manual-status"', actions)
        self.assertNotIn("area-chrome-toolbar-status-row", actions)

        # About / long copy scrolls in work, not chrome.
        about_at = manual.find('data-manual-advanced="1"')
        self.assertGreater(about_at, work_at)
        self.assertGreater(confirm_at, about_at)
        self.assertIn("About Manual capture", manual)

        # Propose actions stay inside work; Confirm dock is sibling footer.
        propose_at = manual.find('data-manual-propose-row="1"')
        self.assertGreater(propose_at, work_at)
        self.assertGreater(confirm_at, propose_at)
        work_end = manual.find("</div>", manual.rfind("manual-advanced"))
        self.assertGreater(confirm_at, work_end)
        self.assertIn('data-manual-confirm-dock="1"', manual)
        self.assertIn("Confirm", manual)
        self.assertIn("Cancel proposal", manual)
        self.assertIn("Proposal ready — Confirm writes; Cancel writes nothing", manual)

        # Review has no second chrome header over the proposal surface.
        review = manual.split('id="manual-review"', 1)[1].split(
            'id="manual-advanced"', 1
        )[0]
        self.assertNotIn("orb-section-label", review)

        # CSS budget: toolbar + confirm tokens.
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        self.assertIn("--chrome-confirm", css)
        toolbar_geo = re.search(
            r"#app-section-manual\[data-manual-density=\"1\"\]\s*>\s*"
            r"\.manual-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(toolbar_geo)
        self.assertIn("max-height: var(--chrome-toolbar)", toolbar_geo.group(0))
        dock_geo = re.search(
            r"#app-section-manual\[data-manual-density=\"1\"\]\s*>\s*"
            r"\.manual-confirm-dock\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(dock_geo)
        self.assertIn("max-height: var(--chrome-confirm)", dock_geo.group(0))
        self.assertIn("flex-shrink: 0", css)

        # A–E layout modes remain selectable (density must hold for each).
        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        # No sticky chrome regression.
        self.assertNotIn("sticky", manual.lower())
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)  # chrome; scan thead sticky is KAN-348


if __name__ == "__main__":
    unittest.main()
