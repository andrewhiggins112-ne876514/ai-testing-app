"""Per-session chat history. Ollama is mocked."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

sent = []


class Client:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None):
        sent.append([item.get("content") for item in json["messages"]])

        class Resp:
            def json(self):
                return {"message": {"role": "assistant", "content": "ok"}}

        return Resp()


class SessionTests(unittest.TestCase):
    def setUp(self):
        main.agent.histories.clear()
        sent.clear()

    def test_two_sessions_and_default(self):
        with patch("agent.agent.httpx.AsyncClient", Client):
            with TestClient(main.app) as client:
                client.post("/chat", json={"message": "a1", "session_id": "a"})
                client.post("/chat", json={"message": "b1", "session_id": "b"})
                client.post("/chat", json={"message": "a2", "session_id": "a"})
                client.post("/chat", json={"message": "d1"})
                response = client.post("/chat", json={"message": "d2", "session_id": "default"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "ok")
        self.assertIn("a1", sent[2])
        self.assertIn("a2", sent[2])
        self.assertNotIn("b1", sent[2])
        self.assertIn("d1", sent[4])
        self.assertIn("d2", sent[4])
        self.assertNotIn("a1", sent[4])

    def test_history_capped_at_50(self):
        main.agent.histories["cap"] = [{"role": "user", "content": str(i)} for i in range(49)]
        with patch("agent.agent.httpx.AsyncClient", Client):
            with TestClient(main.app) as client:
                client.post("/chat", json={"message": "new", "session_id": "cap"})
        hist = main.agent.histories["cap"]
        self.assertEqual(len(hist), 50)
        self.assertEqual(hist[-2]["content"], "new")


if __name__ == "__main__":
    unittest.main()
