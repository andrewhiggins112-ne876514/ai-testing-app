"""KAN-265 / FR-UI-9 — Plans IA: Cases-first, sticky toolbar, Add case menu."""
from __future__ import annotations

import unittest
from pathlib import Path


class PlansIaDesktopUiTests(unittest.TestCase):
    def test_plans_ia_markers_desk93(self):
        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        css = Path("ui/desktop/desktop.css").read_text(encoding="utf-8")
        desk = Path("desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk93", html)
        self.assertIn("desk93", desk)
        self.assertIn('data-plans-ia="1"', html)
        self.assertIn('data-plan-sticky="1"', html)
        self.assertIn('id="plan-sticky-toolbar"', html)
        self.assertIn('data-plan-tabs="1"', html)
        self.assertIn('id="plan-panel-cases"', html)
        self.assertIn('id="plan-panel-draft"', html)
        self.assertIn('id="plan-panel-coverage"', html)
        self.assertIn('id="plan-panel-trace"', html)
        self.assertIn('id="plan-panel-history"', html)
        self.assertIn('id="plan-panel-run"', html)
        self.assertIn('data-plan-add-menu="1"', html)
        self.assertIn('id="plan-add-case-toggle"', html)
        self.assertIn("Add case", html)

        # Cases is the default selected tab; Draft/Schedule are not default.
        cases_tab = html.split('id="plan-tab-cases"', 1)[1].split("</button>", 1)[0]
        self.assertIn('aria-selected="true"', cases_tab)
        draft_tab = html.split('id="plan-tab-draft"', 1)[1].split("</button>", 1)[0]
        self.assertIn('aria-selected="false"', draft_tab)
        run_tab = html.split('id="plan-tab-run"', 1)[1].split("</button>", 1)[0]
        self.assertIn('aria-selected="false"', run_tab)

        # Sticky toolbar keeps picker / open / refresh / search / status.
        toolbar = html.split('id="plan-sticky-toolbar"', 1)[1].split(
            'id="plan-section-tabs"', 1
        )[0]
        for marker in (
            'id="plan-list"',
            'id="plan-load-btn"',
            'id="plan-refresh-btn"',
            'id="plan-search-q"',
            'id="plan-search-btn"',
            'id="plan-status"',
        ):
            self.assertIn(marker, toolbar)

        # Add-case types remain reachable (not removed) via one menu.
        for btn in (
            "plan-add-desktop-btn",
            "plan-add-api-btn",
            "plan-add-contract-btn",
            "plan-add-seed-btn",
            "plan-add-visual-btn",
            "plan-add-a11y-btn",
            "plan-add-perf-btn",
            "plan-add-framework-btn",
        ):
            self.assertIn(f'id="{btn}"', html)
            self.assertIn(btn, html.split('id="plan-add-case-menu"', 1)[1])

        # Schedule detail is collapsed under Run setup, not a top-level forever-scroll peer.
        run_panel = html.split('id="plan-panel-run"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        self.assertIn("plan-schedule-details", run_panel)
        self.assertIn("plan-schedule-save", run_panel)
        self.assertNotIn('id="plan-schedule-save"', html.split('id="plan-panel-cases"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0])

        self.assertIn("showPlanPanel", js)
        self.assertIn('showPlanPanel("cases")', js)
        self.assertIn("closePlanAddCaseMenu", js)
        self.assertIn(".plan-sticky-toolbar", css)
        self.assertIn(".plan-section-tabs", css)
        self.assertIn(".plan-add-case-menu", css)


if __name__ == "__main__":
    unittest.main()
