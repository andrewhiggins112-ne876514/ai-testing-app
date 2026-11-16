"""Comment and note KAN-103 layout-mode CR. REST via local settings. Never prints tokens."""
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

LOCK = (
    "**Design locked 2026-11-16:** App area layout is configurable A–E "
    "(`overlay`, `stage`, `orb_hub`, `split`, `floating`) in App Settings, "
    "not a single mockup pick. Area chrome follows the active orb style accent (FR-UI-3)."
)

COMMENT = """Agent implementation (2026-11-16) — layout modes, not a single mockup pick.

Designer CR: keep A, B, and C, add D (split dock) and E (floating area window), and expose all five as **App area layout** in App Settings.

- Ids: `overlay` (A), `stage` (B), `orb_hub` (C), `split` (D), `floating` (E)
- Persist: localStorage `desktop-area-layout-v1` (validated in `settings/area_layout.py`)
- App drawer is a nav list. Areas open in `#area-surface`. Esc/Back returns home.
- Orb hub is radial spokes, then the overlay shell. App grid stays the list.
- Accents: mystic / aether / neural / apex recolor nav, area shells, HUD chips, hub spokes, and the layout picker (FR-UI-3).
- Mockups: `docs/mockups/kan103_nav/` including `option_d_settings_mystic.png`, `option_d_settings_aether.png`, `option_e_settings_mystic.png`, `option_e_settings_aether.png`.

Story stays open: richer HUD widgets and particle hub polish are not done. HUD v1 is Security/Reports chips in the Screen drawer.
"""

TASK_SUMMARY = "App area layout setting (A–E)"
TASK_BODY = """Development task under KAN-103.

App Settings control **App area layout** with persisted values overlay, stage, orb_hub, split, floating.
Changing the setting switches area chrome. Accents follow the active orb style (FR-UI-3).
Validation: settings/area_layout.py and tests/test_area_layout.py.
"""


def prepend_lock(existing: dict | None) -> dict:
    head = seed.adf_from_lines([LOCK, ""])
    tail = (existing or {}).get("content") or []
    return {"type": "doc", "version": 1, "content": (head.get("content") or []) + tail}


def main() -> int:
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    for key in ("KAN-103", "KAN-102", "KAN-106", "KAN-107", "KAN-108", "KAN-109"):
        existing = None
        r = j._req("GET", f"/rest/api/3/issue/{key}?fields=description")
        if r.status_code >= 300:
            j.failures.append(f"get {key}: {r.status_code}")
        else:
            existing = (r.json().get("fields") or {}).get("description")
        import json

        if existing and "Design locked 2026-11-16" in json.dumps(existing):
            pass
        else:
            put = j._req(
                "PUT",
                f"/rest/api/3/issue/{key}",
                json={"fields": {"description": prepend_lock(existing)}},
                headers={"Content-Type": "application/json"},
            )
            if put.status_code >= 300:
                j.failures.append(f"update {key}: {put.status_code}")
        j.comment(key, COMMENT)

    found = j.search_summaries(
        'project = KAN AND issuetype = Task AND summary ~ "\\"App area layout setting\\""'
    )
    task_key = found.get(TASK_SUMMARY)
    if not task_key:
        task_key = j.create_issue(TASK_SUMMARY, "Task", TASK_BODY)
        if task_key:
            j.link_relates("KAN-103", task_key)
            j.comment(task_key, COMMENT)
    print("layout-task:", task_key or "(not created)")
    if j.failures:
        print("failures:", len(j.failures))
        for item in j.failures:
            print("-", item[:180])
        return 1
    print("jira layout-mode notes posted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
