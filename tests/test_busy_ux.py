"""KAN-97 — busy / long-run UX while agent or tests execute (NFR §4.6)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main  # noqa: E402


class BusyUxShellTests(unittest.TestCase):
    def test_desktop_shell_has_busy_cancel_and_cache_bust(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn('id="chat-busy"', html)
        self.assertIn('id="chat-busy-label"', html)
        self.assertIn('id="chat-busy-elapsed"', html)
        self.assertIn('id="chat-cancel"', html)
        self.assertIn("desk31", html)
        self.assertIn("desk31", desk)

        self.assertIn(".chat-busy", css)
        self.assertIn(".chat-cancel-btn", css)
        self.assertIn(".msg.error", css)

        self.assertIn("setChatBusy", js)
        self.assertIn("AbortController", js)
        self.assertIn("busyLabelForElapsed", js)
        self.assertIn('kind: "error"', js)
        self.assertIn("Long run in progress", js)
        # Drawers/secondary panels must stay interactive — do not blanket-disable #app.
        self.assertNotIn('document.getElementById("app").disabled', js)
        self.assertIn("chatSend.disabled", js)


class ChatEndpointBusyUxTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_chat_ok_true_on_success(self):
        with mock.patch.object(main.agent, "chat", new=mock.AsyncMock(return_value="hello")):
            res = self.client.post("/chat", json={"message": "hi", "session_id": "t"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("reply"), "hello")

    def test_chat_ok_false_on_agent_exception(self):
        with mock.patch.object(
            main.agent,
            "chat",
            new=mock.AsyncMock(side_effect=RuntimeError("tool boom")),
        ):
            res = self.client.post("/chat", json={"message": "run tests", "session_id": "t"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body.get("ok"))
        self.assertEqual(body.get("error"), "agent_error")
        self.assertIn("tool boom", body.get("reply") or "")
        self.assertNotIn("success", (body.get("reply") or "").lower())

    def test_chat_ok_false_on_ollama_http_error(self):
        import httpx

        with mock.patch.object(
            main.agent,
            "chat",
            new=mock.AsyncMock(side_effect=httpx.ConnectError("offline")),
        ):
            res = self.client.post("/chat", json={"message": "hi", "session_id": "t"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body.get("ok"))
        self.assertEqual(body.get("error"), "ollama_unreachable")
        self.assertIn("Ollama", body.get("reply") or "")


if __name__ == "__main__":
    unittest.main()
