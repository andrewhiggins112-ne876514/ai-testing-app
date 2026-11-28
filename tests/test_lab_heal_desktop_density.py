"""KAN-365 — TRACK3-LAB Heal + Desktop density markers (KAN-364)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class LabHealDesktopDensityTests(unittest.TestCase):
    def test_heal_desktop_density_desk151(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk151", html)
        self.assertIn("desk151", desk)
        self.assertIn("desktop.css?v=desk151", html)
        self.assertIn("desktop.js?v=desk151", html)

        lab_section = wires.split("## 8. Lab tools", 1)[1].split("## 9.", 1)[0]
        self.assertIn("**Accepted**", lab_section)
        self.assertIn("### 8c. Heal review", lab_section)
        self.assertIn("### 8d. Desktop Lab", lab_section)

        heal = html.split('id="app-section-heal"', 1)[1].split(
            'id="app-section-desktop"', 1
        )[0]
        desktop = html.split('id="app-section-desktop"', 1)[1].split(
            'id="app-section-plans"', 1
        )[0]

        self.assertIn('data-heal-desktop-density="1"', heal)
        self.assertIn('data-heal-desktop-density="1"', desktop)
        self.assertIn('data-lab-chrome-budget="1"', heal)
        self.assertIn('data-lab-chrome-budget="1"', desktop)

        # Heal: Filter + Refresh (+ bulk) + one status in one toolbar.
        toolbar = heal.split('id="heal-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="heal-run-filter"',
            'data-heal-compact-filter="1"',
            'id="heal-refresh"',
            'data-heal-bulk="1"',
            'id="heal-bulk-approve"',
            'id="heal-status"',
        ):
            self.assertIn(marker, toolbar)
        self.assertEqual(toolbar.count('role="status"'), 1)
        self.assertNotIn('id="heal-approve"', toolbar)
        self.assertNotIn('id="heal-reject"', toolbar)
        self.assertNotIn("Reject selected", toolbar)
        self.assertNotIn("heal-bulk-reject", toolbar)

        heal_toolbar_at = heal.find('id="heal-chrome-toolbar"')
        heal_work_at = heal.find('data-area-work="1"')
        self.assertGreater(heal_work_at, heal_toolbar_at)
        before_heal = heal[:heal_toolbar_at]
        self.assertNotIn("orb-section-label", before_heal)
        self.assertNotIn("<h3", before_heal)

        # Approve/Reject pinned on focused detail (not toolbar).
        detail = heal.split('data-heal-detail="1"', 1)[1].split(
            'id="heal-advanced"', 1
        )[0]
        self.assertIn('data-heal-pin="1"', detail)
        self.assertIn('data-heal-actions="1"', detail)
        self.assertIn('id="heal-approve"', detail)
        self.assertIn('id="heal-reject"', detail)
        self.assertIn('data-scan-scroll="detail"', detail)
        self.assertIn("heal-detail-body", detail)
        self.assertIn('data-heal-focused="0"', heal)
        self.assertIn("function setHealDetailFocused", js)
        self.assertIn('data-heal-focused', js)

        # Bulk Approve confirm copy + no auto-apply / no bulk Reject.
        self.assertIn('data-heal-confirm-copy="1"', heal)
        self.assertIn("Files are not written", js)
        self.assertIn("healBulkAwaitingConfirm", js)
        self.assertNotIn("heal-bulk-reject", js)
        self.assertNotIn("auto-apply", heal.lower())

        advanced = heal.split('id="heal-advanced"', 1)[1]
        self.assertIn("<summary>Policy", advanced)
        self.assertGreater(heal.find('data-heal-advanced="1"'), heal_work_at)

        # Desktop: smoke/demo + one status; Save in detail pin.
        desk_toolbar = desktop.split('id="desk-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="desk-smoke"',
            'id="desk-steps"',
            'id="desk-status"',
        ):
            self.assertIn(marker, desk_toolbar)
        self.assertEqual(desk_toolbar.count('role="status"'), 1)
        self.assertNotIn('id="desk-save"', desk_toolbar)
        self.assertNotIn('id="desk-exe"', desk_toolbar)

        desk_toolbar_at = desktop.find('id="desk-chrome-toolbar"')
        desk_work_at = desktop.find('data-area-work="1"')
        self.assertGreater(desk_work_at, desk_toolbar_at)
        before_desk = desktop[:desk_toolbar_at]
        self.assertNotIn("orb-section-label", before_desk)
        self.assertNotIn("<h3", before_desk)

        desk_detail = desktop.split('data-desk-detail="1"', 1)[1].split(
            'id="desk-advanced"', 1
        )[0]
        self.assertIn('data-desk-pin="1"', desk_detail)
        self.assertIn('id="desk-save"', desk_detail)
        self.assertIn('id="desk-exe"', desk_detail)
        self.assertIn("desk-detail-body", desk_detail)
        self.assertIn('data-scan-scroll="detail"', desk_detail)

        self.assertGreater(desktop.find('data-desk-advanced="1"'), desk_work_at)
        desk_advanced = desktop.split('id="desk-advanced"', 1)[1]
        self.assertIn("<summary>Advanced</summary>", desk_advanced)
        self.assertNotIn('id="desk-save"', desk_advanced)
        self.assertNotIn('id="desk-smoke"', desk_advanced)

        # TRACK5 craft must not regress.
        for marker in (
            'data-scan-craft="1"',
            'data-heal-confirm-copy="1"',
            'data-lab-detail-disclosure="1"',
            'data-evidence-first-detail="1"',
            'data-heal-layout-grammar="1"',
            'data-desktop-layout-grammar="1"',
            "Select a row",
            "Trace: no Playwright trace for this run.",
        ):
            self.assertIn(marker, html)
        self.assertIn('data-scan-craft="1"', heal)
        self.assertIn('data-scan-craft="1"', desktop)

        # CSS density budget + pinned actions.
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        self.assertIn(
            '#app-section-heal[data-heal-desktop-density="1"] > .lab-chrome-toolbar',
            css,
        )
        self.assertIn(
            '#app-section-desktop[data-heal-desktop-density="1"] > .lab-chrome-toolbar',
            css,
        )
        density_block = re.search(
            r"#app-section-heal\[data-heal-desktop-density=\"1\"\]\s*>\s*"
            r"\.lab-chrome-toolbar\s*,[\s\S]*?"
            r"#app-section-desktop\[data-heal-desktop-density=\"1\"\]\s*>\s*"
            r"\.lab-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(density_block)
        self.assertIn("max-height: var(--chrome-toolbar)", density_block.group(0))
        self.assertIn("overflow: hidden", density_block.group(0))
        self.assertIn(".heal-detail-pin", css)
        self.assertIn(".desk-detail-pin", css)

        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        self.assertNotIn("sticky", heal.lower())
        self.assertNotIn("sticky", desktop.lower())
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)


if __name__ == "__main__":
    unittest.main()
