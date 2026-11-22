"""KAN-329 / KAN-330 — Plans Cases FR-UI-11 inherit (scan table + detail)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlanCasesLayoutGrammarTests(unittest.TestCase):
    def test_plans_cases_fr_ui11_grammar_markers_desk110(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk110", html)
        self.assertIn("desk110", desk)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        cases = plans.split('id="plan-panel-cases"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0]

        self.assertIn('data-plan-cases-layout-grammar="1"', plans)
        self.assertIn('data-plan-cases-layout-grammar="1"', cases)
        self.assertIn('data-plan-cases-scan="1"', cases)
        self.assertIn('data-plan-case-detail="1"', cases)
        self.assertIn('id="plan-cases-scan-body"', cases)
        self.assertIn('id="plan-case-detail-pane"', cases)
        self.assertIn('data-plan-cases-list="1"', cases)

        # Columns: Status · Id · Name · Tags · Last (no Sel checkbox column).
        self.assertIn(">Status</th>", cases)
        self.assertIn(">Id</th>", cases)
        self.assertIn(">Name</th>", cases)
        self.assertIn(">Tags</th>", cases)
        self.assertIn(">Last</th>", cases)
        self.assertNotIn(">Sel</th>", cases)

        # Edit / Enabled / Archived live in detail pane — not list-row chrome.
        detail = cases.split('data-plan-case-detail="1"', 1)[1]
        self.assertIn("Edit selected case", detail)
        self.assertIn('id="plan-case-enabled"', detail)
        self.assertIn('id="plan-case-archived"', detail)
        self.assertIn('id="plan-quarantine-set"', detail)
        self.assertIn('id="plan-case-run"', detail)

        # Show archived stays work-header control.
        header = cases.split('data-plan-work-header="1"', 1)[1].split(
            "plan-cases-grammar-split", 1
        )[0]
        self.assertIn('id="plan-show-archived"', header)

        # Plan tabs IA unchanged (FR-UI-9).
        self.assertIn('data-plan-tabs="1"', plans)
        self.assertIn('id="plan-tab-cases"', plans)
        self.assertIn('id="plan-tab-trace"', plans)

        # No text-dump map of numbered case lines in renderPlanCases primary path.
        self.assertIn("function renderPlanCases", js)
        self.assertIn("function focusPlanCaseDetail", js)
        self.assertIn("function syncPlanCaseRowFocus", js)
        self.assertIn("plan-cases-scan-row", js)
        self.assertIn("planCasesScanBody", js)
        self.assertIn("focusPlanCaseDetail", js)

        # CSS grammar: split + scan table + detail pane.
        self.assertIn("data-plan-cases-layout-grammar", css)
        self.assertIn(".plan-cases-scan-table", css)
        self.assertIn(".plan-case-detail-pane", css)
        self.assertIn(".plan-cases-grammar-split", css)


if __name__ == "__main__":
    unittest.main()
