"""Multi-sandbox orchestration (KAN-55 / KAN-95 / FR-PLUG-1 / FR-PLUG-2)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.multi_sandbox import (  # noqa: E402
    MAX_SANDBOXES,
    orchestrate,
    set_plugin_enabled,
)
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

    def test_enabled_list_returns_configured_sandboxes(self):
        set_plugin_enabled(True)
        result = orchestrate(action="list")
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result.get("mode"), "local")
        self.assertGreaterEqual(len(result.get("sandboxes") or []), 1)
        first = result["sandboxes"][0]
        self.assertIn("url", first)
        self.assertIn("profile", first)
        self.assertIn("credentials_scope", first)
        self.assertIn("status", first)

    def test_enabled_plan_is_local_not_mock(self):
        set_plugin_enabled(True)
        result = orchestrate(action="plan")
        self.assertEqual(result["status"], "ok", result)
        plan = result.get("plan") or {}
        self.assertEqual(plan.get("mode"), "local")
        self.assertNotEqual(plan.get("mode"), "mock")
        self.assertTrue(plan.get("steps"))

    def test_upsert_persists_and_list_reflects_config(self):
        set_plugin_enabled(True)
        saved = orchestrate(
            action="upsert",
            sandbox_id="alpha",
            label="Alpha AUT",
            url="https://alpha.example",
        )
        self.assertEqual(saved["status"], "ok", saved)
        listed = orchestrate(action="list")
        self.assertEqual(listed["status"], "ok", listed)
        ids = [s["id"] for s in listed.get("sandboxes") or []]
        self.assertIn("alpha", ids)
        alpha = next(s for s in listed["sandboxes"] if s["id"] == "alpha")
        self.assertEqual(alpha["url"], "https://alpha.example")
        self.assertEqual(alpha["label"], "Alpha AUT")

    def test_prepare_creates_profile_dir(self):
        set_plugin_enabled(True)
        orchestrate(
            action="upsert",
            sandbox_id="prep1",
            label="Prep",
            url="https://prep.example",
        )
        prepared = orchestrate(action="prepare", sandbox_id="prep1")
        self.assertEqual(prepared["status"], "ok", prepared)
        self.assertIn("prep1", prepared.get("prepared") or [])
        box = next(s for s in prepared["sandboxes"] if s["id"] == "prep1")
        self.assertEqual(box["status"], "prepared")
        self.assertTrue(Path(box["profile"]).is_dir())

    def test_max_sandboxes_limit(self):
        set_plugin_enabled(True)
        listed = orchestrate(action="list")
        for s in list(listed.get("sandboxes") or []):
            orchestrate(action="remove", sandbox_id=s["id"])
        for i in range(MAX_SANDBOXES):
            r = orchestrate(
                action="upsert",
                sandbox_id=f"box{i}",
                label=f"Box {i}",
                url=f"https://box{i}.example",
            )
            self.assertEqual(r["status"], "ok", r)
        listed = orchestrate(action="list")
        self.assertEqual(len(listed.get("sandboxes") or []), MAX_SANDBOXES)
        overflow = orchestrate(
            action="upsert",
            sandbox_id="overflow",
            label="Too many",
            url="https://overflow.example",
        )
        self.assertEqual(overflow["status"], "error", overflow)
        self.assertIn("limit", (overflow.get("message") or "").lower())


if __name__ == "__main__":
    unittest.main()
