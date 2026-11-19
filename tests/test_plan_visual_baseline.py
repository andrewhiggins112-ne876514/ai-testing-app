"""Visual baseline screenshots on plan cases (KAN-225 / G5 / FR-TEST-4)."""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from plans.run_case import case_detail, run_single_case
from plans.store import create_plan
from plans.visual_case import add_visual_case, parse_visual_ref
from plugins.visual_baseline import (
    apply_visual_baseline,
    baselines_dir,
    compare_to_baseline,
    default_baseline_name,
    store_baseline,
    write_solid_png,
)


class PlanVisualBaselineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_visual_ref(self):
        parsed = parse_visual_ref('{"baseline":"home.png","url":"http://x"}')
        self.assertEqual(parsed["baseline"], "home.png")
        self.assertEqual(parsed["url"], "http://x")
        bare = parse_visual_ref("home.png")
        self.assertEqual(bare["baseline"], "home.png")

    def test_baseline_is_level_scoped(self):
        folder = baselines_dir(level="OFFICIAL")
        self.assertIn("baselines", str(folder).replace("\\", "/"))
        self.assertIn("OFFICIAL", str(folder))
        secret = baselines_dir(level="SECRET")
        self.assertNotEqual(folder.resolve(), secret.resolve())

    def test_add_visual_case_opts_in(self):
        created = create_plan("VisualSuite")
        pid = created["plan"]["id"]
        out = add_visual_case(pid)
        self.assertEqual(out.get("status"), "ok")
        case = out["case"]
        self.assertEqual(case["source"]["kind"], "visual")
        parsed = parse_visual_ref(case["source"]["ref"])
        self.assertEqual(parsed["baseline"], default_baseline_name())
        detail = case_detail(out["plan"], case["id"])
        self.assertEqual(detail.get("runner"), "visual_baseline")
        self.assertTrue(detail.get("visual_case"))
        self.assertEqual(detail.get("visual_baseline"), default_baseline_name())

    def test_no_baseline_fails_environment(self):
        current = Path(self._tmp.name) / "current.png"
        write_solid_png(current, rgb=(1, 2, 3))
        out = apply_visual_baseline(
            baseline=default_baseline_name(),
            current_path=current,
            update_baseline=False,
            level="OFFICIAL",
        )
        self.assertEqual(out.get("status"), "fail")
        self.assertEqual(out.get("classification"), "environment")
        self.assertIn("no baseline", (out.get("error") or "").lower())

    def test_explicit_update_then_match(self):
        current = Path(self._tmp.name) / "shot.png"
        write_solid_png(current, rgb=(10, 20, 30))
        stored = store_baseline(default_baseline_name(), current, level="OFFICIAL")
        self.assertEqual(stored.get("status"), "pass")
        self.assertTrue(stored.get("updated"))
        same = Path(self._tmp.name) / "same.png"
        write_solid_png(same, rgb=(10, 20, 30))
        cmp = compare_to_baseline(
            default_baseline_name(), same, update_baseline=False, level="OFFICIAL"
        )
        self.assertEqual(cmp.get("status"), "pass")
        self.assertTrue(cmp.get("matched"))
        self.assertFalse(cmp.get("updated"))

    def test_mismatch_links_both_images(self):
        base_src = Path(self._tmp.name) / "base.png"
        cur = Path(self._tmp.name) / "cur.png"
        write_solid_png(base_src, rgb=(255, 0, 0))
        write_solid_png(cur, rgb=(0, 255, 0))
        store_baseline("page.png", base_src, level="OFFICIAL")
        cmp = compare_to_baseline("page.png", cur, level="OFFICIAL")
        self.assertEqual(cmp.get("status"), "fail")
        self.assertEqual(cmp.get("classification"), "product_bug")
        self.assertFalse(cmp.get("matched"))
        self.assertTrue(cmp.get("baseline_path"))
        self.assertTrue(cmp.get("current_path"))
        self.assertNotEqual(cmp.get("baseline_path"), cmp.get("current_path"))
        # Mismatch must not silently overwrite baseline
        baseline_bytes = Path(cmp["baseline_path"]).read_bytes()
        self.assertEqual(baseline_bytes, base_src.read_bytes())

    def test_opt_in_required(self):
        out = apply_visual_baseline(baseline="", current_path="x.png")
        self.assertEqual(out.get("status"), "fail")
        self.assertEqual(out.get("classification"), "environment")
        self.assertIn("opt-in", (out.get("error") or "").lower())

    @patch(
        "plugins.visual_baseline.capture_page_screenshot",
        new_callable=AsyncMock,
    )
    def test_run_stores_baseline_name_and_match(self, mock_cap):
        shot = Path(self._tmp.name) / "live.png"
        write_solid_png(shot, rgb=(7, 7, 7))
        store_baseline(default_baseline_name(), shot, level="OFFICIAL")
        mock_cap.return_value = {
            "status": "pass",
            "screenshot": str(shot),
            "one_browser": True,
            "playwright": {"playwright_mode": "headless"},
        }
        created = create_plan("VisualRun")
        pid = created["plan"]["id"]
        cid = add_visual_case(pid, "Home visual", url="http://example.local")["case"][
            "id"
        ]
        out = asyncio.run(run_single_case(pid, cid))
        self.assertEqual(out.get("status"), "ok")
        self.assertEqual(out.get("runner"), "visual_baseline")
        self.assertTrue(out.get("one_browser"))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertEqual(run.get("visual_baseline"), default_baseline_name())
        evidence = run.get("evidence") or []
        self.assertTrue(any("visual_baseline_result" in str(e) for e in evidence))
        mock_cap.assert_called_once()

    @patch(
        "plugins.visual_baseline.capture_page_screenshot",
        new_callable=AsyncMock,
    )
    def test_run_mismatch_evidence_has_both(self, mock_cap):
        base_src = Path(self._tmp.name) / "b.png"
        cur = Path(self._tmp.name) / "c.png"
        write_solid_png(base_src, rgb=(1, 1, 1))
        write_solid_png(cur, rgb=(9, 9, 9))
        store_baseline(default_baseline_name(), base_src, level="OFFICIAL")
        mock_cap.return_value = {
            "status": "pass",
            "screenshot": str(cur),
            "one_browser": True,
            "playwright": {},
        }
        created = create_plan("VisualMismatch")
        pid = created["plan"]["id"]
        cid = add_visual_case(pid, url="http://example.local")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "fail")
        self.assertEqual(run.get("failure_class"), "product_bug")
        evidence = [str(e) for e in (run.get("evidence") or [])]
        self.assertTrue(any(str(base_src) == e or e.endswith("visual_home.png") for e in evidence))
        self.assertTrue(any(str(cur) == e or e.endswith("c.png") for e in evidence))

    @patch(
        "plugins.visual_baseline.capture_page_screenshot",
        new_callable=AsyncMock,
    )
    def test_explicit_update_baseline_on_run(self, mock_cap):
        shot = Path(self._tmp.name) / "new.png"
        write_solid_png(shot, rgb=(40, 40, 40))
        mock_cap.return_value = {
            "status": "pass",
            "screenshot": str(shot),
            "one_browser": True,
            "playwright": {},
        }
        created = create_plan("VisualUpdate")
        pid = created["plan"]["id"]
        cid = add_visual_case(pid, url="http://example.local")["case"]["id"]
        out = asyncio.run(run_single_case(pid, cid, update_baseline=True))
        run = out.get("run") or {}
        self.assertEqual(run.get("result"), "pass")
        self.assertIn("update_baseline=explicit", run.get("note") or "")
        self.assertTrue((out.get("visual") or {}).get("updated"))

    def test_api_visual_and_ui_desk103(self):
        client = TestClient(main.app)
        created = client.post("/api/plans", json={"name": "VisualApi"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["plan"]["id"]
        res = client.post(f"/api/plans/{pid}/cases/visual", json={})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "ok")
        case = body.get("case") or {}
        self.assertEqual(case.get("source", {}).get("kind"), "visual")
        parsed = parse_visual_ref(case.get("source", {}).get("ref") or "")
        self.assertEqual(parsed["baseline"], default_baseline_name())

        html = Path("ui/desktop/index.html").read_text(encoding="utf-8")
        self.assertIn("plan-add-visual-btn", html)
        self.assertIn("plan-update-baseline-btn", html)
        self.assertIn("desk103", html)
        desk = Path("desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk103", desk)
        js = Path("ui/desktop/desktop.js").read_text(encoding="utf-8")
        self.assertIn("cases/visual", js)
        self.assertIn("visual-baseline", js)
        self.assertIn("plan-add-visual-btn", js)


if __name__ == "__main__":
    unittest.main()
