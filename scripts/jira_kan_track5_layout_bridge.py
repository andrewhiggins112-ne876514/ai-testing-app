"""Create TRACK5-LAYOUT epic + Phase 1–2 Stories + linked tests. Never prints tokens.

Designer Bridge 2026-11-22: layout enhancement pack Accepted; Active = story 1.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35
PROJECT = "KAN"
LABELS = ["fr-ui-11", "track5-layout", "studio-bridge", "layout-enhancement"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

CU = (
    "CU policy: pytest and HTML/JS/CSS markers are the pass gate. "
    "Computer Use only if a step claims visual occlusion or clickability the markers cannot prove. "
    "If the desktop is unsafe, write exactly 'CU skipped — unsafe' on this test ticket. "
    "That sentence does not pass any step. Evidence that only says the area was opened is a fail."
)

MOCK = "docs/mockups/layout_enhancement_pack/"

AREAS = (
    "Settings, Suites, Plans (Cases/Coverage/Trace/History/Draft/Run), Reports, "
    "Documents, Security, Heal, Manual, Desktop Lab, Sandboxes Lab"
)


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    levels = path.parent / "levels"
    level = str(data.get("security_level") or "OFFICIAL").upper()
    cred_path = levels / level / "credentials.json"
    if cred_path.exists():
        creds = json.loads(cred_path.read_text(encoding="utf-8-sig"))
        data = {**data, **creds}
    return (
        (data.get("jira_url") or "https://ai-testing-lab.atlassian.net").rstrip("/"),
        (data["jira_email"], data["jira_api_token"]),
    )


def adf_from_lines(lines_in: List[str]) -> Dict[str, Any]:
    content: List[Dict[str, Any]] = []
    for line in lines_in:
        text = line if line.strip() else " "
        content.append({"type": "paragraph", "content": [{"type": "text", "text": text}]})
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
    return {"type": "doc", "version": 1, "content": content}


def split_lines(text: str) -> List[str]:
    return text.strip().split("\n")


class Jira:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.client = httpx.Client(
            timeout=90.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        self.failures: List[str] = []

    def close(self) -> None:
        self.client.close()

    def _req(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        r = self.client.request(method, f"{self.base}{path}", **kwargs)
        for _ in range(5):
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
        return r

    def find_by_summary(self, summary: str, issue_type: str) -> Optional[str]:
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": (
                    f'project = {PROJECT} AND issuetype = "{issue_type}" '
                    'AND labels = "track5-layout" ORDER BY created DESC'
                ),
                "maxResults": 50,
                "fields": ["summary"],
            },
        )
        if r.status_code >= 300:
            self.failures.append(f"search {issue_type}: {r.status_code}")
            return None
        for issue in r.json().get("issues") or []:
            fields = issue.get("fields") or {}
            if (fields.get("summary") or "").strip() == summary:
                return issue["key"]
        return None

    def create_issue(
        self,
        summary: str,
        issue_type: str,
        body: str,
        parent_epic: Optional[str] = None,
    ) -> Optional[str]:
        existing = self.find_by_summary(summary, issue_type)
        if existing:
            print(f"exists {issue_type}: {existing}")
            return existing
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf_from_lines(split_lines(body)),
            "labels": LABELS,
        }
        if parent_epic and issue_type == "Story":
            # Team-managed often uses parent; company-managed may use Epic Link — try parent.
            fields["parent"] = {"key": parent_epic}
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201 and parent_epic and issue_type == "Story":
            # Retry without parent if site rejects parent on Story
            fields.pop("parent", None)
            r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201:
            self.failures.append(f"create {issue_type} {summary[:48]}: {r.status_code} {r.text[:200]}")
            return None
        key = r.json().get("key")
        print(f"created {issue_type}: {key}")
        return key

    def link_relates(self, a: str, b: str) -> None:
        payload = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": a},
            "outwardIssue": {"key": b},
        }
        r = self._req("POST", "/rest/api/3/issueLink", json=payload)
        if r.status_code >= 300:
            self.failures.append(f"link {a}<->{b}: {r.status_code}")
        else:
            print(f"linked Relates {a} <-> {b}")

    def comment(self, key: str, body_lines: List[str]) -> None:
        r = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf_from_lines(body_lines)},
        )
        if r.status_code >= 300:
            self.failures.append(f"comment {key}: {r.status_code}")
        else:
            print(f"commented {key}")


EPIC_SUMMARY = "TRACK5-LAYOUT — Secondary area structure pack (all App areas)"

EPIC_BODY = f"""
## Intro
Polish FR-UI-11 craft across every secondary App area after TRACK4 grammar shipped. Quiet empty states, keyboard scan, one scroll per pane, Plans compact booleans and case sections, Documents toolbar, Heal confirm copy, Lab detail disclosure; Phase 2 evidence-first detail later. Theme, orb, home/chat, and App nav stay locked.

