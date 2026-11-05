"""Orb config defaults and settings save/load. Uses a temp settings file."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("gradio_orb_under_test", ROOT / "ui" / "gradio_app.py")
gradio_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gradio_app)

from settings.store import load_settings  # noqa: E402


class OrbConfigTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)

    def tearDown(self):
        self.tmp.cleanup()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old

    def test_defaults_when_settings_missing(self):
        self.assertEqual(gradio_app.current_orb_config(), gradio_app.ORB_DEFAULTS)
        data = load_settings()
        self.assertEqual(data["orb_style"], "lightning")
        self.assertEqual(data["orb_calm_color"], "#50cdff")
        self.assertEqual(data["orb_thinking_color"], "#b388ff")
        self.assertEqual(data["orb_size"], 360)

    def test_defaults_fill_when_keys_missing(self):
        self.path.write_text('{"security_level": "OFFICIAL"}\n', encoding="utf-8")
        cfg = gradio_app.current_orb_config()
        self.assertEqual(cfg["style"], "lightning")
        self.assertEqual(cfg["calm_color"], "#50cdff")
        self.assertEqual(cfg["thinking_color"], "#b388ff")
        self.assertEqual(cfg["size"], 360)

    def test_invalid_values_fall_back(self):
        cfg = gradio_app.normalize_orb_config({
            "style": "plasma",
            "calm_color": "red",
            "thinking_color": "#gg0000",
            "size": 9999,
        })
        self.assertEqual(cfg["style"], "lightning")
        self.assertEqual(cfg["calm_color"], "#50cdff")
        self.assertEqual(cfg["thinking_color"], "#b388ff")
        self.assertEqual(cfg["size"], 480)
        low = gradio_app.normalize_orb_config({
            "style": "mist",
            "calm_color": "#AABBCC",
            "thinking_color": "#112233",
            "size": 10,
        })
        self.assertEqual(low["style"], "mist")
        self.assertEqual(low["calm_color"], "#aabbcc")
        self.assertEqual(low["thinking_color"], "#112233")
        self.assertEqual(low["size"], 200)
        self.assertEqual(
            gradio_app.normalize_orb_config({"style": "nebula+lightning", "size": "280"})["style"],
            "nebula+lightning",
        )

    def test_save_then_load(self):
        markup = gradio_app.save_orb_config("nebula+lightning", "#ff00aa", "#00ffcc", 280)
        self.assertIn('data-style="nebula+lightning"', markup)
        self.assertIn('data-calm-color="#ff00aa"', markup)
        self.assertIn('data-thinking-color="#00ffcc"', markup)
        self.assertIn('data-size="280"', markup)
        self.assertIn('id="orb-config"', markup)
        saved = load_settings()
        self.assertEqual(saved["orb_style"], "nebula+lightning")
        self.assertEqual(saved["orb_calm_color"], "#ff00aa")
        self.assertEqual(saved["orb_thinking_color"], "#00ffcc")
        self.assertEqual(saved["orb_size"], 280)
        self.assertIsInstance(saved["orb_size"], int)
        self.assertEqual(gradio_app.current_orb_config(), {
            "style": "nebula+lightning",
            "calm_color": "#ff00aa",
            "thinking_color": "#00ffcc",
            "size": 280,
        })
        for key in ("orb_style", "orb_calm_color", "orb_thinking_color", "orb_size"):
            self.assertNotIn("token", key)
            self.assertNotIn("password", key)
            self.assertNotIn("secret", key)
            self.assertNotIn("credential", key)

    def test_save_invalid_falls_back_in_store(self):
        gradio_app.save_orb_config("nope", "blue", "#b388ff", "nope")
        saved = load_settings()
        self.assertEqual(saved["orb_style"], "lightning")
        self.assertEqual(saved["orb_calm_color"], "#50cdff")
        self.assertEqual(saved["orb_thinking_color"], "#b388ff")
        self.assertEqual(saved["orb_size"], 360)


if __name__ == "__main__":
    unittest.main()
