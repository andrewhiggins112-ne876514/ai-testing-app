"""App drawer toggle must not cover Settings nav (KAN-110 / KAN-101 / KAN-113)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class NavOverlapTests(unittest.TestCase):
    def test_js_parks_toggle_on_open_drawer(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function parkToggleOnOpenDrawer", js)
        self.assertIn("function restoreTogglePlacement", js)
        self.assertIn("drawer-open-tab", js)
        self.assertIn("drawer-app-open", js)
        self.assertIn("parkToggleOnOpenDrawer(toggle, drawer)", js)
        self.assertIn("size + 6", js)

    def test_css_open_drawer_above_chat_and_disables_chat_hits(self):
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        self.assertIn(".side-drawer.open", css)
        self.assertIn("z-index: 9", css)
        self.assertIn("html.drawer-app-open #chat-panel", css)
        self.assertIn("pointer-events: none", css)
        self.assertIn(".drawer-toggle.drawer-open-tab", css)
        self.assertIn("left: 72px", css)
        self.assertIn("z-index: 11", css)

    def test_cache_bust_current(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk100", app)
        self.assertIn("desktop.css?v=desk100", html)
        self.assertIn("desktop.js?v=desk100", html)

    def test_area_chrome_not_sticky_in_scrollport(self):
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-area-chrome-nonoverlap="1"', html)
        self.assertIn(".area-work", css)
        self.assertNotIn("position: sticky", css)


if __name__ == "__main__":
    unittest.main()
