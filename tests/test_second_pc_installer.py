"""Second Windows PC install pack (KAN-237 / G11 / SALES-1 / FR-UI-2)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from installer.second_pc import (  # noqa: E402
    create_second_pc_pack,
    last_second_pc_pack,
    second_pc_status,
)
from settings.store import write_settings  # noqa: E402


class SecondPcInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.packs = Path(self.tmp.name) / "install_packs"
        self._old_settings = os.environ.get("AI_TESTING_SETTINGS")
        self._old_packs = os.environ.get("AI_TESTING_INSTALL_PACKS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ["AI_TESTING_INSTALL_PACKS"] = str(self.packs)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old_settings is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old_settings
        if self._old_packs is None:
            os.environ.pop("AI_TESTING_INSTALL_PACKS", None)
        else:
            os.environ["AI_TESTING_INSTALL_PACKS"] = self._old_packs
        self.tmp.cleanup()

    def test_pack_has_desktop_setup_no_secrets_no_cloud(self):
        out = create_second_pc_pack(session_id="test")
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["shared_cloud_account"])
        self.assertFalse(out["secrets_included"])
        self.assertFalse(out["telemetry_enabled_default"])
        self.assertFalse(out["mandatory_telemetry"])
        self.assertFalse(out["company_rollout_claim"])
        self.assertTrue(out["opens_desktop_app"])
        self.assertTrue(out["local_connections_after_install"])

        folder = Path(out["path"])
        self.assertTrue(folder.is_dir())
        for name in (
            "INSTALL.md",
            "LABEL.txt",
            "pack_manifest.json",
            "SetupSecondPC.ps1",
            "RunDesktop.cmd",
            "desktop_app.py",
            "main.py",
            "requirements.txt",
        ):
            self.assertTrue((folder / name).is_file(), msg=name)

        manifest = json.loads((folder / "pack_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["shared_cloud_account"])
        self.assertFalse(manifest["secrets_included"])
        self.assertFalse(manifest["telemetry_enabled_default"])
        self.assertFalse(manifest["mandatory_telemetry"])
        self.assertFalse(manifest["company_rollout_claim"])

        # Must never ship live settings / credentials from the first PC.
        secret_names = {
            "settings.json",
            "credentials.json",
            ".env",
            ".env.local",
            "secrets.json",
        }
        for path in folder.rglob("*"):
            if path.is_file():
                self.assertNotIn(path.name.lower(), secret_names)

        install = (folder / "INSTALL.md").read_text(encoding="utf-8").lower()
        self.assertIn("local connections", install)
        self.assertIn("draft a plan", install)
        self.assertIn("telemetry", install)

        last = last_second_pc_pack()
        self.assertEqual(last["status"], "ok")
        self.assertEqual(last["folder_name"], out["folder_name"])

        status = second_pc_status()
        self.assertEqual(status["status"], "ok")
        self.assertFalse(status["secrets_in_installer"])
        self.assertFalse(status["shared_cloud_account"])
        self.assertFalse(status["mandatory_telemetry"])

    def test_api_and_desktop_ui_desk97(self):
        client = TestClient(main.app)
        empty = client.get("/api/installer/second-pc")
        self.assertEqual(empty.status_code, 200)
        body = empty.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["shared_cloud_account"])
        self.assertFalse(body["secrets_in_installer"])
        self.assertFalse(body["telemetry_enabled_default"])
        self.assertFalse(body["company_rollout_claim"])

        created = client.post(
            "/api/installer/second-pc-pack",
            json={"session_id": "pytest"},
        )
        self.assertEqual(created.status_code, 200)
        payload = created.json()
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["secrets_included"])
        self.assertTrue(Path(payload["path"]).is_dir())

        last = client.get("/api/installer/second-pc/last")
        self.assertEqual(last.status_code, 200)
        self.assertEqual(last.json().get("folder_name"), payload["folder_name"])

        html = client.get("/ui/desktop/index.html?v=desk97").text
        self.assertIn('id="set-second-pc-pack"', html)
        self.assertIn('id="set-second-pc-status"', html)
        self.assertIn("set-second-pc-hint", html)
        self.assertIn("desk97", html)

        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("/api/installer/second-pc-pack", js)
        self.assertIn("loadSecondPcStatus", js)

        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk97", desk)


if __name__ == "__main__":
    unittest.main()
