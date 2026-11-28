"""KAN-361 — TRACK3-LAB Lab wires Accept + chrome-budget markers (KAN-360)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAB_SECTIONS = (
    ("app-section-heal", "heal-chrome-toolbar", "lab-chrome-toolbar"),
    ("app-section-desktop", "desk-chrome-toolbar", "lab-chrome-toolbar"),
    ("app-section-suites", "suite-chrome-toolbar", "suite-chrome-toolbar"),
    ("app-section-sandboxes", "ms-chrome-toolbar", "lab-chrome-toolbar"),
)

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class LabChromeBudgetTests(unittest.TestCase):
    def test_lab_chrome_budget_markers_desk156(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk156", html)
        self.assertIn("desk156", desk)
        self.assertIn("desktop.css?v=desk156", html)
        self.assertIn("desktop.js?v=desk156", html)

        # Accept gate recorded before geometry Stories 2–4.
        lab_section = wires.split("## 8. Lab tools", 1)[1].split("## 9.", 1)[0]
        self.assertIn("**Accepted**", lab_section)
        self.assertIn("Accept Lab wires", lab_section)
        self.assertIn("- [x] Shared ≤~120px stack", lab_section)

        self.assertEqual(html.count('data-lab-chrome-budget="1"'), 4)

        chunks = {
            "heal": html.split('id="app-section-heal"', 1)[1].split(
                'id="app-section-desktop"', 1
            )[0],
            "desktop": html.split('id="app-section-desktop"', 1)[1].split(
                'id="app-section-plans"', 1
            )[0],
            "suites": html.split('id="app-section-suites"', 1)[1].split(
                'id="app-section-sandboxes"', 1
            )[0],
            "sandboxes": html.split('id="app-section-sandboxes"', 1)[1].split(
                'id="app-drawer-toggle"', 1
            )[0],
        }

        for name, chunk in chunks.items():
            self.assertIn('data-lab-chrome-budget="1"', chunk, msg=name)
            # Exactly one shared chrome toolbar; no sticky-named markers.
            self.assertEqual(
                len(re.findall(r'class="area-chrome-toolbar ', chunk)),
                1,
                msg=name,
            )
            self.assertNotIn("sticky", chunk.lower(), msg=name)

        for section_id, toolbar_id, _cls in LAB_SECTIONS:
            chunk = html.split(f'id="{section_id}"', 1)[1]
            # Stop at next app-section or drawer.
            end = chunk.find('id="app-section-')
            if end < 0:
                end = chunk.find('id="app-drawer-toggle"')
            chunk = chunk[:end] if end > 0 else chunk

            toolbar_at = chunk.find(f'id="{toolbar_id}"')
            work_at = chunk.find('data-area-work="1"')
            self.assertGreater(work_at, toolbar_at, msg=section_id)

            before_chrome = chunk[:toolbar_at]
            self.assertNotIn("orb-section-label", before_chrome, msg=section_id)
            self.assertNotIn("<h3", before_chrome, msg=section_id)
            self.assertNotIn("drawer-hint", before_chrome, msg=section_id)

            # Advanced / Policy under work (not above toolbar).
            adv_markers = (
                'data-heal-advanced="1"',
                'data-desk-advanced="1"',
                'data-suite-advanced="1"',
                'data-ms-advanced="1"',
            )
            found_adv = [m for m in adv_markers if m in chunk]
            self.assertTrue(found_adv, msg=section_id)
            for m in found_adv:
                self.assertGreater(chunk.find(m), work_at, msg=f"{section_id}:{m}")

        # CSS budget: shared --chrome-toolbar on each Lab toolbar.
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        for section_id, _toolbar_id, toolbar_cls in LAB_SECTIONS:
            geo = re.search(
                rf"#{section_id}\[data-lab-chrome-budget=\"1\"\]\s*>\s*"
                rf"\.{re.escape(toolbar_cls)}\s*,?",
                css,
            )
            self.assertIsNotNone(geo, msg=section_id)
        budget_block = re.search(
            r"#app-section-heal\[data-lab-chrome-budget=\"1\"\]\s*>\s*"
            r"\.lab-chrome-toolbar[\s\S]*?"
            r"#app-section-sandboxes\[data-lab-chrome-budget=\"1\"\]\s*>\s*"
            r"\.lab-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(budget_block)
        self.assertIn("max-height: var(--chrome-toolbar)", budget_block.group(0))
        self.assertIn("overflow: hidden", budget_block.group(0))

        # TRACK4/5 craft must not regress.
        for marker in (
            'data-scan-craft="1"',
            'data-lab-detail-disclosure="1"',
            'data-heal-confirm-copy="1"',
            'data-evidence-first-detail="1"',
            "Trace: no Playwright trace for this run.",
        ):
            self.assertIn(marker, html)

        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        # No KAN-310 sticky rename redo in Lab chunks.
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)


if __name__ == "__main__":
    unittest.main()
