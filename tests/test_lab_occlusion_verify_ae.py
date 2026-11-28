"""KAN-367 — TRACK3-LAB Lab occlusion verify across layout modes A–E (KAN-366).

Mirrors Primary KAN-320 contract for Lab areas only (Heal / Desktop / Suites /
Sandboxes). Clickability still needs CU or numbered human confirm — never soft-pass
“opened Lab.” Does not reopen Primary occlusion scope.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")
# When an area is open, orb_hub reuses overlay chrome (desktop.js chromeFor).
CHROME_WHEN_OPEN = ("overlay", "stage", "split", "floating")

LAB_SECTIONS = (
    (
        "app-section-heal",
        "heal-chrome-toolbar",
        ("data-lab-chrome-budget", "data-heal-desktop-density"),
        ("heal-run-filter", "heal-refresh", "heal-status"),
        ("heal-scan", "heal-list"),
    ),
    (
        "app-section-desktop",
        "desk-chrome-toolbar",
        ("data-lab-chrome-budget", "data-heal-desktop-density"),
        ("desk-smoke", "desk-steps", "desk-status"),
        ("desk-scan",),
    ),
    (
        "app-section-suites",
        "suite-chrome-toolbar",
        ("data-lab-chrome-budget", "data-suites-sandboxes-density"),
        ("suite-path", "suite-discover", "suite-list-btn", "suite-run", "suite-run-all", "suite-status"),
        ("suite-list",),
    ),
    (
        "app-section-sandboxes",
        "ms-chrome-toolbar",
        ("data-lab-chrome-budget", "data-suites-sandboxes-density"),
        ("ms-enabled", "ms-save", "ms-action", "ms-run", "ms-status"),
        ("ms-scan",),
    ),
)


def _slice_section(html: str, section_id: str) -> str:
    start = html.find(f'id="{section_id}"')
    assert start >= 0, section_id
    rest = html[start:]
    nxt = rest.find('id="app-section-', 1)
    return rest if nxt < 0 else rest[:nxt]


class LabOcclusionVerifyAETests(unittest.TestCase):
    def test_lab_occlusion_verify_a_to_e_desk158(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk158", html)
        self.assertIn("desk158", desk)
        self.assertIn("desktop.css?v=desk158", html)
        self.assertIn("desktop.js?v=desk158", html)
        self.assertIn('data-lab-occlusion-verify-ae="1"', html)
        # Primary marker remains; Lab story must not reopen Primary scope.
        self.assertIn('data-occlusion-verify-ae="1"', html)
        self.assertIn("KAN-366", wires)
        self.assertIn("Lab A–E verify", wires)

        # Shared surface chrome: title + Back; Esc/Back home wiring.
        self.assertIn('id="area-back"', html)
        self.assertIn('id="area-title"', html)
        self.assertIn("areaBack.addEventListener(\"click\", closeArea)", js)
        self.assertIn('back_to_orb: "Escape"', js)
        self.assertIn("if (ev.key === \"Escape\")", js)
        self.assertIn("backToOrbFromKeyboard", js)

        # Lab areas: density markers + chrome outside .area-work + first work affordances.
        for (
            section_id,
            toolbar_id,
            density_attrs,
            toolbar_controls,
            work_ids,
        ) in LAB_SECTIONS:
            section = _slice_section(html, section_id)
            for attr in density_attrs:
                self.assertIn(f'{attr}="1"', section, section_id)
            toolbar_at = section.find(f'id="{toolbar_id}"')
            work_at = section.find('data-area-work="1"')
            self.assertGreaterEqual(toolbar_at, 0, section_id)
            self.assertGreater(work_at, toolbar_at, section_id)
            before = section[:toolbar_at]
            self.assertNotIn("orb-section-label", before, section_id)
            self.assertNotIn("<h3", before, section_id)
            self.assertNotIn("drawer-hint", before, section_id)
            toolbar = section[toolbar_at:work_at]
            for control_id in toolbar_controls:
                self.assertIn(f'id="{control_id}"', toolbar, f"{section_id}:{control_id}")
            work = section[work_at:]
            for work_id in work_ids:
                self.assertIn(f'id="{work_id}"', work, f"{section_id}:{work_id}")

        # Heal Approve/Reject pinned in detail (clickable when focused).
        heal = _slice_section(html, "app-section-heal")
        heal_work = heal.find('data-area-work="1"')
        pin_at = heal.find('data-heal-pin="1"')
        self.assertGreater(pin_at, heal_work)
        heal_detail = heal[heal.find('data-heal-detail="1"') :]
        self.assertIn('id="heal-approve"', heal_detail)
        self.assertIn('id="heal-reject"', heal_detail)
        heal_toolbar = heal.split('id="heal-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        self.assertNotIn('id="heal-approve"', heal_toolbar)
        self.assertNotIn('id="heal-reject"', heal_toolbar)

        # Desktop Save pinned in detail.
        desktop = _slice_section(html, "app-section-desktop")
        desk_work = desktop.find('data-area-work="1"')
        self.assertGreater(desktop.find('data-desk-pin="1"'), desk_work)
        self.assertIn('id="desk-save"', desktop[desk_work:])

        # Sandboxes Remove confirm stays in detail (never silent / never toolbar-only).
        sandboxes = _slice_section(html, "app-section-sandboxes")
        ms_work = sandboxes.find('data-area-work="1"')
        ms_detail = sandboxes[sandboxes.find('data-ms-detail="1"') :]
        self.assertGreater(sandboxes.find('data-ms-detail="1"'), ms_work)
        self.assertIn('id="ms-remove"', ms_detail)
        self.assertIn('id="ms-remove-confirm"', ms_detail)
        self.assertIn("Confirm remove", ms_detail)
        ms_toolbar = sandboxes.split('id="ms-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        self.assertNotIn('id="ms-remove"', ms_toolbar)
        self.assertNotIn('id="ms-remove-confirm"', ms_toolbar)

        # Compact ▦ only — no tall rail / top app tab bar.
        self.assertIn('data-compact-app-menu="1"', html)
        self.assertIn("app-menu-panel", html)
        self.assertNotIn("tall-rail", html.lower())
        self.assertNotIn("top-app-tab", html.lower())

        # Shared non-scroll chrome stack + work scrolls.
        self.assertIn(".area-surface {", css)
        self.assertIn("flex-direction: column", css)
        self.assertIn("overflow: hidden", css)
        self.assertIn(".area-work", css)
        self.assertIn("overflow: auto", css)
        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)

        # A–E layout modes selectable; each open-chrome variant has CSS.
        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)
        self.assertIn(
            'AREA_LAYOUTS = ["overlay", "stage", "orb_hub", "split", "floating"]', js
        )
        self.assertIn('if (mode === "orb_hub") return "overlay"', js)
        for chrome in CHROME_WHEN_OPEN:
            needle = (
                f'html[data-area-open="true"][data-area-chrome="{chrome}"] '
                f".area-surface"
            )
            self.assertIn(needle, css, chrome)

        # Density + Lab occlusion markers present together.
        for attr in (
            "data-lab-chrome-budget",
            "data-heal-desktop-density",
            "data-suites-sandboxes-density",
            "data-lab-occlusion-verify-ae",
            "data-occlusion-verify-ae",
        ):
            self.assertIn(f'{attr}="1"', html)


if __name__ == "__main__":
    unittest.main()
