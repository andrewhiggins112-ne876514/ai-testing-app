"""KAN-331 / KAN-332 — Plans remaining tabs FR-UI-11 (Coverage Trace History Draft Run)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlansTabsLayoutGrammarTests(unittest.TestCase):
    def test_plans_remaining_tabs_fr_ui11_markers_desk150(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk150", html)
        self.assertIn("desk150", desk)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]

        self.assertIn('data-plans-tabs-layout-grammar="1"', plans)
        self.assertIn('id="plan-tab-cases"', plans)
        self.assertIn('id="plan-panel-cases"', plans)

        coverage = plans.split('id="plan-panel-coverage"', 1)[1].split(
            'id="plan-panel-trace"', 1
        )[0]
        self.assertIn('data-plan-coverage-scan="1"', coverage)
        self.assertIn(">Story</th>", coverage)
        self.assertIn(">Gap</th>", coverage)
        self.assertIn(">Summary</th>", coverage)
        self.assertIn('data-plan-coverage-detail="1"', coverage)
        self.assertNotIn('type="checkbox"', coverage)

        trace = plans.split('id="plan-panel-trace"', 1)[1].split(
            'id="plan-panel-history"', 1
        )[0]
        self.assertIn('data-plan-trace-scan="1"', trace)
        self.assertIn(">Story</th>", trace)
        self.assertIn(">Cases</th>", trace)
        self.assertIn(">Last</th>", trace)
        self.assertIn(">Bugs</th>", trace)
        self.assertIn(">Known</th>", trace)
        self.assertNotIn('type="checkbox"', trace)

        history = plans.split('id="plan-panel-history"', 1)[1].split(
            'id="plan-panel-run"', 1
        )[0]
        self.assertIn('data-plan-history-scan="1"', history)
        self.assertIn(">A</th>", history)
        self.assertIn(">B</th>", history)
        self.assertIn('id="plan-history-list"', history)
        self.assertIn('id="plan-history-a"', history)
        self.assertIn('id="plan-history-b"', history)
        self.assertIn('id="plan-compare-btn"', history)

        draft = plans.split('id="plan-panel-draft"', 1)[1].split(
            'id="plan-panel-coverage"', 1
        )[0]
        self.assertIn('data-plan-draft-form="1"', draft)

        run = plans.split('id="plan-panel-run"', 1)[1]
        self.assertIn('data-plan-run-sections="1"', run)
        pause_idx = run.find('id="plan-pause-on-fail"')
        self.assertGreater(pause_idx, 0)
        pause_slice = run[max(0, pause_idx - 120) : pause_idx + 80]
        self.assertNotIn("check-row", pause_slice)

        self.assertIn("function renderCoverageGaps", js)
        self.assertIn("function renderTraceabilityMatrix", js)
        self.assertIn("function renderSuiteHistory", js)
        self.assertIn("createElement(\"tr\")", js)
        self.assertIn("plan-coverage-scan-row", js)
        self.assertIn("plan-trace-scan-row", js)
        self.assertIn("plan-history-scan-row", js)
        self.assertIn("plan-hist-a", js)
        self.assertIn("plan-hist-b", js)
        self.assertIn("stopPropagation", js)
        self.assertIn("focusCoverageGapDetail", js)
        self.assertIn("focusHistoryRunDetail", js)

        self.assertIn("data-plans-tabs-layout-grammar", css)
        self.assertIn(".plan-tabs-scan-table", css)
        self.assertIn(".plan-tabs-hit-cell", css)
        self.assertIn(".plan-tabs-detail-pane", css)


if __name__ == "__main__":
    unittest.main()
