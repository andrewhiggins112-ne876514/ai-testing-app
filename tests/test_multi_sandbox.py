"""Multi-sandbox orchestration stub (KAN-55 / FR-PLUG-1 / FR-PLUG-2)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.multi_sandbox import orchestrate, set_plugin_enabled  # noqa: E402
from plugins.registry import get_plugin, list_plugins  # noqa: E402


class MultiSandboxTests(unittest.TestCase):
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

    def test_registry_lists_multi_sandbox_default_off(self):
        payload = list_plugins()
        ids = [p["id"] for p in payload["plugins"]]
        self.assertIn("multi_sandbox", ids)
        ms = get_plugin("multi_sandbox")
        self.assertIsNotNone(ms)
        assert ms is not None
        self.assertFalse(ms["enabled"])
        self.assertEqual(ms["toggle_key"], "plugin_multi_sandbox_enabled")
        self.assertTrue(ms["toggleable"])

    def test_disabled_orchestrate_returns_not_enabled(self):
        set_plugin_enabled(False)
        result = orchestrate(action="list")
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(result.get("plugin"), "multi_sandbox")
        msg = (result.get("message") or result.get("error") or "").lower()
        self.assertTrue("enable" in msg or "disabled" in msg)

    def test_enabled_list_returns_stub_sandboxes(self):
        set_plugin_enabled(True)
        result = orchestrate(action="list")
        self.assertEqual(result["status"], "ok", result)
        self.assertGreaterEqual(len(result.get("sandboxes") or []), 1)
        first = result["sandboxes"][0]
        self.assertIn("url", first)
        self.assertIn("profile", first)
        self.assertIn("credentials_scope", first)

    def test_enabled_plan_is_mock_only(self):
        set_plugin_enabled(True)
        result = orchestrate(action="plan")
        self.assertEqual(result["status"], "ok", result)
        plan = result.get("plan") or {}
        self.assertEqual(plan.get("mode"), "mock")
        self.assertTrue(plan.get("steps"))


if __name__ == "__main__":
    unittest.main()
