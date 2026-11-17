"""Read-only export pack (KAN-213 / F6 / FR-REP-3)."""
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
from plans.store import add_case, add_run, create_plan  # noqa: E402
from reports.export_pack import (  # noqa: E402
    create_export_pack,
    export_pack_status,
    last_export_pack,
)
from settings.store import write_settings  # noqa: E402


class ExportPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.packs = Path(self.tmp.name) / "packs"
        self.evidence = Path(self.tmp.name) / "shot.png"
        self.evidence.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        self._old_settings = os.environ.get("AI_TESTING_SETTINGS")
        self._old_packs = os.environ.get("AI_TESTING_EXPORT_PACKS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        os.environ["AI_TESTING_EXPORT_PACKS"] = str(self.packs)
        write_settings({"security_level": "OFFICIAL", "orb_style": "mystic"})

    def tearDown(self):
        if self._old_settings is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old_settings
        if self._old_packs is None:
            os.environ.pop("AI_TESTING_EXPORT_PACKS", None)
        else:
            os.environ["AI_TESTING_EXPORT_PACKS"] = self._old_packs
        self.tmp.cleanup()

    def _seed_run(self):
        created = create_plan(name="Export pack plan", intent="F6 pack")
        self.assertEqual(created["status"], "ok")
        pid = created["plan"]["id"]
        case = add_case(
            pid,
            name="Pack case",
            jira_key="KAN-213",
            source_kind="jira",
            source_ref="Read-only export pack",
        )["case"]
        cid = case["id"]
        run = add_run(
            pid,
            cid,
            result="fail",
            duration_ms=120,
            note="token=supersecretvalue123456",
            evidence=[str(self.evidence)],
        )
        self.assertEqual(run["status"], "ok")
        return pid, cid, run["run"]["id"]

    def test_pack_writes_folder_report_matrix_evidence(self):
        pid, cid, rid = self._seed_run()
        out = create_export_pack(
            pid,
            cid,
            rid,
            sections={
                "summary": True,
                "stories": True,
                "bugs": True,
                "evidence": True,
                "known_issues": True,
                "traceability": True,
                "documents": False,
            },
        )
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["security_level"], "OFFICIAL")
        self.assertFalse(out["requires_app"])
        self.assertFalse(out["cloud"])
        self.assertFalse(out["cloud_shared_drive_default"])
        folder = Path(out["path"])
        self.assertTrue(folder.is_dir())
        for name in (
            "README.md",
            "LABEL.txt",
            "report.md",
            "report.json",
            "matrix.md",
            "matrix.json",
            "manifest.json",
            "evidence/index.json",
        ):
            self.assertTrue((folder / name).is_file(), name)

        label = (folder / "LABEL.txt").read_text(encoding="utf-8")
        self.assertIn("Security level: OFFICIAL", label)
        self.assertIn("Exported at (UTC):", label)
        self.assertIn("Requires this app: no", label)

        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("do **not**", readme)
        self.assertIn("need the AI Testing Agent app", readme)
        self.assertIn("Security level:", readme)

        report_json = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        dumped = json.dumps(report_json)
        self.assertNotIn("supersecretvalue123456", dumped)
        self.assertGreaterEqual(int(out.get("redaction_hits") or 0), 1)

        matrix = json.loads((folder / "matrix.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(int(matrix.get("count") or 0), 1)

        evidence_files = [
            p for p in (folder / "evidence").iterdir() if p.name != "index.json"
        ]
        self.assertTrue(evidence_files)

        last = last_export_pack()
        self.assertTrue(last["available"])
        self.assertEqual(last["security_level"], "OFFICIAL")
        self.assertEqual(last["pack_id"], out["pack_id"])
        self.assertFalse(last["requires_app"])
        self.assertFalse(last["cloud"])

        status = export_pack_status()
        self.assertFalse(status["cloud_shared_drive_default"])
        self.assertTrue(status["opens_without_app"])
        self.assertEqual(status["last"]["pack_id"], out["pack_id"])

    def test_api_export_pack_and_desktop_ui_desk82(self):
        pid, cid, rid = self._seed_run()
        client = TestClient(main.app)
        empty = client.get("/api/export-pack")
        self.assertEqual(empty.status_code, 200)
        body = empty.json()
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["cloud"])
        self.assertTrue(body["opens_without_app"])

        res = client.post(
            "/api/export-pack",
            json={
                "plan_id": pid,
                "case_id": cid,
                "run_id": rid,
                "summary": True,
                "stories": True,
                "bugs": True,
                "evidence": True,
                "known_issues": True,
                "traceability": True,
                "documents": False,
            },
        )
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(Path(payload["path"]).is_dir())
        self.assertIn("LABEL.txt", payload["files"])
        self.assertIn("matrix.md", payload["files"])

        last = client.get("/api/export-pack/last")
        self.assertEqual(last.status_code, 200)
        self.assertTrue(last.json()["available"])
        self.assertEqual(last.json()["pack_id"], payload["pack_id"])

        run_path = client.post(
            f"/api/plans/{pid}/cases/{cid}/runs/{rid}/export-pack",
            json={"traceability": True, "evidence": True},
        )
        self.assertEqual(run_path.status_code, 200)
        self.assertEqual(run_path.json()["status"], "ok")

        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk82", html)
        self.assertIn("desk82", desk)
        self.assertIn('id="rpt-export-pack"', html)
        self.assertIn('id="hud-export-last"', html)
        self.assertIn("hud-export-last-toggle", html)
        self.assertIn("rpt-export-pack-hint", html)
        self.assertIn("/api/export-pack", js)
        self.assertIn("exportChosenPack", js)
        self.assertIn("loadExportPackHud", js)


if __name__ == "__main__":
    unittest.main()
