"""Import Playwright project into in-app suite (KAN-171 / C8 / FR-TEST-5 / FR-PLAN-2)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from plans.import_playwright import (  # noqa: E402
    decode_playwright_ref,
    encode_playwright_ref,
    import_playwright_project,
)
from plans.run_case import run_single_case  # noqa: E402
from plans.store import get_plan  # noqa: E402
from settings.store import write_settings  # noqa: E402


def _make_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps(
            {
                "name": "fixture-pw-import",
                "devDependencies": {"@playwright/test": "^1.40.0"},
            }
        ),
        encoding="utf-8",
    )
    (root / "playwright.config.ts").write_text(
        "import { defineConfig } from '@playwright/test';\n"
        "export default defineConfig({ testDir: './tests' });\n",
        encoding="utf-8",
    )
    tests = root / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "smoke.spec.ts").write_text(
        "import { test, expect } from '@playwright/test';\n"
        "test('smoke', async ({ page }) => { await expect(page).toHaveURL(/.*/); });\n",
        encoding="utf-8",
    )
    (tests / "login.spec.ts").write_text(
        "import { test, expect } from '@playwright/test';\n"
        "test('login happy', async ({ page }) => { await expect(page).toHaveURL(/.*/); });\n",
        encoding="utf-8",
    )
    return root


class PlanImportPlaywrightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})
        self.project = _make_project(Path(self.tmp.name) / "pw-project")
        self.marker = self.project / "KEEP_ME.txt"
        self.marker.write_text("do not delete", encoding="utf-8")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_encode_decode_ref_roundtrip(self):
        ref = encode_playwright_ref(
            suite_path=str(self.project),
            file="tests/smoke.spec.ts",
            title="smoke",
            grep="smoke",
        )
        decoded = decode_playwright_ref(ref)
        self.assertEqual(decoded["file"], "tests/smoke.spec.ts")
        self.assertEqual(decoded["title"], "smoke")
        self.assertEqual(decoded["grep"], "smoke")
        self.assertTrue(decoded["suite_path"])

    def test_import_creates_plan_cases_without_deleting_files(self):
        out = import_playwright_project(suite_path=str(self.project))
        self.assertEqual(out["status"], "ok", out)
        self.assertFalse(out.get("external_files_deleted"))
        self.assertTrue(out.get("npx_suite_unchanged"))
        self.assertTrue(self.marker.exists())
        self.assertTrue((self.project / "tests" / "smoke.spec.ts").exists())
        plan = out["plan"]
        cases = plan["suite"]["cases"]
        self.assertGreaterEqual(len(cases), 1)
        kinds = {c["source"]["kind"] for c in cases}
        self.assertEqual(kinds, {"playwright"})
        self.assertIn(str(self.project.resolve()), plan["sources"].get("playwright_suites") or [])

    def test_import_into_existing_plan_skips_duplicates(self):
        first = import_playwright_project(suite_path=str(self.project))
        pid = first["plan"]["id"]
        count1 = len(first["plan"]["suite"]["cases"])
        second = import_playwright_project(suite_path=str(self.project), plan_id=pid)
        self.assertEqual(second["status"], "ok", second)
        self.assertEqual(second.get("cases_added"), 0)
        self.assertGreaterEqual(second.get("cases_skipped_duplicate"), 1)
        reloaded = get_plan(pid)["plan"]
        self.assertEqual(len(reloaded["suite"]["cases"]), count1)

    def test_invalid_path_fails_clearly(self):
        missing = Path(self.tmp.name) / "missing-pw"
        out = import_playwright_project(suite_path=str(missing))
        self.assertNotEqual(out["status"], "ok")
        self.assertFalse(out.get("external_files_deleted"))

    def test_run_imported_case_uses_playwright_suite(self):
        out = import_playwright_project(suite_path=str(self.project))
        self.assertEqual(out["status"], "ok", out)
        plan = out["plan"]
        case = plan["suite"]["cases"][0]
        fake = {
            "status": "pass",
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "evidence": [],
            "message": "ok",
            "playwright_mode": "headed",
            "suite_path": str(self.project),
        }
        with patch("plugins.playwright_suite.run_suite", return_value=fake) as mocked:
            result = asyncio.run(run_single_case(plan["id"], case["id"]))
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result.get("runner"), "playwright_suite")
        self.assertEqual(result["run"]["result"], "pass")
        mocked.assert_called_once()
        kwargs = mocked.call_args.kwargs
        self.assertTrue(kwargs.get("suite_path"))

    def test_api_import_playwright(self):
        client = TestClient(main.app)
        res = client.post(
            "/api/plans/import-playwright",
            json={"suite_path": str(self.project)},
        )
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(payload["status"], "ok", payload)
        self.assertFalse(payload.get("external_files_deleted"))
        self.assertGreaterEqual(payload.get("cases_added"), 1)

    def test_desktop_ui_has_import_controls_desk60(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk60", html)
        self.assertIn("desk60", desk)
        self.assertIn("plan-pw-path", html)
        self.assertIn("plan-import-pw-btn", html)
        self.assertIn("plan-import-pw-add-btn", html)
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("/api/plans/import-playwright", js)


if __name__ == "__main__":
    unittest.main()
