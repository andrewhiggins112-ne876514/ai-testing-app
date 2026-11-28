"""KAN-275 — Manual Primary App area + Plans deep-link shell."""
from __future__ import annotations

import unittest
from pathlib import Path

from ui.app_areas import LAB_APP_MENU_AREAS, PRIMARY_APP_MENU_AREAS

ROOT = Path(__file__).resolve().parents[1]


class ManualIaDesktopUiTests(unittest.TestCase):
    def test_manual_primary_shell_markers_desk151(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk151", html)
        self.assertIn("desk151", desk)
        self.assertIn('data-manual-ia="1"', html)
        self.assertIn('data-manual-assist-honest="1"', html)
        self.assertIn('data-manual-assist-status="1"', html)
        self.assertIn('id="app-section-manual"', html)
        self.assertIn('data-manual-chrome="1"', html)
        self.assertIn('data-manual-primary="1"', html)
        self.assertIn('data-manual-shell="1"', html)
        self.assertIn('data-manual-deeplink="1"', html)
        self.assertIn('id="plan-start-manual"', html)
        self.assertIn("Start manual on this case", html)
        self.assertIn('id="manual-charter"', html)
        self.assertIn('id="manual-plan-id"', html)
        self.assertIn('id="manual-case-id"', html)
        self.assertIn('id="manual-story-key"', html)
        self.assertIn('id="manual-start"', html)
        self.assertIn('data-manual-start="1"', html)
        # Charter Frame Start is enabled (KAN-277); shell markers from KAN-275 remain.

        nav = html.split('id="app-drawer"', 1)[1].split('id="screen-drawer"', 1)[0]
        primary = nav.split('data-nav-group="primary"', 1)[1].split(
            'data-nav-group="lab"', 1
        )[0]
        self.assertIn('data-section="manual"', primary)
        self.assertNotIn('data-section="manual"', nav.split('data-nav-group="lab"', 1)[1])
        # Primary order: … Plans, Manual, Reports …
        plans_i = primary.find('data-section="plans"')
        manual_i = primary.find('data-section="manual"')
        reports_i = primary.find('data-section="reports"')
        self.assertLess(plans_i, manual_i)
        self.assertLess(manual_i, reports_i)

        self.assertEqual(
            PRIMARY_APP_MENU_AREAS,
            ("chat", "settings", "plans", "manual", "reports", "documents"),
        )
        self.assertNotIn("manual", LAB_APP_MENU_AREAS)

        self.assertIn(".manual-chrome-toolbar", css)
        self.assertIn(".manual-primary", css)
        self.assertIn("function openManualFromPlansDeepLink", js)
        self.assertIn("function fillManualFromPlanContext", js)
        self.assertIn('manual: "Manual"', js)
        self.assertIn("manual: { section: manualSection", js)

    def test_gradio_manual_stub_minimal(self):
        gradio = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        self.assertIn('"Manual"', gradio)
        self.assertIn("gradio-area-manual", gradio)
        self.assertIn("data-manual-shell", gradio)
        self.assertIn("app-menu-nav-manual", gradio)


if __name__ == "__main__":
    unittest.main()
