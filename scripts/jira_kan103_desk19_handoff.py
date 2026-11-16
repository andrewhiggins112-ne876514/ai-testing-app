"""PM / doc-keeper: desk19 Jira + description sync (re-runnable). Never prints tokens."""
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

HANDOFF = r"""PM handoff (2026-11-16, desk19 — git main `a355f2d` / `4d246d0`).

**Shipped this session**
- KAN-102 CR: App areas = dedicated `#area-surface` shells (App drawer is nav list; Esc/Back closes). App Settings ≠ Orb settings.
- App **area layout** A–E (`overlay`, `stage`, `orb_hub`, `split`, `floating`) in App Settings; persist `desktop-area-layout-v1`. Accents follow orb style (FR-UI-3).
- Mockups: `docs/mockups/kan103_nav/` + plan `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`.
- **KAN-75** heal proposal UI stays **deferred** until KAN-103 polish closes.

**Next agent pick-up**
- Active story **KAN-103** (open): **KAN-107** richer HUD widgets; **KAN-109** hub particle polish; optional Computer Use on native `desktop_app.py` (desk19).
- Read `docs/ops/WORK_LOG.md` Active slice first.

**Verify**
- `.\venv\Scripts\python.exe -m pytest tests/test_area_layout.py -v` (4 passed).
- Desktop: App → Settings → App area layout; switch mystic/aether orb style and open an App area.
"""

BUG_FIX = """Fix — dedicated area surfaces (desk19).

**Root cause:** App drawer swapped inline `app-section-*` blocks (KAN-102).
**Fix:** Nav opens `#area-surface` with layout modes A–E; inline sections only host area content inside the surface shell.
**Files:** `ui/desktop/*`, `settings/area_layout.py`, `tests/test_area_layout.py`.
**Verify:** `desktop_app.py` desk19; each App nav item opens a dedicated surface (not drawer expansion).
"""

TASK_106 = """Task complete (area screens routing).

Dedicated surfaces per App nav item via `#area-surface`; drawer closes on open; all seven areas wired. Esc/Back returns home.
"""

TASK_112 = """Task complete — App area layout setting (A–E).

Five persisted modes + validation in `settings/area_layout.py`; picker in App Settings area; pytest `tests/test_area_layout.py` (4 passed).
"""

TASK_108 = """Task complete — App Settings vs Orb settings (FR-SET-3).

Jira URL, credential status, connectors, and **App area layout** on App → Settings surface only. Orb style/size/spin remain Screen drawer only. HUD widget toggles stub in Screen drawer (full widgets = KAN-107).
"""

TASK_OPEN_107 = """Handoff — still open.

v1 ships Security/Reports HUD chips + Screen drawer toggles only. Remaining: richer per-area HUD widgets on home per mockups (FR-UI-6).
"""

TASK_OPEN_109 = """Handoff — still open / later.

v1 ships simple radial hub spokes then overlay. Particle/neural polish and launcher flourish remain (optional phase).
"""

TASK_OPEN_110 = """Handoff — still open.

Re-test **KAN-101** drawer toggle vs Settings nav overlap under new area chrome; close when no longer reproduces.
"""

TEST_104 = r"""Agent pytest evidence (story not Done).

`.\venv\Scripts\python.exe -m pytest tests/test_area_layout.py -v` — **4 passed** (2026-11-16).

Manual / Computer Use checklist on native desktop window still open: home + area layouts A–E + style accent switch + HUD toggles. Parent KAN-103 stays open until KAN-107/109 and full verify land.
"""

STORY_103 = """Implementation progress — not Done.

**Done under this story:** area routing (KAN-106), layout A–E (KAN-112), App vs Orb split (KAN-108), KAN-102 defect class fixed.
**Open:** KAN-107 HUD widgets, KAN-109 hub polish, KAN-110 KAN-101 check, full test evidence KAN-104.
"""

