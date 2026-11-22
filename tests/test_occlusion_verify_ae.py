"""KAN-321 — Track3 occlusion verify Primary across layout modes A–E (KAN-320).

Encodes TRACK3_AREA_WIRES §9 + ENTERPRISE_LAYOUT_NOTE §5 checklist as HTML/CSS/JS
structure. Clickability still needs CU or numbered human confirm — never soft-pass.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")
# When an area is open, orb_hub reuses overlay chrome (desktop.js chromeFor).
CHROME_WHEN_OPEN = ("overlay", "stage", "split", "floating")

PRIMARY_SECTIONS = (
    ("app-section-plans", "plan-chrome-toolbar", "data-plans-cases-geometry"),
    ("app-section-manual", "manual-chrome-toolbar", "data-manual-density"),
    ("app-section-reports", "rpt-chrome-toolbar", "data-reports-documents-density"),
    ("app-section-documents", "doc-chrome-toolbar", "data-reports-documents-density"),
    ("app-section-settings", "set-chrome-toolbar", "data-settings-security-density"),
    ("app-section-security", "sec-chrome-toolbar", "data-settings-security-density"),
)


def _slice_section(html: str, section_id: str) -> str:
    start = html.find(f'id="{section_id}"')
    assert start >= 0, section_id
    # Next app-section or end of host — take a generous window.
    rest = html[start:]
    nxt = rest.find('id="app-section-', 1)
    return rest if nxt < 0 else rest[:nxt]


class OcclusionVerifyAETests(unittest.TestCase):
    def test_occlusion_verify_primary_a_to_e_desk118(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )
        note = (ROOT / "docs" / "design" / "ENTERPRISE_LAYOUT_NOTE.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk118", html)
        self.assertIn("desk118", desk)
        self.assertIn('data-occlusion-verify-ae="1"', html)
        self.assertIn("KAN-320", wires)
        self.assertIn("A–E verify contract", wires)
        self.assertIn("Occlusion checklist", note)

        # 1. Surface title + Back; Esc/Back returns home (wiring).
        self.assertIn('id="area-back"', html)
        self.assertIn('id="area-title"', html)
        self.assertIn("areaBack.addEventListener(\"click\", closeArea)", js)
        self.assertIn('back_to_orb: "Escape"', js)
        self.assertIn("if (ev.key === \"Escape\")", js)
        self.assertIn("backToOrbFromKeyboard", js)

        # 2–4. Primary areas: chrome outside .area-work; first work affordances present.
        for section_id, toolbar_id, density_attr in PRIMARY_SECTIONS:
            section = _slice_section(html, section_id)
            self.assertIn(f'{density_attr}="1"', section, section_id)
            toolbar_at = section.find(f'id="{toolbar_id}"')
            work_at = section.find('data-area-work="1"')
            self.assertGreater(work_at, toolbar_at, section_id)
            before = section[:toolbar_at]
            self.assertNotIn("orb-section-label", before, section_id)
            self.assertNotIn("drawer-hint", before, section_id)

        plans = _slice_section(html, "app-section-plans")
        tabs_at = plans.find('id="plan-section-tabs"')
        work_plans = plans.find('data-area-work="1"')
        self.assertGreater(tabs_at, plans.find('id="plan-chrome-toolbar"'))
        self.assertGreater(work_plans, tabs_at)
        self.assertIn('id="plan-tab-cases"', plans)
        self.assertIn('id="plan-search-q"', plans)
        self.assertIn("Add case", plans)

        # 5. Manual Confirm/Cancel dock outside work (every mode uses same DOM).
        manual = _slice_section(html, "app-section-manual")
        work_m = manual.find('data-area-work="1"')
        confirm_at = manual.find('id="manual-confirm-row"')
        self.assertGreater(confirm_at, work_m)
        self.assertIn('data-manual-confirm-dock="1"', manual)
        self.assertIn('id="manual-confirm-yes"', manual)
        self.assertIn('id="manual-confirm-no"', manual)
        self.assertIn("Confirm", manual)
        self.assertIn("Cancel proposal", manual)
        dock_geo = re.search(
            r"#app-section-manual\[data-manual-density=\"1\"\]\s*>\s*"
            r"\.manual-confirm-dock\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(dock_geo)
        self.assertIn("max-height: var(--chrome-confirm)", dock_geo.group(0))
        self.assertIn("flex-shrink: 0", css)

        # 6. Settings/Security chrome stays outside work.
        settings = _slice_section(html, "app-section-settings")
        security = _slice_section(html, "app-section-security")
        self.assertIn('data-settings-section-rail="1"', settings)
        self.assertIn('data-settings-section="layout"', settings)
        self.assertGreater(
            settings.find('id="cred-status-list"'),
            settings.find('data-area-work="1"'),
        )
        sec_actions = security.split('id="sec-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="sec-level"',
            'id="sec-propose"',
            'id="sec-confirm"',
            'id="sec-profile"',
        ):
            self.assertIn(marker, sec_actions)

        # 7. Compact ▦ only — no tall rail / top app tab bar.
        self.assertIn('data-compact-app-menu="1"', html)
        self.assertIn("app-menu-panel", html)
        self.assertNotIn("tall-rail", html.lower())
        self.assertNotIn("top-app-tab", html.lower())

        # Shared non-scroll chrome stack + no sticky regression.
        self.assertIn(".area-surface {", css)
        self.assertIn("flex-direction: column", css)
        self.assertIn("overflow: hidden", css)
        self.assertIn(".area-work", css)
        self.assertIn("overflow: auto", css)
        self.assertIn("position: static", css)
        self.assertNotIn("position: sticky", css)
        self.assertIn("--chrome-max: 120px", css)

        # A–E layout modes selectable; each open-chrome variant has CSS.
        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)
        self.assertIn('AREA_LAYOUTS = ["overlay", "stage", "orb_hub", "split", "floating"]', js)
        self.assertIn('if (mode === "orb_hub") return "overlay"', js)
        for chrome in CHROME_WHEN_OPEN:
            needle = (
                f'html[data-area-open="true"][data-area-chrome="{chrome}"] '
                f".area-surface"
            )
            self.assertIn(needle, css, chrome)

        # Density markers from geometry stories remain on surface.
        for attr in (
            "data-area-chrome-nonoverlap",
            "data-area-chrome-scaffold",
            "data-plans-cases-geometry",
            "data-manual-density",
            "data-reports-documents-density",
            "data-settings-security-density",
            "data-occlusion-verify-ae",
        ):
            self.assertIn(f'{attr}="1"', html)


if __name__ == "__main__":
    unittest.main()
