"""KAN-354 / KAN-355 — TRACK5 Phase 2 evidence-first detail slot (updated KAN-372 copy)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Track5EvidenceFirstDetailTests(unittest.TestCase):
    def test_evidence_first_detail_markers_desk158(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk158", html)
        self.assertIn("desk158", desk)
        self.assertIn("desktop.css?v=desk158", html)
        self.assertIn("desktop.js?v=desk158", html)

        reports = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        heal = html.split('id="app-section-heal"', 1)[1].split(
            'id="app-section-desktop"', 1
        )[0]
        desktop = html.split('id="app-section-desktop"', 1)[1].split(
            'id="app-section-plans"', 1
        )[0]
        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        suites = html.split('id="app-section-suites"', 1)[1].split(
            'id="app-section-sandboxes"', 1
        )[0]
        documents = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]
        sandboxes = html.split('id="app-section-sandboxes"', 1)[1].split(
            'id="app-drawer-toggle"', 1
        )[0]
        settings = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        security = html.split('id="app-section-security"', 1)[1].split(
            'id="app-section-reports"', 1
        )[0]

        for block, name in (
            (reports, "reports"),
            (heal, "heal"),
            (desktop, "desktop"),
            (plans, "plans"),
            (manual, "manual"),
            (suites, "suites"),
        ):
            with self.subTest(area=name):
                self.assertIn('data-evidence-first-detail="1"', block)
                self.assertIn('data-evidence-first="1"', block)
                self.assertIn('data-playwright-trace="1"', block)
                self.assertIn("no Playwright trace for this run", block)
                self.assertNotIn("not hooked", block)
                self.assertNotIn("not a Playwright trace", block)
                self.assertIn("not OCR-redacted", block)
                # Open control is injected by JS when a real .zip path is present.
                self.assertNotIn('id="trace-run"', block)

        # Evidence slot precedes edit fields on run-bearing details.
        rpt_detail = reports.split('id="rpt-detail"', 1)[1]
        self.assertLess(
            rpt_detail.find("rpt-evidence-first"),
            rpt_detail.find('id="rpt-markdown"'),
        )
        heal_detail = heal.split('id="heal-detail"', 1)[1]
        self.assertLess(
            heal_detail.find("heal-evidence-first"),
            heal_detail.find('id="heal-detail-id"'),
        )
        plan_live = plans.split('id="plan-case-detail-live"', 1)[1]
        self.assertLess(
            plan_live.find("plan-case-evidence-first"),
            plan_live.find('data-plan-case-section="edit"'),
        )
        manual_detail = manual.split('id="manual-detail"', 1)[1]
        self.assertLess(
            manual_detail.find("manual-evidence-first"),
            manual_detail.find('id="manual-detail-charter"'),
        )
        suite_detail = suites.split('id="suite-detail"', 1)[1]
        self.assertLess(
            suite_detail.find("suite-evidence-first"),
            suite_detail.find('id="suite-detail-name"'),
        )
        desk_detail = desktop.split('id="desk-detail"', 1)[1]
        self.assertLess(
            desk_detail.find("desk-evidence-first"),
            desk_detail.find('id="desk-exe"'),
        )

        # Optional areas: slot present but marked optional (absent until evidence).
        for block, marker_id in (
            (documents, "doc-evidence-first"),
            (settings, "set-env-evidence-first"),
            (security, "sec-audit-evidence-first"),
            (sandboxes, "ms-evidence-first"),
        ):
            with self.subTest(optional=marker_id):
                self.assertIn(marker_id, block)
                self.assertIn('data-evidence-first-optional="1"', block)

        self.assertIn("fillEvidenceFirst", js)
        self.assertIn("hideEvidenceFirst", js)
        self.assertIn("EVIDENCE_TRACE_CAPTURED", js)
        self.assertIn("EVIDENCE_TRACE_NONE", js)
        self.assertIn("Open Playwright Trace", js)
        self.assertIn("/api/playwright-trace/open", js)
        self.assertNotIn("not hooked yet", js)
        self.assertIn("not OCR-redacted", js)
        self.assertIn(".evidence-first", css)
        self.assertIn("desk158", desk)


if __name__ == "__main__":
    unittest.main()
