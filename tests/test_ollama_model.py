"""Choose Ollama model (KAN-129 / FR-CONN-1 / FR-SET-3)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.agent import _chat_payload  # noqa: E402
from settings.ollama_models import (  # noqa: E402
    get_ollama_model,
    list_ollama_models,
    model_is_available,
    resolve_chat_model,
)
from settings.store import (  # noqa: E402
    app_settings_status,
    load_settings,
    save_app_settings,
    write_settings,
)


class OllamaModelTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_model_is_available_variants(self):
        models = ["qwen2.5-coder:7b", "llama3:latest"]
        self.assertTrue(model_is_available("qwen2.5-coder:7b", models))
        self.assertTrue(model_is_available("qwen2.5-coder", models))
        self.assertFalse(model_is_available("missing-model", models))

    def test_save_rejects_missing_model(self):
        with patch(
            "settings.ollama_models.list_ollama_models",
            return_value={
                "status": "ok",
                "models": ["qwen2.5-coder:7b"],
                "message": "1 model available.",
            },
        ):
            bad = save_app_settings(ollama_model="not-installed:9b")
        self.assertEqual(bad["status"], "error")
        self.assertIn("not installed", bad["message"].lower())
        self.assertEqual((load_settings().get("ollama_model") or ""), "")

    def test_save_persists_available_model(self):
        with patch(
            "settings.ollama_models.list_ollama_models",
            return_value={
                "status": "ok",
                "models": ["qwen2.5-coder:7b", "qwen3:8b"],
                "message": "2 models available.",
            },
        ):
            ok = save_app_settings(ollama_model="qwen3:8b")
        self.assertEqual(ok["status"], "updated", ok)
        self.assertEqual(load_settings().get("ollama_model"), "qwen3:8b")
        self.assertEqual(get_ollama_model(), "qwen3:8b")
        status = app_settings_status()
        self.assertEqual(status["ollama_model"], "qwen3:8b")

    def test_chat_payload_uses_settings_model_only(self):
        data = load_settings()
        data["ollama_model"] = "qwen3:8b"
        write_settings(data)
        body = _chat_payload([{"role": "user", "content": "hi"}])
        self.assertEqual(body["model"], "qwen3:8b")
        # Switching settings changes the name only — one model key, no second process.
        self.assertIsInstance(body["model"], str)

    def test_resolve_chat_model_missing(self):
        data = load_settings()
        data["ollama_model"] = "ghost:1b"
        write_settings(data)
        with patch(
            "settings.ollama_models.list_ollama_models",
            return_value={"status": "ok", "models": ["qwen2.5-coder:7b"], "message": "ok"},
        ):
            resolved = resolve_chat_model()
        self.assertEqual(resolved["status"], "error")
        self.assertEqual(resolved["error"], "model_missing")

    def test_api_ollama_models_and_settings(self):
        from main import app

        client = TestClient(app)
        fake = {
            "status": "ok",
            "models": ["qwen2.5-coder:7b"],
            "selected": "qwen2.5-coder:7b",
            "message": "1 model available.",
            "ollama_url": "http://localhost:11434",
        }
        with patch("main.list_ollama_models", return_value=fake), patch(
            "settings.ollama_models.list_ollama_models",
            return_value=fake,
        ):
            listed = client.get("/api/ollama-models")
            self.assertEqual(listed.status_code, 200)
            self.assertIn("qwen2.5-coder:7b", listed.json().get("models") or [])

            saved = client.post(
                "/api/app-settings",
                json={"ollama_model": "qwen2.5-coder:7b"},
            )
            self.assertEqual(saved.status_code, 200)
            self.assertEqual(saved.json().get("status"), "updated")


if __name__ == "__main__":
    unittest.main()
