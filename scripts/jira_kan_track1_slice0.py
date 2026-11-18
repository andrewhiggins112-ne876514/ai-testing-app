"""
Council Track 1 Slice-0 → Jira: Epic + Stories + linked test tickets.

Covers Plans IA tidy, stub honesty, other App-area UI tidy, Manual Primary,
and Charter Frame MVP — not Manual-only.

Credentials from local settings / level credentials. Never prints tokens.

Usage:
  python scripts/jira_kan_track1_slice0.py
  python scripts/jira_kan_track1_slice0.py --dry-run
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

EPIC_SUMMARY = "Council Track 1 — UX tidy + Manual Charter Frame"

# (summary, fr_ids, intro, user_story, behaviour, acceptance, out_of_scope, technical_notes, roadmap)
STORIES: List[Dict[str, Any]] = [
    {
        "summary": "Track1: Plans IA tidy — Cases-first sections + sticky toolbar",
        "fr_ids": ["FR-UI-9", "FR-UI-7", "FR-PLAN-1", "FR-PLAN-2"],
        "intro": (
            "Council Track 1 (2026-11-18) first Build slice. Plans became a forever-scroll of every growth feature. "
            "Reorganise for progressive disclosure so testers can open a plan, see cases, and run without hunting."
        ),
        "user_story": (
            "As a senior test engineer, I want the Plans area organised into clear sections with Cases first "
            "so that I can find and run work without endless scrolling."
        ),
        "behaviour": (
            "Default landing for an open plan is Cases (list + select/edit), not Draft or Schedule. "
            "Sticky toolbar: plan picker, Open/Refresh, search, one-line status. "
            "Sections/tabs: Draft & import; Cases; Coverage & drift; Traceability; History; Run setup. "
            "One Add case menu (types inside) instead of a button farm. "
            "Move env manage / sandbox manage / schedule detail into Settings, Sandboxes, or collapsed Run setup. "
            "Do not remove capabilities — relocate and collapse. Gradio may get a lighter pass; desktop is primary."
        ),
        "acceptance": [
            "Given an open plan on desktop Plans, When the area loads, Then Cases is the default primary content above the fold (not Draft/Schedule).",
            "Given Plans, When the sticky toolbar is visible, Then plan picker, open/refresh, search, and status remain reachable while scrolling section content.",
            "Given Plans, When adding a case, Then types are reached from one Add case control (not a long row of separate primary Add buttons).",
            "Given Coverage, Traceability, History, and Schedule/run-policy controls, When browsing Plans, Then they live under secondary sections/tabs or collapsed Run setup — not competing with the case list as equal forever-scroll chapters.",
            "Given existing plan APIs and data, When IA changes ship, Then no plan/case/run data is deleted and all prior capabilities remain reachable.",
        ],
        "out_of_scope": [
            "Charter Frame / Manual recorder (later Track1 stories).",
            "Live FR-MAN-2 circles.",
            "Real Selenium/Cypress runners.",
            "Voice (KAN-81).",
        ],
        "technical_notes": [
            "ui/desktop/index.html, ui/desktop/desktop.js, desktop_app.py cache-bust.",
            "Verify with desktop_app.py + Computer Use; pytest for DOM markers / section ids.",
            "docs/FUNCTIONAL_SPEC.md FR-UI-9; docs/ops/ROADMAP.md TRACK1-IA.",
        ],
        "roadmap": "TRACK1-IA — first Active Build story after Slice-0.",
    },
    {
        "summary": "Track1: Framework stub honesty — labels, disable Run, no Selenium default",
        "fr_ids": ["FR-PLUG-3", "FR-TEST-2"],
        "intro": (
            "G9/KAN-233 correctly returns not-implemented for Selenium/Cypress, but UI can imply they run "
            "(including Plans framework defaulting toward Selenium). Make stubs honest without cutting options."
        ),
        "user_story": (
            "As a tester, I want Selenium and Cypress clearly marked not ready and not runnable "
            "so that I am never misled into thinking a stub run passed."
        ),
        "behaviour": (
            "Label Playwright as ready; Selenium/Cypress as not implemented / never pass. "
            "Disable or block Run for non-ready frameworks. "
            "Default framework selection must be Playwright (never Selenium/Cypress). "
            "Keep selectable stubs (cut nothing). Settings and Plans must agree."
        ),
        "acceptance": [
            "Given Plans or Settings framework controls, When listing frameworks, Then Playwright is labelled ready and Selenium/Cypress are labelled not implemented (or equivalent honest stub wording).",
            "Given a Selenium or Cypress case/selection, When the user attempts Run, Then the run does not report pass and UI makes clear it is not implemented.",
            "Given a new framework case or default select, When the control initialises, Then the default is Playwright — never Selenium or Cypress.",
            "Given existing stub runners, When this ships, Then Selenium/Cypress options remain available (not removed).",
        ],
        "out_of_scope": [
            "Implementing real Selenium/Cypress runners.",
            "Plans IA section redesign (sibling story).",
            "Voice.",
        ],
        "technical_notes": [
            "plugins/framework_switch.py, plans/framework_case.py, ui/desktop Plans + Settings.",
            "tests/test_framework_switch.py, tests/test_plan_framework_case.py — extend.",
            "Do not reopen KAN-233 as failed; this is honesty UX deepen.",
        ],
        "roadmap": "TRACK1-IA companion — can ship with or immediately after Plans IA tidy.",
    },
    {
        "summary": "Track1: Suites area UI tidy — progressive disclosure",
        "fr_ids": ["FR-UI-7", "FR-TEST-5"],
        "intro": (
            "Council review: after Plans, Suites has the same stack-risk (path, list, run, import-adjacent chrome). "
            "Tidy so import/run existing Playwright suites stays usable without a dense scroll."
        ),
        "user_story": (
            "As a tester, I want the Suites area to show path + suite list + run actions clearly "
            "so that I can import and run an existing Playwright project without UI clutter."
        ),
        "behaviour": (
            "Primary: suite path status, list/discover, run selected. "
            "Secondary: advanced options / help collapsed. "
            "Align visual hierarchy with Plans Cases-first pattern where sensible. "
            "Do not change npx Playwright suite runner behaviour."
        ),
        "acceptance": [
            "Given Suites on desktop, When the area opens, Then path/status and suite list/run are above the fold without hunting through unrelated chrome.",
            "Given advanced or help content, When present, Then it is collapsed or secondary — not equal weight to list/run.",
            "Given existing playwright_suite APIs, When tidy ships, Then discover/list/run behaviour is unchanged and external project files are never deleted.",
        ],
        "out_of_scope": [
            "New suite runners (Selenium/Cypress).",
            "Plans IA (sibling).",
            "Manual Charter Frame.",
        ],
        "technical_notes": [
            "ui/desktop Suites section; plugins/playwright_suite.py unchanged functionally.",
            "Verify desktop_app.py + Computer Use; pytest DOM markers.",
        ],
        "roadmap": "TRACK1-IA — after Plans tidy (or parallel if capacity).",
    },
    {
        "summary": "Track1: Reports area UI tidy — library-first polish",
        "fr_ids": ["FR-UI-7", "FR-REP-4", "FR-REP-2"],
        "intro": (
            "Reports is already library/viewer (KAN-247) with section toggles in Report Settings. "
            "Council asked for secondary-screen tidy: reduce residual clutter, clarify empty state and open-detail flow."
        ),
        "user_story": (
            "As a test manager, I want Reports to feel like a clear library of past runs "
            "so that I can open evidence without scrolling past settings-like chrome."
        ),
        "behaviour": (
            "Keep library-first: list → open detail (markdown/screenshot/JSON as available). "
            "Empty state explains how a run produces a report; deep link to Report Settings remains. "
            "No section-include editor in Reports area (stays Settings). "
            "Visual hierarchy and spacing cleanup only — no new report metrics engine."
        ),
        "acceptance": [
            "Given Reports on desktop, When opened, Then the report list (or clear empty state) is primary — not section toggles.",
            "Given a saved report, When selected, Then detail opens without requiring Report Settings.",
            "Given Report Settings deep link, When used, Then it opens Settings → Report category (FR-SET-4).",
            "Given this tidy, When shipped, Then no report files are deleted and exporter behaviour is unchanged.",
        ],
        "out_of_scope": [
            "New report section types.",
            "Cloud upload of reports.",
            "Plans/Suites tidy (siblings).",
        ],
        "technical_notes": [
            "ui/desktop Reports; /api/reports*; FR-REP-4 already shipped — this is polish.",
        ],
        "roadmap": "TRACK1-IA — after Plans (and ideally Suites).",
    },
    {
        "summary": "Track1: Secondary App areas UI tidy — Documents, Heal, Desktop, Sandboxes",
        "fr_ids": ["FR-UI-7", "FR-UI-8"],
        "intro": (
            "Human ask: apart from main UI, several screens need tidying/reordering. "
            "Light consistent pass on Documents, Heal review, Desktop, and Sandboxes so Lab tools match Primary area clarity."
        ),
        "user_story": (
            "As a tester, I want Lab tool areas to share a calm primary-action layout "
            "so that Documents, Heal, Desktop, and Sandboxes feel consistent and less scroll-heavy."
        ),
        "behaviour": (
            "Per area: one primary job above the fold; secondary/help collapsed. "
            "Documents: ingest/list primary. Heal: proposals list + approve/reject primary. "
            "Desktop: smoke/status primary. Sandboxes: list + prepare/status primary. "
            "Do not remove Lab tools from App menu. No behaviour change to heal policy or desktop runner beyond layout."
        ),
        "acceptance": [
            "Given each of Documents, Heal review, Desktop, Sandboxes, When opened on desktop, Then the primary action/list is visible without a long undifferentiated scroll of equal-weight blocks.",
            "Given Lab tools App menu group, When navigating, Then all four areas remain reachable (FR-UI-8).",
            "Given heal proposals / desktop smoke / sandbox records / documents, When tidy ships, Then data and confirm gates are unchanged.",
        ],
        "out_of_scope": [
            "New heal algorithms.",
            "New sandbox orchestration features.",
            "Manual area (sibling stories).",
            "Settings hub redesign (already categorised).",
        ],
        "technical_notes": [
            "ui/desktop index/js for each app-section; keep API contracts.",
            "Verify with Computer Use spot-checks per area.",
        ],
        "roadmap": "TRACK1-IA — after Plans; can follow Suites/Reports.",
    },
    {
        "summary": "Track1: Manual Primary App area + Plans deep-link shell",
        "fr_ids": ["FR-UI-1", "FR-UI-7", "FR-MAN-1"],
        "intro": (
            "Council choice A3: Manual is a Primary App menu item and Plans offers Start manual on this case. "
            "Shell only — session recorder/frame may land in the next story if split, but navigation must exist."
        ),
        "user_story": (
            "As a tester, I want Manual in the Primary App menu and a Plans deep-link "
            "so that I can start a session from home or from a case without hunting."
        ),
        "behaviour": (
            "Add Manual to Primary group (Chat, Settings, Plans, Manual, Reports, Documents). "
            "Dedicated area surface; Esc/Back → orb home (not a second landing). "
            "Plans: Start manual on this case pre-fills plan/case/story when known. "
            "Empty/start form shell ready for Charter Frame session controls."
        ),
        "acceptance": [
            "Given the compact App menu, When opened, Then Manual appears under Primary (not only Lab tools).",
            "Given Manual, When opened then Esc/Back, Then orb home returns (one home).",
            "Given a Plans case with optional Jira key, When Start manual on this case is used, Then Manual opens with plan/case (and story when known) pre-filled.",
            "Given Gradio, When this ships, Then desktop is required; Gradio Manual may be stub/minimal.",
        ],
        "out_of_scope": [
            "Live FR-MAN-2 circles / mist-watch.",
            "Silent video / keylogger.",
            "Voice.",
        ],
        "technical_notes": [
            "ui/desktop App menu Primary list; area routing; Plans deep-link button.",
            "docs/design/H1_MANUAL_SESSION_CAPTURE.md §9.7.",
        ],
        "roadmap": "TRACK1-H1 — after TRACK1-IA tidy stories.",
    },
    {
        "summary": "Track1: FR-MAN-1 Charter Frame MVP — session, region frame, assist/mist toggles, review/confirm",
        "fr_ids": ["FR-MAN-1", "FR-JIRA-4", "FR-JIRA-5", "FR-AGENT-4", "FR-SEC-1"],
        "intro": (
            "Implement H1 Charter Frame per design §9 (KAN-241 remains design-Done). "
            "Free-region snip frame; agent-assist and armed-mist toggles default OFF (G1); "
            "story required when Jira-bound; test ticket optional; End → review → confirm batch."
        ),
        "user_story": (
            "As a tester, I want to record a manual session inside a calm region frame with optional agent assist "
            "so that I can capture evidence and propose ticket updates only after I confirm."
        ),
        "behaviour": (
            "Explicit Start (charter); optional Jira story (required if ticket-bound) + optional test key. "
            "Charter Frame: resizable free region; click-through to AUT; optional inner mist only if mist toggle on. "
            "Agent assist OFF: notes + opt-in stills only. Assist ON: local unpublished drafts only — never live Jira. "
            "End → review → Propose bug/comment/step-update → two-step confirm; cancel writes nothing. "
            "Level-scoped session store; E3 redaction; no silent video/keylog. FR-MAN-2 live circles out of scope."
        ),
        "acceptance": [
            "Given Manual, When Start is not pressed, Then no frame and no capture run in the background.",
            "Given Start with charter, When the session opens, Then a free-region Charter Frame can be resized and defaults to click-through for the AUT.",
            "Given agent assist and mist toggles, When a new session starts, Then both default OFF; turning mist on shows light mist only inside the frame; assist OFF never produces AI step/bug drafts during Record.",
            "Given ticket-bound mode, When linking Jira, Then story key is required and test key is optional; Start does not write to Jira.",
            "Given End session, When Propose is chosen, Then previews appear and Jira writes occur only after explicit confirm; Cancel writes nothing.",
            "Given OFFICIAL vs SECRET, When listing sessions, Then only the active level’s sessions are visible and paths stay isolated.",
        ],
        "out_of_scope": [
            "FR-MAN-2 live OCR/circles (parked; needs DPIA).",
            "Cursor Computer Use as product watcher.",
            "Voice capture.",
            "Cloud sync of sessions.",
            "Real Selenium/Cypress runners.",
        ],
        "technical_notes": [
            "docs/design/H1_MANUAL_SESSION_CAPTURE.md §9; plans/manual_session_design.py outline.",
            "Reuse plans/defect_packet.py, B7 notes, jira confirm + audit.",
            "Storage: plans/{LEVEL}/sessions/ under LOCALAPPDATA.",
            "Verify pytest isolation/confirm; desktop Computer Use for frame/toggles.",
        ],
        "roadmap": "TRACK1-H1 — after Manual shell; do not implement FR-MAN-2.",
    },
]


def epic_body() -> str:
    return "\n".join(
        [
            "Intro",
            "Council Full Room 2026-11-18 Track 1: tidy secondary UX (Plans first, then other App areas) "
            "and stub honesty, then implement FR-MAN-1 Charter Frame with Manual as Primary. "
            "Live on-screen AI circles are FR-MAN-2 and stay parked.",
            "",
            "Who this is for",
            "Senior testers (daily), test managers (audit evidence), designers (IA), Cursor Build agents.",
            "",
            "Problem / outcome",
            "Catalogue A–H designs complete; Active was stuck on deferred voice. Plans and other screens are dense; "
            "Selenium/Cypress look runnable; Manual recorder design exists but is unshipped.",
            "",
            "Requirements",
            "FR-UI-9 Plans IA; FR-PLUG-3 stub honesty; FR-UI-7 area polish; FR-UI-1 Manual Primary; FR-MAN-1 Charter Frame; FR-MAN-2 parked.",
            "",
            "Scope",
            "In: Plans/Suites/Reports/Lab-area tidy; stub honesty; Manual shell; Charter Frame MVP (assist/mist toggles default off).",
            "Out: Voice KAN-81; FR-MAN-2 live circles; real Selenium/Cypress runners; cutting stubs.",
            "",
            "Success criteria",
            "Stories completed in order with linked test evidence; WORK_LOG Active points at next open Track1 story; nothing existing removed.",
            "",
            "Dependencies / risks",
            "Home PC VRAM — no live vision in MVP. Jira writes stay two-step confirm. OFFICIAL/SECRET isolation.",
            "",
            "Technical notes",
            "docs/FUNCTIONAL_SPEC.md; docs/design/H1_MANUAL_SESSION_CAPTURE.md §9–§10; docs/ops/ROADMAP.md TRACK1-IA/H1.",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print(f"DRY RUN Epic: {EPIC_SUMMARY}")
        for s in STORIES:
            print(f"  Story: {s['summary']}")
            print(f"  test:  Test: {s['summary']}")
        return 0

    spec_text = (REPO / "docs" / "FUNCTIONAL_SPEC.md").read_text(encoding="utf-8")
    frs = seed.parse_frs(spec_text)
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    created: List[Tuple[str, str]] = []
    try:
        existing_epics = j.search_summaries(
            f'project = KAN AND issuetype = Epic AND summary ~ "Council Track 1" ORDER BY key ASC'
        )
        epic_key = existing_epics.get(EPIC_SUMMARY)
        if not epic_key:
            # fuzzy: any matching summary
            for summ, key in existing_epics.items():
                if "Council Track 1" in summ:
                    epic_key = key
                    break
        if not epic_key:
            epic_key = j.create_issue(
                EPIC_SUMMARY, "Epic", epic_body(), labels=["council", "track1"]
            )
        if not epic_key:
            print("FAIL: could not create/find epic")
            for f in j.failures:
                print(" ", f)
            return 1
        print("Epic", epic_key)

        for s in STORIES:
            summary = s["summary"]
            existing = j.search_summaries(f'project = KAN AND summary ~ "Track1" ORDER BY created DESC')
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
                    labels=["council", "track1"],
                )
            if not story_key:
                print("FAIL story", summary[:60])
                continue

            test_summary = f"Test: {summary}"
            test_key = None
            for summ, key in existing.items():
                if summ.strip() == test_summary:
                    test_key = key
                    break
            if not test_key:
                # also search exact
                existing_t = j.search_summaries(
                    f'project = KAN AND issuetype = test AND summary ~ "Track1" ORDER BY created DESC'
                )
                for summ, key in existing_t.items():
                    if summ.strip() == test_summary:
                        test_key = key
                        break
            if not test_key:
                tdesc = seed.test_description(summary, s["acceptance"])
                test_key = j.create_issue(
                    test_summary, "test", tdesc, labels=["test", "track1"]
                )
            if test_key:
                j.link_relates(story_key, test_key)
            created.append((story_key, test_key or "-"))
            print("Story", story_key, "test", test_key, "|", summary[:70])

        # Comment on design story KAN-241
        j.comment(
            "KAN-241",
            "\n".join(
                [
                    "Council Track 1 CR (2026-11-18) — this ticket stays design-Done.",
                    f"Implement via epic {epic_key} Charter Frame + Manual stories (not a reopen of KAN-241 as recorder shipped).",
                    "See docs/design/H1_MANUAL_SESSION_CAPTURE.md §9–§10; FR-MAN-2 live circles parked.",
                ]
            ),
        )
        print("Commented KAN-241")
    finally:
        j.close()

    if j.failures:
        print("Failures:")
        for f in j.failures:
            print(" ", f)
        return 1

    print("CREATED")
    for sk, tk in created:
        print(f"  {sk} ↔ {tk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
