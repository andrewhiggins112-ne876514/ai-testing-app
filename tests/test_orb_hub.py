"""Orb hub particle chrome stays wired for layout mode orb_hub (KAN-109)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class OrbHubTests(unittest.TestCase):
    def test_hub_markup_has_particle_layer_and_seven_spokes(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="orb-hub"', html)
        self.assertIn("hub-particle-layer", html)
        self.assertIn("hub-spoke-lines", html)
        self.assertIn("hub-particles", html)
        self.assertEqual(html.count('class="hub-spoke shell-surface"'), 7)
        for section in (
            "settings",
            "security",
            "reports",
            "documents",
            "desktop",
            "suites",
            "sandboxes",
        ):
            self.assertIn(f'data-section="{section}"', html)

    def test_hub_js_uses_open_helper(self):
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("function setHubOpen", js)
        self.assertIn('classList.add("is-open")', js)
        self.assertIn('setAttribute("aria-expanded"', js)

    def test_cache_bust_desk21(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk21b", app)
        self.assertIn("desktop.css?v=desk21b", html)
        self.assertIn("desktop.js?v=desk21b", html)


if __name__ == "__main__":
    unittest.main()
