"""
KAN-103 mockup gate — Active slice reprioritize, ticket descriptions, comments.
REST only via local settings; never prints tokens.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "jira_kan_seed_backlog", REPO / "scripts" / "jira_kan_seed_backlog.py"
)
seed = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(seed)

DESIGN_NOTE = (
    "**Design status:** Pending user mockup choice — candidates A / B / C in "
    "`docs/mockups/kan103_nav/` (README + PNGs). Do not implement shell routing until Designer locks A, B, C, or hybrid."
)

MOCKUP_COMMENT = """Active slice reprioritized (2026-11-15 evening):
- **Next implement:** Story **KAN-103**, starting Task **KAN-106** (area screens) after mockup choice.
- **KAN-75** (heal proposal review UI) deferred behind this UX fix so drawer-inline shell stops spawning defects (KAN-101 class).
- **Gate before coding:** Designer picks navigation mockup **A**, **B**, or **C** (or hybrid).

Mockups:
- Plan: `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`
- Index: `docs/mockups/kan103_nav/index.html`
- README: `docs/mockups/kan103_nav/README.md`

Options summary:
- **A** — Full-bleed glass overlay over dimmed orb+chat; Esc/back home.
- **B** — Area stage with orb pip in corner; HUD widgets home-only.
- **C** — Orb hub spokes to areas (KAN-109) then same overlay as A; App drawer a11y fallback.

**Please reply on this ticket with A, B, C, or hybrid.** Design is not locked until then.
"""


def adf_contains(adf: dict | None, needle: str) -> bool:
    if not adf:
        return False
    import json

    return needle in json.dumps(adf)


def prepend_design_status(existing_adf: dict | None) -> dict:
    head = seed.adf_from_lines([DESIGN_NOTE, ""])
    head_blocks = head.get("content") or []
    tail = (existing_adf or {}).get("content") or []
    return {"type": "doc", "version": 1, "content": head_blocks + tail}


def fetch_description(j: seed.Jira, key: str) -> dict | None:
    r = j._req("GET", f"/rest/api/3/issue/{key}?fields=description")
    if r.status_code >= 300:
        j.failures.append(f"get {key}: {r.status_code}")
        return None
    return r.json().get("fields", {}).get("description")


def update_description(j: seed.Jira, key: str) -> None:
    existing = fetch_description(j, key)
    if adf_contains(existing, "Pending user mockup choice"):
        return
    adf = prepend_design_status(existing)
    r = j._req(
        "PUT",
        f"/rest/api/3/issue/{key}",
        json={"fields": {"description": adf}},
        headers={"Content-Type": "application/json"},
    )
    if r.status_code >= 300:
        j.failures.append(f"update {key}: {r.status_code}")


def main() -> int:
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    for key in ("KAN-103", "KAN-106", "KAN-107", "KAN-108"):
        update_description(j, key)

    for key in ("KAN-103", "KAN-102", "KAN-75"):
        j.comment(key, MOCKUP_COMMENT)

    defer_75 = (
        "Deferred behind **KAN-103** nav/area-screen UX (KAN-102 bug class). "
        "Resume after Designer mockup choice in `docs/mockups/kan103_nav/` and KAN-106 ships."
    )
    j.comment("KAN-75", defer_75)

    bug_note = (
        "Fix implementation now tracked under **KAN-103** (Active). "
        "Shell pattern depends on mockup **A/B/C** in `docs/mockups/kan103_nav/` — not locked yet."
    )
    j.comment("KAN-102", bug_note)

    j.close()
    print("failures", j.failures)
    return 1 if j.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())