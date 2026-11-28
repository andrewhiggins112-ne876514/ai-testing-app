"""KAN-388 / KAN-389 — user-friendly full plan document view (FR-PLAN-1 deepen)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlanDocumentViewUiTests(unittest.TestCase):
    def test_plan_document_view_markers_desk149(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk149", html)
        self.assertIn("desk149", desk)
        self.assertIn("desktop.css?v=desk149", html)
        self.assertIn("desktop.js?v=desk149", html)

        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertIn('id="plan-tab-document"', plans)
        self.assertIn('data-plan-panel="document"', plans)
        self.assertIn('id="plan-panel-document"', plans)
        self.assertIn('data-plan-document-view="1"', plans)
        self.assertIn('data-plan-document-article="1"', plans)
        self.assertIn('data-plan-document-body="1"', plans)
        self.assertIn('data-plan-document-empty="1"', plans)
        self.assertIn("readable narrative", plans.lower())

        # Document sits beside Cases; not the Draft form (plan-doc-* is import text).
        doc_panel = plans.split('id="plan-panel-document"', 1)[1].split(
            'id="plan-panel-draft"', 1
        )[0]
        self.assertNotIn('id="plan-doc-name"', doc_panel)
        self.assertNotIn('id="plan-doc-text"', doc_panel)
        self.assertNotIn("<table", doc_panel)

        self.assertIn("function renderPlanDocument", js)
        self.assertIn("function planDocumentLastNarrative", js)
        self.assertIn("renderPlanDocument(plan)", js)
        self.assertIn("renderPlanDocument(null)", js)
        self.assertIn("Open in Cases", js)
        self.assertIn("Last result:", js)
        self.assertIn("Stored as local JSON", js)

        self.assertIn(".plan-document-article", css)
        self.assertIn(".plan-document-case", css)
        self.assertIn("KAN-388", css)


class PlanDocumentStorageTests(unittest.TestCase):
    """AC2: files remain under plans/{LEVEL}/*.json — no new required SQL DB."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self._old = os.environ.get("AI_TESTING_SETTINGS")
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings)
        from settings.store import write_settings

        write_settings({"security_level": "PERSONAL", "orb_style": "classic"})

    def tearDown(self) -> None:
        if self._old is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old
        self.tmp.cleanup()

    def test_plan_storage_remains_level_json_files(self) -> None:
        store_src = (ROOT / "plans" / "store.py").read_text(encoding="utf-8")
        self.assertIn("plans_dir", store_src)
        self.assertIn('glob("*.json")', store_src)
        self.assertNotIn("sqlalchemy", store_src.lower())
        self.assertNotIn("sqlite3", store_src.lower())

        from plans.store import add_case, create_plan, get_plan, plans_dir
        from settings.store import app_data_dir

        created = create_plan(
            "KAN-388 doc view",
            intent="Readable plan narrative for review.",
            level="PERSONAL",
        )
        self.assertEqual(created["status"], "ok", created)
        pid = created["plan"]["id"]
        added = add_case(
            pid,
            "Smoke open home",
            tags=["smoke", "doc-view"],
            level="PERSONAL",
        )
        self.assertEqual(added["status"], "ok", added)

        loaded = get_plan(pid, level="PERSONAL")
        self.assertEqual(loaded["status"], "ok", loaded)
        path = plans_dir("PERSONAL") / f"{pid}.json"
        self.assertTrue(path.is_file(), f"expected JSON at {path}")
        self.assertTrue(str(path).replace("\\", "/").endswith(f"/plans/PERSONAL/{pid}.json"))
        self.assertTrue(str(app_data_dir()) in str(path) or path.is_relative_to(app_data_dir()))
        self.assertEqual(loaded["plan"]["intent"], "Readable plan narrative for review.")
        cases = loaded["plan"]["suite"]["cases"]
        self.assertEqual(len(cases), 1)
        self.assertIn("smoke", cases[0]["tags"])
        self.assertIn("doc-view", cases[0]["tags"])


if __name__ == "__main__":
    unittest.main()
