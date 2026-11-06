#!/usr/bin/env python3
"""
Local zero-token helper.
Reads PROJECT_MEMORY.md and prints a short suggested next prompt.
Run:  python scripts/next_prompt.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "PROJECT_MEMORY.md"

def main():
    if not MEMORY.exists():
        print("PROJECT_MEMORY.md not found")
        return
    text = MEMORY.read_text(encoding="utf-8")
    # Very simple extraction of Current State section
    start = text.find("## Current State")
    end = text.find("## ", start + 10) if start != -1 else -1
    state = text[start:end].strip() if start != -1 else "(no Current State section)"

    print("=== Suggested next prompt (copy into a fresh Cursor chat) ===\n")
    print("Read PROJECT_MEMORY.md and AGENTS.md once. Continue from Current State.")
    print("Prefer free / Auto / Composer model.")
    print("Keep the change small. Do not touch orb visual matching unless explicitly asked.")
    print("\nCurrent State snippet:")
    print(state[:800] + ("..." if len(state) > 800 else ""))
    print("\n=== End of prompt ===")

if __name__ == "__main__":
    main()
