"""KAN-293 / KAN-294 — Manual propose/confirm harden (failure class + visibility)."""
from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import manual_session as ms

ROOT = Path(__file__).resolve().parents[1]


def _run(coro):
    return asyncio.run(coro)


class ProposeHardenStoreTests(unittest.TestCase):
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

    def test_defaults_advertise_propose_harden(self):
        info = ms.defaults_info()
        self.assertTrue(info["propose_harden"])
        self.assertTrue(info["failure_class_gates_create_bug"])
        self.assertTrue(info["explicit_bug_pick"])
        self.assertTrue(info["confirm_dock_outside_scroll"])
        self.assertTrue(info["confirm_writes_jira_with_audit"])
        self.assertIn("product_bug", info["failure_classes"])

    def test_create_bug_packet_has_defect_shape(self):
        started = ms.start_session("Charter symptom")
        sid = started["session"]["id"]
        ms.add_note(sid, "Actual failure detail")
        ms.end_session(sid)
        preview = ms.propose(sid, "create_bug", failure_class="product_bug")
        self.assertEqual(preview["status"], "ok")
        packet = preview["proposal"]["packet"]
        for key in (
            "symptom",
            "expected",
            "actual",
            "environment",
            "replication_steps",
            "evidence_paths",
            "failure_class",
            "confirm_required",
        ):
            self.assertIn(key, packet)
        self.assertEqual(packet["failure_class"], "product_bug")
        self.assertTrue(packet["replication_steps"])
        self.assertIn("Actual failure detail", packet["actual"])

    def test_non_product_bug_blocked_without_explicit(self):
        started = ms.start_session("Env issue")
        sid = started["session"]["id"]
        ms.add_note(sid, "timeout")
        ms.end_session(sid)
        blocked = ms.propose(sid, "create_bug", failure_class="environment")
        self.assertEqual(blocked["status"], "error")
        self.assertEqual(blocked["error"], "product_bug_only")
        self.assertIn("comment_on_story", blocked["redirect_kinds"])

    def test_explicit_bug_pick_allows_non_product_bug(self):
        started = ms.start_session("Test defect filed as bug")
        sid = started["session"]["id"]
        ms.add_note(sid, "flaky locator")
        ms.end_session(sid)
        preview = ms.propose(
            sid,
            "create_bug",
            failure_class="test_defect",
            explicit_bug=True,
        )
        self.assertEqual(preview["status"], "ok")
        packet = preview["proposal"]["packet"]
        self.assertTrue(packet["explicit_bug_pick"])
        self.assertEqual(packet["selected_failure_class"], "test_defect")
        self.assertEqual(packet["classification"], "product_bug")
        self.assertEqual(packet["failure_class"], "product_bug")

    def test_confirm_create_bug_writes_and_audits(self):
        started = ms.start_session(
            "Bug write",
            ticket_bound=True,
            jira_story_key="KAN-293",
        )
        sid = started["session"]["id"]
        ms.add_note(sid, "repro step")
        ms.end_session(sid)
        preview = ms.propose(sid, "create_bug")
        pid = preview["proposal"]["id"]

        async def fake_create_bug(**kwargs):
            self.assertEqual(kwargs.get("classification"), "product_bug")
            self.assertTrue(kwargs.get("replication_steps"))
            return {
                "status": "confirmation_required",
                "confirm_id": "cid",
                "preview": {"summary": "x"},
            }

        async def fake_resolve(session_id, word):
            self.assertEqual(word, "confirm")
            return {"status": "created", "key": "KAN-999"}

        with mock.patch(
            "plugins.jira_plugin.create_bug", side_effect=fake_create_bug
        ), mock.patch(
            "plugins.jira_plugin.resolve_create", side_effect=fake_resolve
        ):
            confirmed = _run(ms.confirm_proposal(sid, pid, confirm=True))

        self.assertEqual(confirmed["status"], "ok")
        self.assertTrue(confirmed["writes_jira"])
        self.assertEqual(confirmed["issue_key"], "KAN-999")
        self.assertEqual(confirmed["proposal"]["state"], "submitted")
        self.assertTrue(confirmed["proposal"]["jira_written"])

    def test_confirm_cancel_writes_nothing(self):
        started = ms.start_session("Cancel prop")
        sid = started["session"]["id"]
        ms.end_session(sid)
        preview = ms.propose(sid, "create_bug")
        pid = preview["proposal"]["id"]
        cancelled = _run(ms.confirm_proposal(sid, pid, confirm=False))
        self.assertEqual(cancelled["status"], "ok")
        self.assertFalse(cancelled["writes_jira"])
        self.assertEqual(cancelled["proposal"]["state"], "cancelled")

    def test_confirm_create_bug_failure_leaves_pending(self):
        started = ms.start_session("No jira")
        sid = started["session"]["id"]
        ms.add_note(sid, "x")
        ms.end_session(sid)
        preview = ms.propose(sid, "create_bug")
        pid = preview["proposal"]["id"]

        async def fake_create_bug(**_kwargs):
            return {"status": "error", "message": "Jira is not configured"}

        with mock.patch(
            "plugins.jira_plugin.create_bug", side_effect=fake_create_bug
        ):
            failed = _run(ms.confirm_proposal(sid, pid, confirm=True))
        self.assertEqual(failed["status"], "error")
        self.assertFalse(failed["writes_jira"])
        self.assertEqual(failed["proposal"]["state"], "pending_review")


class ProposeHardenUiAndApiTests(unittest.TestCase):
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

    def test_api_blocks_environment_without_explicit(self):
        started = self.client.post(
            "/api/manual-sessions/start",
            json={"charter": "API harden"},
        ).json()
        sid = started["session"]["id"]
        self.client.post(f"/api/manual-sessions/{sid}/notes", json={"text": "n"})
        self.client.post(f"/api/manual-sessions/{sid}/end")
        blocked = self.client.post(
            f"/api/manual-sessions/{sid}/propose",
            json={"kind": "create_bug", "failure_class": "known_issue"},
        ).json()
        self.assertEqual(blocked["status"], "error")
        self.assertEqual(blocked["error"], "product_bug_only")

        ok = self.client.post(
            f"/api/manual-sessions/{sid}/propose",
            json={
                "kind": "create_bug",
                "failure_class": "known_issue",
                "explicit_bug": True,
            },
        ).json()
        self.assertEqual(ok["status"], "ok")
        self.assertTrue(ok["proposal"]["packet"]["explicit_bug_pick"])

    def test_desktop_markers_desk143(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk143", html)
        self.assertIn("desk143", desk)
        self.assertIn('data-manual-propose-harden="1"', html)
        self.assertIn('data-manual-failure-class="1"', html)
        self.assertIn('data-manual-explicit-bug="1"', html)
        self.assertIn('data-manual-confirm-dock="1"', html)
        self.assertIn("manual-confirm-dock", css)
        self.assertIn("manualFailureClassValue", js)
        self.assertIn("explicit_bug", js)
        self.assertIn("formatManualProposalPreview", js)

        manual = html.split('id="app-section-manual"', 1)[1].split(
            'id="app-section-suites"', 1
        )[0]
        work_at = manual.find('data-area-work="1"')
        work_end = manual.find("</div>", manual.rfind("manual-advanced"))
        confirm_at = manual.find('id="manual-confirm-row"')
        self.assertGreater(confirm_at, work_at)
        # Confirm dock is after the area-work closing region (sibling footer).
        self.assertGreater(confirm_at, work_end)
        self.assertIn("flex-shrink: 0", css)


if __name__ == "__main__":
    unittest.main()
