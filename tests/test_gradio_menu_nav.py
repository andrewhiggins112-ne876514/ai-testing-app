"""KAN-248 / UI-NAV-IA-2 — Gradio App menu button (no persistent top tab bar)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GradioMenuNavTests(unittest.TestCase):
    def test_source_has_menu_not_tabs(self):
        src = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        self.assertNotIn("with gr.Tabs()", src)
        self.assertNotIn('gr.Tab("Chat")', src)
        self.assertIn('elem_id="app-menu-btn"', src)
        self.assertIn('elem_id="app-menu-panel"', src)
        self.assertIn('elem_id="app-menu-nav-chat"', src)
        self.assertIn('elem_id="app-menu-nav-settings"', src)
        self.assertIn('elem_id="app-menu-nav-plans"', src)
        self.assertIn('elem_id="app-menu-nav-manual"', src)
        self.assertIn('elem_id="app-menu-nav-reports"', src)
        self.assertIn('elem_id="app-menu-nav-documents"', src)
        self.assertIn(
            '("Chat", "Settings", "Plans", "Manual", "Reports", "Documents")',
            src,
        )
        self.assertIn("select_app_area", src)
        self.assertIn("GRADIO_APP_AREAS", src)
        # Tab strip must not be the navigation surface.
        self.assertIn(".tab-nav", src)
        self.assertIn("display: none", src)

    def test_orb_gear_still_orb_only(self):
        src = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        self.assertIn('elem_id="orb-settings-btn"', src)
        self.assertIn('elem_id="orb-settings-panel"', src)
        self.assertIn("toggle_orb_settings", src)
        # Gear panel is orb look/presets, not App Settings.
        panel_start = src.find('elem_id="orb-settings-panel"')
        panel_chunk = src[panel_start : panel_start + 1800]
        self.assertIn("Orb", panel_chunk)
        self.assertIn("Presets", panel_chunk)
        self.assertNotIn("Jira base URL", panel_chunk)
        self.assertNotIn("Security level", panel_chunk)

    def test_select_app_area_shows_one_panel(self):
        from ui import gradio_app

        closed, panel, label, *vis = gradio_app.select_app_area("Plans")
        self.assertFalse(closed)
        self.assertEqual(label, "**Plans**")
        self.assertIsInstance(panel, dict)
        self.assertFalse(panel.get("visible", True))
        names = list(gradio_app.GRADIO_APP_AREAS)
        self.assertEqual(len(vis), len(names))
        for name, update in zip(names, vis):
            self.assertIsInstance(update, dict)
            self.assertEqual(update.get("visible"), name == "Plans")

    def test_select_unknown_falls_back_to_chat(self):
        from ui import gradio_app

        _closed, _panel, label, *vis = gradio_app.select_app_area("Nope")
        self.assertEqual(label, "**Chat**")
        self.assertTrue(vis[0].get("visible"))
        self.assertFalse(vis[1].get("visible"))

    def test_toggle_app_menu(self):
        from ui import gradio_app

        open_flag, panel = gradio_app.toggle_app_menu(False)
        self.assertTrue(open_flag)
        self.assertTrue(panel.get("visible"))
        open_flag, panel = gradio_app.toggle_app_menu(True)
        self.assertFalse(open_flag)
        self.assertFalse(panel.get("visible"))

    def test_desktop_uses_compact_menu_not_top_tabs(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="app-drawer-toggle"', html)
        self.assertIn('id="app-drawer"', html)
        self.assertIn("app-menu-panel", html)
        self.assertIn('data-compact-app-menu="1"', html)
        self.assertNotIn('class="tab-nav"', html)
        self.assertNotIn("<nav class=\"top-tabs\">", html)


if __name__ == "__main__":
    unittest.main()
