"""KAN-324 / KAN-325 — Settings FR-UI-11 layout grammar markers."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECTIONS = (
    "layout",
    "connections",
    "environments",
    "model",
    "report",
    "credentials",
)


class SettingsLayoutGrammarTests(unittest.TestCase):
    def test_settings_fr_ui11_grammar_markers_desk158(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk158", html)
        self.assertIn("desk158", desk)
        settings = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        self.assertIn('data-settings-layout-grammar="1"', settings)
        self.assertIn('data-settings-section-rail="1"', settings)
        self.assertIn('data-settings-rail-stable="1"', settings)
        self.assertIn('id="settings-section-rail"', settings)

        for key in SECTIONS:
            self.assertIn(f'data-settings-section="{key}"', settings)
            self.assertIn(f'data-settings-section-panel="{key}"', settings)

        # Only the selected section is visible; others start hidden in markup.
        self.assertIn(
            'data-settings-section-panel="layout" role="tabpanel">', settings
        )
        for key in ("connections", "environments", "model", "report", "credentials"):
            self.assertIn(
                f'data-settings-section-panel="{key}" role="tabpanel" hidden>',
                settings,
            )

        # Compact scan tables + dedicated checkbox cell + detail panes.
        self.assertIn('data-settings-scan-table="environments"', settings)
        self.assertIn('data-settings-scan-table="report-blocks"', settings)
        self.assertIn('data-settings-checkbox-cell="1"', settings)
        self.assertIn('data-settings-checkbox-stop="1"', settings)
        self.assertIn('data-settings-detail="environments"', settings)
        self.assertIn('data-settings-detail="report-blocks"', settings)
        self.assertIn('data-settings-danger="environments"', settings)

        # Delete lives in detail, not list-row chrome.
        env_scan = settings.split('id="set-env-scan"', 1)[1].split(
            'id="set-env-detail"', 1
        )[0]
        self.assertNotIn('id="set-env-delete"', env_scan)
        self.assertIn('id="set-env-delete"', settings)
        self.assertIn('id="set-env-delete-confirm"', settings)
        self.assertGreater(
            settings.find('id="set-env-delete"'),
            settings.find('data-settings-detail="environments"'),
        )

        # Clear credentials stay in detail danger zone.
        self.assertIn('data-settings-danger="credentials"', settings)
        cred_detail = settings.split('data-settings-detail="credentials"', 1)[1]
        self.assertIn('id="cred-clear-email-btn"', cred_detail)

        # Old App/Report toolbar tabs gone from Settings chrome.
        toolbar = settings.split('id="set-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        self.assertNotIn("settings-cat-btn", toolbar)
        self.assertNotIn('id="settings-cat-btn-app"', settings)
        self.assertIn('id="set-status"', toolbar)

        # JS: rail + row-focus + checkbox stop + back-compat deeplink.
        self.assertIn("function setSettingsSection", js)
        self.assertIn("function setSettingsCategory", js)
        self.assertIn("focusEnvironmentDetail", js)
        self.assertIn("focusReportBlock", js)
        self.assertIn("data-settings-checkbox-stop", js)
        self.assertIn('settingsCategoryPending = "report"', js)
        self.assertIn('setSettingsCategory("report")', js)
        self.assertIn("stopPropagation", js)

        # CSS grammar: only selected panel shows; rail stays put (no area-work scroll).
        self.assertIn('data-settings-layout-grammar="1"', css)
        self.assertIn(".settings-section-rail", css)
        self.assertIn(".settings-section-panel[hidden]", css)
        self.assertIn("display: none !important", css)
        self.assertIn(".settings-section-panel:not([hidden])", css)
        self.assertIn("overflow: hidden", css)
        self.assertIn(".settings-scan-table", css)
        self.assertIn(".settings-hit", css)
        self.assertIn("width: 28px", css)
        self.assertIn(".settings-detail-pane", css)
        self.assertIn("settingsSectionRail", js)
        self.assertIn("main.scrollTop = 0", js)

        # Security remains its own App area (not a Settings rail item).
        security = html.split('id="app-section-security"', 1)[1].split(
            'id="app-section-reports"', 1
        )[0]
        self.assertIn('id="sec-propose"', security)
        self.assertNotIn('data-settings-section="security"', settings)


if __name__ == "__main__":
    unittest.main()
