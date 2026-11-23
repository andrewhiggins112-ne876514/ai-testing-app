"""KAN-269 — Suites area UI tidy: sticky path/run, primary list, collapsed advanced."""
from __future__ import annotations

import unittest
from pathlib import Path


class SuitesIaDesktopUiTests(unittest.TestCase):
    def test_suites_ia_markers_desk125(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        css = Path("ui/desktop/desktop.css").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk125", html)
        self.assertIn("desk125", desk)
        self.assertIn('data-suites-ia="1"', html)
        self.assertIn('data-suite-chrome="1"', html)
        self.assertIn('id="suite-chrome-toolbar"', html)
        self.assertIn('data-suite-primary="1"', html)
        self.assertIn('data-suite-list="1"', html)
        self.assertIn('id="suite-list"', html)
        self.assertIn('id="suite-list-btn"', html)
        self.assertIn('id="suite-run"', html)
        self.assertIn('id="suite-run-all"', html)
        self.assertIn('id="suite-discover"', html)
        self.assertIn('data-suite-advanced="1"', html)
        self.assertIn('id="suite-advanced"', html)
        self.assertIn('id="suite-import"', html)

        toolbar = html.split('id="suite-chrome-toolbar"', 1)[1].split(
            'id="suite-primary"', 1
        )[0]
        for marker in (
            'id="suite-path"',
            'id="suite-discover"',
            'id="suite-list-btn"',
            'id="suite-run"',
            'id="suite-run-all"',
            'id="suite-status"',
            'id="suite-saved"',
        ):
            self.assertIn(marker, toolbar)

        # Import is secondary (advanced), not equal-weight in the sticky toolbar.
        self.assertNotIn('id="suite-import"', toolbar)
        advanced = html.split('id="suite-advanced"', 1)[1].split(
            'id="app-section-sandboxes"', 1
        )[0]
        self.assertIn('id="suite-import"', advanced)
        self.assertIn("<summary>", advanced)

        # Primary list sits above advanced help.
        primary_pos = html.find('id="suite-primary"')
        advanced_pos = html.find('id="suite-advanced"')
        self.assertGreater(primary_pos, 0)
        self.assertGreater(advanced_pos, primary_pos)

        self.assertIn("renderSuiteList", js)
        self.assertIn("/api/playwright-suite/list", js)
        self.assertIn("suiteSelected", js)
        self.assertIn("postSuiteRun", js)
        self.assertIn(".suite-chrome-toolbar", css)
        self.assertIn(".suite-scan-table", css)
        self.assertIn(".suite-advanced", css)

        # Unchanged Discover / Import / Run control ids remain for API wiring.
        self.assertIn('id="suite-discover"', html)
        self.assertIn('id="suite-import"', html)
        self.assertIn('id="suite-run"', html)


if __name__ == "__main__":
    unittest.main()