## Who this is for
- Senior Test Engineer — daily scan craft in every App area
- Developers implementing shared desktop CSS/JS
- Designer — Accepted mockups in {MOCK}

## Problem / outcome
TRACK4 delivered scan+detail grammar. Residual craft is inconsistent (empty heroes missing, scroll fight, page-width Plans booleans). This epic makes the grammar feel finished without Lab density, voice, or FR-MAN-2.

## Requirements
FR-UI-11 enhancement (2026-11-22 Bridge): quiet empty line; unfocused detail shows Select a row; keyboard Up/Down/Enter/Esc without confirming side effects; one scroll per pane with sticky scan header; Plans compact Show archived / Enabled / Archived / Pause on fail; Plans case detail sections Edit / Run / Quarantine / Known issue with pinned Save/Run; Documents tab-scoped toolbar; Heal Approve selected confirm names count and files not written (no bulk Reject); Lab Advanced disclosure on Desktop/Suites/Sandboxes; optional Suites/Reports filter in existing toolbar; Phase 2 evidence-first detail later. Areas: {AREAS}.

## Scope
In: structure craft inside existing areas. Out: theme/orb/home/App nav; TRACK3-LAB density; KAN-81 voice; FR-MAN-2; KPI dashboards; bulk Heal Reject; real Playwright trace runner.

## Success criteria
Phase 1 stories Done with marker pytest; every area named in AC; Phase 2 separate story.

## Dependencies / risks
Mockups Accepted. Keyboard must not approve heal or confirm Jira. CU only when markers insufficient.

## Technical notes
ui/desktop/index.html, desktop.css, desktop.js. Markers per story. {CU}

## Mockups
{MOCK}README.md, 00-structure-wire.html, 01a–01k themed areas, 02-annotated-build-note.html, 03-rejected.html
"""

STORIES: List[Dict[str, str]] = [
    {
        "id": "1",
        "summary": "All areas: quiet empty, keyboard scan, and one scroll per pane",
        "test": "Test: TRACK5 all-areas empty keyboard scroll markers",
        "roadmap": "TRACK5-LAYOUT-1",
        "body": f"""
## Intro
Shared Phase 1 craft for every secondary App area: quiet empty scan, Select a row detail, keyboard scan contract, one scroll per pane with sticky scan header.

## Who this is for
Senior Test Engineer scanning any App area; agents implementing shared desktop grammar.

## User story
As a test engineer, I want empty scans and keyboard focus to behave the same in every area, so that I can move through collections without hero cards or a third scroll fighting the split.

## Requirements
FR-UI-11 enhancement Phase 1 shared craft. Areas: {AREAS}. Theme/orb/home/App nav locked. Charter Frame untouched.

## Behaviour
- Empty collection: one quiet line (area-specific; no secrets; no KPI/hero).
- Rows present but none focused: detail shows Select a row; Save/Run/Confirm not armed as if focused.
- Keyboard: Up/Down move focused row; Enter focuses detail; Esc returns to scan (area Esc/Back to orb unchanged). Shortcuts never confirm Jira, approve/reject heal, delete, restore, or remove.
- Scan and detail each own their scroll; scan thead sticky inside scan scroller; .area-work is not a third scroll on the split at desktop width. Chrome including Manual Confirm dock stays outside work scroll in layouts A–E.
- Structure-token guard: no new rail on one-collection areas; no second rail beside Plans/Documents tabs.

