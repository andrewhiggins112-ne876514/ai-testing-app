"""Desktop .exe plugin (KAN-47 smoke + KAN-87 structured steps / FR-TEST-3)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import desktop_runner  # noqa: E402
from plugins.desktop_runner import (  # noqa: E402
    SUPPORTED_ACTIONS,
    demo_notepad_steps,
    run_desktop,
    set_plugin_enabled,
)
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

    def test_disabled_steps_returns_enable_message(self):
        set_plugin_enabled(False)
        result = run_desktop(
            exe_path=sys.executable,
            steps=[{"action": "wait", "seconds": 0.1}],
        )
        self.assertEqual(result["status"], "disabled")
        self.assertIn("enable", (result.get("message") or result.get("error") or "").lower())

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

    def test_unsupported_step_fails_clearly(self):
        if sys.platform != "win32":
            self.skipTest("Windows-only plugin")
        set_plugin_enabled(True)
        result = run_desktop(
            exe_path=sys.executable,
            steps=[{"action": "click_button", "value": "OK"}],
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("Unsupported", result.get("error") or "")
        self.assertTrue(result.get("steps"))
        self.assertEqual(result["steps"][0]["status"], "fail")

    def test_wait_step_passes(self):
        if sys.platform != "win32":
            self.skipTest("Windows-only plugin")
        set_plugin_enabled(True)
        result = run_desktop(
            exe_path=sys.executable,
            args=["-c", "import time; time.sleep(2)"],
            steps=[{"action": "wait", "seconds": 0.2}, {"action": "close"}],
            timeout_s=3.0,
        )
        self.assertEqual(result["status"], "pass", result)
        actions = [s["action"] for s in result.get("steps") or []]
        self.assertIn("wait", actions)
        self.assertIn("close", actions)

    def test_notepad_wait_window_and_type(self):
        if sys.platform != "win32":
            self.skipTest("Windows-only plugin")
        notepad = Path(r"C:\Windows\System32\notepad.exe")
        if not notepad.is_file():
            self.skipTest("notepad.exe not found")
        set_plugin_enabled(True)
        result = run_desktop(
            exe_path=str(notepad),
            timeout_s=8.0,
            steps=demo_notepad_steps(),
        )
        self.assertEqual(result["status"], "pass", result)
        actions = [s["action"] for s in result.get("steps") or []]
        self.assertIn("wait_window", actions)
        self.assertIn("type_text", actions)
        for step in result["steps"]:
            self.assertEqual(step["status"], "pass", step)

    def test_supported_actions_documented(self):
        self.assertIn("wait_window", SUPPORTED_ACTIONS)
        self.assertIn("type_text", SUPPORTED_ACTIONS)
        self.assertIn("launch", SUPPORTED_ACTIONS)


if __name__ == "__main__":
    unittest.main()
