"""KAN-319 — Track3 Settings + Security density from accepted wire (KAN-318)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT_MODES = ("overlay", "stage", "orb_hub", "split", "floating")


class SettingsSecurityDensityTests(unittest.TestCase):
    def test_settings_security_density_desk109(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        wires = (ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("desk109", html)
        self.assertIn("desk109", desk)
        self.assertIn('data-settings-security-density="1"', html)
        self.assertIn("Accepted", wires)
        self.assertIn("KAN-318", wires)

        settings = html.split('id="app-section-settings"', 1)[1].split(
            'id="app-section-security"', 1
        )[0]
        security = html.split('id="app-section-security"', 1)[1].split(
            'id="app-section-reports"', 1
        )[0]
        self.assertIn('data-settings-security-density="1"', settings)
        self.assertIn('data-settings-security-density="1"', security)

        # Settings: category toolbar → work (no intro h3/hint above chrome).
        set_toolbar = settings.find('id="set-chrome-toolbar"')
        set_work = settings.find('data-area-work="1"')
        self.assertGreater(set_work, set_toolbar)
        before_set = settings[:set_toolbar]
        self.assertNotIn("orb-section-label", before_set)
        self.assertNotIn("drawer-hint", before_set)

        set_actions = settings.split('id="set-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in ('id="set-status"',):
            self.assertIn(marker, set_actions)
        self.assertNotIn("settings-cat-btn", set_actions)
        self.assertNotIn('id="set-jira-url"', set_actions)
        self.assertNotIn('id="rpt-summary"', set_actions)
        self.assertNotIn('id="sec-level"', set_actions)

        self.assertGreater(settings.find('data-settings-about="1"'), set_work)
        self.assertGreater(settings.find('data-settings-section-rail="1"'), set_work)
        self.assertGreater(settings.find('id="settings-section-layout"'), set_work)
        self.assertGreater(settings.find('id="settings-section-report"'), set_work)
        self.assertIn("Credential status", settings.split('data-area-work="1"', 1)[1])
        self.assertIn('id="cred-status-list"', settings.split('data-area-work="1"', 1)[1])

        # Security: level chrome → work (privacy/audit scroll; level never Advanced-only).
        sec_toolbar = security.find('id="sec-chrome-toolbar"')
        sec_work = security.find('data-area-work="1"')
        self.assertGreater(sec_work, sec_toolbar)
        before_sec = security[:sec_toolbar]
        self.assertNotIn("orb-section-label", before_sec)
        self.assertNotIn("drawer-hint", before_sec)

        sec_actions = security.split('id="sec-chrome-toolbar"', 1)[1].split(
            'data-area-work="1"', 1
        )[0]
        for marker in (
            'id="sec-level"',
            'id="sec-propose"',
            'id="sec-confirm"',
            'id="sec-profile"',
            'id="sec-status"',
        ):
            self.assertIn(marker, sec_actions)
        self.assertNotIn('id="priv-propose"', sec_actions)
        self.assertNotIn('id="backup-create"', sec_actions)

        work_sec = security.split('data-area-work="1"', 1)[1]
        self.assertIn("Privacy", work_sec)
        self.assertIn('id="priv-propose"', work_sec)
        self.assertIn("Local side-effects audit", work_sec)
        self.assertIn("Backup", work_sec)
        self.assertNotIn('id="sec-level"', work_sec)
        self.assertIn('data-sec-about="1"', work_sec)

        self.assertIn("--chrome-max: 120px", css)
        self.assertIn("--chrome-toolbar", css)
        set_geo = re.search(
            r"#app-section-settings\[data-settings-security-density=\"1\"\]\s*>\s*"
            r"\.settings-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(set_geo)
        self.assertIn("max-height: var(--chrome-toolbar)", set_geo.group(0))
        sec_geo = re.search(
            r"#app-section-security\[data-settings-security-density=\"1\"\]\s*>\s*"
            r"\.sec-chrome-toolbar\s*\{([^}]*)\}",
            css,
        )
        self.assertIsNotNone(sec_geo)
        self.assertIn("max-height: var(--chrome-toolbar)", sec_geo.group(0))

        for mode in LAYOUT_MODES:
            self.assertIn(f'value="{mode}"', html)

        self.assertNotIn("sticky", settings.lower())
        self.assertNotIn("sticky", security.lower())
        self.assertNotIn("position: sticky", css)


if __name__ == "__main__":
    unittest.main()
