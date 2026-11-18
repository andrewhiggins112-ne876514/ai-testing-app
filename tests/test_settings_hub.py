"""KAN-249 / FR-SET-4 — Settings hub App / Report category switch."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SettingsHubTests(unittest.TestCase):
    def test_desktop_settings_has_app_report_categories(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        settings_block = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        self.assertIn('class="settings-cat-switch"', settings_block)
        self.assertIn('data-settings-cat="app"', settings_block)
        self.assertIn('data-settings-cat="report"', settings_block)
        self.assertIn('id="settings-cat-app"', settings_block)
        self.assertIn('id="settings-cat-report"', settings_block)
        self.assertIn('id="rpt-summary"', settings_block)
        self.assertIn('id="rpt-save"', settings_block)
        # Report toggles live in Report panel, not mixed as a trailing scroll after App only.
        app_panel = settings_block.split('id="settings-cat-app"', 1)[1].split(
            'id="settings-cat-report"', 1
        )[0]
        report_panel = settings_block.split('id="settings-cat-report"', 1)[1]
        self.assertIn("App settings", app_panel)
        self.assertIn('id="set-jira-url"', app_panel)
        self.assertNotIn('id="rpt-summary"', app_panel)
        self.assertIn('id="report-settings-heading"', report_panel)
        self.assertIn('id="rpt-summary"', report_panel)
        self.assertIn("setSettingsCategory", js)
        self.assertIn("settingsCategoryPending", js)
        self.assertIn("desk95", desk)
        self.assertIn("desk95", html)

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

    def test_desktop_report_deeplink_selects_report_category(self):
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
