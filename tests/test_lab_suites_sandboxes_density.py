"""KAN-363 — TRACK3-LAB Suites + Sandboxes density markers (KAN-362)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class LabSuitesSandboxesDensityTests(unittest.TestCase):
    def test_suites_sandboxes_density_desk156(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk156", html)
        self.assertIn("desk156", desk)
        self.assertIn("desktop.css?v=desk156", html)
        self.assertIn("desktop.js?v=desk156", html)

        lab_section = wires.split("## 8. Lab tools", 1)[1].split("## 9.", 1)[0]
        self.assertIn("**Accepted**", lab_section)
        self.assertIn("### 8a. Suites", lab_section)
        self.assertIn("### 8b. Sandboxes", lab_section)

        suites = html.split('id="app-section-suites"', 1)[1].split(
            'id="app-section-sandboxes"', 1
        )[0]
        sandboxes = html.split('id="app-section-sandboxes"', 1)[1].split(
            'id="app-drawer-toggle"', 1
        )[0]

        self.assertIn('data-suites-sandboxes-density="1"', suites)
        self.assertIn('data-suites-sandboxes-density="1"', sandboxes)
        self.assertIn('data-lab-chrome-budget="1"', suites)
        self.assertIn('data-lab-chrome-budget="1"', sandboxes)

        # Suites Done gate: path + actions + ONE status; no separate saved row.
        toolbar = suites.split('id="suite-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="suite-path"',
            'id="suite-discover"',
            'id="suite-list-btn"',
            'id="suite-run"',
            'id="suite-run-all"',
            'id="suite-status"',
        ):
            self.assertIn(marker, toolbar)
        self.assertNotIn('id="suite-saved"', toolbar)
        self.assertNotIn('id="suite-saved"', suites)
        self.assertNotIn("suite-toolbar-saved", suites)
        self.assertEqual(toolbar.count('role="status"'), 1)
        self.assertNotIn('id="suite-import"', toolbar)

        suite_toolbar_at = suites.find('id="suite-chrome-toolbar"')
        suite_work_at = suites.find('data-area-work="1"')
        self.assertGreater(suite_work_at, suite_toolbar_at)
        before_suite = suites[:suite_toolbar_at]
        self.assertNotIn("orb-section-label", before_suite)
        self.assertNotIn("<h3", before_suite)

        advanced = suites.split('id="suite-advanced"', 1)[1]
        self.assertIn('id="suite-import"', advanced)
        self.assertGreater(suites.find('data-suite-advanced="1"'), suite_work_at)

        # JS merges saved path into the single status line.
        self.assertIn("function suiteReadyStatusText", js)
        self.assertIn("function setSuiteReadyStatus", js)
        self.assertIn("Ready · Saved:", js)
        self.assertIn("suiteSavedPath", js)
        self.assertNotIn('getElementById("suite-saved")', js)

        # Sandboxes: compact Enable/Save/Action/Orchestrate + one status;
        # Remove confirm stays in detail.
        ms_toolbar = sandboxes.split('id="ms-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="ms-enabled"',
            'id="ms-save"',
            'id="ms-action"',
            'id="ms-run"',
            'id="ms-status"',
            'data-ms-compact-check="1"',
        ):
            self.assertIn(marker, ms_toolbar)
        self.assertEqual(ms_toolbar.count('role="status"'), 1)
        self.assertNotIn('id="ms-remove"', ms_toolbar)
        self.assertNotIn('id="ms-remove-confirm"', ms_toolbar)
        self.assertNotIn('id="ms-upsert"', ms_toolbar)

        detail = sandboxes.split('data-ms-detail="1"', 1)[1].split(
            'id="ms-advanced"', 1
        )[0]
        self.assertIn('id="ms-remove"', detail)
        self.assertIn('id="ms-remove-confirm"', detail)
        confirm_tag = detail.split('id="ms-remove-confirm"', 1)[1].split(">", 1)[0]
        self.assertIn("disabled", confirm_tag)

        ms_work_at = sandboxes.find('data-area-work="1"')
        self.assertGreater(sandboxes.find('data-ms-advanced="1"'), ms_work_at)
        ms_advanced = sandboxes.split('id="ms-advanced"', 1)[1]
        self.assertIn("<summary>Advanced</summary>", ms_advanced)
        self.assertNotIn('id="ms-enabled"', ms_advanced)
        self.assertNotIn('id="ms-remove"', ms_advanced)

        # TRACK5 craft must not regress on either area.
        for marker in (
            'data-scan-craft="1"',
            'data-lab-detail-disclosure="1"',
            'data-suite-layout-grammar="1"',
            'data-sandboxes-layout-grammar="1"',
            'data-scan-quiet-empty="1"',
            'data-scan-unfocused="1"',
            "Select a row",
        ):
            self.assertIn(marker, html)
        self.assertIn('data-scan-craft="1"', suites)
        self.assertIn('data-scan-craft="1"', sandboxes)

        # CSS density budget on both toolbars (shared selector block).
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        self.assertIn(
            '#app-section-suites[data-suites-sandboxes-density="1"] > .suite-chrome-toolbar',
            css,
        )
        self.assertIn(
            '#app-section-sandboxes[data-suites-sandboxes-density="1"] > .lab-chrome-toolbar',
            css,
        )
        density_block = re.search(
            r"#app-section-suites\[data-suites-sandboxes-density=\"1\"\]\s*>\s*"
            r"\.suite-chrome-toolbar\s*,[\s\S]*?"
            r"#app-section-sandboxes\[data-suites-sandboxes-density=\"1\"\]\s*>\s*"
            r"\.lab-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(density_block)
        self.assertIn("max-height: var(--chrome-toolbar)", density_block.group(0))
        self.assertIn("overflow: hidden", density_block.group(0))

        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        self.assertNotIn("sticky", suites.lower())
        self.assertNotIn("sticky", sandboxes.lower())
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)


if __name__ == "__main__":
    unittest.main()
