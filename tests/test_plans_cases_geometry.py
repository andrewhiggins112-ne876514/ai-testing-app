"""KAN-313 — Track3 Plans · Cases geometry from accepted wire (KAN-312)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class PlansCasesGeometryTests(unittest.TestCase):
    def test_plans_cases_geometry_desk126(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk126", html)
        self.assertIn("desk126", desk)
        self.assertIn('data-plans-cases-geometry="1"', html)
        self.assertIn("Accepted", wires)
        self.assertIn("KAN-312", wires)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertIn('data-plans-cases-geometry="1"', plans)

        # Chrome stack: toolbar → tabs → work (no intro h3/hint above chrome).
        toolbar_at = plans.find('id="plan-chrome-toolbar"')
        tabs_at = plans.find('id="plan-section-tabs"')
        work_at = plans.find('data-area-work="1"')
        self.assertGreater(tabs_at, toolbar_at)
        self.assertGreater(work_at, tabs_at)
        before_chrome = plans[:toolbar_at]
        self.assertNotIn("orb-section-label", before_chrome)
        self.assertNotIn("drawer-hint", before_chrome)

        # About / long copy scrolls in work, not chrome.
        about_at = plans.find('data-plan-about="1"')
        self.assertGreater(about_at, work_at)

        # Cases default; wire-short tab labels.
        cases_tab = plans.split('id="plan-tab-cases"', 1)[1].split("</button>", 1)[0]
        self.assertIn('aria-selected="true"', cases_tab)
        self.assertIn(">Cases<", plans)
        self.assertIn(">Draft<", plans)
        self.assertIn(">Coverage<", plans)
        self.assertIn(">Trace<", plans)
        self.assertIn(">Run<", plans)

        # Cases panel: Add case work-header before case list (primary surface).
        cases = plans.split('id="plan-panel-cases"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0]
        header_at = cases.find('data-plan-work-header="1"')
        add_at = cases.find('data-plan-add-menu="1"')
        list_at = cases.find('data-plan-cases-list="1"')
        edit_at = cases.find('data-plan-case-section="edit"')
        self.assertGreater(add_at, header_at)
        self.assertGreater(list_at, add_at)
        self.assertGreater(edit_at, list_at)
        self.assertIn("Add case", cases)
        # Single Add case menu — not a farm of top-level add buttons outside the menu.
        menu = cases.split('id="plan-add-case-menu"', 1)[1]
        for btn in (
            "plan-add-desktop-btn",
            "plan-add-api-btn",
            "plan-add-contract-btn",
            "plan-add-seed-btn",
            "plan-add-visual-btn",
            "plan-add-a11y-btn",
            "plan-add-perf-btn",
            "plan-add-framework-btn",
        ):
            self.assertIn(f'id="{btn}"', menu)

        # CSS budget: surface/toolbar/tabs tokens + Plans max-heights.
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        self.assertIn("--chrome-tabs", css)
        geo = re.search(
            r"#app-section-plans\[data-plans-cases-geometry=\"1\"\]\s*>\s*"
            r"\.plan-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(geo)
        self.assertIn("max-height: var(--chrome-toolbar)", geo.group(0))
        tabs_geo = re.search(
            r"#app-section-plans\[data-plans-cases-geometry=\"1\"\]\s*>\s*"
            r"\.plan-section-tabs\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(tabs_geo)
        self.assertIn("max-height: var(--chrome-tabs)", tabs_geo.group(0))
        self.assertIn("flex-wrap: nowrap", tabs_geo.group(0))

        # A–E layout modes remain selectable (density must hold for each).
        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        # No sticky chrome regression.
        self.assertNotIn("sticky", plans.lower())
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)  # chrome; scan thead sticky is KAN-348


if __name__ == "__main__":
    unittest.main()
