"""KAN-253 / KAN-256 / KAN-260 — Desktop compact App menu (Primary + Lab tools)."""
from __future__ import annotations

import unittest
from pathlib import Path

from ui.app_areas import LAB_APP_MENU_AREAS, PRIMARY_APP_MENU_AREAS

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
        self.assertIn("desk89", html)
        self.assertIn('data-default-along="16"', html)

    def test_app_nav_has_primary_and_lab_groups(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        nav_start = html.index('class="app-nav"')
        nav_end = html.index("</nav>", nav_start)
        nav = html[nav_start:nav_end]
        self.assertIn('data-nav-group="primary"', nav)
        self.assertIn('data-nav-group="lab"', nav)
        self.assertIn("Primary", nav)
        self.assertIn("Lab tools", nav)
        for section in PRIMARY_APP_MENU_AREAS:
            self.assertIn(f'data-section="{section}"', nav)
        for section in LAB_APP_MENU_AREAS:
            self.assertIn(f'data-section="{section}"', nav)
        # Drift UI from C5 must remain after menu merge.
        self.assertIn("plan-drift-check-btn", html)

    def test_app_areas_constants_match_story(self):
        self.assertEqual(
            PRIMARY_APP_MENU_AREAS,
            ("chat", "settings", "plans", "reports", "documents"),
        )
        self.assertEqual(
            LAB_APP_MENU_AREAS,
            ("security", "heal", "desktop", "suites", "sandboxes"),
        )

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
        self.assertIn(".app-nav-group", css)
        self.assertIn(".app-nav-group-label", css)
        self.assertIn("KAN-256", css)

    def test_js_positions_compact_panel(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function isCompactAppMenu", js)
        self.assertIn("function positionAppMenuPanel", js)
        self.assertIn("dataset.compactAppMenu", js)
        self.assertIn("appMenuCompactV2", js)
        self.assertIn("KAN-256", js)
        self.assertIn('section === "chat"', js)
        self.assertIn("function parkToggleOnOpenDrawer", js)
        self.assertIn("isCompactAppMenu(drawer)", js)
        self.assertIn("postAcceptanceDrift", js)

    def test_cache_bust_desk89(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk89", app)
        self.assertIn("desktop.css?v=desk89", html)
        self.assertIn("desktop.js?v=desk89", html)

    def test_open_area_still_closes_menu(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn('if (appDrawer && appDrawer.classList.contains("open"))', js)
        self.assertIn("setDrawer(appDrawer, appToggle, false)", js)


if __name__ == "__main__":
    unittest.main()
