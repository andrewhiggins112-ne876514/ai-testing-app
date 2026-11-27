"""KAN-496 / KAN-497 — Option A readable run steps + evidence gallery."""
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
    build_step_outcomes_from_playwright,
    honest_empty_reason,
    human_step_label,
    normalize_step_outcomes,
    representative_screenshot,
)
from plans.store import add_case, add_run, create_plan, get_plan  # noqa: E402
from plugins.evidence_shot import resolve_allowed_shot  # noqa: E402
from settings.store import write_settings  # noqa: E402


class StepOutcomeHelpersTests(unittest.TestCase):
    def test_human_labels_are_plain_language(self) -> None:
        self.assertEqual(
            human_step_label({"action": "goto", "value": "https://shop.fixture.local/guest"}),
            "Open /guest",
        )
        self.assertEqual(
            human_step_label({"action": "click", "selector": "Add oak lamp"}),
            "Click Add oak lamp",
        )
        self.assertIn("Expect", human_step_label({"action": "expect_text", "value": "Order placed"}))

    def test_normalize_merges_definitions(self) -> None:
        outcomes = normalize_step_outcomes(
            [{"action": "goto", "status": "pass", "duration_ms": 120}],
            definitions=[{"action": "goto", "value": "https://example.test/a"}],
        )
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["label"], "Open /a")
        self.assertEqual(outcomes[0]["status"], "pass")
        self.assertEqual(outcomes[0]["duration_ms"], 120)

    def test_honest_empty_never_fake_green(self) -> None:
        reason = honest_empty_reason(
            {"result": "fail", "note": "page closed", "evidence": []},
            case_tags=["smoke"],
        )
        self.assertIn("None captured", reason)
        self.assertIn("not substituted", reason)
        self.assertIn("page closed", reason)
        self.assertEqual(
            representative_screenshot({"evidence": ["C:/x/trace.zip", "C:/x/shot.png"]}),
            "C:/x/shot.png",
        )

    def test_build_from_playwright(self) -> None:
        out = build_step_outcomes_from_playwright(
            {
                "steps": [
                    {"action": "click", "selector": "#pay", "status": "fail", "error": "missing"},
                ]
            }
        )
        self.assertEqual(out[0]["status"], "fail")
        self.assertEqual(out[0]["error"], "missing")
        self.assertIn("Click", out[0]["label"])


class RunEvidencePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self) -> None:
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_add_run_persists_step_outcomes(self) -> None:
        created = create_plan("Evidence plan", intent="demo")
        self.assertEqual(created["status"], "ok", created)
        pid = created["plan"]["id"]
        case = add_case(pid, "Guest checkout", tags=["smoke"])["case"]
        steps = normalize_step_outcomes(
            [
                {"action": "goto", "value": "https://shop.fixture.local/guest", "status": "pass"},
                {
                    "action": "expect_text",
                    "value": "Order placed",
                    "status": "pass",
                    "duration_ms": 40,
                },
            ]
        )
        recorded = add_run(
            pid,
            case["id"],
            result="pass",
            duration_ms=1800,
            evidence=[str(Path(self.tmp.name) / "ok.png")],
            step_outcomes=steps,
        )
        self.assertEqual(recorded["status"], "ok", recorded)
        run = recorded["run"]
        self.assertEqual(len(run["step_outcomes"]), 2)
        self.assertEqual(run["step_outcomes"][0]["label"], "Open /guest")
        loaded = get_plan(pid)
        detail = case_detail(loaded["plan"], case["id"])
        self.assertEqual(detail["status"], "ok")
        self.assertEqual(len(detail["last_run"]["step_outcomes"]), 2)
        self.assertTrue(str(detail["evidence_shot"]).endswith("ok.png"))


class RunEvidenceUiContractTests(unittest.TestCase):
    def test_option_a_markers_desk145(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk145", html)
        self.assertIn("desk145", desk)
        self.assertIn("desktop.css?v=desk145", html)
        self.assertIn("desktop.js?v=desk145", html)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        live = plans.split('id="plan-case-detail-live"', 1)[1]
        self.assertIn('data-run-story="1"', live)
        self.assertIn("data-run-story-steps", live)
        self.assertIn("data-run-story-thumb", live)
        self.assertIn("data-run-story-none", live)
        self.assertIn("None captured", live)
        self.assertIn('data-evidence-first="1"', live)
        self.assertLess(
            live.find("plan-case-evidence-first"),
            live.find('data-plan-case-section="edit"'),
        )
        self.assertIn("fillPlanRunStory", js)
        self.assertIn("openPlanRunEvidenceDeep", js)
        self.assertIn("step_outcomes", js)
        self.assertIn(".run-story-steps", css)
        self.assertIn(".run-story-none", css)
        self.assertNotIn("fake green", css.lower())


class EvidenceShotApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "ai_testing_app"
        self.shots = self.root / "screenshots"
        self.shots.mkdir(parents=True)
        self.shot = self.shots / "cap.png"
        self.shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
        self._env = mock.patch.dict("os.environ", {"LOCALAPPDATA": str(self.tmp.name)})
        self._env.start()
        self.addCleanup(self._env.stop)
        self.client = TestClient(app)

    def test_resolve_allows_screenshots_root(self) -> None:
        path, err = resolve_allowed_shot(str(self.shot))
        self.assertIsNone(err)
        self.assertEqual(path, self.shot.resolve())

    def test_open_validate_ok(self) -> None:
        res = self.client.post(
            "/api/evidence-shot/open",
            json={"path": str(self.shot), "action": "validate", "launch": False},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("ok"))

    def test_open_rejects_outside(self) -> None:
        outside = Path(self.tmp.name) / "other.png"
        outside.write_bytes(b"x")
        res = self.client.post(
            "/api/evidence-shot/open",
            json={"path": str(outside), "action": "validate", "launch": False},
        )
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
