"""KAN-195 / E2 — Audit log for local side effects (FR-SEC-2)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.quarantine import clear_quarantine, set_quarantine  # noqa: E402
from plans.store import add_case, create_plan, update_case  # noqa: E402
from settings.local_audit import (  # noqa: E402
    append_local_audit,
    list_local_audit,
    local_audit_path,
)
from settings.privacy import delete_local_data, privacy_status  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class LocalSideEffectsAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.local = Path(self.tmp.name) / "local"
        self.local.mkdir()
        self._old = {
            key: os.environ.get(key)
            for key in ("AI_TESTING_SETTINGS", "LOCALAPPDATA")
        }
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ["LOCALAPPDATA"] = str(self.local)
        write_settings(load_settings())

    def tearDown(self):
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _read_audit(self):
        path = local_audit_path()
        if not path.is_file():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_plan_edit_quarantine_wipe_append_time_action_ids_level_session(self):
        created = create_plan(name="Audit plan")
        plan_id = created["plan"]["id"]
        added = add_case(plan_id, "Case A")
        case_id = added["case"]["id"]

        updated = update_case(
            plan_id,
            case_id,
            enabled=False,
            session_id="sess-edit",
        )
        self.assertEqual(updated["status"], "ok")

        expires = (
            datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=3)
        ).isoformat()
        q = set_quarantine(
            plan_id,
            case_id,
            reason="flake",
            expires_at=expires,
            session_id="sess-q",
        )
        self.assertEqual(q["status"], "ok")
        cleared = clear_quarantine(plan_id, case_id, session_id="sess-clear")
        self.assertEqual(cleared["status"], "ok")

        wipe = delete_local_data(
            ["reports"],
            confirm=True,
            session_id="sess-wipe",
        )
        self.assertEqual(wipe["status"], "deleted")

        entries = self._read_audit()
        actions = [e["action"] for e in entries]
        self.assertIn("plan_case_edit", actions)
        self.assertIn("quarantine_set", actions)
        self.assertIn("quarantine_clear", actions)
        self.assertIn("local_data_wipe", actions)

        edit = next(e for e in entries if e["action"] == "plan_case_edit")
        self.assertEqual(edit["plan_id"], plan_id)
        self.assertEqual(edit["case_id"], case_id)
        self.assertEqual(edit["security_level"], "OFFICIAL")
        self.assertEqual(edit["session_id"], "sess-edit")
        self.assertIn("timestamp", edit)
        self.assertIn("enabled", edit.get("detail", {}).get("fields_changed", []))

        qset = next(e for e in entries if e["action"] == "quarantine_set")
        self.assertEqual(qset["session_id"], "sess-q")
        self.assertEqual(qset["plan_id"], plan_id)

        wipe_entry = next(e for e in entries if e["action"] == "local_data_wipe")
        self.assertEqual(wipe_entry["session_id"], "sess-wipe")
        self.assertIn("reports", wipe_entry.get("detail", {}).get("categories", []))

    def test_no_tokens_or_document_body_in_audit(self):
        token = "super-secret-token-value"
        body = "Customer document body with PII"
        entry = append_local_audit(
            "plan_case_edit",
            plan_id="p1",
            case_id="c1",
            session_id="s1",
            detail={
                "fields_changed": ["note"],
                "jira_api_token": token,
                "token": token,
                "body": body,
                "document_body": body,
                "text": body,
            },
        )
        blob = json.dumps(entry)
        self.assertNotIn(token, blob)
        self.assertNotIn(body, blob)
        self.assertNotIn("jira_api_token", blob)
        self.assertNotIn("document_body", blob)

        listed = list_local_audit(limit=10)
        self.assertTrue(listed["jira_write_audit_remains"])
        self.assertFalse(listed["cloud_siem"])
        listed_blob = json.dumps(listed)
        self.assertNotIn(token, listed_blob)
        self.assertNotIn(body, listed_blob)

    def test_declined_wipe_writes_no_audit(self):
        before = self._read_audit()
        out = delete_local_data(["reports"], confirm=False)
        self.assertEqual(out["status"], "confirmation_required")
        self.assertEqual(self._read_audit(), before)

    def test_privacy_inventory_includes_local_side_effects_audit(self):
        status = privacy_status()
        self.assertIn("local_side_effects_audit", status["deletable_categories"])
        self.assertIn("local_side_effects_audit", status["categories"])
        # Jira write audit category remains available for wipe inventory.
        self.assertIn("jira_write_audit", status["deletable_categories"])

    def test_desktop_security_opens_local_audit_desk64(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk64", html)
        self.assertIn("desk64", desk)
        self.assertIn('id="local-audit-list"', html)
        self.assertIn('id="local-audit-refresh"', html)
        self.assertIn('id="priv-local-audit"', html)
        self.assertIn("/api/local-audit", js)
        self.assertIn("loadLocalAudit", js)


if __name__ == "__main__":
    unittest.main()
