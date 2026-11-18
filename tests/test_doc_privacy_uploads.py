"""KAN-193 / E1 — Document privacy for uploads (FR-SEC-2 / FR-LEARN-5)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins import doc_ingest  # noqa: E402
from plugins.doc_ingest import apply_proposal, ingest_document  # noqa: E402
from plugins.doc_uploads import (  # noqa: E402
    list_uploads,
    record_upload,
    set_upload_consent,
)
from reports.sections import (  # noqa: E402
    build_sections,
    default_sections,
    normalize_sections,
    render_markdown,
)
from settings.privacy import delete_local_data, privacy_status  # noqa: E402
from settings.store import load_settings, write_settings  # noqa: E402


class DocPrivacyUploadsTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings(load_settings())
        doc_ingest.clear_pending()

    def tearDown(self):
        doc_ingest.clear_pending()
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_upload_records_filename_time_level_consent(self):
        rec = record_upload(
            filename="customer-spec.md",
            text="Target: https://example.com\nJira project: KAN\n",
            consent=False,
        )
        self.assertEqual(rec["filename"], "customer-spec.md")
        self.assertTrue(rec["uploaded_at"])
        self.assertEqual(rec["security_level"], "OFFICIAL")
        self.assertFalse(rec["consent"])
        self.assertFalse(rec["cloud_sync"])

        listed = list_uploads()
        self.assertEqual(listed["count"], 1)
        self.assertFalse(listed["bodies_included"])
        self.assertNotIn("body", listed["uploads"][0])

        set_upload_consent(rec["id"], consent=True)
        again = list_uploads()["uploads"][0]
        self.assertTrue(again["consent"])
        self.assertTrue(again["consent_at"])

    def test_ingest_records_upload_and_consent_on_apply(self):
        out = ingest_document(
            text=(
                "# Spec\n"
                "Target: https://aut.example.test\n"
                "Jira project: KAN\n"
                "jira api token: secret-token-value\n"
            ),
            filename="paste.md",
            session_id="e1-test",
        )
        self.assertIn(out["status"], {"proposal", "ideas_only"})
        self.assertTrue(out.get("upload_id"))
        self.assertFalse(out.get("consent"))
        upload = out.get("upload") or {}
        self.assertEqual(upload.get("filename"), "paste.md")
        self.assertEqual(upload.get("security_level"), "OFFICIAL")

        if out["status"] == "proposal":
            applied = apply_proposal(
                out["proposal_id"],
                session_id="e1-test",
                confirm=True,
            )
            self.assertEqual(applied["status"], "applied")
            self.assertTrue(applied.get("consent"))
            listed = list_uploads()["uploads"]
            match = next(u for u in listed if u["id"] == out["upload_id"])
            self.assertTrue(match["consent"])

    def test_privacy_inventory_includes_uploads_and_delete_wipes(self):
        record_upload(filename="wipe-me.md", text="customer data here", consent=False)
        status = privacy_status()
        self.assertIn("uploads", status["categories"])
        self.assertIn("uploads", status["deletable_categories"])
        self.assertTrue(status["categories"]["uploads"]["exists"])
        self.assertGreaterEqual(status["categories"]["uploads"]["items"], 1)

        propose = delete_local_data(["uploads"], confirm=False)
        self.assertEqual(propose["status"], "confirmation_required")
        self.assertEqual(list_uploads()["count"], 1)

        wiped = delete_local_data(["uploads"], confirm=True)
        self.assertEqual(wiped["status"], "deleted")
        self.assertEqual(list_uploads()["count"], 0)

    def test_exports_omit_document_bodies_unless_section_on(self):
        record_upload(
            filename="secret-spec.md",
            text="CUSTOMER_SECRET_BODY",
            consent=False,
        )
        defaults = default_sections()
        self.assertFalse(defaults["documents"])

        off = build_sections({"status": "pass", "title": "Run", "steps": []}, "", defaults)
        self.assertNotIn("documents", off)
        md_off = render_markdown(off)
        self.assertNotIn("CUSTOMER_SECRET_BODY", md_off)
        self.assertNotIn("## Documents", md_off)

        on_flags = normalize_sections({**defaults, "documents": True})
        on = build_sections({"status": "pass", "title": "Run", "steps": []}, "", on_flags)
        self.assertIn("documents", on)
        self.assertTrue(on["documents"]["bodies_included"])
        bodies = [item.get("body") for item in on["documents"]["items"]]
        self.assertIn("CUSTOMER_SECRET_BODY", bodies)
        md_on = render_markdown(on)
        self.assertIn("## Documents", md_on)
        self.assertIn("CUSTOMER_SECRET_BODY", md_on)

    def test_desktop_shell_marks_upload_privacy_controls(self):
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn("desk89", html)
        self.assertIn('id="rpt-documents"', html)
        self.assertIn('id="priv-uploads"', html)
        self.assertIn('id="doc-uploads-list"', html)
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("/api/doc-uploads", js)
        self.assertIn("documents:", js)
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk89", desk)


if __name__ == "__main__":
    unittest.main()
