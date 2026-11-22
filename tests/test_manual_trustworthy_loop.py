"""KAN-283 / KAN-284 — Trustworthy Manual session loop (headed)."""
from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import manual_session as ms

ROOT = Path(__file__).resolve().parents[1]


class TrustworthyLoopStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._root = Path(self._tmpdir.name)
        self._level_patch = mock.patch(
            "settings.store.get_security_level", return_value="OFFICIAL"
        )
        self._dir_patch = mock.patch(
            "settings.store.app_data_dir", return_value=self._root
        )
        self._level_patch.start()
        self._dir_patch.start()
        self.addCleanup(self._level_patch.stop)
        self.addCleanup(self._dir_patch.stop)
        ms.reset_open_cache()

    def test_defaults_advertise_trustworthy_loop(self):
        info = ms.defaults_info()
        self.assertTrue(info["trustworthy_loop"])
        self.assertFalse(info["cancel_writes_jira"])
        self.assertTrue(info["confirm_uses_fr_jira_5"])
        self.assertTrue(info["in_app_cancel_confirm"])
        self.assertEqual(info["loop_stages"], ["idle", "recording", "review"])
        self.assertFalse(info["agent_assist_default"])
        self.assertFalse(info["armed_mist_default"])

    def test_cancel_confirm_writes_nothing_to_jira(self):
        started = ms.start_session("Loop cancel charter")
        sid = started["session"]["id"]
        ms.add_note(sid, "temp note")
        need = ms.cancel_session(sid, confirm=False)
        self.assertEqual(need["error"], "confirm_required")
        done = ms.cancel_session(sid, confirm=True)
        self.assertEqual(done["status"], "ok")
        self.assertFalse(done["writes_jira"])
        self.assertTrue(done.get("discarded"))
        self.assertEqual(done["session"]["status"], "cancelled")
        self.assertIsNone(ms.get_open_session())

    def test_end_propose_cancel_confirm_no_jira_write(self):
        started = ms.start_session(
            "Loop propose",
            ticket_bound=True,
            jira_story_key="KAN-283",
        )
        sid = started["session"]["id"]
        ms.add_note(sid, "Saw failure")
        ended = ms.end_session(sid)
        self.assertEqual(ended["status"], "ok")
        self.assertIn("review", ended)

        preview = ms.propose(sid, "create_bug")
        self.assertEqual(preview["status"], "ok")
        self.assertFalse(preview["writes_jira"])
        self.assertTrue(preview["proposal"]["confirm_required"])
        pid = preview["proposal"]["id"]

        cancelled = asyncio.run(ms.confirm_proposal(sid, pid, confirm=False))
        self.assertEqual(cancelled["status"], "ok")
        self.assertFalse(cancelled["writes_jira"])
        self.assertEqual(cancelled["proposal"]["state"], "cancelled")

        preview2 = ms.propose(sid, "comment_on_story")
        pid2 = preview2["proposal"]["id"]

        async def fake_add_comment(**_kwargs):
            return {
                "status": "confirmation_required",
                "confirm_id": "c1",
                "preview": {},
            }

        async def fake_resolve(_sid, word):
            self.assertEqual(word, "confirm")
            return {"status": "commented", "issue_key": "KAN-283"}

        with mock.patch(
            "plugins.jira_plugin.add_comment", side_effect=fake_add_comment
        ), mock.patch(
            "plugins.jira_plugin.resolve_create", side_effect=fake_resolve
        ):
            confirmed = asyncio.run(ms.confirm_proposal(sid, pid2, confirm=True))
        self.assertEqual(confirmed["status"], "ok")
        self.assertTrue(confirmed["writes_jira"])
        self.assertEqual(confirmed["proposal"]["state"], "submitted")
        self.assertTrue(confirmed["proposal"].get("jira_written"))


class TrustworthyLoopUiAndApiTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._root = Path(self._tmpdir.name)
        self._level_patch = mock.patch(
            "settings.store.get_security_level", return_value="OFFICIAL"
        )
        self._dir_patch = mock.patch(
            "settings.store.app_data_dir", return_value=self._root
        )
        self._level_patch.start()
        self._dir_patch.start()
        self.addCleanup(self._level_patch.stop)
        self.addCleanup(self._dir_patch.stop)
        ms.reset_open_cache()
        from main import app

        self.client = TestClient(app)

    def test_api_loop_start_note_end_propose_cancel(self):
        defaults = self.client.get("/api/manual-sessions/defaults").json()
        self.assertTrue(defaults["trustworthy_loop"])
        self.assertTrue(defaults["in_app_cancel_confirm"])

        started = self.client.post(
            "/api/manual-sessions/start",
            json={"charter": "API loop", "agent_assist": False, "armed_mist": False},
        ).json()
        self.assertEqual(started["status"], "ok")
        sid = started["session"]["id"]

        note = self.client.post(
            f"/api/manual-sessions/{sid}/notes", json={"text": "step one"}
        ).json()
        self.assertEqual(note["status"], "ok")

        ended = self.client.post(f"/api/manual-sessions/{sid}/end").json()
        self.assertEqual(ended["status"], "ok")

        prop = self.client.post(
            f"/api/manual-sessions/{sid}/propose",
            json={"kind": "create_bug"},
        ).json()
        self.assertEqual(prop["status"], "ok")
        pid = prop["proposal"]["id"]
        cancel = self.client.post(
            f"/api/manual-sessions/{sid}/proposals/{pid}/confirm",
            json={"confirm": False},
        ).json()
        self.assertFalse(cancel["writes_jira"])
        self.assertEqual(cancel["proposal"]["state"], "cancelled")

    def test_desktop_trustworthy_loop_markers_desk122(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk122", html)
        self.assertIn("desk122", desk)
        self.assertIn('data-manual-loop="1"', html)
        self.assertIn('data-loop-stage="idle"', html)
        self.assertIn('data-manual-loop-stage="1"', html)
        self.assertIn('data-charter-cancel-confirm="1"', html)
        self.assertIn('data-charter-cancel-yes="1"', html)
        self.assertIn('data-charter-dock-controls="1"', html)
        self.assertIn('data-manual-confirm="1"', html)
        self.assertIn('data-charter-note="1"', html)
        self.assertIn('data-charter-end="1"', html)
        self.assertIn('data-manual-review="1"', html)
        self.assertIn(".charter-cancel-confirm", css)
        self.assertIn('#app-section-manual[data-loop-stage="review"]', css)
        self.assertIn("function setManualLoopStage", js)
        self.assertIn("function requestCancelManualSession", js)
        self.assertIn("function showCharterCancelConfirm", js)
        self.assertIn("function addCharterNoteFromDock", js)
        self.assertNotIn("window.confirm(", js)
        self.assertIn("FR-JIRA-5", js)


if __name__ == "__main__":
    unittest.main()
