"""Desktop App menu — Gradio-style popover + parity (KAN-253 / KAN-256 / KAN-257).

These tests are intentionally strict. KAN-253 false-greened because earlier checks
only looked for class name strings while the menu still behaved as a tall rail.
"""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from ui.app_areas import (
    APP_MENU_EXCLUDED_SECTIONS,
    PRIMARY_APP_MENU_AREAS,
    PRIMARY_APP_MENU_SECTIONS,
)

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_HTML = ROOT / "ui" / "desktop" / "index.html"
DESKTOP_CSS = ROOT / "ui" / "desktop" / "desktop.css"
DESKTOP_JS = ROOT / "ui" / "desktop" / "desktop.js"
DESKTOP_APP = ROOT / "desktop_app.py"
GRADIO = ROOT / "ui" / "gradio_app.py"
CACHE = "desk47"


def _css_rule_block(css: str, selector: str) -> str:
    """Return the first {...} body for an exact selector line."""
    pattern = re.compile(
        re.escape(selector) + r"\s*\{([^}]+)\}",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(css)
    if not match:
        raise AssertionError(f"CSS rule not found for selector {selector!r}")
    return match.group(1)


class _AppDrawerTree(HTMLParser):
    """Track whether #area-section-host appears inside #app-drawer."""

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[str | None] = []
        self.in_app_drawer = False
        self.host_inside_app_drawer = False
        self.app_nav_sections: list[str] = []
        self._in_app_nav = False
        self.app_drawer_classes: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k: (v or "") for k, v in attrs}
        el_id = ad.get("id", "")
        classes = ad.get("class", "")
        self._stack.append(el_id or None)

        if el_id == "app-drawer":
            self.in_app_drawer = True
            self.app_drawer_classes = classes
        if el_id == "area-section-host" and self.in_app_drawer:
            self.host_inside_app_drawer = True
        if "app-nav" in classes.split() and self.in_app_drawer:
            self._in_app_nav = True
        if (
            self._in_app_nav
            and tag == "button"
            and "app-nav-item" in classes.split()
        ):
            section = ad.get("data-section", "")
            if section:
                self.app_nav_sections.append(section)

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        el_id = self._stack.pop()
        if el_id == "app-drawer":
            self.in_app_drawer = False
        if tag == "nav" and self._in_app_nav:
            self._in_app_nav = False


class DesktopAppMenuTests(unittest.TestCase):
    def test_shared_areas_module_is_source_of_truth(self):
        self.assertEqual(
            PRIMARY_APP_MENU_AREAS,
            ("Chat", "Settings", "Plans", "Reports", "Documents"),
        )
        gradio_src = GRADIO.read_text(encoding="utf-8")
        self.assertIn("PRIMARY_APP_MENU_AREAS", gradio_src)
        self.assertIn("from ui.app_areas import", gradio_src)
        from ui import gradio_app

        self.assertEqual(tuple(gradio_app.GRADIO_APP_AREAS), PRIMARY_APP_MENU_AREAS)

    def test_desktop_nav_exactly_matches_primary_areas(self):
        html = DESKTOP_HTML.read_text(encoding="utf-8")
        parser = _AppDrawerTree()
        parser.feed(html)
        self.assertEqual(tuple(parser.app_nav_sections), PRIMARY_APP_MENU_SECTIONS)
        self.assertEqual(len(parser.app_nav_sections), len(PRIMARY_APP_MENU_AREAS))
        for excluded in APP_MENU_EXCLUDED_SECTIONS:
            self.assertNotIn(excluded, parser.app_nav_sections)

    def test_area_host_must_not_live_inside_app_menu(self):
        html = DESKTOP_HTML.read_text(encoding="utf-8")
        parser = _AppDrawerTree()
        parser.feed(html)
        self.assertFalse(
            parser.host_inside_app_drawer,
            "area-section-host must not be nested under #app-drawer (tall-menu false green)",
        )
        body_i = html.index('id="area-body"')
        host_i = html.index('id="area-section-host"')
        app_i = html.index('id="app-drawer"')
        self.assertLess(body_i, host_i)
        self.assertGreater(app_i, host_i)

    def test_app_drawer_is_not_side_drawer_class(self):
        html = DESKTOP_HTML.read_text(encoding="utf-8")
        parser = _AppDrawerTree()
        parser.feed(html)
        classes = set(parser.app_drawer_classes.split())
        self.assertIn("app-menu-panel", classes)
        self.assertNotIn("side-drawer", classes)
        self.assertIn('data-compact-app-menu="1"', html)
        self.assertIn("▦", html)
        self.assertIn(CACHE, html)
        self.assertIn('data-default-along="16"', html)

    def test_css_popover_geometry_not_tall_rail(self):
        css = DESKTOP_CSS.read_text(encoding="utf-8")
        body = _css_rule_block(css, "#app-drawer.app-menu-panel")
        self.assertIn("position: fixed", body)
        self.assertIn("height: fit-content", body)
        self.assertIn("inset: unset", body)
        # Tall side-rail fingerprints must not appear in the App menu rule.
        self.assertNotIn("top: 24px", body)
        self.assertNotIn("bottom: 88px", body)
        self.assertNotRegex(body, r"width:\s*0\b")
        self.assertNotRegex(body, r"height:\s*100%")
        open_body = _css_rule_block(css, "#app-drawer.app-menu-panel.open")
        self.assertIn("pointer-events: auto", open_body)
        # Side-drawer open width stretch must not be the App menu open rule.
        self.assertNotIn("width: var(--drawer-size", open_body)

    def test_js_positions_compact_panel_and_closes_on_nav(self):
        js = DESKTOP_JS.read_text(encoding="utf-8")
        self.assertIn("function isCompactAppMenu", js)
        self.assertIn("function positionAppMenuPanel", js)
        self.assertIn("dataset.compactAppMenu", js)
        self.assertIn("appMenuCompactV2", js)
        self.assertIn('section === "chat"', js)
        self.assertIn('if (appDrawer && appDrawer.classList.contains("open"))', js)
        self.assertIn("setDrawer(appDrawer, appToggle, false)", js)
        # Must not re-apply tall rail sizing to the App menu.
        self.assertIn("isCompactAppMenu(drawer)", js)

    def test_cache_bust_current(self):
        app = DESKTOP_APP.read_text(encoding="utf-8")
        html = DESKTOP_HTML.read_text(encoding="utf-8")
        self.assertIn(CACHE, app)
        self.assertIn(f"desktop.css?v={CACHE}", html)
        self.assertIn(f"desktop.js?v={CACHE}", html)

    def test_gradio_menu_buttons_match_primary_areas(self):
        src = GRADIO.read_text(encoding="utf-8")
        for name in PRIMARY_APP_MENU_AREAS:
            self.assertIn(f'app-menu-nav-{name.lower()}"', src)
        self.assertNotIn("with gr.Tabs()", src)
        self.assertNotIn('gr.Tab("Chat")', src)


if __name__ == "__main__":
    unittest.main()
