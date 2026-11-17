"""KAN-253 / UI-NAV-IA-4 — Desktop compact App menu (match Gradio ▦ panel)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopAppMenuTests(unittest.TestCase):
    def test_html_is_compact_panel_not_tall_side_drawer(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="app-drawer-toggle"', html)
        self.assertIn("▦", html)
        self.assertIn('id="app-drawer"', html)
        self.assertIn('data-compact-app-menu="1"', html)
        self.assertIn('class="app-menu-panel', html)
        self.assertIn('class="app-nav"', html)
        # Must not be the tall side-drawer rail for App.
        self.assertNotIn('id="app-drawer" class="side-drawer', html)
        self.assertNotIn('class="side-drawer app-drawer', html)
        self.assertNotIn('class="tab-nav"', html)
        self.assertNotIn('<nav class="top-tabs">', html)
        self.assertIn("desk44", html)

    def test_css_compact_panel_rules(self):
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        self.assertIn("#app-drawer.app-menu-panel", css)
        self.assertIn("#app-drawer.app-menu-panel.open", css)
        self.assertIn("max-height: min(70vh, 520px)", css)
        self.assertIn(".app-menu-title", css)

    def test_js_positions_compact_panel(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function isCompactAppMenu", js)
        self.assertIn("function positionAppMenuPanel", js)
        self.assertIn("dataset.compactAppMenu", js)
        self.assertIn("KAN-253", js)
        # Screen drawer still uses seam-tab parking; App skips tall rail.
        self.assertIn("function parkToggleOnOpenDrawer", js)
        self.assertIn("isCompactAppMenu(drawer)", js)

    def test_cache_bust_desk44(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk44", app)
        self.assertIn("desktop.css?v=desk44", html)
        self.assertIn("desktop.js?v=desk44", html)

    def test_open_area_still_closes_menu(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        # Choosing a nav item must close the compact panel (FR-UI-1/7).
        self.assertIn("if (appDrawer && appDrawer.classList.contains(\"open\"))", js)
        self.assertIn("setDrawer(appDrawer, appToggle, false)", js)


if __name__ == "__main__":
    unittest.main()
