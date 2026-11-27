"""KAN-311 — Track3 shared chrome scaffold + retire sticky naming (KAN-310)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRIMARY_SECTIONS = (
    "app-section-plans",
    "app-section-manual",
    "app-section-reports",
    "app-section-documents",
    "app-section-settings",
)


class Track3ChromeScaffoldTests(unittest.TestCase):
    def test_shared_chrome_scaffold_desk144(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk144", html)
        self.assertIn("desk144", desk)
        self.assertIn('data-area-chrome-scaffold="1"', html)
        self.assertIn("Accepted", wires)

        # Sticky naming retired (product HTML/CSS).
        self.assertNotIn("sticky", html.lower())
        self.assertNotIn("sticky-toolbar", css)
        pre_craft = css.split("/* KAN-348")[0]
        self.assertNotIn("position: sticky", pre_craft)  # chrome; scan thead sticky is KAN-348

        # Shared scaffold class on every area toolbar (10: Primary + Lab + Settings/Security).
        self.assertEqual(
            len(re.findall(r'class="area-chrome-toolbar ', html)),
            10,
        )
        self.assertIn(".area-chrome-toolbar", css)
        self.assertIn("flex-shrink: 0", css)
        self.assertIn("var(--chrome-toolbar)", css)

        for section in PRIMARY_SECTIONS:
            self.assertIn(f'id="{section}"', html)

        # Primary areas: no *-sticky-* markers; chrome IDs present where toolbars exist.
        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        reports = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        documents = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]

        for chunk, markers in (
            (plans, ('id="plan-chrome-toolbar"', 'data-plan-chrome="1"')),
            (manual, ('id="manual-chrome-toolbar"', 'data-manual-chrome="1"')),
            (reports, ('id="rpt-chrome-toolbar"', 'data-rpt-chrome="1"')),
            (documents, ('id="doc-chrome-toolbar"', 'data-doc-chrome="1"')),
        ):
            self.assertNotIn("sticky", chunk.lower())
            for m in markers:
                self.assertIn(m, chunk)
            # Exactly one chrome toolbar element (shared + area class on the same node).
            self.assertEqual(
                len(re.findall(r'class="area-chrome-toolbar ', chunk)),
                1,
            )

        # Plans: search lives in the one toolbar; results scroll in .area-work.
        toolbar = plans.split('id="plan-chrome-toolbar"', 1)[1].split(
            'id="plan-section-tabs"', 1
        )[0]
        self.assertIn('id="plan-search-q"', toolbar)
        self.assertIn('id="plan-status"', toolbar)
        work = plans.split('data-area-work="1"', 1)[1]
        self.assertIn('id="plan-search-results"', work)
        self.assertNotIn('id="plan-search-results"', toolbar)

        # Chrome remains outside .area-work (toolbar before work).
        for chunk, toolbar_id in (
            (plans, "plan-chrome-toolbar"),
            (manual, "manual-chrome-toolbar"),
            (reports, "rpt-chrome-toolbar"),
            (documents, "doc-chrome-toolbar"),
        ):
            t_at = chunk.find(f'id="{toolbar_id}"')
            w_at = chunk.find('data-area-work="1"')
            self.assertGreater(w_at, t_at, msg=toolbar_id)

        # Shared CSS applies static chrome (not sticky-inside-scrollport).
        shared = re.search(
            r"\.area-chrome-toolbar\s*,[\s\S]*?\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(shared)
        self.assertIn("position: static", shared.group(0))
        self.assertIn("flex-shrink: 0", shared.group(0))


if __name__ == "__main__":
    unittest.main()
