"""
Council Track 2 Slice-0 → Jira: Epic + Bug + Stories + linked test tickets.

Order (human CR 2026-11-18): non-overlapping chrome first → FR-MAN-1 completion
stories → enterprise layout research note → tokens after note accepted.
FR-MAN-2 and voice stay parked.

Credentials from local settings. Never prints tokens.

Usage:
  python scripts/jira_kan_track2_slice0.py
  python scripts/jira_kan_track2_slice0.py --dry-run
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

EPIC_SUMMARY = "Council Track 2 — Area chrome + Manual completion"

BUG: Dict[str, Any] = {
    "summary": "Bug: Sticky area chrome covers fields and buttons",
    "body": "\n".join(
        [
            "Symptom",
            "Sticky toolbars inside scrolling App area bodies can cover primary fields, section tabs, "
            "and primary buttons (including Confirm/Cancel) on Plans, Suites, Reports, Manual, and Lab.",
            "",
            "Expected",
            "Area chrome is a non-overlapping header; work surface controls stay fully visible and clickable "
            "at rest and while scrolling (FR-UI-9 Track 2 CR).",
            "",
            "Actual",
            "`position: sticky; top: 0` inside `.area-body { overflow: auto }` with no reliable scroll-padding; "
            "multi-row toolbars eat the form viewport.",
            "",
            "Environment",
            "Windows native desktop_app.py (pywebview / Edge WebView2); desk87–desk93 UI tidy track.",
            "",
            "Replication steps",
            "1. Run .\\venv\\Scripts\\python.exe desktop_app.py",
            "2. Open App menu → Plans (or Suites / Reports / Manual / Lab Documents)",
            "3. Scroll the area body and/or use a short window height so the sticky bar wraps",
            "4. Observe fields, tabs, or primary buttons under or behind the sticky chrome",
            "",
            "Relates",
            "Track 2 chrome Story (fix); KAN-265 Plans IA; KAN-275 Manual shell.",
        ]
    ),
}

# Build order = list order. First Story is Active after Slice-0.
STORIES: List[Dict[str, Any]] = [
    {
        "summary": "Track2: Non-overlapping area chrome (FR-UI-9)",
        "fr_ids": ["FR-UI-9", "FR-UI-7"],
        "intro": (
            "Council Track 2 first Build slice. Track 1 sticky toolbars occlude fields and buttons. "
            "Implement non-overlapping area chrome across Plans, Suites, Reports, Manual, and Lab."
        ),
        "user_story": (
            "As a senior test engineer, I want area command bars that never cover my fields or buttons "
            "so that I can use Plans and Manual without fighting the chrome."
        ),
        "behaviour": (
            "Move area primary chrome outside the scrollport (or equivalent). "
            "Sticky inside scrolling .area-body is not required. "
            "Primary fields, section tabs, primary buttons, Confirm/Cancel stay fully visible and clickable. "
            "Keep progressive disclosure and Cases-first Plans IA. Do not rewrite nav or kill orb home."
        ),
        "acceptance": [
            "Given desktop Plans/Suites/Reports/Manual/Lab, When the area is open at a short window height, Then primary fields, section tabs, and primary buttons are fully visible and clickable (not covered by chrome).",
            "Given a confirm row (Manual propose/confirm or equivalent), When chrome is present, Then Confirm and Cancel remain clickable.",
            "Given FR-UI-9, When this ships, Then area chrome is a non-overlapping header (sticky-inside-scrollport not required).",
            "Given existing area APIs and IDs, When chrome geometry changes, Then capabilities remain reachable (no cut).",
            "Given desktop_app.py, When verified, Then Computer Use evidence shows clickable primary controls (not only HTML markers).",
        ],
        "out_of_scope": [
            "New nav paradigm / tall rail / top tab bar.",
            "Design-system / token project (later research note).",
            "FR-MAN-2; voice.",
        ],
        "technical_notes": [
            "ui/desktop/index.html, desktop.css, desktop.js; desktop_app.py cache-bust.",
            "Fix related Bug: Sticky area chrome covers fields and buttons.",
            "tests/test_nav_overlap.py and area IA tests — extend; Computer Use mandatory.",
        ],
        "roadmap": "TRACK2-CHROME — first Active Build story.",
    },
    {
        "summary": "Track2: Trustworthy Manual session loop (headed)",
        "fr_ids": ["FR-MAN-1", "FR-JIRA-5"],
        "intro": (
            "KAN-277 shipped a thin MVP; headed Start→notes→End→review→confirm was not proven as a calm daily loop. "
            "Make Manual trustworthy on the native window."
        ),
        "user_story": (
            "As a senior test engineer, I want one calm Start → exercise → note → End → review → Cancel/Confirm loop "
            "so that I trust Manual for real exploratory work."
        ),
        "behaviour": (
            "Start, charter, Charter Frame, notes, opt-in stills, End review, Propose, Cancel, Confirm "
            "are all reachable without chrome fights. Cancel writes nothing to Jira. "
            "Confirm stays two-step. Assist/mist defaults remain off. No voice, no live circles."
        ),
        "acceptance": [
            "Given Manual on desktop_app.py, When Start with charter, Then Charter Frame appears and notes/stills/End/Cancel are reachable.",
            "Given an open session, When Cancel after confirm, Then no Jira write occurs and local draft is discarded per product rules.",
            "Given End → Propose → Confirm path, When Cancel at confirm, Then nothing is written to Jira; When Confirm yes, Then write uses existing FR-JIRA-5 path + audit.",
            "Given Computer Use, When the loop is exercised, Then evidence is recorded on the linked test ticket (not marker-only pytest).",
        ],
        "out_of_scope": [
            "Window/monitor snap (sibling story).",
            "Real Ollama assist drafts (sibling).",
            "FR-MAN-2; voice.",
        ],
        "technical_notes": [
            "plans/manual_session.py; ui/desktop Manual + charter overlay; /api/manual-sessions*.",
            "Depends on Track2 chrome story (or ship after it).",
        ],
        "roadmap": "TRACK2-MAN — after chrome.",
    },
    {
        "summary": "Track2: Real agent-assist local drafts (honest assist)",
        "fr_ids": ["FR-MAN-1", "FR-AGENT-4"],
        "intro": (
            "Assist-on currently can echo notes into assist_drafts. Completion requires real local unpublished "
            "step/bug drafts via Ollama, or explicit honesty that hints are not AI."
        ),
        "user_story": (
            "As a tester, I want Assist-on to produce real local unpublished drafts "
            "so that review is useful without silent Jira writes."
        ),
        "behaviour": (
            "Assist default remains OFF. When ON, produce real local unpublished step/bug drafts using local Ollama "
            "(7B–8B). Never silent Jira. Never keylog/clipboard/mic. "
            "If AI is unavailable, UI states that clearly — no fake AI."
        ),
        "acceptance": [
            "Given assist OFF, When recording, Then no AI step/bug drafts are produced.",
            "Given assist ON and Ollama available, When notes/stills accumulate, Then local unpublished drafts appear in review (not mere note echo labelled as AI).",
            "Given assist ON and Ollama unavailable, When the session runs, Then the UI shows an honest unavailable state (no fake drafts).",
            "Given any assist draft, When Propose/Confirm, Then Jira writes still require two-step confirm.",
        ],
        "out_of_scope": [
            "Live OCR/circles (FR-MAN-2).",
            "Cloud LLM requirement.",
            "Voice.",
        ],
        "technical_notes": [
            "plans/manual_session.py assist_drafts; local Ollama client already in app.",
            "Home PC: one 7B–8B model; do not pull 32B.",
        ],
        "roadmap": "TRACK2-MAN — after trustworthy loop.",
    },
    {
        "summary": "Track2: Charter Frame window/monitor snap",
        "fr_ids": ["FR-MAN-1"],
        "intro": (
            "H1 §9 B1 locked free-region snip for MVP and deferred window/monitor snap. "
            "Completion includes snap targets so testers can quickly frame an AUT window or monitor."
        ),
        "user_story": (
            "As a tester, I want to snap the Charter Frame to a window or monitor "
            "so that I do not hand-draw the region every session."
        ),
        "behaviour": (
            "Keep free-region resize/drag. Add snap-to-window and snap-to-monitor actions. "
            "Frame remains click-through to AUT except chrome. No full-desktop blocking glass."
        ),
        "acceptance": [
            "Given an open Charter Frame, When snap-to-monitor is chosen, Then the frame matches the selected monitor bounds (within product DPI rules).",
            "Given snap-to-window, When a target window is chosen, Then the frame matches that window’s bounds.",
            "Given free-region mode, When the user resizes, Then prior free-region behaviour still works.",
            "Given mist/assist toggles, When snapping, Then toggles and click-through chrome rules remain unchanged.",
        ],
        "out_of_scope": [
            "Silent video; FR-MAN-2 circles.",
            "Capturing passwords/OTP deliberately.",
        ],
        "technical_notes": [
            "Charter Frame overlay in ui/desktop; Windows geometry APIs via pywebview/python — prefer existing stack.",
            "docs/design/H1_MANUAL_SESSION_CAPTURE.md §9.1 B1.",
        ],
        "roadmap": "TRACK2-MAN — after assist honesty.",
    },
    {
        "summary": "Track2: Page context from headed AUT + annotate still",
        "fr_ids": ["FR-MAN-1", "FR-TEST-4"],
        "intro": (
            "H1 §2 allows page URL/title when a headed AUT/Playwright context already exists, "
            "and annotate-still during record. Wire these for completion."
        ),
        "user_story": (
            "As a tester, I want known AUT page context and annotated stills on the session "
            "so that bug proposals have usable evidence."
        ),
        "behaviour": (
            "When lab already has a headed Playwright/AUT context, attach URL + document title to the session/notes. "
            "Never global keylog. Opt-in stills support annotate-still (human). Redaction E3 applies."
        ),
        "acceptance": [
            "Given a headed AUT context is known, When a Manual session is recording, Then URL and title can appear on the session evidence without a keylogger.",
            "Given no AUT context, When recording, Then the session still works (notes/stills only) without errors.",
            "Given an opt-in still, When annotate-still is used, Then annotation is stored with the still locally.",
            "Given export/propose paths, When secrets appear in URL/title/notes, Then E3 redaction rules apply.",
        ],
        "out_of_scope": [
            "Continuous screen grab / OCR circles.",
            "Clipboard/mic capture.",
        ],
        "technical_notes": [
            "Reuse existing Playwright session/context if present; plans/manual_session stills APIs.",
        ],
        "roadmap": "TRACK2-MAN — after window snap.",
    },
    {
        "summary": "Track2: Manual session library + GDPR session wipe",
        "fr_ids": ["FR-MAN-1", "FR-SEC-2", "FR-SEC-1"],
        "intro": (
            "Completion needs a usable session list (open/ended), reopen review for ended drafts, "
            "and privacy wipe covering Manual sessions per level."
        ),
        "user_story": (
            "As a tester, I want to find past Manual sessions and delete them with GDPR wipe "
            "so that level-scoped evidence stays under my control."
        ),
        "behaviour": (
            "List sessions for active level only. Reopen ended draft for review/propose when allowed. "
            "Privacy wipe / lab delete includes sessions/{session_id} for that level. "
            "OFFICIAL/SECRET never merge."
        ),
        "acceptance": [
            "Given OFFICIAL vs SECRET, When listing sessions, Then only the active level’s sessions appear.",
            "Given an ended session draft, When reopened from the library, Then review/propose remains available without silent Jira.",
            "Given GDPR/privacy wipe for a level, When confirmed, Then that level’s Manual session files and stills are removed.",
            "Given level switch confirm, When switching levels, Then the previous level’s open session is not visible on the new level.",
        ],
        "out_of_scope": [
            "Cloud sync (H3).",
            "Cross-level merge.",
        ],
        "technical_notes": [
            "plans/manual_session.py list_sessions; settings/privacy wipe hooks; Security Privacy UI.",
        ],
        "roadmap": "TRACK2-MAN — after page context.",
    },
    {
        "summary": "Track2: Manual propose/confirm harden (failure class + visibility)",
        "fr_ids": ["FR-MAN-1", "FR-JIRA-4", "FR-JIRA-5", "FR-HEAL-4"],
        "intro": (
            "Harden End→review→propose so defect packets are complete, failure class gates Bug create, "
            "and Confirm/Cancel cannot be occluded."
        ),
        "user_story": (
            "As a tester, I want clear propose previews and always-visible Confirm/Cancel "
            "so that I never file the wrong ticket or lose the confirm controls."
        ),
        "behaviour": (
            "Propose Bug uses defect-packet shape; create_bug only for product_bug (or explicit Bug pick). "
            "Comment / local note / step-update preview remain. Confirm UI always on-screen and clickable. "
            "Audit on successful write."
        ),
        "acceptance": [
            "Given failure class product_bug (or explicit Bug), When Propose Bug + Confirm, Then create_bug path is used with symptom/expected/actual/environment/replication.",
            "Given non-product_bug without explicit Bug pick, When proposing, Then Bug create is blocked or redirected per FR-HEAL-4.",
            "Given review/confirm UI, When the window is short, Then Confirm and Cancel stay fully visible and clickable.",
            "Given successful confirm, When write completes, Then jira_write_audit gains an entry and session marks submitted items.",
        ],
        "out_of_scope": [
            "YOLO auto-file.",
            "FR-MAN-2.",
        ],
        "technical_notes": [
            "Reuse plans/defect_packet.py, failure_class, jira confirm helpers.",
        ],
        "roadmap": "TRACK2-MAN — after session library.",
    },
    {
        "summary": "Track2: Enterprise layout research note (docs)",
        "fr_ids": ["FR-UI-9", "FR-UI-7"],
        "intro": (
            "Docs-only research: calm Windows enterprise density for this desktop shell. "
            "Not a component library. Feeds a later tokens story after human accepts the note."
        ),
        "user_story": (
            "As the designer/PO, I want a short local layout note "
            "so that later chrome polish follows researched practices without a SaaS rebrand."
        ),
        "behaviour": (
            "Write 1–2 pages under docs/design/: type scale, spacing, header max height, occlusion checklist, "
            "one Plans wire. Local-first; no cloud fonts/telemetry. Orb home stays."
        ),
        "acceptance": [
            "Given docs/design/, When the note ships, Then it covers type, spacing, header height, occlusion checklist, and one Plans wire.",
            "Given product constraints, When the note ships, Then it forbids tall rail, top tab bar, purple SaaS clone, and cloud font CDNs.",
            "Given human review, When the note is accepted, Then a later tokens Build story may proceed; coding tokens is out of this story.",
        ],
        "out_of_scope": [
            "Implementing tokens/CSS in this story.",
            "Rewriting navigation.",
        ],
        "technical_notes": [
            "docs/design/ENTERPRISE_LAYOUT_NOTE.md (or similar).",
            "After human accepts → Track2 tokens story.",
        ],
        "roadmap": "TRACK2-UX — after Manual completion stories.",
    },
    {
        "summary": "Track2: Apply enterprise layout tokens (after note accepted)",
        "fr_ids": ["FR-UI-9", "FR-UI-3"],
        "intro": (
            "Apply the accepted enterprise layout note as small CSS/token changes in the existing shell. "
            "Blocked until the research note story is Done and the human accepts the note."
        ),
        "user_story": (
            "As a test manager, I want the desktop shell to look calmly enterprise "
            "so that sponsor demos match the product’s seriousness."
        ),
        "behaviour": (
            "Implement spacing/type/header height from the accepted note inside current accent system. "
            "No second shell, no WebGL restyle of classic orbs, no cloud fonts."
        ),
        "acceptance": [
            "Given the accepted layout note, When tokens ship, Then desktop areas match the note’s spacing/type/header rules.",
            "Given orb home and accents, When tokens ship, Then FR-UI-3 accents remain and orb home is unchanged.",
            "Given occlusion checklist, When verified on desktop_app.py, Then chrome still does not cover primary controls.",
        ],
        "out_of_scope": [
            "New design system package.",
            "Voice; FR-MAN-2.",
        ],
        "technical_notes": [
            "ui/desktop/desktop.css variables; cache-bust desktop_app.py.",
            "Do not start until research note accepted.",
        ],
        "roadmap": "TRACK2-UX — last; after note acceptance.",
    },
]


def epic_body() -> str:
    return "\n".join(
        [
            "Intro",
            "Council Full Room 2026-11-18 Track 2 (human CR): fix sticky occlusion, then complete FR-MAN-1 "
            "beyond the KAN-277 MVP, then enterprise layout research → tokens after acceptance.",
            "",
            "Who this is for",
            "Senior testers (daily Manual/Plans), test managers (sponsor-ready chrome), designer/PO, Cursor Build agents.",
            "",
            "Problem / outcome",
            "Track 1 tidy left sticky bars covering fields; Manual MVP is thin; enterprise look is not yet suitable.",
            "",
            "Requirements",
            "FR-UI-9 non-overlapping area chrome; FR-MAN-1 completion (loop, assist, snap, page context, library/GDPR, propose harden); "
            "layout research note; tokens after accept. FR-MAN-2 parked. Voice deferred.",
            "",
            "Scope",
            "In: chrome geometry; Manual completion stories listed on this epic; docs layout note; later tokens.",
            "Out: Voice KAN-81; FR-MAN-2 live circles; nav rewrite; component library; cutting Gradio/orb/stubs.",
            "",
            "Success criteria",
            "Stories completed in listed order with linked test evidence; WORK_LOG Active never points at KAN-81 while this track is open.",
            "",
            "Dependencies / risks",
            "Home PC VRAM for assist drafts. Confirm/Cancel visibility is compliance-sensitive. OFFICIAL/SECRET isolation.",
            "",
            "Technical notes",
            "docs/FUNCTIONAL_SPEC.md FR-UI-9 / FR-MAN-1; docs/design/H1_MANUAL_SESSION_CAPTURE.md; docs/ops/ROADMAP.md TRACK2-*.",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print(f"DRY RUN Epic: {EPIC_SUMMARY}")
        print(f"  Bug: {BUG['summary']}")
        for s in STORIES:
            print(f"  Story: {s['summary']}")
            print(f"  test:  Test: {s['summary']}")
        return 0

    spec_text = (REPO / "docs" / "FUNCTIONAL_SPEC.md").read_text(encoding="utf-8")
    frs = seed.parse_frs(spec_text)
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)

    created: List[Tuple[str, str]] = []
    bug_key: Optional[str] = None
    epic_key: Optional[str] = None
    first_story: Optional[str] = None

    try:
        existing_epics = j.search_summaries(
            'project = KAN AND issuetype = Epic AND summary ~ "Council Track 2" ORDER BY key ASC'
        )
        epic_key = existing_epics.get(EPIC_SUMMARY)
        if not epic_key:
            for summ, key in existing_epics.items():
                if "Council Track 2" in summ:
                    epic_key = key
                    break
        if not epic_key:
            epic_key = j.create_issue(
                EPIC_SUMMARY, "Epic", epic_body(), labels=["council", "track2"]
            )
        if not epic_key:
            print("FAIL: could not create/find epic")
            for f in j.failures:
                print(" ", f)
            return 1
        print("Epic", epic_key)

        # Bug (idempotent by summary)
        existing_bugs = j.search_summaries(
            'project = KAN AND issuetype = Bug AND summary ~ "Sticky area chrome" ORDER BY created DESC'
        )
        bug_key = existing_bugs.get(BUG["summary"])
        if not bug_key:
            for summ, key in existing_bugs.items():
                if "Sticky area chrome" in summ:
                    bug_key = key
                    break
        if not bug_key:
            bug_key = j.create_issue(
                BUG["summary"], "Bug", BUG["body"], labels=["council", "track2", "occlusion"]
            )
        print("Bug", bug_key)

        existing = j.search_summaries(
            'project = KAN AND summary ~ "Track2" ORDER BY created DESC'
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
                    labels=["council", "track2"],
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
                    'project = KAN AND issuetype = test AND summary ~ "Track2" ORDER BY created DESC'
                )
                for summ, key in existing_t.items():
                    if summ.strip() == test_summary:
                        test_key = key
                        break
            if not test_key:
                tdesc = seed.test_description(summary, s["acceptance"])
                test_key = j.create_issue(
                    test_summary, "test", tdesc, labels=["test", "track2"]
                )
            if test_key:
                j.link_relates(story_key, test_key)
            if bug_key and idx == 0:
                j.link_relates(story_key, bug_key)
                j.link_relates(bug_key, "KAN-265")
                j.link_relates(bug_key, "KAN-275")
            created.append((story_key, test_key or "-"))
            print("Story", story_key, "test", test_key, "|", summary[:70])

        # CR comments on prior Done tickets
        cr_note = "\n".join(
            [
                "Council Track 2 CR (2026-11-18) — human accepted:",
                "1) FR-UI-9 non-overlapping header (sticky no longer required).",
                "2) Fix-first: chrome occlusion before Manual deepen.",
                "3) Full FR-MAN-1 completion backlog under epic "
                + str(epic_key)
                + " (MVP KAN-277 stays Done; do not reopen as failed).",
                "4) Next Build waits until Active points at Track2 chrome — not KAN-81 voice.",
                "FR-MAN-2 and voice remain parked/deferred.",
            ]
        )
        for key in ("KAN-265", "KAN-275", "KAN-277", "KAN-241"):
            j.comment(key, cr_note)
            print("Commented", key)

        # Pointer file for WORK_LOG consumers
        pointer = REPO / "docs" / "ops" / "TRACK2_ACTIVE_POINTER.txt"
        pointer.write_text(
            f"epic={epic_key}\nbug={bug_key}\nfirst_story={first_story}\n",
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
    print(f"  Epic {epic_key}  Bug {bug_key}  Active {first_story}")
    for sk, tk in created:
        print(f"  {sk} ↔ {tk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
