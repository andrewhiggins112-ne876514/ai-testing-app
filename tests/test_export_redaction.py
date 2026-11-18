"""KAN-197 / E3 — Redact secrets in evidence and exports (FR-SEC-5 + FR-REP-3)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plans.evidence_bundle import write_failure_bundle  # noqa: E402
from reports.exporter import export_run  # noqa: E402
from reports.redact import (  # noqa: E402
    PLACEHOLDER,
    redact_export_payload,
    redact_text,
    redaction_status,
    screenshot_redaction_warning,
)


class ExportRedactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.local = Path(self.tmp.name) / "local"
        self.reports = Path(self.tmp.name) / "reports"
        self.local.mkdir()
        self.reports.mkdir()
        self._old = {
            key: os.environ.get(key)
            for key in ("AI_TESTING_SETTINGS", "LOCALAPPDATA", "AI_TESTING_REPORTS")
        }
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ["LOCALAPPDATA"] = str(self.local)
        os.environ["AI_TESTING_REPORTS"] = str(self.reports)
        from settings.store import load_settings, write_settings

        write_settings(load_settings())

    def tearDown(self):
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_pattern_redaction_and_hit_count(self):
        text = "api_token=ATATT3xFfGF0-secret-value Bearer abc.def.ghi"
        cleaned, hits = redact_text(text)
        self.assertNotIn("ATATT3xFfGF0-secret-value", cleaned)
        self.assertNotIn("abc.def.ghi", cleaned)
        self.assertIn(PLACEHOLDER, cleaned)
        self.assertGreaterEqual(hits, 2)

    def test_stored_token_value_redacted(self):
        from settings.store import _save_credentials, get_security_level

        token = "stored-jira-token-value-xyz"
        _save_credentials(
            get_security_level(),
            {
                "jira_url": "https://example.atlassian.net",
                "jira_email": "a@b.c",
                "jira_api_token": token,
                "target_secret": "",
            },
        )
        cleaned, hits = redact_text(f"note leaked {token} in log")
        self.assertNotIn(token, cleaned)
        self.assertIn(PLACEHOLDER, cleaned)
        self.assertGreaterEqual(hits, 1)

    def test_export_summary_counts_hits_and_warns_screenshot(self):
        result = {
            "title": "Leak check",
            "status": "fail",
            "error": "password=hunter2-fail",
            "screenshot": str(self.reports / "shot.png"),
            "steps": [{"action": "login", "status": "fail", "error": "password=hunter2-fail"}],
            "evidence": [{"kind": "screenshot", "path": str(self.reports / "shot.png")}],
        }
        (self.reports / "shot.png").write_bytes(b"PNG")
        exported = export_run(result, "run with api_token=ABC123TOKENVALUE", "test")
        self.assertIsInstance(exported, dict)
        self.assertGreaterEqual(int(exported.get("redaction_hits") or 0), 1)
        self.assertTrue(exported.get("screenshot_redaction_warning"))

        json_files = list(self.reports.glob("*.json"))
        self.assertTrue(json_files)
        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        blob = json.dumps(payload)
        self.assertNotIn("hunter2-fail", blob)
        self.assertNotIn("ABC123TOKENVALUE", blob)
        summary = (payload.get("sections") or {}).get("summary") or {}
        self.assertIn("redaction_hits", summary)
        self.assertGreaterEqual(int(summary["redaction_hits"]), 1)
        self.assertTrue(summary.get("screenshot_redaction_warning"))

        md_files = list(self.reports.glob("*.md"))
        self.assertTrue(md_files)
        md = md_files[0].read_text(encoding="utf-8")
        self.assertIn("Redaction hits:", md)
        self.assertIn("Screenshot warning:", md)

    def test_evidence_index_redacts_console_and_warns(self):
        bundle = write_failure_bundle(
            run_id="r-redact",
            plan_id="p1",
            case_id="c1",
            playwright={
                "status": "fail",
                "screenshot": str(self.local / "fail.png"),
                "steps": [
                    {
                        "action": "type",
                        "error": "secret=super-secret-value-99",
                    }
                ],
                "error": "api_token=ATATT-leaked-token-001",
            },
        )
        written = Path(bundle["bundle_path"])
        self.assertTrue(written.is_file())
        data = json.loads(written.read_text(encoding="utf-8"))
        text = json.dumps(data)
        self.assertNotIn("super-secret-value-99", text)
        self.assertNotIn("ATATT-leaked-token-001", text)
        self.assertGreaterEqual(int(data.get("redaction_hits") or 0), 1)
        self.assertTrue(data.get("screenshot_redaction_warning"))
        self.assertFalse(data.get("ocr_redaction"))

    def test_redaction_status_never_echoes_secrets(self):
        from settings.store import _save_credentials, get_security_level

        secret = "never-echo-this-token-value"
        _save_credentials(
            get_security_level(),
            {
                "jira_url": "",
                "jira_email": "",
                "jira_api_token": secret,
                "target_secret": "also-hidden-target-secret",
            },
        )
        status = redaction_status()
        blob = json.dumps(status)
        self.assertNotIn(secret, blob)
        self.assertNotIn("also-hidden-target-secret", blob)
        self.assertTrue(status.get("patterns_enabled"))
        self.assertTrue(status.get("stored_tokens_enabled"))
        self.assertFalse(status.get("ocr_redaction"))
        self.assertFalse(status.get("wipes_secrets"))
        self.assertGreaterEqual(int(status.get("stored_secrets_configured") or 0), 1)

    def test_api_redaction_endpoint(self):
        from fastapi.testclient import TestClient
        import main

        client = TestClient(main.app)
        res = client.get("/api/redaction")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertTrue(body.get("patterns_enabled"))
        self.assertIn("screenshot_warning", body)

    def test_screenshot_warning_helper(self):
        self.assertIsNone(screenshot_redaction_warning({"links": []}))
        warn = screenshot_redaction_warning({"screenshot": "a.png"})
        self.assertIsNotNone(warn)
        self.assertIn("OCR", warn)

    def test_redact_export_payload_meta(self):
        payload = {
            "request": "password=abc12345",
            "sections": {"summary": {"title": "t", "status": "pass"}},
            "result": {"screenshot": "x.png"},
        }
        out = redact_export_payload(payload)
        self.assertIn("redaction", out)
        self.assertGreaterEqual(out["redaction"]["redaction_hits"], 1)
        self.assertEqual(
            out["sections"]["summary"]["redaction_hits"],
            out["redaction"]["redaction_hits"],
        )

    def test_desktop_security_redaction_ui_desk99(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (root / "desktop_app.py").read_text(encoding="utf-8")
        js = (root / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk99", html)
        self.assertIn("desk99", desk)
        self.assertIn("redaction-status", html)
        self.assertIn("redaction-screenshot-warn", html)
        self.assertIn("Export &amp; evidence redaction", html)
        self.assertIn("/api/redaction", js)
        self.assertIn("loadRedactionStatus", js)
        self.assertIn("redaction_hits", js)


if __name__ == "__main__":
    unittest.main()
