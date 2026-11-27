"""KAN-379 / KAN-380 — OPERATE-3 loop-hit UI polish (Run disclosure, Manual idle, triage)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperateLoopPolishTests(unittest.TestCase):
    def test_operate3_markers_and_desk142(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk142", html)
        self.assertIn("desk142", desk)
        self.assertIn("desktop.css?v=desk142", html)
        self.assertIn("desktop.js?v=desk142", html)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertIn('data-operate-loop-polish="1"', plans)
        run = plans.split('id="plan-panel-run"', 1)[1]
        self.assertIn('data-operate-run-disclosure="1"', run)
        self.assertIn('data-operate-run-primary="1"', run)
        self.assertIn('id="plan-run-by-tag"', run)
        self.assertIn('id="plan-env-details"', run)
        self.assertIn('id="plan-sandbox-details"', run)
        self.assertIn('id="plan-parallel-details"', run)
        self.assertIn('id="plan-schedule-details"', run)

        # Primary run actions appear before advanced env disclosure.
        primary_at = run.find('data-operate-run-primary="1"')
        env_at = run.find('id="plan-env-details"')
        tag_at = run.find('id="plan-run-by-tag"')
        self.assertGreater(primary_at, -1)
        self.assertGreater(env_at, primary_at)
        self.assertGreater(tag_at, primary_at)
        self.assertLess(tag_at, env_at)

        # Env / sandbox / schedule live inside collapsed details (not forever-scroll).
        env_block = run[env_at : run.find('id="plan-sandbox-details"')]
        self.assertIn("<summary>", env_block)
        self.assertIn('id="plan-env-active"', env_block)

        cases = plans.split('id="plan-panel-cases"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0]
        self.assertIn('data-operate-evidence-affordance="1"', cases)
        self.assertIn('data-operate-triage-strip="1"', cases)
        self.assertIn('data-operate-heal-badge="1"', cases)
        self.assertIn('data-operate-open-heal="1"', cases)
        self.assertIn('data-operate-open-reports="1"', cases)
        self.assertIn('id="plan-run-failure-class"', cases)
        # Failure class sits in triage (near evidence), not buried only under Run sec.
        triage_at = cases.find('id="plan-case-triage-strip"')
        fail_at = cases.find('id="plan-run-failure-class"')
        self.assertGreater(triage_at, -1)
        self.assertGreater(fail_at, triage_at)
        run_sec = cases.split('data-plan-case-section="run"', 1)[1].split(
            'data-plan-case-section="quarantine"', 1
        )[0]
        self.assertNotIn('id="plan-run-failure-class"', run_sec)

        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        self.assertIn('data-manual-idle-split="1"', manual)
        self.assertIn('data-manual-idle-library="1"', manual)
        self.assertIn('data-manual-idle-start="1"', manual)
        self.assertIn('data-manual-idle-links="1"', manual)
        lib_at = manual.find('data-manual-idle-library="1"')
        start_at = manual.find('data-manual-idle-start="1"')
        self.assertGreater(lib_at, -1)
        self.assertGreater(start_at, lib_at)
        # Optional link fields collapsed behind disclosure; Start stays above.
        start_block = manual[start_at:]
        start_btn = start_block.find('id="manual-start"')
        links_at = start_block.find('data-manual-idle-links="1"')
        self.assertGreater(start_btn, -1)
        self.assertGreater(links_at, start_btn)
        self.assertIn('id="manual-plan-id"', start_block[links_at:])

        self.assertIn("function syncPlanCaseTriageStrip", js)
        self.assertIn("planTriageOpenHeal", js)
        self.assertIn('openArea("heal")', js)
        self.assertIn('openArea("reports")', js)
        self.assertIn("syncPlanCaseTriageStrip", js)

        self.assertIn("data-operate-run-disclosure", css)
        self.assertIn("data-operate-triage-strip", css)
        self.assertIn("data-manual-idle-split", css)
        self.assertIn(".plan-run-primary", css)
        self.assertIn(".plan-case-triage-strip", css)
        self.assertIn(".plan-triage-heal-badge", css)


if __name__ == "__main__":
    unittest.main()
