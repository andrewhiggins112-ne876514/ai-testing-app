"""
Council Track 3 Slice-0 → Jira: Epic + Stories + linked test tickets.

Primary-only enterprise area density (FR-UI-10). Lab follow-on.
Hard Designer accept on wires before HTML/CSS geometry.
Verify density in all layout modes A–E.

Credentials from local settings. Never prints tokens.

Usage:
  python scripts/jira_kan_track3_slice0.py
  python scripts/jira_kan_track3_slice0.py --dry-run
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "jira_kan_seed_backlog", REPO / "scripts" / "jira_kan_seed_backlog.py"
)
seed = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(seed)

EPIC_SUMMARY = "Council Track 3 — Enterprise area density (Primary)"


def epic_body() -> str:
    return "\n".join(
        [
            "Intro",
            "Apply accepted enterprise density as real App-area geometry on Primary screens. "
            "Track 2 shipped non-overlap (KAN-281) and CSS tokens (KAN-297) with geometry unchanged — "
            "Designer confirmed the product still looks like sticky filter-bar chrome. "
            "Track 3 rebuilds shared chrome bands and Primary surfaces against FR-UI-10.",
            "",
            "Who this is for",
            "Designer — visual density under demos. Senior test engineer — Plans/Manual/Reports usable. "
            "Security — Settings/Security chrome without mixing OFFICIAL/SECRET.",
            "",
            "Requirements",
            "**FR-UI-10** — Enterprise area density: Primary areas use accepted Track 3 wires; "
            "one non-scrolling chrome stack ≤ ~120px; work scrolls in .area-work; no sticky naming; "
            "Plans Cases wire; Manual Confirm dock visible; Settings/Security outside-scrollport chrome; "
            "density holds in all layout modes A–E. Hard accept gate on wires before geometry Build. "
            "Lab Heal/Desktop/Suites/Sandboxes = follow-on epic.",
            "**FR-UI-9** — Non-overlap and Plans IA remain Done; tokens (KAN-297) do not satisfy FR-UI-10.",
            "**FR-UI-7** — Layout modes A–E stay; verify density in every mode.",
            "**FR-UI-1 / FR-UI-2 / FR-UI-3** — Orb home, desktop-primary, orb accents unchanged.",
            "",
            "Scope — in",
            "Slice-0 wires pack; shared chrome scaffold + retire sticky names; Plans Cases geometry; "
            "Manual density; Reports+Documents; Settings+Security area-work; occlusion verify all A–E.",
            "",
            "Scope — out",
            "Lab full density (TRACK3-LAB follow-on). Voice KAN-81. FR-MAN-2. Gradio-first. "
            "Tall rail / top app tabs / purple SaaS / CDN fonts. Orb home rewrite. Token-only stories.",
            "",
            "Success criteria",
            "Designer can open Primary areas at ~1280×720 in every layout mode A–E and see work-first rooms, "
            "not a filter-bar farm. Wires accepted before first geometry story.",
            "",
            "Dependencies / risks",
            "Depends on accepted ENTERPRISE_LAYOUT_NOTE + TRACK3_AREA_WIRES accept. "
            "Risk: rename-only ship repeating KAN-297 miss.",
            "",
            "Technical notes",
            "ui/desktop/* ; desktop_app.py cache-bust; docs/design/TRACK3_AREA_WIRES.md; "
            "pytest markers + CU/human for occlusion across A–E.",
            "",
            "Mockups",
            "docs/design/ENTERPRISE_LAYOUT_NOTE.md §6; docs/design/TRACK3_AREA_WIRES.md",
        ]
    )


STORIES: List[Dict[str, Any]] = [
    {
        "summary": "Track3: Slice-0 Primary wires pack (accept gate)",
        "fr_ids": ["FR-UI-10", "FR-UI-7"],
        "intro": (
            "Docs-only Slice-0. Inventory Primary areas and write target ASCII wires. "
            "Designer must Accept before any HTML/CSS geometry Build."
        ),
        "user_story": (
            "As the Designer, I want signed wires for Plans, Manual, Reports, Documents, and Settings/Security "
            "so that Build cannot ship another tokens-only miss."
        ),
        "behaviour": (
            "Complete docs/design/TRACK3_AREA_WIRES.md with full Primary wires and A–E verify notes. "
            "Extend Plans Cases from ENTERPRISE_LAYOUT_NOTE. Outline Lab as follow-on only. "
            "Stop for Designer Accept Track 3 wires. No CSS/HTML/class renames in this story."
        ),
        "acceptance": [
            "Given TRACK3_AREA_WIRES.md, When Slice-0 finishes, Then Primary areas each have a wire and chrome budget ≤~120px documented.",
            "Given Designer decisions, When the pack is ready, Then Accept/Amend/Reject is requested and geometry stories stay blocked until Accept.",
            "Given Lab tools, When documented, Then they are marked follow-on (not Track 3 Primary Build).",
            "Given this story, When Done, Then no product HTML/CSS geometry changed.",
        ],
        "out_of_scope": [
            "HTML/CSS geometry or sticky class renames.",
            "Lab Heal/Desktop/Suites/Sandboxes geometry.",
            "Voice / FR-MAN-2.",
        ],
        "technical_notes": [
            "docs/design/TRACK3_AREA_WIRES.md, ENTERPRISE_LAYOUT_NOTE.md pointer.",
            "tests may marker-check wire file exists; no desktop CU required for docs-only.",
        ],
        "roadmap": "TRACK3-UX — first Active; blocked for geometry until wires Accept.",
    },
    {
        "summary": "Track3: Shared chrome scaffold + retire sticky naming",
        "fr_ids": ["FR-UI-10", "FR-UI-9"],
        "intro": (
            "After wires Accept: one shared chrome band pattern on Primary areas; "
            "retire *-sticky-toolbar names. Rename alone with unchanged two-row filter chrome fails."
        ),
        "user_story": (
            "As a senior test engineer, I want one calm chrome band without sticky naming "
            "so that areas feel like work rooms, not filter-bar farms."
        ),
        "behaviour": (
            "Replace plan/manual/rpt/lab sticky class and data markers with shared area-chrome names. "
            "Single toolbar holds search/filter; Heal-style second filter strip not on Primary. "
            "Chrome remains outside .area-work. Visual AC: one band, not token-only."
        ),
        "acceptance": [
            "Given Primary areas, When open, Then HTML has no *-sticky-toolbar / data-*-sticky markers on those areas.",
            "Given search/filter, When present, Then they live in the single toolbar (no second filter strip).",
            "Given chrome, When scrolled, Then it stays outside .area-work and does not cover the first work row.",
            "Given wires Accept missing, When Build starts, Then this story must not start.",
        ],
        "out_of_scope": ["Plans Cases full wire heights (next story).", "Lab areas.", "Voice."],
        "technical_notes": [
            "ui/desktop/index.html, desktop.css, desktop.js; cache-bust desktop_app.py.",
            "Update IA tests that assert old sticky markers.",
        ],
        "roadmap": "TRACK3-UX after wires Accept.",
    },
    {
        "summary": "Track3: Plans Cases geometry from accepted wire",
        "fr_ids": ["FR-UI-10", "FR-UI-9"],
        "intro": "Implement Plans · Cases real geometry from accepted wire (heights, Cases default, one Add case).",
        "user_story": (
            "As a senior test engineer, I want Cases-first Plans with compact chrome "
            "so that the case list owns the window at ~1280×720."
        ),
        "behaviour": (
            "Surface bar / toolbar / tabs match wire budget. Cases default landing. One Add case menu. "
            "Case list scrolls; chrome does not. Prove in all layout modes A–E."
        ),
        "acceptance": [
            "Given Plans open, When Cases tab is default, Then the case list is the primary work surface under ≤~120px chrome.",
            "Given ~1280×720, When layout mode is each of overlay/stage/orb_hub/split/floating, Then chrome budget holds and first case row is visible.",
            "Given Add case, When opened, Then a single menu covers prior add types (no button farm).",
        ],
        "out_of_scope": ["Manual Confirm dock (next).", "Lab Plans knobs forever-scroll return."],
        "technical_notes": ["ui/desktop Plans section; tests/test_plans_ia.py extend; A–E via layout picker."],
        "roadmap": "TRACK3-UX",
    },
    {
        "summary": "Track3: Manual density + Confirm dock",
        "fr_ids": ["FR-UI-10", "FR-MAN-1"],
        "intro": "Apply shared density to Manual idle/review; Confirm/Cancel dock always fully visible.",
        "user_story": (
            "As a senior test engineer, I want Manual review chrome that never hides Confirm/Cancel "
            "so that the propose loop stays trustworthy."
        ),
        "behaviour": (
            "Same chrome budget as Plans. Proposal list without second header. "
            "Confirm dock outside .area-work, fully visible in all A–E modes when proposals exist."
        ),
        "acceptance": [
            "Given Manual review with proposals, When each layout mode A–E is selected, Then Confirm and Cancel are fully visible and clickable without scrolling the dock away.",
            "Given Manual chrome, When work scrolls, Then no second sticky/filter strip covers the proposal list.",
        ],
        "out_of_scope": ["FR-MAN-2 live circles.", "Voice."],
        "technical_notes": ["manual-* chrome; tests/test_manual_propose_harden.py; A–E verify."],
        "roadmap": "TRACK3-UX",
    },
    {
        "summary": "Track3: Reports + Documents density",
        "fr_ids": ["FR-UI-10", "FR-REP-4"],
        "intro": "Apply accepted wires to Reports library and Documents primary surfaces.",
        "user_story": (
            "As a test manager, I want Reports and Documents to open as calm libraries "
            "so that reading content is first, not toolbar chrome."
        ),
        "behaviour": (
            "One toolbar with search/filter; body scrolls underneath. "
            "Report Settings deep-link unchanged. Density holds in all A–E."
        ),
        "acceptance": [
            "Given Reports/Documents, When open at ~1280×720 in each layout mode A–E, Then chrome ≤~120px and list/body is the primary surface.",
            "Given filters/search, When present, Then they sit in the single toolbar.",
        ],
        "out_of_scope": ["Report section toggles returning to Reports area.", "Lab."],
        "technical_notes": ["rpt-* / doc-* sections; IA tests extend."],
        "roadmap": "TRACK3-UX",
    },
    {
        "summary": "Track3: Settings + Security area-work alignment",
        "fr_ids": ["FR-UI-10", "FR-SET-4", "FR-SEC-1"],
        "intro": (
            "Stop scrolling whole Settings/Security as one piece; adopt outside-scrollport chrome. "
            "Level and credential controls stay visible; OFFICIAL/SECRET unmixed."
        ),
        "user_story": (
            "As a security-conscious tester, I want Settings and Security chrome that keeps "
            "classification and credentials readable while forms scroll."
        ),
        "behaviour": (
            "Title/primary actions in non-scrolling band; form in .area-work. "
            "No collapsing classification into Advanced. Density in all A–E."
        ),
        "acceptance": [
            "Given Settings and Security, When open in each layout mode A–E, Then chrome is outside the scrollport and level/credential affordances stay visible.",
            "Given OFFICIAL vs SECRET, When switching levels, Then stores remain isolated (no merge).",
        ],
        "out_of_scope": ["New connectors.", "Heal/Lab density."],
        "technical_notes": ["app-section-settings / security; security isolation tests stay green."],
        "roadmap": "TRACK3-UX",
    },
    {
        "summary": "Track3: Occlusion verify Primary across A–E",
        "fr_ids": ["FR-UI-10", "FR-UI-7"],
        "intro": (
            "Verification story: occlusion/density checklist across Primary areas in all layout modes. "
            "pytest/HTML first; CU or human-hands for clickability — no soft pass."
        ),
        "user_story": (
            "As a senior test engineer, I want proven clickable chrome in every layout mode "
            "so that Track 3 density is real, not marker-only."
        ),
        "behaviour": (
            "Run ENTERPRISE_LAYOUT_NOTE occlusion checklist on Primary areas for overlay, stage, "
            "orb_hub, split, and floating. Document CU skip/flake or numbered human confirm."
        ),
        "acceptance": [
            "Given each Primary area, When each layout mode A–E is used at ~1280×720, Then primary controls are not covered and Esc/Back returns home.",
            "Given Manual with proposals, When verified, Then Confirm/Cancel remain clickable in every mode.",
            "Given CU unsafe, When used, Then test ticket records CU skipped/flake or human confirm — never soft-pass opened orb home.",
        ],
        "out_of_scope": ["New features.", "Lab occlusion (follow-on)."],
        "technical_notes": [
            "Tiered Computer Use; classic orb; pause Ollama for CU window.",
            "Linked test ticket carries evidence.",
        ],
        "roadmap": "TRACK3-UX close-out gate.",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        print("DRY-RUN epic:", EPIC_SUMMARY)
        for s in STORIES:
            print(" ", s["summary"])
        return 0

    spec_text = (REPO / "docs" / "FUNCTIONAL_SPEC.md").read_text(encoding="utf-8")
    frs = seed.parse_frs(spec_text)
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    created: List[Tuple[str, str]] = []
    epic_key: Optional[str] = None
    first_story: Optional[str] = None

    try:
        existing_epics = j.search_summaries(
            'project = KAN AND issuetype = Epic AND summary ~ "Council Track 3" ORDER BY key ASC'
        )
        epic_key = existing_epics.get(EPIC_SUMMARY)
        if not epic_key:
            for summ, key in existing_epics.items():
                if "Council Track 3" in summ:
                    epic_key = key
                    break
        if not epic_key:
            epic_key = j.create_issue(
                EPIC_SUMMARY, "Epic", epic_body(), labels=["council", "track3"]
            )
        if not epic_key:
            print("FAIL: could not create/find epic")
            for f in j.failures:
                print(" ", f)
            return 1
        print("Epic", epic_key)

        existing = j.search_summaries(
            'project = KAN AND summary ~ "Track3" ORDER BY created DESC'
        )

        for idx, s in enumerate(STORIES):
            summary = s["summary"]
            story_key = None
            for summ, key in existing.items():
                if summ.strip() == summary:
                    story_key = key
                    break
            if not story_key:
                desc = seed.story_description(
                    intro=s["intro"],
                    user_story=s["user_story"],
                    fr_ids=s["fr_ids"],
                    frs=frs,
                    behaviour=s["behaviour"],
                    acceptance=s["acceptance"],
                    out_of_scope=s["out_of_scope"],
                    technical_notes=s["technical_notes"],
                    roadmap=s["roadmap"],
                )
                story_key = j.create_issue(
                    summary,
                    "Story",
                    desc,
                    parent=epic_key,
                    labels=["council", "track3"],
                )
            if not story_key:
                print("FAIL story", summary[:60])
                continue
            if idx == 0:
                first_story = story_key

            test_summary = f"Test: {summary}"
            test_key = None
            for summ, key in existing.items():
                if summ.strip() == test_summary:
                    test_key = key
                    break
            if not test_key:
                existing_t = j.search_summaries(
                    'project = KAN AND issuetype = test AND summary ~ "Track3" ORDER BY created DESC'
                )
                for summ, key in existing_t.items():
                    if summ.strip() == test_summary:
                        test_key = key
                        break
            if not test_key:
                tdesc = seed.test_description(summary, s["acceptance"])
                test_key = j.create_issue(
                    test_summary, "test", tdesc, labels=["test", "track3"]
                )
            if test_key:
                j.link_relates(story_key, test_key)
            created.append((story_key, test_key or "-"))
            print("Story", story_key, "test", test_key, "|", summary[:70])

        cr_note = "\n".join(
            [
                "Council Track 3 CR (2026-11-18) — Designer confirm:",
                "1) Wire accept gate before geometry — yes.",
                "2) Primary-only Track 3; Lab follow-on — yes.",
                "3) Verify density in all layout modes A–E — yes.",
                f"Epic {epic_key}. KAN-297 stays Done (tokens ≠ redesign).",
                "Voice / FR-MAN-2 remain parked.",
            ]
        )
        for key in ("KAN-295", "KAN-297", "KAN-279"):
            j.comment(key, cr_note)
            print("Commented", key)

        pointer = REPO / "docs" / "ops" / "TRACK3_ACTIVE_POINTER.txt"
        pointer.write_text(
            f"epic={epic_key}\nfirst_story={first_story}\n",
            encoding="utf-8",
        )
        print("Pointer", pointer)
    finally:
        j.close()

    if j.failures:
        print("Failures:")
        for f in j.failures:
            print(" ", f)
        return 1

    print("CREATED")
    print(f"  Epic {epic_key}  Active {first_story}")
    for sk, tk in created:
        print(f"  {sk} ↔ {tk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
