"""KAN-371 — Suites path expandvars + toolbar status wrap (KAN-370)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

from plugins.playwright_suite import discover_suite, _resolve_root  # noqa: E402


class SuitePathStatusKan370Tests(unittest.TestCase):
    def test_expandvars_and_status_wrap_desk163(self) -> None:
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        py = (ROOT / "plugins" / "playwright_suite.py").read_text(encoding="utf-8")

        self.assertIn("desk163", html)
        self.assertIn("desk163", desk)
        self.assertIn("KAN-370", css)
        self.assertIn("os.path.expandvars", py)

        block = css.split("KAN-370", 1)[1].split("KAN-364", 1)[0] if "KAN-364" in css.split("KAN-370", 1)[1] else css.split("KAN-370", 1)[1][:800]
        # Density status must wrap, not ellipsis-clip.
        self.assertIn("white-space: normal", css)
        self.assertIn("overflow-wrap: anywhere", css)
        dens = css.split(
            "#app-section-suites[data-suites-sandboxes-density=\"1\"] .suite-toolbar-status",
            1,
        )[1].split("}", 1)[0]
        self.assertNotIn("text-overflow: ellipsis", dens)
        self.assertNotIn("white-space: nowrap", dens)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "kan370_suite"
            fixture.mkdir()
            (fixture / "demo.spec.ts").write_text("// seed\n", encoding="utf-8")
            env_key = "KAN370_SUITE_ROOT"
            with patch.dict(os.environ, {env_key: str(fixture)}):
                # Windows-style %VAR% and Unix $VAR
                for raw in (f"%{env_key}%", f"${env_key}"):
                    root, err = _resolve_root(raw)
                    self.assertIsNone(err, raw)
                    self.assertIsNotNone(root)
                    self.assertEqual(root, fixture.resolve())

                missing = discover_suite(suite_path=f"%{env_key}%\\nope")
                self.assertEqual(missing["status"], "fail")
                err = missing.get("error") or ""
                self.assertIn("Path not found", err)
                # Full path present in error (not only truncated UI).
                self.assertIn("nope", err.lower())


if __name__ == "__main__":
    unittest.main()
