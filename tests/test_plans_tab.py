"""Gradio Plans tab — same level-scoped store as desktop (KAN-157 / C1)."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("gradio_plans_under_test", ROOT / "ui" / "gradio_app.py")
gradio_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gradio_app)


class PlansTabTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_local = os.environ.get("LOCALAPPDATA")
        os.environ["LOCALAPPDATA"] = self._tmp.name
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        settings_store.load_settings()

    def tearDown(self):
        from settings import store as settings_store

        settings_store._SETTINGS_CACHE = None  # type: ignore[attr-defined]
        if self._old_local is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = self._old_local
        self._tmp.cleanup()

    def test_empty_lists_placeholder(self):
        self.assertEqual(gradio_app.list_plan_choices(), [gradio_app._NONE_PLAN])
        self.assertEqual(gradio_app.list_case_choices(None), [gradio_app._NONE_CASE])
        detail = gradio_app.format_plan_case_detail(None, None)
        self.assertIn("OFFICIAL", detail)
        self.assertIn("0", detail)

    def test_lists_plans_for_active_level_only(self):
        from plans.store import add_case, create_plan
        from settings.store import set_security_level

        create_plan("Official plan", intent="o", level="OFFICIAL")
        create_plan("Secret plan", intent="s", level="SECRET")
        set_security_level("OFFICIAL", confirm=True)
        choices = gradio_app.list_plan_choices()
        self.assertEqual(len(choices), 1)
        self.assertIn("Official plan", choices[0])
        self.assertNotIn("Secret plan", "".join(choices))

        set_security_level("SECRET", confirm=True)
        secret_choices = gradio_app.list_plan_choices()
        self.assertEqual(len(secret_choices), 1)
        self.assertIn("Secret plan", secret_choices[0])

        set_security_level("OFFICIAL", confirm=True)
        created = create_plan("With case", level="OFFICIAL")
        pid = created["plan"]["id"]
        added = add_case(pid, "Case A", note="n")
        cid = added["case"]["id"]
        plan_label = gradio_app._plan_choice_label(created["plan"])
        cases = gradio_app.list_case_choices(plan_label)
        self.assertEqual(len(cases), 1)
        self.assertIn(cid, cases[0])

    def test_refresh_shows_desktop_run_result(self):
        from plans.store import add_case, add_run, create_plan

        created = create_plan("Desk plan", intent="shared")
        pid = created["plan"]["id"]
        added = add_case(pid, "Shared case")
        cid = added["case"]["id"]
        plan_label = gradio_app._plan_choice_label(created["plan"])
        case_label = gradio_app._case_choice_label(added["case"])

        before = gradio_app.format_plan_case_detail(plan_label, case_label)
        self.assertIn("none yet", before.lower())

        add_run(pid, cid, result="fail", duration_ms=42, failure_class="product_bug", note="boom")
        plan_u, case_u, detail, status = gradio_app.refresh_plans_ui(plan_label, case_label)
        self.assertIn("fail", detail.lower())
        self.assertIn("42ms", detail)
        self.assertIn("plan", status.lower())
        self.assertEqual(plan_u["value"], plan_label)
        self.assertEqual(case_u["value"], case_label)

    @patch("plans.run_case.run_single_case", new_callable=AsyncMock)
    def test_run_case_calls_same_path(self, mock_run):
        from plans.store import add_case, create_plan

        mock_run.return_value = {
            "status": "ok",
            "message": "Case finished: pass.",
            "run": {"result": "pass"},
        }
        created = create_plan("Run me")
        pid = created["plan"]["id"]
        added = add_case(pid, "Go")
        cid = added["case"]["id"]
        plan_label = gradio_app._plan_choice_label(created["plan"])
        case_label = gradio_app._case_choice_label(added["case"])

        _pu, _cu, _detail, status = gradio_app.run_gradio_plan_case(plan_label, case_label)
        mock_run.assert_awaited_once()
        args, kwargs = mock_run.await_args
        self.assertEqual(args[0], pid)
        self.assertEqual(args[1], cid)
        self.assertEqual(kwargs.get("session_id"), "gradio-plan-run")
        self.assertIn("pass", status.lower())

    def test_existing_tabs_still_defined(self):
        """C1 must not remove Chat / Settings / Reports / Documents panels."""
        source = (ROOT / "ui" / "gradio_app.py").read_text(encoding="utf-8")
        for tab in ('gr.Tab("Chat")', 'gr.Tab("Settings")', 'gr.Tab("Reports")', 'gr.Tab("Documents")'):
            self.assertIn(tab, source)
        self.assertIn('gr.Tab("Plans")', source)


if __name__ == "__main__":
    unittest.main()
