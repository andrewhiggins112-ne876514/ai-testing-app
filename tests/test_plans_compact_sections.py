"""KAN-350 / KAN-351 — Plans compact booleans and case-detail sections."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlansCompactSectionsTests(unittest.TestCase):
    def test_plans_compact_booleans_and_case_sections_desk127(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk127", html)
        self.assertIn("desk127", desk)
        self.assertIn("desktop.css?v=desk127", html)
        self.assertIn("desktop.js?v=desk127", html)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertIn('data-plans-compact-booleans="1"', plans)
        self.assertIn('data-plan-case-sections="1"', plans)

        # Four compact boolean controls — not page-width stack-label / check-row.
        for cid in (
            "plan-show-archived",
            "plan-case-enabled",
            "plan-case-archived",
            "plan-pause-on-fail",
        ):
            idx = plans.find(f'id="{cid}"')
            self.assertGreater(idx, 0, msg=cid)
            window = plans[max(0, idx - 160) : idx + 40]
            self.assertIn("plan-compact-check", window, msg=cid)
            self.assertNotIn("stack-label", window, msg=cid)
            self.assertNotIn("check-row", window, msg=cid)

        cases = plans.split('id="plan-panel-cases"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0]
        detail = cases.split('data-plan-case-detail="1"', 1)[1]

        # Named sections keep every prior field id.
        for section in ("edit", "run", "quarantine", "known"):
            self.assertIn(f'data-plan-case-section="{section}"', detail, msg=section)
        for fid in (
            "plan-case-id",
            "plan-case-name",
            "plan-case-note",
            "plan-case-tags",
            "plan-case-priority",
            "plan-case-step-timeout",
            "plan-case-enabled",
            "plan-case-archived",
            "plan-case-up",
            "plan-case-down",
            "plan-update-baseline-btn",
            "plan-run-note",
            "plan-notes-save",
            "plan-keyboard-hint",
            "plan-start-manual",
            "plan-rerun-failed",
            "plan-defect-preview",
            "plan-pause-actions",
            "plan-pause-continue",
            "plan-pause-stop",
            "plan-rerun-out",
            "plan-run-failure-class",
            "plan-run-failure-save",
            "plan-flake-hint",
            "plan-flake-summary",
            "plan-quarantine-reason",
            "plan-quarantine-expires",
            "plan-quarantine-set",
            "plan-quarantine-clear",
            "plan-flake-refresh",
            "plan-known-note",
            "plan-known-jira",
            "plan-known-save",
            "plan-known-clear",
            "plan-case-detail",
            "plan-defect-out",
            "plan-degraded-hint",
            "plan-case-save",
            "plan-case-run",
        ):
            self.assertIn(f'id="{fid}"', detail, msg=fid)

        # Pinned Save / Run outside the scrolling section body.
        self.assertIn('data-plan-case-pin="1"', detail)
        self.assertIn('data-plan-case-sections-scroll="1"', detail)
        pin = detail.split('data-plan-case-pin="1"', 1)[1]
        self.assertIn('id="plan-case-save"', pin)
        self.assertIn('id="plan-case-run"', pin)
        scroll = detail.split('data-plan-case-sections-scroll="1"', 1)[1].split(
            'data-plan-case-pin="1"', 1
        )[0]
        self.assertNotIn('id="plan-case-save"', scroll)
        self.assertNotIn('id="plan-case-run"', scroll)

        # CSS: compact check + pin sticky while body scrolls.
        self.assertIn("data-plans-compact-booleans", css)
        self.assertIn(".plan-compact-check", css)
        self.assertIn(".plan-case-detail-pin", css)
        self.assertIn(".plan-case-detail-scroll", css)
        self.assertIn("data-plan-case-focused", css)

        # KAN-356 — detail scroll chain: selectors must match the aside attributes;
        # pane clips, body scrolls; grid row is minmax(0,1fr) so height is bounded.
        self.assertIn('data-scan-scroll="detail"', detail)
        aside_open = cases.split('id="plan-case-detail-pane"', 1)[1].split(">", 1)[0]
        self.assertNotIn("data-scan-scroll", aside_open)
        self.assertIn('data-plan-case-sections="1"', aside_open)
        # Dead selector regression — must not target #plan-panel-cases[data-plan-case-sections]
        self.assertNotIn(
            '#plan-panel-cases[data-plan-case-sections="1"]',
            css,
        )
        scroll_rule = css.split(
            "#plan-case-detail-pane[data-plan-case-sections=\"1\"] .plan-case-detail-scroll",
            1,
        )[1].split("}", 1)[0]
        self.assertIn("overflow-y: auto", scroll_rule)
        self.assertIn("flex: 1 1 0", scroll_rule)
        live_rule = css.split(
            "#plan-case-detail-pane[data-plan-case-sections=\"1\"] .plan-case-detail-live",
            1,
        )[1].split("}", 1)[0]
        self.assertIn("flex: 1 1 0", live_rule)
        self.assertIn("min-height: 0", live_rule)
        pane_rule = css.split(
            "#plan-panel-cases[data-plan-cases-layout-grammar=\"1\"] .plan-case-detail-pane",
            1,
        )[1].split("}", 1)[0]
        self.assertIn("overflow: hidden", pane_rule)
        split_rule = css.split(
            "#plan-panel-cases[data-plan-cases-layout-grammar=\"1\"] .plan-cases-grammar-split",
            1,
        )[1].split("}", 1)[0]
        self.assertIn("align-items: stretch", split_rule)
        self.assertIn("grid-template-rows: minmax(0, 1fr)", split_rule)

        # JS focus chrome shows pin only when a case is focused.
        self.assertIn("function syncPlanCaseDetailFocusChrome", js)
        self.assertIn("data-plan-case-focused", js)
        self.assertIn("planCaseDetailLive", js)
        self.assertIn("planCaseDetailPin", js)

        # Other areas' compact checks must not regress.
        self.assertIn("settings-compact-check", html)
        self.assertIn("manual-compact-check", html)
        self.assertIn("ms-compact-check", html)
        self.assertIn("sec-compact-check", html)


if __name__ == "__main__":
    unittest.main()
