"""Import/run existing Playwright suites (KAN-59 / FR-TEST-5)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import playwright_suite as suite  # noqa: E402
from plugins.playwright_suite import (  # noqa: E402
    discover_suite,
    list_suite_tests,
    run_suite,
    set_suite_path,
    suite_status,
)
from settings.store import load_settings  # noqa: E402


def _make_project(root: Path, *, with_config: bool = True, with_spec: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps(
            {
                "name": "fixture-pw-suite",
                "devDependencies": {"@playwright/test": "^1.40.0"},
            }
        ),
        encoding="utf-8",
    )
    if with_config:
        (root / "playwright.config.ts").write_text(
            "import { defineConfig } from '@playwright/test';\n"
            "export default defineConfig({ testDir: './tests' });\n",
            encoding="utf-8",
        )
    if with_spec:
        tests = root / "tests"
        tests.mkdir(exist_ok=True)
        (tests / "smoke.spec.ts").write_text(
            "import { test, expect } from '@playwright/test';\n"
            "test('smoke', async ({ page }) => { await expect(page).toHaveURL(/.*/); });\n",
            encoding="utf-8",
        )
    return root


class PlaywrightSuiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        self.settings.write_text("{}", encoding="utf-8")
        self.project = _make_project(Path(self.tmp.name) / "pw-project")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_invalid_path_fails_clearly(self):
        result = discover_suite(suite_path=str(Path(self.tmp.name) / "missing"))
        self.assertEqual(result["status"], "fail")
        self.assertIn("not found", (result.get("error") or "").lower())
        self.assertNotEqual(result["status"], "pass")

    def test_empty_path_fails_without_settings(self):
        result = run_suite(suite_path="")
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result.get("error"))
        self.assertIn("suite path", (result.get("error") or "").lower())

    def test_discover_valid_project(self):
        result = discover_suite(suite_path=str(self.project))
        self.assertEqual(result["status"], "ok", result)
        self.assertTrue(result.get("config"))
        self.assertGreaterEqual(result.get("spec_count") or 0, 1)
        self.assertTrue(result.get("has_playwright_dep"))

    def test_import_saves_settings_path(self):
        result = set_suite_path(str(self.project), confirm=True)
        self.assertEqual(result["status"], "ok", result)
        settings = load_settings()
        self.assertEqual(
            Path(settings["playwright_suite_path"]).resolve(),
            self.project.resolve(),
        )
        status = suite_status()
        self.assertTrue(status.get("discovered"))

    def test_list_falls_back_to_filesystem(self):
        with patch.object(
            suite,
            "_npx_playwright",
            return_value={
                "ok": False,
                "error": "npx not found on PATH",
                "stdout": "",
                "stderr": "",
                "returncode": None,
            },
        ):
            result = list_suite_tests(suite_path=str(self.project))
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result.get("source"), "filesystem")
        titles = [t.get("file") or t.get("title") for t in result.get("tests") or []]
        self.assertTrue(any("smoke.spec.ts" in (t or "") for t in titles))

    def test_run_suite_parses_json_reporter(self):
        fake_json = json.dumps(
            {
                "stats": {
                    "expected": 1,
                    "unexpected": 0,
                    "skipped": 0,
                    "flaky": 0,
                },
                "suites": [
                    {
                        "title": "tests/smoke.spec.ts",
                        "specs": [
                            {
                                "title": "smoke",
                                "ok": True,
                                "file": "tests/smoke.spec.ts",
                                "tests": [
                                    {
                                        "results": [
                                            {
                                                "status": "passed",
                                                "attachments": [
                                                    {"path": "test-results/shot.png"}
                                                ],
                                            }
                                        ]
                                    }
                                ],
                            }
                        ],
                        "suites": [],
                    }
                ],
            }
        )

        def _fake_cli(args, cwd, timeout_s=300.0):
            self.assertIn("test", args)
            self.assertIn("--reporter=json", args)
            return {
                "ok": True,
                "error": None,
                "stdout": fake_json,
                "stderr": "",
                "returncode": 0,
            }

        with patch.object(suite, "_npx_playwright", side_effect=_fake_cli):
            result = run_suite(suite_path=str(self.project))
        self.assertEqual(result["status"], "pass", result)
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertTrue(result.get("evidence"))

    def test_run_suite_failed_tests_not_false_success(self):
        fake_json = json.dumps(
            {
                "stats": {"expected": 0, "unexpected": 1, "skipped": 0, "flaky": 0},
                "suites": [
                    {
                        "title": "tests/smoke.spec.ts",
                        "specs": [
                            {
                                "title": "smoke",
                                "ok": False,
                                "file": "tests/smoke.spec.ts",
                                "tests": [{"results": [{"status": "failed"}]}],
                            }
                        ],
                        "suites": [],
                    }
                ],
            }
        )
        with patch.object(
            suite,
            "_npx_playwright",
            return_value={
                "ok": True,
                "error": "exit 1",
                "stdout": fake_json,
                "stderr": "",
                "returncode": 1,
            },
        ):
            result = run_suite(suite_path=str(self.project))
        self.assertEqual(result["status"], "fail", result)
        self.assertEqual(result["failed"], 1)
        self.assertTrue(result.get("error"))


if __name__ == "__main__":
    unittest.main()
