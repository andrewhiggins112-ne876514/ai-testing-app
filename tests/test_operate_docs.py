"""KAN-381 / KAN-382 — OPERATE-4 Documents demo pack (fixtures + OFFICIAL seed + draft)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Accidental real-org leakage — fictional demo may say "never employer docs".
FORBIDDEN_SNIPPETS = (
    "atlassian.net",
    "dell.com",
    "confidential client",
    "internal.corp",
)


class OperateDocsFixtureTests(unittest.TestCase):
    def test_fixture_files_present_with_marker(self) -> None:
        from plugins.operate_docs import (
            GUIDE_NAME,
            MARKER,
            SPEC_NAME,
            fixture_paths,
            fixture_present,
        )

        present = fixture_present()
        self.assertTrue(present.get("ok"), present)
        self.assertEqual(present.get("marker"), MARKER)
        self.assertEqual(present.get("upload_names"), [SPEC_NAME, GUIDE_NAME])
        paths = fixture_paths()
        for key in ("spec", "guide"):
            path = paths[key]
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn(MARKER, text)
            self.assertIn("Operate Demo Catalog", text)
            lower = text.casefold()
            for bad in FORBIDDEN_SNIPPETS:
                self.assertNotIn(bad, lower, f"{key} must not contain {bad!r}")

    def test_extract_ideas_from_fixtures(self) -> None:
        from plugins.doc_ingest import extract_test_ideas
        from plugins.operate_docs import fixture_paths

        for key, path in fixture_paths().items():
            text = path.read_text(encoding="utf-8")
            ideas = extract_test_ideas(text, limit=20)
            self.assertGreaterEqual(
                len(ideas),
                3,
                f"{key} should yield several extractable ideas; got {ideas!r}",
            )


class OperateDocsSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_seed_lists_both_docs_on_official(self) -> None:
        from plugins.doc_uploads import list_uploads
        from plugins.operate_docs import GUIDE_NAME, SPEC_NAME, seed_operate_docs

        out = seed_operate_docs(level="OFFICIAL")
        self.assertEqual(out.get("status"), "ok", out)
        self.assertTrue(out.get("created"))
        self.assertTrue(out.get("both_present"))

        listed = list_uploads(level="OFFICIAL", include_bodies=False)
        names = {str(u.get("filename") or "") for u in (listed.get("uploads") or [])}
        self.assertIn(SPEC_NAME, names)
        self.assertIn(GUIDE_NAME, names)
        for row in listed.get("uploads") or []:
            if row.get("filename") in {SPEC_NAME, GUIDE_NAME}:
                self.assertTrue(row.get("consent"), row)
                self.assertEqual(row.get("security_level"), "OFFICIAL")

        again = seed_operate_docs(level="OFFICIAL")
        self.assertEqual(again.get("status"), "ok", again)
        self.assertFalse(again.get("created"))
        self.assertEqual(len(again.get("reused_uploads") or []), 2)

    def test_draft_plan_from_docs_no_jira(self) -> None:
        from plugins.operate_docs import (
            GUIDE_NAME,
            PLAN_NAME,
            SPEC_NAME,
            draft_plan_from_operate_docs,
        )

        out = draft_plan_from_operate_docs(level="OFFICIAL")
        self.assertEqual(out.get("status"), "ok", out)
        self.assertFalse(out.get("jira_write"))
        self.assertTrue(out.get("created_plan"))
        self.assertGreater(out.get("case_count") or 0, 0)
        self.assertEqual(out.get("plan_name"), PLAN_NAME)
        self.assertEqual(out.get("documents"), [SPEC_NAME, GUIDE_NAME])

        plan = out.get("plan") or {}
        cases = list((plan.get("suite") or {}).get("cases") or [])
        self.assertGreaterEqual(len(cases), 3)
        for case in cases:
            self.assertIn("document", case.get("tags") or [])
            source = case.get("source") or {}
            self.assertEqual(source.get("kind"), "document")
            self.assertTrue(str(source.get("ref") or "").strip())

        again = draft_plan_from_operate_docs(level="OFFICIAL")
        self.assertEqual(again.get("status"), "ok", again)
        self.assertFalse(again.get("created_plan"))
        self.assertEqual(again.get("plan_id"), out.get("plan_id"))


if __name__ == "__main__":
    unittest.main()
