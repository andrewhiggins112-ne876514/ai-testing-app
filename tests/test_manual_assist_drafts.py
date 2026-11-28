"""KAN-285 — real local Ollama assist drafts (honest unavailable, no note-echo)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import manual_assist as ma
from plans import manual_session as ms


class ManualAssistDraftsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self._level_patch = mock.patch(
            "settings.store.get_security_level", return_value="OFFICIAL"
        )
        self._dir_patch = mock.patch(
            "settings.store.app_data_dir", return_value=self.root
        )
        self._level_patch.start()
        self._dir_patch.start()
        self.addCleanup(self._level_patch.stop)
        self.addCleanup(self._dir_patch.stop)
        ms.reset_open_cache()
        ma.set_chat_impl(None)
        self.addCleanup(lambda: ma.set_chat_impl(None))

    def test_assist_off_end_produces_no_drafts(self):
        started = ms.start_session("Explore login")
        sid = started["session"]["id"]
        ms.add_note(sid, "Button misaligned")
        ended = ms.end_session(sid)
        self.assertEqual(ended["status"], "ok")
        self.assertEqual(ended["session"]["assist_status"], "off")
        self.assertEqual(ended["session"]["assist_drafts"], [])
        self.assertEqual(ended["review"]["assist_drafts"], [])

    def test_assist_on_notes_do_not_echo_as_ai(self):
        started = ms.start_session("Explore", agent_assist=True)
        sid = started["session"]["id"]
        note = ms.add_note(sid, "Crash on save")
        self.assertEqual(note["session"]["assist_drafts"], [])
        self.assertNotIn(
            "Local draft from note:",
            str(note["session"].get("assist_message") or ""),
        )
        self.assertEqual(note["session"]["assist_status"], "pending")

    def test_assist_on_ollama_ok_real_drafts_at_end(self):
        def fake_chat(_system: str, _user: str):
            return {
                "ok": True,
                "content": (
                    '[{"kind":"possible_bug_hint","title":"Save crash",'
                    '"text":"Reproduce: open form, click Save, app exits."},'
                    '{"kind":"step_draft","title":"Regression",'
                    '"text":"Add step: assert Save keeps session alive."}]'
                ),
            }

        ma.set_chat_impl(fake_chat)
        started = ms.start_session("Crash hunt", agent_assist=True)
        sid = started["session"]["id"]
        ms.add_note(sid, "App exits on Save")
        ended = ms.end_session(sid)
        self.assertEqual(ended["status"], "ok")
        self.assertEqual(ended["session"]["assist_status"], "ready")
        drafts = ended["session"]["assist_drafts"]
        self.assertGreaterEqual(len(drafts), 1)
        self.assertFalse(drafts[0]["published"])
        self.assertEqual(drafts[0]["source"], "ollama")
        self.assertNotIn("Local draft from note:", drafts[0]["text"])
        self.assertTrue(ended["review"]["confirm_required_for_jira"])
        # Propose still two-step
        preview = ms.propose(sid, "create_bug")
        self.assertFalse(preview["writes_jira"])
        self.assertTrue(preview["proposal"]["confirm_required"])

    def test_assist_on_ollama_unavailable_honest(self):
        def fake_chat(_system: str, _user: str):
            return {
                "ok": False,
                "error": "ollama_unavailable",
                "message": "Ollama is unavailable — no fake AI drafts.",
            }

        ma.set_chat_impl(fake_chat)
        started = ms.start_session("Offline assist", agent_assist=True)
        sid = started["session"]["id"]
        ms.add_note(sid, "Something odd")
        ended = ms.end_session(sid)
        self.assertEqual(ended["session"]["assist_status"], "unavailable")
        self.assertEqual(ended["session"]["assist_drafts"], [])
        self.assertIn("unavailable", ended["session"]["assist_message"].lower())
        self.assertEqual(ended["review"]["assist_status"], "unavailable")

    def test_defaults_advertise_honest_assist(self):
        info = ms.defaults_info()
        self.assertTrue(info["honest_assist_drafts"])
        self.assertTrue(info["assist_drafts_at_end"])
        self.assertFalse(info["agent_assist_default"])

    def test_api_and_html_markers(self):
        from main import app

        client = TestClient(app)
        defaults = client.get("/api/manual-sessions/defaults").json()
        self.assertTrue(defaults.get("honest_assist_drafts"))
        html = client.get("/ui/desktop/index.html?v=desk159").text
        self.assertIn("data-manual-assist-honest", html)
        self.assertIn("data-manual-assist-status", html)
        self.assertIn("desk159", open("desktop_app.py", encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
