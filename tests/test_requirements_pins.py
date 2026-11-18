"""Requirements pins match the cutting-edge / stale-advice gate (ops Phase 1)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements.txt"

# Packages that agents must version-match via Context7 / venv (AGENTS.md gate).
PINNED = (
    "fastapi",
    "uvicorn",
    "playwright",
    "httpx",
    "gradio",
    "pydantic",
    "pywebview",
    "Pillow",
)


class RequirementsPinsTests(unittest.TestCase):
    def test_gate_packages_have_version_bounds(self):
        text = REQ.read_text(encoding="utf-8")
        for name in PINNED:
            # Pillow may appear as Pillow; match line start ignoring case.
            pat = re.compile(
                rf"(?im)^\s*{re.escape(name)}\s*[>=<!~]=",
            )
            self.assertIsNotNone(
                pat.search(text),
                f"{name} must be pinned with a version bound in requirements.txt",
            )


if __name__ == "__main__":
    unittest.main()
