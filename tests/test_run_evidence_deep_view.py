"""KAN-498 / KAN-499 — Plans run-evidence deep view (frames 05–07)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from plans.run_case import case_detail  # noqa: E402
from plans.step_outcomes import (  # noqa: E402
    deep_view_captured_pages,
    run_allows_shot_path,
)
from plans.store import add_case, add_run, create_plan, get_plan  # noqa: E402
from settings.store import write_settings  # noqa: E402


class DeepViewHelpersTests(unittest.TestCase):
    def test_one_png_attaches_to_fail_step(self) -> None:
        run = {
            "result": "fail",
            "evidence": [r"C:\shots\fail.png", r"C:\shots\trace.zip"],
            "step_outcomes": [
                {"action": "goto", "status": "pass", "label": "Open /bag"},
                {
                    "action": "expect_visible",
                    "status": "fail",
                    "label": "Expect Pay visible",
                    "error": "missing",
                },
            ],
        }
        pages = deep_view_captured_pages(run, case_tags=["smoke"])
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["step_index"], 2)
        self.assertTrue(pages[0]["path"].endswith("fail.png"))
        self.assertTrue(run_allows_shot_path(run, pages[0]["path"]))
        self.assertFalse(run_allows_shot_path(run, r"C:\shots\other.png"))

    def test_per_step_shots_and_omit_empty(self) -> None:
        run = {
            "result": "pass",
            "evidence": [r"C:\a.png", r"C:\b.png"],
            "step_outcomes": [
                {
                    "action": "goto",
                    "status": "pass",
                    "screenshot": r"C:\a.png",
                    "label": "Open /guest",
                },
                {"action": "fill", "status": "pass", "label": "Fill qty"},
                {
                    "action": "expect_text",
                    "status": "pass",
                    "screenshot": r"C:\b.png",
                    "label": 'Expect "Order placed"',
                },
            ],
        }
        pages = deep_view_captured_pages(run, case_tags=["smoke"])
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["step_index"], 1)
        self.assertEqual(pages[1]["step_index"], 3)

    def test_success_shots_off_hides_pass_pngs_for_non_smoke(self) -> None:
        run = {
            "result": "pass",
            "evidence": [r"C:\ok.png"],
            "step_outcomes": [
                {
                    "action": "goto",
                    "status": "pass",
                    "screenshot": r"C:\ok.png",
                    "label": "Open /x",
                }
            ],
        }
        hidden = deep_view_captured_pages(
            run, case_tags=["regression"], success_shots_enabled=False
        )
        self.assertEqual(hidden, [])
        shown = deep_view_captured_pages(
            run, case_tags=["smoke"], success_shots_enabled=False
        )
        self.assertEqual(len(shown), 1)

    def test_zero_png_returns_empty_strip(self) -> None:
        run = {
            "result": "fail",
            "evidence": [r"C:\trace.zip"],
            "step_outcomes": [
                {"action": "click", "status": "fail", "error": "boom"},
            ],
        }
        self.assertEqual(deep_view_captured_pages(run), [])


class DeepViewPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "classic"})

    def tearDown(self) -> None:
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_case_detail_includes_captured_pages(self) -> None:
        created = create_plan("Deep view plan", intent="demo")
        pid = created["plan"]["id"]
        case = add_case(pid, "Pay missing", tags=["smoke"])["case"]
        shot = str(Path(self.tmp.name) / "fail.png")
        Path(shot).write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 16)
        add_run(
            pid,
            case["id"],
            result="fail",
            duration_ms=2400,
            failure_class="product_bug",
            evidence=[shot, str(Path(self.tmp.name) / "trace.zip")],
            step_outcomes=[
                {"action": "goto", "status": "pass", "label": "Open /bag"},
                {
                    "action": "expect_visible",
                    "status": "fail",
                    "label": "Expect Pay",
                    "error": "missing",
                },
            ],
        )
        loaded = get_plan(pid)
        detail = case_detail(loaded["plan"], case["id"])
        self.assertEqual(detail["status"], "ok")
        pages = detail["evidence_captured_pages"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["step_index"], 2)


class DeepViewUiContractTests(unittest.TestCase):
    def test_deep_view_markers_desk146(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk146", html)
        self.assertIn("desk146", desk)
        self.assertIn("desktop.css?v=desk146", html)
        self.assertIn("desktop.js?v=desk146", html)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertIn('data-run-evidence-deep="1"', plans)
        self.assertIn("data-run-story-more", plans)
        self.assertIn("More evidence", plans)
        self.assertIn("data-run-story-open-deep", plans)
        self.assertIn("plan-run-evidence-deep", plans)
        self.assertIn("data-run-deep-back", plans)
        self.assertIn("Back to case", plans)
        self.assertIn("data-run-deep-strip", plans)
        self.assertIn("Captured pages only", plans)
        self.assertIn("network / console / dom", plans.lower())
        self.assertNotIn("trace.playwright.dev", plans.lower())
        self.assertNotIn('data-plan-panel="evidence"', html)

        self.assertIn("openPlanRunEvidenceDeep", js)
        self.assertIn("closePlanRunEvidenceDeep", js)
        self.assertIn("focusPlanDeepView", js)
        self.assertIn("evidence_captured_pages", js)
        self.assertIn(".plan-run-evidence-deep", css)
        self.assertIn("data-run-evidence-deep-open", css)


class DeepViewScreenshotApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "ai_testing_app"
        self.shots = self.root / "screenshots"
        self.shots.mkdir(parents=True)
        self.shot = self.shots / "cap.png"
        self.shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL"})
        self._env = mock.patch.dict(
            "os.environ",
            {
                "LOCALAPPDATA": str(self.tmp.name),
                "AI_TESTING_SETTINGS": str(self.settings),
            },
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.addCleanup(self._restore_settings)
        self.client = TestClient(app)

    def _restore_settings(self) -> None:
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old

    def test_path_query_serves_run_png(self) -> None:
        created = create_plan("Shot plan", intent="demo")
        pid = created["plan"]["id"]
        case = add_case(pid, "Case", tags=["smoke"])["case"]
        recorded = add_run(
            pid,
            case["id"],
            result="pass",
            evidence=[str(self.shot)],
            step_outcomes=[{"action": "goto", "status": "pass"}],
        )
        run_id = recorded["run"]["id"]
        res = self.client.get(
            f"/api/plans/{pid}/cases/{case['id']}/runs/{run_id}/screenshot",
            params={"path": str(self.shot)},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"\x89PNG"))

    def test_path_query_rejects_foreign_png(self) -> None:
        created = create_plan("Shot plan 2", intent="demo")
        pid = created["plan"]["id"]
        case = add_case(pid, "Case", tags=["smoke"])["case"]
        recorded = add_run(
            pid,
            case["id"],
            result="pass",
            evidence=[str(self.shot)],
            step_outcomes=[{"action": "goto", "status": "pass"}],
        )
        run_id = recorded["run"]["id"]
        other = self.shots / "other.png"
        other.write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 32)
        res = self.client.get(
            f"/api/plans/{pid}/cases/{case['id']}/runs/{run_id}/screenshot",
            params={"path": str(other)},
        )
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
