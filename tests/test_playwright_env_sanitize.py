"""KAN-495 — sanitize Cursor sandbox PLAYWRIGHT_BROWSERS_PATH for product runs."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PlaywrightEnvSanitizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
        else:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self._prev

    def test_clears_cursor_sandbox_cache(self) -> None:
        from plugins.playwright_env import sanitize_playwright_browsers_path

        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = (
            r"C:\Users\User\AppData\Local\Temp\cursor-sandbox-cache\abc\playwright"
        )
        out = sanitize_playwright_browsers_path()
        self.assertTrue(out.get("cleared"), out)
        self.assertEqual(out.get("reason"), "cursor_sandbox_cache")
        self.assertIsNone(os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))

    def test_clears_missing_chromium_override(self) -> None:
        from plugins.playwright_env import sanitize_playwright_browsers_path

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "browsers"
            empty.mkdir()
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(empty)
            out = sanitize_playwright_browsers_path()
        self.assertTrue(out.get("cleared"), out)
        self.assertEqual(out.get("reason"), "chromium_missing")

    def test_keeps_valid_override(self) -> None:
        from plugins.playwright_env import sanitize_playwright_browsers_path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chrome = root / "chromium-1255" / "chrome-win64" / "chrome.exe"
            chrome.parent.mkdir(parents=True)
            chrome.write_text("fake", encoding="utf-8")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(root)
            out = sanitize_playwright_browsers_path()
            self.assertFalse(out.get("cleared"), out)
            self.assertEqual(os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), str(root))

    def test_missing_browser_error_is_environment(self) -> None:
        from plans.run_case import _map_playwright_result

        result, cls, _ = _map_playwright_result(
            {
                "status": "fail",
                "error": (
                    "BrowserType.launch_persistent_context: Executable doesn't exist at "
                    r"C:\Temp\cursor-sandbox-cache\x\playwright\chromium-1255\chrome-win64\chrome.exe"
                    "\nPlease run playwright install"
                ),
                "steps": [],
            }
        )
        self.assertEqual(result, "error")
        self.assertEqual(cls, "environment")

    def test_desktop_app_imports_sanitize(self) -> None:
        text = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("sanitize_playwright_browsers_path", text)


if __name__ == "__main__":
    unittest.main()
