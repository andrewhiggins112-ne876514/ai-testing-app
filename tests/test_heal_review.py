"""Heal proposal review API + desktop markup (KAN-75 / FR-HEAL-2/5)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.heal_policy import (  # noqa: E402
    HealProposal,
    approve_heal,
    evaluate_and_log,
    list_pending_heals,
    reject_heal,
)


class HealReviewTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "heal_audit.jsonl"
        self.env = mock.patch.dict(
            os.environ, {"LOCALAPPDATA": self._tmpdir.name}, clear=False
        )
        self.env.start()
        # heal_log_path uses LOCALAPPDATA/ai_testing_app — point file via path= arg.

    def tearDown(self):
        self.env.stop()
        self._tmpdir.cleanup()

    def _seed_pending(self):
        decision = evaluate_and_log(
            HealProposal(
                kind="locator",
                original="#email",
                proposed="Email address",
                classification="test_defect",
                evidence={"original": "#email", "proposed": "Email address", "action": "fill"},
            )
        )
        self.assertTrue(decision.allowed)
        # evaluate_and_log wrote to default path under LOCALAPPDATA/ai_testing_app
        from plugins.heal_policy import heal_log_path

        path = heal_log_path()
        self.assertTrue(path.is_file())
        pending = list_pending_heals(path=path)
        self.assertEqual(pending["count"], 1)
        return pending["pending"][0]["id"], path

    def test_list_shows_locator_diff(self):
        pid, path = self._seed_pending()
        listed = list_pending_heals(path=path)
        item = listed["pending"][0]
        self.assertEqual(item["id"], pid)
        self.assertIn("locator only", item["proposal"])
        self.assertIn("#email", item["proposal"])
        self.assertEqual(item["review_status"], "pending_review")

    def test_approve_records_approver_and_clears_pending(self):
        pid, path = self._seed_pending()
        result = approve_heal(pid, reviewer="tester_a", path=path)
        self.assertTrue(result["ok"])
        self.assertEqual(result["review_status"], "approved")
        self.assertEqual(result["approver"], "tester_a")
        listed = list_pending_heals(path=path)
        self.assertEqual(listed["count"], 0)
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        entry = json.loads(lines[-1])
        self.assertEqual(entry["approver"], "tester_a")
        self.assertEqual(entry["review_status"], "approved")

    def test_reject_not_accepted(self):
        pid, path = self._seed_pending()
        result = reject_heal(pid, reviewer="tester_b", path=path)
        self.assertTrue(result["ok"])
        self.assertEqual(result["review_status"], "rejected")
        self.assertIsNone(result.get("approver"))
        self.assertEqual(result.get("rejected_by"), "tester_b")
        listed = list_pending_heals(path=path)
        self.assertEqual(listed["count"], 0)
        entry = json.loads(path.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["review_status"], "rejected")
        self.assertIsNone(entry.get("approver"))

    def test_desktop_heal_section_and_api_routes(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('id="app-section-heal"', html)
        self.assertIn('data-section="heal"', html)
        self.assertIn("Heal proposal review", html)
        self.assertIn("loadHealProposals", js)
        self.assertIn("/api/heal/proposals", js)
        self.assertIn("/api/heal/approve", js)
        self.assertIn("/api/heal/reject", main)
        self.assertIn('"/api/heal/proposals"', main)

    def test_cache_bust_desk_token(self):
        app = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk124", app)
        self.assertIn("desk124", html)
        self.assertRegex(html, r"desktop\.css\?v=desk\d+")
        self.assertRegex(html, r"desktop\.js\?v=desk\d+")


if __name__ == "__main__":
    unittest.main()
