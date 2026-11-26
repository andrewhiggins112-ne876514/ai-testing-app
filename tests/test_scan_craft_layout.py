"""KAN-348 / KAN-349 — TRACK5 shared scan craft (quiet empty, Select a row, keyboard, one scroll)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AREAS = (
    "settings",
    "security",
    "reports",
    "documents",
    "heal",
    "desktop",
    "plans",
    "manual",
    "suites",
    "sandboxes",
)


class ScanCraftLayoutTests(unittest.TestCase):
    def test_all_areas_scan_craft_markers_desk130(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk130", html)
        self.assertIn("desk130", desk)

        for area in AREAS:
            chunk = html.split(f'id="app-section-{area}"', 1)[1]
            # Stop at next app-section or end of drawer content.
            next_bits = chunk.split('id="app-section-', 1)
            section = next_bits[0]
            self.assertIn('data-scan-craft="1"', section, msg=area)
            self.assertIn('data-scan-quiet-empty="1"', section, msg=f"{area} quiet empty")
            self.assertIn('data-scan-unfocused="1"', section, msg=f"{area} unfocused")
            self.assertIn("Select a row", section, msg=f"{area} Select a row")
            self.assertIn('data-scan-kbd="1"', section, msg=f"{area} kbd")
            self.assertIn('data-scan-scroll="scan"', section, msg=f"{area} scan scroll")
            self.assertIn('data-scan-scroll="detail"', section, msg=f"{area} detail scroll")
            self.assertIn(
                'data-scan-no-outer-scroll="1"',
                section,
                msg=f"{area} no outer scroll",
            )

        # Structure-token guard: one-collection areas must not gain a section rail.
        for area in ("suites", "reports", "heal", "manual", "desktop", "sandboxes"):
            chunk = html.split(f'id="app-section-{area}"', 1)[1].split(
                'id="app-section-', 1
            )[0]
            self.assertNotIn("settings-section-rail", chunk, msg=area)
            self.assertNotIn("data-settings-section-rail", chunk, msg=area)
            self.assertNotIn(f"data-{area}-section-rail", chunk, msg=area)

        # Plans / Documents keep tabs — no second rail beside them.
        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertNotIn("settings-section-rail", plans)
        docs = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]
        self.assertNotIn("settings-section-rail", docs)

        # Shared CSS craft
        self.assertIn("data-scan-craft", css)
        self.assertIn("data-scan-no-outer-scroll", css)
        self.assertIn("position: sticky", css)
        self.assertIn("scan-quiet-empty", css)

        # Shared JS keyboard contract (Space never activates row; arrows move)
        self.assertIn("function onScanRowKeydown", js)
        self.assertIn("function focusScanFromDetail", js)
        self.assertIn('key === "ArrowDown"', js)
        self.assertIn('key === "ArrowUp"', js)
        self.assertIn('key === " "', js)
        self.assertIn("checkboxStop", js)

        # Charter Frame markup still present (untouched contract)
        self.assertIn("charter-frame-root", html)


if __name__ == "__main__":
    unittest.main()
