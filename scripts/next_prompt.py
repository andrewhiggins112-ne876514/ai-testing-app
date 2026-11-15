#!/usr/bin/env python3
"""
Local zero-token helper.
Prints a ready-to-paste “pick up where we left off” prompt from WORK_LOG + MEMORY.
Run:  python scripts/next_prompt.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "PROJECT_MEMORY.md"
WORK_LOG = ROOT / "docs" / "ops" / "WORK_LOG.md"
ROADMAP = ROOT / "docs" / "ops" / "ROADMAP.md"


def _active_slice(text: str) -> str:
    m = re.search(
        r"## Active slice.*?\n\n---",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return "(no Active slice table — check docs/ops/WORK_LOG.md)"
    return m.group(0).strip()


def _current_state_snip(text: str, limit: int = 600) -> str:
    start = text.find("## Current State")
    if start == -1:
        return "(no Current State)"
    end = text.find("## ", start + 10)
    chunk = text[start:end].strip() if end != -1 else text[start:].strip()
    return chunk[:limit] + ("..." if len(chunk) > limit else "")


def main() -> None:
    if not WORK_LOG.exists():
        print("docs/ops/WORK_LOG.md not found")
        return
    log = WORK_LOG.read_text(encoding="utf-8")
    mem = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else ""

    print("=== Copy into a fresh Cursor Agent chat ===\n")
    print("Pick up where we left off.")
    print()
    print("1. Read docs/ops/WORK_LOG.md Active slice (below).")
    print("2. Open that Jira story for Requirements + AC.")
    print("3. Implement that one story now. Keep the diff small.")
    print("4. When done: append WORK_LOG, update PROJECT_MEMORY/ROADMAP if needed,")
    print("   add a Jira comment on the story summarising what shipped.")
    print()
    print("--- Active slice ---")
    print(_active_slice(log))
    print()
    print("--- Current State (short) ---")
    print(_current_state_snip(mem))
    print()
    print("Repo: D:\\Projects\\ai_testing_app")
    print("=== End ===")


if __name__ == "__main__":
    main()