RESOLUTION_MARKER = "Resolution (desk19"
RESOLUTION = """**Resolution (desk19, Done 2026-11-16):** Fixed under Story **KAN-103**. App drawer is nav-only; each area opens a dedicated `#area-surface` (not inline `app-section-*` expansion). **App area layout** modes overlay / stage / orb_hub / split / floating persist as `desktop-area-layout-v1` in App Settings. Shell chrome follows the active orb style accent (FR-UI-3). Verify: `desktop_app.py` cache `desk19`; pytest `tests/test_area_layout.py`."""

PROGRESS_MARKER = "Progress (desk19"
STORY_PROGRESS = """**Progress (desk19):** Tasks **KAN-106**, **KAN-108**, **KAN-112** Done; Bug **KAN-102** Done. **Next implement:** Task **KAN-107** (HUD widgets). Still open: **KAN-109** hub polish, **KAN-110** KAN-101 overlap, test **KAN-104** Computer Use evidence. Active slice: `docs/ops/WORK_LOG.md`."""


def prepend_paragraph(j: seed.Jira, key: str, marker: str, text: str) -> None:
    import json

    r = j._req("GET", f"/rest/api/3/issue/{key}?fields=description")
    if r.status_code >= 300:
        j.failures.append(f"get {key}: {r.status_code}")
        return
    existing = (r.json().get("fields") or {}).get("description")
    if existing and marker in json.dumps(existing):
        print(f"  {key} description already has {marker}")
        return
    head = seed.adf_from_lines([text, ""])
    tail = (existing or {}).get("content") or []
    body = {"type": "doc", "version": 1, "content": (head.get("content") or []) + tail}
    put = j._req(
        "PUT",
        f"/rest/api/3/issue/{key}",
        json={"fields": {"description": body}},
        headers={"Content-Type": "application/json"},
    )
    if put.status_code >= 300:
        j.failures.append(f"update {key} desc: {put.status_code}")
    else:
        print(f"  {key} description updated")


def go_done(j: seed.Jira, key: str) -> None:
    if j.transition_done(key):
        print(f"  {key} -> Done")
    else:
        print(f"  {key} Done transition failed")


def go_in_progress(j: seed.Jira, key: str) -> None:
    mapping = j.transitions(key)
    tid = mapping.get("In Progress")
    if tid:
        r = j._req(
            "POST",
            f"/rest/api/3/issue/{key}/transitions",
            json={"transition": {"id": tid}},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code < 300:
            print(f"  {key} -> In Progress")
            return
    # fallback: any non-Done forward transition
    for name, tid in mapping.items():
        if name not in ("Done", "To Do"):
            r = j._req(
                "POST",
                f"/rest/api/3/issue/{key}/transitions",
                json={"transition": {"id": tid}},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code < 300:
                print(f"  {key} -> {name}")
                return
    print(f"  {key} In Progress transition failed")


def main() -> int:
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    prepend_paragraph(j, "KAN-102", RESOLUTION_MARKER, RESOLUTION)
    prepend_paragraph(j, "KAN-103", PROGRESS_MARKER, STORY_PROGRESS)

    j.comment("KAN-103", STORY_103)
    j.comment("KAN-103", HANDOFF)
    j.comment("KAN-102", BUG_FIX)
    j.comment("KAN-102", HANDOFF)
    j.comment("KAN-104", TEST_104)
    j.comment("KAN-106", TASK_106)
    j.comment("KAN-112", TASK_112)
    j.comment("KAN-108", TASK_108)
    j.comment("KAN-107", TASK_OPEN_107)
    j.comment("KAN-109", TASK_OPEN_109)
    j.comment("KAN-110", TASK_OPEN_110)
    for key in ("KAN-106", "KAN-107", "KAN-108", "KAN-109", "KAN-110", "KAN-112"):
        j.comment(key, HANDOFF)

    go_in_progress(j, "KAN-103")
    go_done(j, "KAN-102")
    go_done(j, "KAN-106")
    go_done(j, "KAN-112")
    go_done(j, "KAN-108")

    j.comment(
        "KAN-105",
        "Duplicate story — do not use. Canonical nav story is **KAN-103** (desk19 handoff).",
    )

    if j.failures:
        print("failures:", len(j.failures))
        for item in j.failures:
            print("-", item[:200])
        return 1
    print("handoff posted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())