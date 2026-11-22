"""KAN-249 / FR-SET-4 — Settings hub; desktop uses FR-UI-11 section rail (KAN-324)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SettingsHubTests(unittest.TestCase):
    def test_desktop_settings_has_section_rail(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        settings_block = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        self.assertIn('id="set-chrome-toolbar"', settings_block)
        self.assertIn('data-area-work="1"', settings_block)
        self.assertIn('data-settings-section-rail="1"', settings_block)
        self.assertIn('data-settings-section="layout"', settings_block)
        self.assertIn('data-settings-section="report"', settings_block)
        self.assertIn('id="settings-section-layout"', settings_block)
        self.assertIn('id="settings-section-report"', settings_block)
        self.assertIn('id="rpt-summary"', settings_block)
        self.assertIn('id="rpt-save"', settings_block)
        layout_panel = settings_block.split(
            'id="settings-section-layout"', 1
        )[1].split('id="settings-section-connections"', 1)[0]
        report_panel = settings_block.split('id="settings-section-report"', 1)[1]
        self.assertIn('id="area-layout-picker"', layout_panel)
        self.assertNotIn('id="rpt-summary"', layout_panel)
        self.assertIn('id="report-settings-heading"', report_panel)
        self.assertIn('id="rpt-summary"', report_panel)
        self.assertIn("setSettingsCategory", js)
        self.assertIn("setSettingsSection", js)
        self.assertIn("settingsCategoryPending", js)
        self.assertIn("desk121", desk)
        self.assertIn("desk121", html)

    def test_desktop_security_stays_separate(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        security = html.split('id="app-section-security"', 1)[1].split(
            'id="app-section-reports"', 1
        )[0]
        self.assertIn("Confirm switch", security)
        self.assertIn("Confirm delete", security)
        self.assertIn('id="sec-propose"', security)
        self.assertIn('id="priv-propose"', security)
        settings = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        self.assertNotIn('id="sec-propose"', settings)
        self.assertNotIn('id="priv-propose"', settings)

    def test_desktop_report_deeplink_selects_report_section(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function openReportSettings", js)
        self.assertIn('settingsCategoryPending = "report"', js)
        self.assertIn('setSettingsCategory("report")', js)

    def test_gradio_settings_category_switch(self):
        src = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        self.assertIn("GRADIO_SETTINGS_CATEGORIES", src)
        self.assertIn("select_settings_category", src)
        self.assertIn('elem_id="settings-cat-switch"', src)
        self.assertIn('elem_id="settings-cat-app"', src)
        self.assertIn('elem_id="settings-cat-report"', src)
        settings_idx = src.find('elem_id="gradio-area-settings"')
        reports_idx = src.find('elem_id="gradio-area-reports"')
        chunk = src[settings_idx:reports_idx]
        self.assertIn("Report Settings", chunk)
        self.assertIn("Save sections", chunk)
        # Category radio before Report panel.
        self.assertLess(
            chunk.find('elem_id="settings-cat-switch"'),
            chunk.find('elem_id="settings-cat-report"'),
        )

    def test_select_settings_category_toggles_panels(self):
        from ui import gradio_app

        state, app_u, report_u = gradio_app.select_settings_category("Report")
        self.assertEqual(state, "Report")
        self.assertFalse(app_u.get("visible"))
        self.assertTrue(report_u.get("visible"))
        state, app_u, report_u = gradio_app.select_settings_category("App")
        self.assertEqual(state, "App")
        self.assertTrue(app_u.get("visible"))
        self.assertFalse(report_u.get("visible"))
        state, app_u, report_u = gradio_app.select_settings_category("Nope")
        self.assertEqual(state, "App")
        self.assertTrue(app_u.get("visible"))


if __name__ == "__main__":
    unittest.main()