## Acceptance criteria
1. Given each secondary area with an empty collection, When the scan is shown, Then a single quiet empty line is present and no hero/KPI card is present.
2. Given rows and no selection, When the detail is shown, Then it shows Select a row and primary destructive/save actions are not presented as if a row were focused.
3. Given a focused scan, When Up/Down/Enter/Esc are used as specified, Then focus moves without confirming side effects.
4. Given a split scan+detail at desktop width, When both panes overflow, Then each scrolls independently and the scan header stays visible in the scan pane.
5. Given Settings, Security, Manual, Reports, Documents, Heal, Desktop, Suites, Sandboxes, and Plans, When markers are inspected, Then the same empty/keyboard/scroll behaviour applies. Manual Charter Frame markup is unchanged.
6. Given pytest for this story, When it runs, Then it exits 0 on HTML/JS/CSS markers. {CU}

## {DOD}

## Out of scope
Plans compact booleans and case sections (story 2). Documents/Heal/Lab disclosure (story 3). Evidence-first Phase 2. TRACK3-LAB. Voice. FR-MAN-2.

## Dependencies
Accepted mockups {MOCK}. Active Build story for TRACK5 Phase 1.

## Technical notes
ui/desktop/* shared scan helpers. Roadmap {{{{ROADMAP}}}}. Mock: 00-structure-wire.html + every 01*-themed-*.html Empty preview.

## Mockups
{MOCK}
""".replace("{{{{ROADMAP}}}}", "TRACK5-LAYOUT-1"),
        "test_body": f"""
## Intro
Verifies All areas: quiet empty, keyboard scan, and one scroll per pane.

## Who this is for
Testers and Cursor agents.

## Test procedure
1. Run the story pytest module once landed. Expected: exit 0; markers for empty line, select-a-row detail, keyboard contract attributes, and dual-pane scroll on every secondary area named in the story.
2. Spot-check desktop_app.py → App → Suites (or Plans) → empty vs focused row. Expected: quiet empty; Select a row; arrow keys move focus without approving anything.
3. {CU}

## Acceptance criteria
Slim copy of parent AC 1–6.

## Evidence
Pytest command + pass count; optional CU note.
""",
    },
    {
        "id": "2",
        "summary": "Plans: compact booleans and case-detail sections",
        "test": "Test: TRACK5 Plans compact booleans and case sections",
        "roadmap": "TRACK5-LAYOUT-2",
        "body": f"""
## Intro
Plans residual FR-UI-11 craft: compact Show archived / Enabled / Archived / Pause on fail; case detail grouped Edit / Run / Quarantine / Known issue with pinned Save and Run.

## Who this is for
Senior Test Engineer editing cases; developers in #app-section-plans.

## User story
As a test engineer, I want Plans booleans on compact hits and a sectioned case detail, so that I can edit without page-width labels or scrolling past Save.

## Requirements
FR-UI-11 enhancement Plans clause. Other areas that already use compact checks must not regress.

## Behaviour
- #plan-show-archived, #plan-case-enabled, #plan-case-archived, #plan-pause-on-fail use compact checkbox pattern (not page-width stack-label / check-row).
- Case detail keeps every existing field under named sections Edit, Run, Quarantine, Known issue. Save and Run selected case stay visible while section body scrolls.
- History A/B radios remain radio cells. Cases scan grammar unchanged.

## Acceptance criteria
1. Given Plans Cases and Run, When inspecting those four controls, Then each uses a compact checkbox class and the label is not a page-width hit.
2. Given a focused case, When the detail is shown, Then Edit / Run / Quarantine / Known issue sections exist and no prior field id is removed.
3. Given Save and Run selected case, When the section body scrolls, Then those actions remain visible.
4. Given Manual/Security/Desktop/Sandboxes/Documents/Heal compact checks, When this ships, Then they do not regress.
5. Pytest markers exit 0. {CU}

## {DOD}

## Out of scope
Shared empty/keyboard (story 1). Documents/Heal/Lab (story 3). Theme/nav.

## Dependencies
Prefer after story 1. Mock 01c-themed-plans-cases.html, 01d-themed-plans-tabs.html.

## Technical notes
ui/desktop Plans panels. Roadmap TRACK5-LAYOUT-2.

## Mockups
{MOCK}01c-themed-plans-cases.html
""",
        "test_body": f"""
## Intro
Verifies Plans compact booleans and case-detail sections.

## Test procedure
1. Pytest for plan markers. Expected: exit 0.
2. desktop_app.py → Plans → Cases: compact Enabled/Archived; sections visible; Save pinned.
3. {CU}

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest command + pass count.
""",
    },
    {
        "id": "3",
        "summary": "Documents toolbar, Heal confirm copy, and Lab detail disclosure",
        "test": "Test: TRACK5 Documents Heal Lab disclosure markers",
        "roadmap": "TRACK5-LAYOUT-3",
        "body": f"""
## Intro
Phase 1 area-specific craft: Documents tab-scoped toolbar; Heal bulk Approve confirm copy; Desktop/Suites/Sandboxes detail disclosure for secondary fields.

## Who this is for
Test engineers using Documents, Heal, and Lab tools.

## User story
As a test engineer, I want Documents actions to match the active tab, Heal confirm to name what I approve, and Lab secondary fields collapsed, so that primary actions stay clear without TRACK3-LAB density.

## Requirements
FR-UI-11 enhancement Documents/Heal/Lab disclosure. No bulk Reject. Confirms unchanged.

## Behaviour
- Documents: Propose toolbar shows Parse; Uploads shows Refresh. Confirm/Decline stay off the scan row. Keep remains a checkbox cell.
- Heal: Approve selected confirm names the count and states files are not written. Reject stays on focused detail only. Sel never approves.
- Lab: Desktop, Suites, Sandboxes detail show primary Save/Run first; secondary fields in one closed disclosure. Remove/smoke/save confirm rules unchanged. Heal Approve/Reject stay visible (not inside disclosure).
- Settings, Security, Manual, Reports, Plans: no-regression (no second rail/toolbar; Charter Frame untouched).
- Suites/Reports optional filter may live in the existing toolbar only.

## Acceptance criteria
1. Given Documents Propose vs Uploads, When switching tabs, Then the toolbar actions match the tab and Confirm/Decline are not on the scan row.
2. Given Heal with N selected, When Approve selected is proposed, Then confirm copy includes the count and files are not written; no bulk Reject control exists.
3. Given Desktop, Suites, and Sandboxes detail, When first shown, Then secondary fields are inside a closed disclosure and primary actions remain visible.
4. Given Settings/Security/Manual/Reports/Plans, When this ships, Then no second App rail or Charter Frame change appears.
5. Pytest markers exit 0. {CU}

## {DOD}

## Out of scope
TRACK3-LAB density epic. Evidence-first Phase 2. Voice. FR-MAN-2.

## Dependencies
Prefer after story 1. Mocks 01f, 01h, 01b, 01j, 01k.

## Technical notes
Roadmap TRACK5-LAYOUT-3. data-*-detail-disclosure markers on Lab areas.

## Mockups
{MOCK}
""",
        "test_body": f"""
## Intro
Verifies Documents toolbar, Heal confirm copy, Lab disclosure.

## Test procedure
1. Pytest markers exit 0.
2. Spot-check Documents tabs, Heal confirm text, Lab Advanced closed.
3. {CU}

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest command + pass count.
""",
    },
    {
        "id": "4",
        "summary": "All run-bearing areas: evidence-first detail slot",
        "test": "Test: TRACK5 evidence-first detail slot markers",
        "roadmap": "TRACK5-LAYOUT-4",
        "body": f"""
## Intro
Phase 2: detail panes for run-bearing rows lead with last-result evidence before edit fields. Does not add a Playwright tracing runner.

## Who this is for
Senior Test Engineer and developers reviewing failures.

## User story
As a test engineer, I want the detail pane to lead with last result and evidence links, so that I see the failure before editing fields — without a fake Trace control.

## Requirements
FR-UI-11 enhancement Phase 2 evidence-first slot. Redaction unchanged. Trace line must say capture is not hooked yet.

## Behaviour
- Plans cases, Reports, Heal, Manual session review, Suites last run, Desktop last smoke: detail leads with status/time/failure class (and screenshot link where stored) before edit fields.
- Documents/Settings/Security/Sandboxes: slot only when the row has evidence; otherwise absent.
- Screenshot opens from detail with existing non-OCR warning. Scan columns are not image cards.
- Trace copy states runner hook is not present; no control that pretends trace.notice.txt is a real trace.

## Acceptance criteria
1. Given a focused run-bearing row with evidence, When detail opens, Then the evidence slot precedes edit fields.
2. Given a row without evidence on Documents/Settings/Security/Sandboxes, When detail opens, Then the evidence slot is absent.
3. Given a screenshot link, When opened, Then the non-OCR warning still applies.
4. Given Trace wording, When shown, Then it states capture is not hooked; no fake Trace runner control.
5. Pytest markers exit 0. {CU}

## {DOD}

## Out of scope
Real Playwright trace runner (separate later story). TRACK3-LAB. Voice. FR-MAN-2. KPI galleries.

## Dependencies
After Phase 1 stories 1–3 Done. Not Active until then.

## Technical notes
Roadmap TRACK5-LAYOUT-4. Mock Phase 2 dashed hints on Reports/Heal/Manual.

## Mockups
{MOCK}01e-themed-reports.html, 01h-themed-heal.html, 01i-themed-manual.html
""",
        "test_body": f"""
## Intro
Verifies evidence-first detail slot (Phase 2).

## Test procedure
1. Pytest markers exit 0 after implementation.
2. Spot-check Plans/Reports/Heal detail leading with evidence.
3. Confirm Trace copy says not hooked. {CU}

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest command + pass count.
""",
    },
]


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    created: Dict[str, str] = {}
    try:
        epic = j.create_issue(EPIC_SUMMARY, "Epic", EPIC_BODY)
        if not epic:
            print("FATAL: epic not created", file=sys.stderr)
            return 1
        created["epic"] = epic

        for s in STORIES:
            story = j.create_issue(s["summary"], "Story", s["body"], parent_epic=epic)
            if not story:
                continue
            created[f"story{s['id']}"] = story
            j.link_relates(epic, story)
            test = j.create_issue(s["test"], "test", s["test_body"])
            if test:
                created[f"test{s['id']}"] = test
                j.link_relates(story, test)
                j.comment(
                    test,
                    [
                        f"Bridge created for {s['summary']}.",
                        f"Roadmap {s['roadmap']}. Mock pack {MOCK}.",
                        "Do not mark Done until pytest evidence exists.",
                    ],
                )
            j.comment(
                story,
                [
                    f"Studio+Council Bridge 2026-11-22. Epic {epic}.",
                    f"Roadmap {s['roadmap']}. Mock pack Accepted: {MOCK}",
                    "Active Build: story 1 only until Done; Phase 2 is story 4.",
                    "Deferred unchanged: TRACK3-LAB, KAN-81/82 voice, FR-MAN-2.",
                ],
            )

        j.comment(
            epic,
            [
                "TRACK5-LAYOUT Bridge 2026-11-22.",
                "Phase 1: stories 1–3. Phase 2: story 4 (not Active until Phase 1 Done).",
                f"Mockups: {MOCK}",
                "After pack: TRACK3-LAB density, then real Playwright trace deepen.",
            ],
        )

        out = Path(__file__).resolve().parents[1] / "docs" / "ops" / "TRACK5_LAYOUT_KEYS.json"
        out.write_text(json.dumps(created, indent=2) + "\n", encoding="utf-8")
        print("keys:", json.dumps(created))
        print("wrote", out)
        if j.failures:
            print("failures:", *j.failures, sep="\n  ", file=sys.stderr)
            return 2
        return 0
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
