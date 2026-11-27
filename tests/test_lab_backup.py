"""Lab backup / restore (KAN-199 / E4 / FR-SET-1 / FR-SEC-1)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from settings.backup import (  # noqa: E402
    backup_status,
    create_backup,
    restore_backup,
)
from settings.store import (  # noqa: E402
    app_data_dir,
    load_settings,
    set_security_level,
    write_settings,
)


class LabBackupTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "settings.json"
        os.environ["AI_TESTING_SETTINGS"] = str(self.path)
        write_settings(load_settings())
        set_security_level("OFFICIAL", confirm=True)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def _seed_lab(self, *, level: str = "OFFICIAL", with_secret: bool = True):
        root = app_data_dir()
        plans = root / "plans" / level
        plans.mkdir(parents=True, exist_ok=True)
        plan = {
            "id": "planbackup1",
            "name": "Backup plan",
            "security_level": level,
            "cases": [
                {
                    "id": "c1",
                    "title": "Case",
                    "runs": [
                        {
                            "run_id": "rbackup1",
                            "result": "fail",
                            "evidence": [{"kind": "bundle", "path": "x"}],
                        }
                    ],
                }
            ],
        }
        (plans / "planbackup1.json").write_text(
            json.dumps(plan, indent=2), encoding="utf-8"
        )
        evidence = root / "evidence" / "rbackup1"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "bundle.json").write_text(
            json.dumps({"run_id": "rbackup1", "token": "should-stay"}),
            encoding="utf-8",
        )
        (evidence / "trace.notice.txt").write_text("notice\n", encoding="utf-8")
        write_settings(
            {
                **load_settings(),
                "orb_style": "mystic",
                "security_level": level,
                "jira_api_token": "SHOULD-NOT-APPEAR",
            }
        )
        if with_secret:
            creds = root / "levels" / level / "credentials.json"
            creds.parent.mkdir(parents=True, exist_ok=True)
            creds.write_text(
                json.dumps({"jira_api_token": "secret-token-value", "jira_url": "https://x"}),
                encoding="utf-8",
            )
        return plans, evidence

    def test_backup_status_defaults(self):
        status = backup_status()
        self.assertEqual(status["status"], "ok")
        self.assertFalse(status["secrets_default"])
        self.assertFalse(status["cloud_backup"])
        self.assertEqual(status["security_level"], "OFFICIAL")

    def test_create_backup_omits_secrets_by_default(self):
        self._seed_lab()
        result = create_backup(include_settings=True, include_secrets=False)
        self.assertEqual(result["status"], "created")
        self.assertFalse(result["include_secrets"])
        self.assertTrue(result["include_settings"])
        self.assertGreaterEqual(result["contents"]["plans"], 1)
        self.assertGreaterEqual(result["contents"]["evidence_indexes"], 1)
        path = Path(result["path"])
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path, "r") as zf:
            names = [n.replace("\\", "/") for n in zf.namelist()]
            self.assertIn("manifest.json", names)
            self.assertTrue(any(n.startswith("plans/OFFICIAL/") for n in names))
            self.assertIn("evidence/rbackup1/bundle.json", names)
            self.assertIn("settings.json", names)
            self.assertFalse(any("credentials.json" in n for n in names))
            settings_blob = json.loads(zf.read("settings.json").decode("utf-8"))
            self.assertNotIn("jira_api_token", settings_blob)
            self.assertEqual(settings_blob.get("orb_style"), "mystic")

    def test_restore_requires_confirm_and_reports_replaced(self):
        self._seed_lab()
        created = create_backup(include_settings=False)
        path = created["path"]
        # Mutate live plan so restore has something to overwrite
        plans = app_data_dir() / "plans" / "OFFICIAL" / "planbackup1.json"
        plans.write_text(
            json.dumps({"id": "planbackup1", "name": "CHANGED", "cases": []}),
            encoding="utf-8",
        )
        propose = restore_backup(path, confirm=False)
        self.assertEqual(propose["status"], "confirmation_required")
        self.assertIn("preview", propose)
        live = json.loads(plans.read_text(encoding="utf-8"))
        self.assertEqual(live["name"], "CHANGED")

        done = restore_backup(path, confirm=True)
        self.assertEqual(done["status"], "restored")
        self.assertGreaterEqual(done["replaced"]["plans_count"], 1)
        self.assertGreaterEqual(done["replaced"]["evidence_indexes_count"], 1)
        restored = json.loads(plans.read_text(encoding="utf-8"))
        self.assertEqual(restored["name"], "Backup plan")

    def test_restore_refuses_level_mismatch(self):
        self._seed_lab(level="OFFICIAL")
        created = create_backup()
        set_security_level("SECRET", confirm=True)
        blocked = restore_backup(created["path"], confirm=True)
        self.assertEqual(blocked["status"], "error")
        self.assertIn("refused", blocked["message"].lower())
        self.assertEqual(blocked["backup_security_level"], "OFFICIAL")
        self.assertEqual(blocked["active_security_level"], "SECRET")

    def test_restore_refuses_mixed_level_archive(self):
        self._seed_lab()
        created = create_backup()
        path = Path(created["path"])
        # Inject a SECRET plan into the zip to simulate a mixed archive
        with zipfile.ZipFile(path, "a") as zf:
            zf.writestr(
                "plans/SECRET/evil.json",
                json.dumps({"id": "evil", "cases": []}),
            )
        blocked = restore_backup(path, confirm=False)
        self.assertEqual(blocked["status"], "error")
        self.assertIn("mix", blocked["message"].lower())

    def test_api_backup_and_desktop_ui_desk141(self):
        self._seed_lab()
        client = TestClient(main.app)
        status = client.get("/api/backup")
        self.assertEqual(status.status_code, 200)
        body = status.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["cloud_backup"])
        self.assertFalse(body["secrets_default"])

        created = client.post(
            "/api/backup",
            json={"include_settings": True, "include_secrets": False},
        )
        self.assertEqual(created.status_code, 200)
        payload = created.json()
        self.assertEqual(payload["status"], "created")
        self.assertFalse(payload["include_secrets"])

        propose = client.post(
            "/api/backup/restore",
            json={"path": payload["path"], "confirm": False},
        )
        self.assertEqual(propose.status_code, 200)
        self.assertEqual(propose.json()["status"], "confirmation_required")

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk141", html)
        self.assertIn("desk141", desk)
        self.assertIn("backup-create", html)
        self.assertIn("backup-restore-confirm", html)
        self.assertIn("Backup &amp; restore", html)
        self.assertIn('data-sec-backup-scan="1"', html)
        self.assertIn("/api/backup", js)
        self.assertIn("loadBackupStatus", js)


if __name__ == "__main__":
    unittest.main()
