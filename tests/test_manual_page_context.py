"""KAN-289 / KAN-290 — page context from headed AUT + annotate still + E3."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import aut_page_context as apc
from plans import manual_session as ms
from reports.redact import PLACEHOLDER

ROOT = Path(__file__).resolve().parents[1]


class ManualPageContextTests(unittest.TestCase):
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
        apc.reset_page_context_cache()

    def test_no_aut_context_session_still_works(self):
        started = ms.start_session("Explore without AUT")
        self.assertEqual(started["status"], "ok")
        sid = started["session"]["id"]
        ctx = started["session"]["page_context"]
        self.assertFalse(ctx["known"])
        note = ms.add_note(sid, "Saw a glitch")
        self.assertEqual(note["status"], "ok")
        refreshed = ms.refresh_page_context(sid)
        self.assertEqual(refreshed["status"], "ok")
        self.assertFalse(refreshed["page_context"]["known"])
        self.assertFalse(refreshed["keylog"])

    def test_known_aut_context_attaches_url_title(self):
        apc.set_page_context(
            "https://aut.example/login?token=secretvalue123456",
            "Login — AUT",
            source="playwright_pause",
        )
        started = ms.start_session("With AUT")
        self.assertEqual(started["status"], "ok")
        ctx = started["session"]["page_context"]
        self.assertTrue(ctx["known"])
        self.assertIn("aut.example/login", ctx["url"])
        self.assertEqual(ctx["title"], "Login — AUT")
        self.assertFalse(ctx["keylog"])

        apc.clear_page_context()
        apc.set_page_context(
            "https://aut.example/dashboard",
            "Dashboard",
            source="playwright_pause",
        )
        sid = started["session"]["id"]
        refreshed = ms.refresh_page_context(sid)
        self.assertTrue(refreshed["page_context"]["known"])
        self.assertIn("dashboard", refreshed["page_context"]["url"])
        self.assertEqual(refreshed["page_context"]["title"], "Dashboard")

    def test_annotate_still_stored_locally(self):
        started = ms.start_session("Annotate still")
        sid = started["session"]["id"]
        still_res = ms.attach_still(sid)
        self.assertEqual(still_res["status"], "ok")
        still_id = still_res["still"]["id"]
        annotated = ms.annotate_still(sid, still_id, "Highlight: submit button missing")
        self.assertEqual(annotated["status"], "ok")
        self.assertTrue(annotated["still"]["annotated"])
        self.assertEqual(
            annotated["still"]["annotation"], "Highlight: submit button missing"
        )
        # Also allow annotation at attach time.
        still2 = ms.attach_still(sid, annotation="Inline annotation")
        self.assertTrue(still2["still"]["annotated"])
        self.assertEqual(still2["still"]["annotation"], "Inline annotation")

    def test_propose_applies_e3_redaction_to_url_title_notes(self):
        secret = "SuperSecretTokenValue9999"
        with mock.patch(
            "reports.redact._stored_secret_values", return_value=[secret]
        ):
            apc.set_page_context(
                f"https://aut.example/path?api_token={secret}",
                f"Title with {secret}",
                source="manual",
            )
            started = ms.start_session("Redact propose")
            sid = started["session"]["id"]
            ms.add_note(sid, f"Note leaked {secret} in log")
            still = ms.attach_still(sid, annotation=f"Ann {secret}")
            ms.end_session(sid)
            proposed = ms.propose(sid, "create_bug")
            self.assertEqual(proposed["status"], "ok")
            self.assertGreaterEqual(int(proposed.get("redaction_hits") or 0), 1)
            packet = proposed["proposal"]["packet"]
            blob = (
                packet["actual"]
                + packet["environment"]
                + "\n".join(packet["replication_steps"])
                + (packet.get("page_context") or {}).get("url", "")
                + (packet.get("page_context") or {}).get("title", "")
            )
            self.assertNotIn(secret, blob)
            self.assertIn(PLACEHOLDER, blob)
            # Still annotation also redacted into replication steps.
            self.assertTrue(
                any("Still annotation:" in s for s in packet["replication_steps"])
            )
            self.assertTrue(still["still"]["annotated"])


class ManualPageContextApiAndUiTests(unittest.TestCase):
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
        apc.reset_page_context_cache()

    def test_api_page_context_and_annotate(self):
        from main import app

        client = TestClient(app)
        r = client.post(
            "/api/manual-sessions/page-context",
            json={
                "url": "https://aut.example/x",
                "title": "Example AUT",
                "source": "manual",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["page_context"]["known"])

        start = client.post(
            "/api/manual-sessions/start",
            json={"charter": "API page context"},
        )
        self.assertEqual(start.status_code, 200)
        sid = start.json()["session"]["id"]
        self.assertTrue(start.json()["session"]["page_context"]["known"])

        still = client.post(f"/api/manual-sessions/{sid}/stills", json={})
        self.assertEqual(still.status_code, 200)
        still_id = still.json()["still"]["id"]
        ann = client.post(
            f"/api/manual-sessions/{sid}/stills/{still_id}/annotate",
            json={"annotation": "circle the error toast"},
        )
        self.assertEqual(ann.status_code, 200)
        self.assertTrue(ann.json()["still"]["annotated"])

        refresh = client.post(f"/api/manual-sessions/{sid}/page-context/refresh")
        self.assertEqual(refresh.status_code, 200)
        self.assertTrue(refresh.json()["page_context"]["known"])

    def test_desktop_markers_desk133(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk133", desk)
        self.assertIn('data-manual-page-context="1"', html)
        self.assertIn('data-annotate-still="1"', html)
        self.assertIn("charter-page-refresh", html)
        self.assertIn("charter-annotate-still", html)
        self.assertIn("charter-page-context", html)


if __name__ == "__main__":
    unittest.main()
