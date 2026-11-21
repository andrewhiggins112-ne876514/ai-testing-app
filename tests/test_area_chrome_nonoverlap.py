"""KAN-281 / FR-UI-9 — non-overlapping area chrome (Track 2)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AreaChromeNonoverlapTests(unittest.TestCase):
    def test_markers_and_desk104(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk104", html)
        self.assertIn("desk104", desk)
        self.assertIn('data-area-chrome-nonoverlap="1"', html)
        self.assertEqual(html.count('data-area-work="1"'), 10)
        for section in (
            "app-section-settings",
            "app-section-security",
            "app-section-plans",
            "app-section-suites",
            "app-section-reports",
            "app-section-manual",
            "app-section-documents",
            "app-section-heal",
            "app-section-desktop",
            "app-section-sandboxes",
        ):
            self.assertIn(f'id="{section}"', html)

        # Confirm/Cancel remain in Manual DOM (clickable when review open).
        self.assertIn('id="manual-confirm-yes"', html)
        self.assertIn('id="manual-confirm-no"', html)
        self.assertIn('id="manual-confirm-row"', html)

        # Toolbars keep IDs; scrollport is .area-work, not sticky-inside-.area-body.
        self.assertIn(".area-work", css)
        self.assertIn("data-area-chrome-nonoverlap", html)
        self.assertIn("position: static", css)
        self.assertNotIn("position: sticky", css)

        # Shared scaffold + area modifiers must not reintroduce sticky positioning.
        self.assertIn(".area-chrome-toolbar", css)
        for cls in (
            "area-chrome-toolbar",
            "plan-chrome-toolbar",
            "suite-chrome-toolbar",
            "rpt-chrome-toolbar",
            "manual-chrome-toolbar",
            "lab-chrome-toolbar",
            "settings-chrome-toolbar",
            "sec-chrome-toolbar",
        ):
            self.assertIn(f".{cls}", css)
        shared = re.search(
            r"\.area-chrome-toolbar\s*,[\s\S]*?\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(shared)
        self.assertIn("position: static", shared.group(0))
        self.assertNotIn("position: sticky", shared.group(0))

        # Plans tabs stay outside the work scrollport (before area-work).
        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        tabs_at = plans.find('id="plan-section-tabs"')
        work_at = plans.find('data-area-work="1"')
        cases_at = plans.find('id="plan-panel-cases"')
        self.assertGreater(work_at, tabs_at)
        self.assertGreater(cases_at, work_at)

        # KAN-293 — Confirm dock is outside .area-work (footer, always visible).
        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        work_at = manual.find('data-area-work="1"')
        confirm_at = manual.find('id="manual-confirm-row"')
        self.assertGreater(confirm_at, work_at)
        self.assertIn('data-manual-confirm-dock="1"', manual)
        self.assertIn("manual-confirm-dock", css)


if __name__ == "__main__":
    unittest.main()
