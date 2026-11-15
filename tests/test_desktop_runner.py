"""Desktop .exe smoke plugin (KAN-47 / FR-TEST-3 / FR-PLUG-2)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import desktop_runner  # noqa: E402
from plugins.desktop_runner import run_desktop, set_plugin_enabled  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class DesktopRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        self.settings.write_text("{}", encoding="utf-8")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_disabled_returns_graceful_message(self):
        set_plugin_enabled(False)
        result = run_desktop(exe_path=sys.executable)
        self.assertEqual(result["status"], "disabled")
        self.assertIn("enable", (result.get("message") or result.get("error") or "").lower())
        self.assertEqual(result.get("plugin"), "desktop_runner")

    def test_missing_path_fails(self):
        set_plugin_enabled(True)
        result = run_desktop(exe_path="")
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result.get("error"))

    def test_smoke_python_executable_passes(self):
        if sys.platform != "win32":
            self.skipTest("Windows-only plugin")
        set_plugin_enabled(True)
        # Short-lived CLI that exits 0 — valid smoke per harness contract.
        result = run_desktop(
            exe_path=sys.executable,
            timeout_s=2.0,
            args=["-c", "print('desktop-smoke-ok')"],
        )
        self.assertEqual(result["status"], "pass", result)
        self.assertEqual(result.get("plugin"), "desktop_runner")
        self.assertIn("desktop-smoke-ok", result.get("logs") or "")
        self.assertTrue(result.get("exe_path"))

    def test_uses_target_app_path_from_settings(self):
        if sys.platform != "win32":
            self.skipTest("Windows-only plugin")
        settings = load_settings()
        settings["plugin_desktop_enabled"] = True
        settings["target_app_path"] = sys.executable
        write_settings(settings)
        result = run_desktop(args=["-c", "print('from-settings')"], timeout_s=2.0)
        self.assertEqual(result["status"], "pass", result)
        self.assertIn("from-settings", result.get("logs") or "")

    def test_does_not_import_playwright_runner(self):
        """Smoke path must stay separate from Playwright (FR-TEST-3)."""
        import importlib

        # Drop cached playwright_runner if present so we can prove desktop does not load it.
        sys.modules.pop("plugins.playwright_runner", None)
        before = set(sys.modules)
        importlib.reload(desktop_runner)
        desktop_runner.run_desktop(exe_path="C:\\does\\not\\exist.exe")
        after = set(sys.modules)
        loaded = after - before
        self.assertFalse(
            any("playwright_runner" in name for name in loaded),
            f"desktop_runner pulled in playwright modules: {loaded}",
        )
        self.assertNotIn("plugins.playwright_runner", sys.modules)


if __name__ == "__main__":
    unittest.main()
