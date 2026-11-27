"""KAN-337 / KAN-338 — Security FR-UI-11 (rail + Include cell + confirm)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityLayoutGrammarTests(unittest.TestCase):
    def test_security_fr_ui11_rail_scan_markers_desk141(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk141", html)
        self.assertIn("desk141", desk)

        security = html.split('id="app-section-security"', 1)[1].split(
            'id="app-section-reports"', 1
        )[0]

        self.assertIn('data-security-layout-grammar="1"', security)
        self.assertIn('data-sec-rail="1"', security)
        self.assertIn('data-sec-privacy-scan="1"', security)
        self.assertIn('data-sec-audit-scan="1"', security)
        self.assertIn('data-sec-backup-scan="1"', security)
        self.assertIn('data-sec-section="level"', security)
        self.assertIn('data-sec-section="privacy"', security)
        self.assertIn('data-sec-section="audit"', security)
        self.assertIn('data-sec-section="redact"', security)
        self.assertIn('data-sec-section="backup"', security)
        self.assertIn(">Level<", security)
        self.assertIn(">Privacy<", security)
        self.assertIn(">Audit<", security)
        self.assertIn(">Redaction<", security)
        self.assertIn(">Backup<", security)
        self.assertIn(">Include</th>", security)
        self.assertIn(">Artifact</th>", security)
        self.assertIn(">Time</th>", security)
        self.assertIn(">Action</th>", security)
        self.assertIn(">Ref</th>", security)
        self.assertIn(">When</th>", security)
        self.assertIn(">Secrets</th>", security)

        for marker in (
            'id="sec-confirm"',
            'id="priv-confirm"',
            'id="backup-restore-confirm"',
        ):
            self.assertIn(marker, security)
            # Confirm buttons start disabled on first paint.
            slice_from = security.split(marker, 1)[1][:120]
            self.assertIn("disabled", slice_from)

        self.assertIn('id="sec-propose"', security)
        self.assertIn('id="priv-propose"', security)
        self.assertIn('id="priv-reports"', security)
        self.assertIn('id="priv-uploads"', security)
        self.assertIn('data-priv-sessions="1"', security)
        self.assertIn('id="local-audit-list"', security)
        self.assertIn('id="backup-create"', security)
        self.assertIn("Backup &amp; restore", security)

        # Ban page-width check-row grammar and secret substrings in the section.
        self.assertNotIn('class="check-row"', security)
        self.assertNotIn("jira_api_token", security)
        self.assertNotIn("api_token", security)

        # App menu still has a single Lab-tools Security item (hub spoke may mirror).
        app_menu = html.split('id="app-drawer"', 1)[1].split(
            'id="app-drawer-hint"', 1
        )[0]
        self.assertEqual(app_menu.count('data-section="security"'), 1)
        self.assertNotIn('data-settings-section="security"', html)

        # JS: Include cell stopPropagation; rail + audit/backup scan builders.
        self.assertIn("function setSecuritySection", js)
        self.assertIn("function focusPrivArtifact", js)
        self.assertIn("function loadLocalAudit", js)
        self.assertIn("function fillBackupSelect", js)
        self.assertIn('data-sec-checkbox-stop', js)
        self.assertIn("stopPropagation", js)
        self.assertIn('createElement("tr")', js)
        self.assertIn("sec-scan-row", js)
        self.assertIn('setSecuritySection("privacy")', js)

        # CSS grammar: 28px hit + rail + split.
        self.assertIn('data-security-layout-grammar="1"', css)
        self.assertIn(".sec-scan-table", css)
        self.assertIn(".sec-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".sec-detail-pane", css)
        self.assertIn(".sec-grammar-split", css)
        self.assertIn(".sec-section-rail", css)


if __name__ == "__main__":
    unittest.main()
