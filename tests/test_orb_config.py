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
        self.assertEqual(data["orb_shape"], "sphere")
        self.assertEqual(data["orb_spin_speed"], 1.0)
        self.assertEqual(data["orb_turbulence"], 1.0)
        self.assertEqual(data["orb_pulse"], 1.0)
        self.assertEqual(data["orb_glow"], 1.0)

    def test_defaults_fill_when_keys_missing(self):
        self.path.write_text('{"security_level": "OFFICIAL"}\n', encoding="utf-8")
        cfg = gradio_app.current_orb_config()
        self.assertEqual(cfg["style"], "lightning")
        self.assertEqual(cfg["calm_color"], "#50cdff")
        self.assertEqual(cfg["thinking_color"], "#b388ff")
        self.assertEqual(cfg["size"], 360)
        self.assertEqual(cfg["shape"], "sphere")
        self.assertEqual(cfg["spin_speed"], 1.0)
        self.assertEqual(cfg["turbulence"], 1.0)
        self.assertEqual(cfg["pulse"], 1.0)
        self.assertEqual(cfg["glow"], 1.0)

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
        clamped = gradio_app.normalize_orb_config({
            "shape": "cube",
            "spin_speed": -1,
            "turbulence": 9,
            "pulse": "nope",
            "glow": 2.4,
        })
        self.assertEqual(clamped["shape"], "sphere")
        self.assertEqual(clamped["spin_speed"], 0.0)
        self.assertEqual(clamped["turbulence"], 2.0)
        self.assertEqual(clamped["pulse"], 1.0)
        self.assertEqual(clamped["glow"], 2.0)
        allowed = gradio_app.normalize_orb_config({
            "shape": "ring",
            "spin_speed": 0,
            "turbulence": "1.5",
            "pulse": 2,
            "glow": 0.25,
        })
        self.assertEqual(allowed["shape"], "ring")
        self.assertEqual(allowed["spin_speed"], 0.0)
        self.assertEqual(allowed["turbulence"], 1.5)
        self.assertEqual(allowed["pulse"], 2.0)
        self.assertEqual(allowed["glow"], 0.25)

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
            "shape": "sphere",
            "spin_speed": 1.0,
            "turbulence": 1.0,
            "pulse": 1.0,
            "glow": 1.0,
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
        self.assertEqual(saved["orb_shape"], "sphere")
        self.assertEqual(saved["orb_spin_speed"], 1.0)

    def test_shape_and_intensity_save_load(self):
        markup = gradio_app.save_orb_config(
            "mist", "#50cdff", "#b388ff", 360, "oval", 0, 2, 0.5, 1.5
        )
        self.assertIn('data-shape="oval"', markup)
        self.assertIn('data-spin-speed="0.0"', markup)
        self.assertIn('data-turbulence="2.0"', markup)
        self.assertIn('data-pulse="0.5"', markup)
        self.assertIn('data-glow="1.5"', markup)
        saved = load_settings()
        self.assertEqual(saved["orb_shape"], "oval")
        self.assertEqual(saved["orb_spin_speed"], 0.0)
        self.assertEqual(saved["orb_turbulence"], 2.0)
        self.assertEqual(saved["orb_pulse"], 0.5)
        self.assertEqual(saved["orb_glow"], 1.5)
        self.assertEqual(gradio_app.current_orb_config()["shape"], "oval")
        bad = gradio_app.save_orb_config("lightning", "#50cdff", "#b388ff", 360, "square", -4, 8, "x", 3)
        self.assertIn('data-shape="sphere"', bad)
        reloaded = load_settings()
        self.assertEqual(reloaded["orb_shape"], "sphere")
        self.assertEqual(reloaded["orb_spin_speed"], 0.0)
        self.assertEqual(reloaded["orb_turbulence"], 2.0)
        self.assertEqual(reloaded["orb_pulse"], 1.0)
        self.assertEqual(reloaded["orb_glow"], 2.0)

    def test_preset_save_load_delete(self):
        markup, dropdown, status = gradio_app.save_orb_preset(
            "Calm Blue", "mist", "#112233", "#445566", 240, "oval", 0.5, 1.2, 0.8, 1.1
        )
        self.assertIn("Saved preset 'Calm Blue'", status)
        self.assertIn('data-style="mist"', markup)
        self.assertEqual(gradio_app.list_orb_preset_names(), ["Calm Blue"])
        saved = load_settings()
        self.assertEqual(saved["orb_active_preset"], "Calm Blue")
        self.assertEqual(saved["orb_presets"]["Calm Blue"]["shape"], "oval")
        self.assertEqual(saved["orb_style"], "mist")

        gradio_app.save_orb_config("lightning", "#50cdff", "#b388ff", 360, "sphere", 1, 1, 1, 1)
        loaded = gradio_app.load_orb_preset("Calm Blue")
        self.assertIn("Loaded preset 'Calm Blue'", loaded[-1])
        self.assertEqual(loaded[1], "mist")
        self.assertEqual(loaded[5], "oval")
        self.assertEqual(gradio_app.current_orb_config()["calm_color"], "#112233")

        _, deleted = gradio_app.delete_orb_preset("Calm Blue")
        self.assertIn("Deleted preset 'Calm Blue'", deleted)
        self.assertEqual(gradio_app.list_orb_preset_names(), [])
        self.assertEqual(load_settings().get("orb_active_preset"), "")

    def test_preset_name_rejected(self):
        _, _, status = gradio_app.save_orb_preset(
            "!!!", "mist", "#112233", "#445566", 240, "oval", 1, 1, 1, 1
        )
        self.assertIn("Preset name must", status)
        self.assertEqual(gradio_app.list_orb_preset_names(), [])

    def test_toggle_orb_settings(self):
        opened, update = gradio_app.toggle_orb_settings(False)
        self.assertTrue(opened)
        self.assertTrue(update["visible"])
        closed, update2 = gradio_app.toggle_orb_settings(True)
        self.assertFalse(closed)
        self.assertFalse(update2["visible"])


if __name__ == "__main__":
    unittest.main()
