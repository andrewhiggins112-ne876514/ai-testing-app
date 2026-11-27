"""KAN-277 / KAN-278 — FR-MAN-1 Charter Frame MVP."""
from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import manual_session as ms
from plans.store import add_case, create_plan, plans_dir

ROOT = Path(__file__).resolve().parents[1]


class ManualSessionStoreTests(unittest.TestCase):
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

    def test_no_background_until_start_and_defaults_off(self):
        info = ms.defaults_info()
        self.assertFalse(info["agent_assist_default"])
        self.assertFalse(info["armed_mist_default"])
        self.assertFalse(info["background_capture"])
        self.assertIsNone(info["open_session_id"])
        listed = ms.list_sessions()
        self.assertEqual(listed["sessions"], [])
        self.assertFalse(listed["frame_visible"])

    def test_start_requires_charter_and_story_when_bound(self):
        bad = ms.start_session("")
        self.assertEqual(bad["error"], "charter_required")
        bound = ms.start_session("Explore login", ticket_bound=True)
        self.assertEqual(bound["error"], "story_required_when_bound")
        ok = ms.start_session(
            "Explore login",
            ticket_bound=True,
            jira_story_key="KAN-277",
            jira_test_key="KAN-278",
        )
        self.assertEqual(ok["status"], "ok")
        self.assertFalse(ok["writes_jira"])
        self.assertFalse(ok["session"]["agent_assist"])
        self.assertFalse(ok["session"]["armed_mist"])
        self.assertEqual(ok["session"]["jira_story_key"], "KAN-277")
        self.assertEqual(ok["session"]["jira_test_key"], "KAN-278")

    def test_one_open_per_level_and_isolation(self):
        first = ms.start_session("A")
        self.assertEqual(first["status"], "ok")
        second = ms.start_session("B")
        self.assertEqual(second["error"], "session_already_open")

        sid = first["session"]["id"]
        path = plans_dir("OFFICIAL") / "sessions" / f"{sid}.json"
        self.assertTrue(path.is_file())
        secret_list = ms.list_sessions(level="SECRET")
        self.assertEqual(secret_list["sessions"], [])
        self.assertIsNone(ms.get_open_session(level="SECRET"))

    def test_assist_off_no_drafts_mist_toggle_and_notes(self):
        started = ms.start_session("Charter only")
        sid = started["session"]["id"]
        note = ms.add_note(sid, "Saw a glitch")
        self.assertEqual(note["status"], "ok")
        self.assertEqual(note["session"]["assist_drafts"], [])

        toggled = ms.update_session_toggles(sid, agent_assist=True, armed_mist=True)
        self.assertTrue(toggled["session"]["agent_assist"])
        self.assertTrue(toggled["session"]["armed_mist"])
        # KAN-285: notes never echo as AI drafts mid-session
        note2 = ms.add_note(sid, "With assist")
        self.assertEqual(note2["session"]["assist_drafts"], [])
        self.assertEqual(note2["session"]["assist_status"], "pending")

        off = ms.update_session_toggles(sid, agent_assist=False)
        self.assertEqual(off["session"]["assist_drafts"], [])
        self.assertEqual(off["session"]["assist_status"], "off")

    def test_end_propose_confirm_cancel_writes_nothing_to_jira(self):
        started = ms.start_session(
            "Bound explore",
            ticket_bound=True,
            jira_story_key="KAN-100",
        )
        sid = started["session"]["id"]
        ms.add_note(sid, "Failure detail")
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
            return {"status": "commented", "issue_key": "KAN-100"}

        with mock.patch(
            "plugins.jira_plugin.add_comment", side_effect=fake_add_comment
        ), mock.patch(
            "plugins.jira_plugin.resolve_create", side_effect=fake_resolve
        ):
            confirmed = asyncio.run(ms.confirm_proposal(sid, pid2, confirm=True))
        self.assertEqual(confirmed["status"], "ok")
        self.assertTrue(confirmed["writes_jira"])
        self.assertEqual(confirmed["proposal"]["state"], "submitted")

    def test_cancel_open_requires_confirm(self):
        started = ms.start_session("Will cancel")
        sid = started["session"]["id"]
        need = ms.cancel_session(sid, confirm=False)
        self.assertEqual(need["error"], "confirm_required")
        done = ms.cancel_session(sid, confirm=True)
        self.assertEqual(done["status"], "ok")
        self.assertFalse(done["writes_jira"])


class ManualSessionApiAndUiTests(unittest.TestCase):
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

    def test_api_start_end_propose_flow(self):
        empty = self.client.get("/api/manual-sessions")
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["sessions"], [])

        defaults = self.client.get("/api/manual-sessions/defaults").json()
        self.assertFalse(defaults["agent_assist_default"])
        self.assertFalse(defaults["armed_mist_default"])

        started = self.client.post(
            "/api/manual-sessions/start",
            json={"charter": "API explore", "agent_assist": False, "armed_mist": False},
        ).json()
        self.assertEqual(started["status"], "ok")
        sid = started["session"]["id"]

        note = self.client.post(
            f"/api/manual-sessions/{sid}/notes", json={"text": "step one"}
        ).json()
        self.assertEqual(note["status"], "ok")
        self.assertEqual(note["session"]["assist_drafts"], [])

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

    def test_desktop_charter_frame_markers_desk139(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk139", html)
        self.assertIn("desk139", desk)
        self.assertIn('data-charter-frame="1"', html)
        self.assertIn('data-charter-mvp="1"', html)
        self.assertIn('data-manual-start="1"', html)
        self.assertIn('data-manual-review="1"', html)
        self.assertIn("charter-frame-root", html)
        self.assertIn(".charter-frame-rect", css)
        self.assertIn(".charter-frame-mist", css)
        self.assertIn("function startManualSession", js)
        self.assertIn("function showCharterFrame", js)
        self.assertIn("/api/manual-sessions/start", js)
        self.assertNotIn('disabled title="Charter Frame Start lands', html)

    def test_local_case_note_propose(self):
        plan = create_plan(name="Manual note plan")
        self.assertEqual(plan["status"], "ok")
        pid = plan["plan"]["id"]
        added = add_case(pid, name="Explorer case")
        self.assertEqual(added["status"], "ok")
        case_id = added["case"]["id"]
        started = ms.start_session(
            "Note attach", plan_id=pid, case_id=case_id
        )
        sid = started["session"]["id"]
        ms.add_note(sid, "Explorer note for case")
        ms.end_session(sid)
        prop = ms.propose(sid, "attach_local_case_note")
        self.assertEqual(prop["status"], "ok")
        confirmed = asyncio.run(
            ms.confirm_proposal(sid, prop["proposal"]["id"], confirm=True)
        )
        self.assertEqual(confirmed["status"], "ok")
        self.assertFalse(confirmed["writes_jira"])


if __name__ == "__main__":
    unittest.main()
