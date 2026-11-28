"""KAN-291 — Manual session library + GDPR session wipe."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from plans import manual_session as ms  # noqa: E402
from plans.store import plans_dir  # noqa: E402
from settings.privacy import delete_local_data, local_data_inventory  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class ManualSessionLibraryTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings({**load_settings(), "security_level": "OFFICIAL"})
        ms.reset_open_cache()

    def tearDown(self):
        ms.reset_open_cache()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_list_sessions_level_isolation(self):
        started = ms.start_session("official charter", level="OFFICIAL")
        self.assertEqual(started["status"], "ok")
        sid = started["session"]["id"]
        ms.end_session(sid, level="OFFICIAL")

        secret_start = ms.start_session("secret charter", level="SECRET")
        self.assertEqual(secret_start["status"], "ok")
        secret_id = secret_start["session"]["id"]
        ms.end_session(secret_id, level="SECRET")

        official = ms.list_sessions(level="OFFICIAL")
        secret = ms.list_sessions(level="SECRET")
        official_ids = {s["id"] for s in official["sessions"]}
        secret_ids = {s["id"] for s in secret["sessions"]}
        self.assertIn(sid, official_ids)
        self.assertNotIn(secret_id, official_ids)
        self.assertIn(secret_id, secret_ids)
        self.assertNotIn(sid, secret_ids)
        self.assertTrue(official.get("library"))
        ended = next(s for s in official["sessions"] if s["id"] == sid)
        self.assertTrue(ended["reviewable"])

    def test_reopen_ended_draft_no_silent_jira(self):
        started = ms.start_session("reopen me")
        sid = started["session"]["id"]
        ms.add_note(sid, "step one")
        ms.end_session(sid)
        reopened = ms.reopen_review(sid)
        self.assertEqual(reopened["status"], "ok")
        self.assertTrue(reopened.get("reopened"))
        self.assertFalse(reopened.get("writes_jira"))
        self.assertIn("review", reopened)
        propose = ms.propose(sid, "create_bug", failure_class="product_bug")
        self.assertEqual(propose["status"], "ok")
        self.assertFalse(propose.get("writes_jira", False))

    def test_gdpr_wipe_removes_manual_sessions_for_active_level_only(self):
        off = ms.start_session("wipe me", level="OFFICIAL")
        off_id = off["session"]["id"]
        ms.attach_still(off_id, level="OFFICIAL")
        ms.end_session(off_id, level="OFFICIAL")
        off_json = plans_dir("OFFICIAL") / "sessions" / f"{off_id}.json"
        off_stills = plans_dir("OFFICIAL") / "sessions" / off_id
        self.assertTrue(off_json.is_file())

        sec = ms.start_session("keep me", level="SECRET")
        sec_id = sec["session"]["id"]
        ms.end_session(sec_id, level="SECRET")
        sec_json = plans_dir("SECRET") / "sessions" / f"{sec_id}.json"
        self.assertTrue(sec_json.is_file())

        write_settings({**load_settings(), "security_level": "OFFICIAL"})
        inv = local_data_inventory(["sessions"])
        self.assertGreaterEqual(inv["sessions"]["manual_sessions"]["session_count"], 1)

        wiped = delete_local_data(["sessions"], confirm=True)
        self.assertEqual(wiped["status"], "deleted")
        self.assertFalse(off_json.exists())
        self.assertFalse(off_stills.exists())
        self.assertTrue(sec_json.is_file())
        after = ms.list_sessions(level="OFFICIAL")
        self.assertEqual(after["sessions"], [])
        secret_list = ms.list_sessions(level="SECRET")
        self.assertEqual(len(secret_list["sessions"]), 1)

    def test_api_library_and_reopen_and_ui_markers(self):
        from main import app

        client = TestClient(app)
        listed = client.get("/api/manual-sessions").json()
        self.assertEqual(listed["status"], "ok")
        self.assertTrue(listed.get("library"))

        start = client.post(
            "/api/manual-sessions/start",
            json={"charter": "library api", "agent_assist": False},
        ).json()
        self.assertEqual(start["status"], "ok")
        sid = start["session"]["id"]
        client.post(f"/api/manual-sessions/{sid}/notes", json={"text": "n1"})
        ended = client.post(f"/api/manual-sessions/{sid}/end").json()
        self.assertEqual(ended["status"], "ok")

        reopen = client.post(f"/api/manual-sessions/{sid}/reopen").json()
        self.assertEqual(reopen["status"], "ok")
        self.assertTrue(reopen.get("reopened"))
        self.assertFalse(reopen.get("writes_jira"))

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk159", html)
        self.assertIn("desk159", desk)
        self.assertIn('data-manual-library="1"', html)
        self.assertIn('data-manual-library-panel="1"', html)
        self.assertIn('data-priv-sessions="1"', html)
        self.assertIn("function reopenManualFromLibrary", js)
        self.assertIn("function clearManualUiForLevelSwitch", js)
        self.assertIn("/api/manual-sessions/", js)
        self.assertIn("/reopen", js)


if __name__ == "__main__":
    unittest.main()
