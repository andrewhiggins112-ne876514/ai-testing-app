"""
PM one-shot: KAN-102 CR — create Story/Tasks/test, update Bug KAN-102, comment related.
Credentials via load_creds from jira_kan_seed_backlog — never prints tokens.
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

STORY_SUMMARY = "Desktop nav: dedicated area screens + agent-home widgets + App Settings split"
EPIC = "KAN-27"


def task_description(intro: str, scope: str, done_when: str) -> str:
    return "\n".join(
        [
            "Intro",
            intro,
            "",
            "Scope",
            scope,
            "",
            "Done when",
            done_when,
        ]
    )


def main() -> int:
    spec_text = (REPO / "docs" / "FUNCTIONAL_SPEC.md").read_text(encoding="utf-8")
    frs = seed.parse_frs(spec_text)
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    existing = j.search_summaries(f'project = KAN AND summary = "{STORY_SUMMARY}"')
    story_key = existing.get(STORY_SUMMARY)
    if not story_key:
        acceptance = [
            "Given the desktop agent home, When the app loads, Then chat and the central orb remain primary and App areas do not render as inline drawer expansions on that canvas.",
            "Given the Screen drawer widget settings, When the user toggles an area HUD widget, Then the widget shows or hides on the agent home and layout prefs persist like other shell widgets (FR-UI-6).",
            "Given an App drawer area (Settings, Security, Reports, Documents, Desktop, Suites, Sandboxes, etc.), When the user selects it, Then a dedicated full-window (or equivalent) area surface opens — not an inline app-section panel in the drawer list (FR-UI-7).",
            "Given App → Settings, When the user configures the product, Then connectors, Jira URL, and credentials status appear there — distinct from Orb visual settings (style/size/spin) which stay in the Screen drawer only (FR-SET-3 / FR-UI-3).",
            "Given the App drawer chrome, When area screens are active, Then KAN-101 drawer-toggle overlap with Settings nav is resolved or regression-tested.",
        ]
        desc = seed.story_description(
            intro=(
                "Product CR (2026-11-15): Agent home = chat + orb; mockup side panels are toggleable HUD widgets, "
                "not App-area content. Each App area is its own dedicated screen. App Settings ≠ Orb settings. "
                "Addresses Bug KAN-102."
            ),
            user_story=(
                "As a tester using the desktop shell, I want each App area on its own screen and optional HUD widgets "
                "on the agent home so that navigation matches the product model and settings are not conflated."
            ),
            fr_ids=["FR-UI-1", "FR-UI-3", "FR-UI-6", "FR-UI-7", "FR-SET-1", "FR-SET-3"],
            frs=frs,
            behaviour=(
                "Replace inline app-section swapping in the App drawer with routing to dedicated area surfaces. "
                "Introduce agent-home HUD widget toggles in the Screen drawer alongside chat/orb/widget chrome. "
                "Move App-wide configuration to the App → Settings area screen; keep orb visuals in Screen drawer only. "
                "Optional later: orb-as-hub particle launcher — separate Task, lower priority."
            ),
            acceptance=acceptance,
            out_of_scope=[
                "Orb radial hub / particle link navigation (future flourish — Task only).",
                "Gradio parity for every area screen (desktop-first).",
                "Voice input (KAN-81).",
            ],
            technical_notes=[
                "Primary paths: ui/desktop/index.html, ui/desktop/desktop.js, ui/desktop/desktop.css.",
                "May need shell routing state and API reuse from existing /api/* endpoints.",
                "Verify via desktop_app.py + Computer Use; pytest where DOM/routing helpers exist.",
                "Plan: docs/ops/KAN102_NAV_WIDGETS_PLAN.md",
            ],
            roadmap="UI-DESK-4 in docs/ops/ROADMAP.md; epic KAN-27.",
        )
        story_key = j.create_issue(STORY_SUMMARY, "Story", desc, parent=EPIC)
        if story_key:
            j.link_relates(story_key, "KAN-102")
            j.link_relates(story_key, "KAN-101")

    tasks_spec = [
        (
            "Area screens: dedicated surfaces per App nav item (routing)",
            task_description(
                "Implement FR-UI-7 — dedicated area screens.",
                "Extract inline app-section-* content from the App drawer into full-window (or overlay) area "
                "surfaces with stable routing/state. App drawer nav selects an area surface; does not expand sections inline.",
                "Each listed App area opens a dedicated surface; pytest or manual routing checklist passes; no regression on agent home primary layout.",
            ),
        ),
        (
            "Agent-home HUD widgets + Screen drawer toggles",
            task_description(
                "Implement FR-UI-6 — toggleable HUD widgets on agent home.",
                "Add per-area HUD widgets (status chips / mini panels) on the agent home canvas. Visibility toggles live "
                "in the Screen drawer with existing chat/orb/widget-settings controls — not under App → Settings.",
                "Widgets toggle on/off from Screen drawer; layout persists with desktop-shell-layout-v1 patterns.",
            ),
        ),
        (
            "App Settings screen vs Orb settings (Screen drawer only)",
            task_description(
                "Implement FR-SET-3 — split App Settings from Orb settings.",
                "App → Settings area screen holds app-wide config (connectors, Jira URL, credential status). "
                "Orb visual controls remain only in Screen drawer (FR-UI-3). Remove conflation in App drawer Settings list.",
                "App Settings screen shows app-wide config; orb style/slider controls absent from App Settings.",
            ),
        ),
        (
            "[Later] Orb hub radial / particle area launcher",
            task_description(
                "Optional navigation flourish — lower priority.",
                "Explore orb-as-hub zoom with particle/neural links to open area screens (design flourish from KAN-102 discussion).",
                "Spike or behind flag only; must not block area screens or widget model.",
            ),
        ),
        (
            "Fix App drawer toggle overlap (KAN-101 coordination)",
            task_description(
                "Coordinate KAN-101 with new area-screen shell.",
                "Resolve App drawer toggle overlapping Settings nav hit target when area screens and drawer chrome ship.",
                "KAN-101 replication steps fail on fixed build; linked test notes overlap resolved.",
            ),
        ),
    ]

    task_keys: list[str] = []
    if story_key:
        for summary, tdesc in tasks_spec:
            full = f"{summary}"
            found = j.search_summaries(f'project = KAN AND summary = "{full}"')
            tkey = found.get(full)
            if not tkey:
                tkey = j.create_issue(full, "Task", tdesc)
                if tkey:
                    j.link_relates(story_key, tkey)
            if tkey:
                task_keys.append(tkey)

        test_summary = f"Test: {STORY_SUMMARY}"
        if not j.search_summaries(f'project = KAN AND summary = "{test_summary}"'):
            test_ac = [
                "Agent home shows chat + orb primary; no inline App-area section on home canvas.",
                "Screen drawer toggles show/hide HUD widgets on agent home.",
                "Each App nav item opens a dedicated area surface.",
                "App Settings holds app-wide config; Orb settings only in Screen drawer.",
                "App drawer toggle does not overlap Settings nav (KAN-101).",
            ]
            td = seed.test_description(STORY_SUMMARY, test_ac)
            tk = j.create_issue(test_summary, "test", td, labels=["test"])
            if tk and story_key:
                j.link_relates(story_key, tk)

    bug_desc = "\n".join(
        [
            "Symptom",
            "Desktop App drawer swaps inline app-section-* panels for Settings, Security, Reports, etc.",
            "",
            "Expected",
            "Agent home = chat + central orb primary. Mockup side panels = optional HUD widgets (FR-UI-6), toggled from Screen/widget settings — not App-area content.",
            "Each App area opens its own dedicated full-window surface (FR-UI-7). App → Settings = main app/connectors config (FR-SET-3). Orb visual settings stay in Screen drawer only (FR-UI-3).",
            "",
            "Actual",
            "Inline section expansion inside the App drawer (pre-CR implementation).",
            "",
            "Environment",
            "Windows desktop shell (desktop_app.py / ui/desktop/).",
            "",
            "Replication steps",
            "1. Launch desktop_app.py.",
            "2. Open App drawer and click Settings, Security, Reports, etc.",
            "3. Observe inline section swap inside drawer instead of dedicated area screen.",
            "",
            "Product decision",
            "2026-11-15 CR locked — implement under parent Story (see Relates). Plan: docs/ops/KAN102_NAV_WIDGETS_PLAN.md",
        ]
    )
    from typing import Any, Dict

    import httpx

    adf = seed.adf_from_lines(bug_desc.split("\n"))
    r = j._req(
        "PUT",
        f"/rest/api/3/issue/KAN-102",
        json={"fields": {"description": adf}},
        headers={"Content-Type": "application/json"},
    )
    if r.status_code >= 300:
        j.failures.append(f"update KAN-102: {r.status_code}")

    comment_102 = (
        "Product CR locked (2026-11-15): widgets on agent home (Screen drawer toggles) vs dedicated App area screens; "
        "App Settings ≠ Orb settings. Parent implementation Story created/linked; see docs/FUNCTIONAL_SPEC FR-UI-6/7, "
        "FR-SET-3 and docs/ops/KAN102_NAV_WIDGETS_PLAN.md."
    )
    if story_key:
        comment_102 += f" Story: {story_key}."
    j.comment("KAN-102", comment_102)

    cr_note = (
        "Product CR (KAN-102, 2026-11-15): Desktop App Settings moves to a dedicated **area screen** under the "
        "new nav model — not an inline App drawer section. App Settings = connectors/Jira/credentials; Orb settings "
        "remain in Screen drawer only. HUD widgets on agent home are toggled from Screen/widget settings. "
        f"Implementation Story: {story_key or '(see KAN-102 links)'}."
    )
    for key in ("KAN-73", "KAN-101", "KAN-74"):
        j.comment(key, cr_note)

    j.close()
    print("story_key", story_key)
    print("task_keys", task_keys)
    print("failures", j.failures)
    return 1 if j.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())