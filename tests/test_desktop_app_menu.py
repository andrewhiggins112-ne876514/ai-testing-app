"""KAN-253 / KAN-256 — Desktop compact App menu (Gradio-style ▦ popover)."""
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
        self.assertIn('class="app-menu-panel"', html)
        self.assertIn('class="app-nav"', html)
        self.assertNotIn('id="app-drawer" class="side-drawer', html)
        self.assertNotIn('class="side-drawer app-drawer', html)
        self.assertNotIn('class="tab-nav"', html)
        self.assertNotIn('<nav class="top-tabs">', html)
        self.assertIn("desk46", html)
        self.assertIn('data-default-along="16"', html)

    def test_area_host_not_nested_in_app_menu(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        app_i = html.index('id="app-drawer"')
        host_i = html.index('id="area-section-host"')
        body_i = html.index('id="area-body"')
        # Host must live under area-body, not under the App menu aside.
        self.assertLess(body_i, host_i)
        self.assertGreater(app_i, host_i)

    def test_css_compact_popover_rules(self):
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        self.assertIn("#app-drawer.app-menu-panel", css)
        self.assertIn("#app-drawer.app-menu-panel.open", css)
        self.assertIn("position: fixed", css)
        self.assertIn("height: fit-content", css)
        self.assertIn(".app-menu-title", css)
        self.assertIn("KAN-256", css)

    def test_js_positions_compact_panel(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function isCompactAppMenu", js)
        self.assertIn("function positionAppMenuPanel", js)
        self.assertIn("dataset.compactAppMenu", js)
        self.assertIn("appMenuCompactV2", js)
        self.assertIn("KAN-256", js)
        self.assertIn("function parkToggleOnOpenDrawer", js)
        self.assertIn("isCompactAppMenu(drawer)", js)

    def test_cache_bust_desk46(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk46", app)
        self.assertIn("desktop.css?v=desk46", html)
        self.assertIn("desktop.js?v=desk46", html)

    def test_open_area_still_closes_menu(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn('if (appDrawer && appDrawer.classList.contains("open"))', js)
        self.assertIn("setDrawer(appDrawer, appToggle, false)", js)


if __name__ == "__main__":
    unittest.main()
