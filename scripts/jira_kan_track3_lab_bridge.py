"""Create TRACK3-LAB epic + Stories + linked tests. Never prints tokens.

Council+Designer Bridge 2026-11-23: Lab density FR-UI-10 follow-on.
Active = Story 1 (wires Accept + chrome budget). Geometry 2–4 after Accept.
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
LABELS = ["fr-ui-10", "track3-lab", "council-bridge", "lab-density"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

CU = (
    "CU policy: pytest and HTML/JS/CSS markers are the pass gate for geometry stories. "
    "Computer Use only on the Lab A–E occlusion story (or if a step claims clickability markers cannot prove). "
    "If the desktop is unsafe, write exactly 'CU skipped — unsafe' on this test ticket. "
    "That sentence does not pass any step. Evidence that only says a Lab area was opened is a fail."
)

WIRES = "docs/design/TRACK3_AREA_WIRES.md §8"
AREAS = "Heal, Desktop Lab, Suites, Sandboxes"

FR_UI_10 = (
    "FR-UI-10 (Enterprise area density — Track 3): Primary App areas "
    "(Settings, Plans, Manual, Reports, Documents) use accepted Track 3 wires for real geometry — "
    "not token-only CSS. Shared non-scrolling chrome stack: surface bar + one toolbar + optional section tabs; "
    "common-case chrome ≤ ~120px; work content scrolls in .area-work. Filter/search live in that one toolbar "
    "(no second filter strip; class/marker names must not say sticky). Plans · Cases matches the enterprise "
    "Cases wire. Manual Confirm/Cancel stay fully visible on their dock. Settings and Security use the same "
    "outside-scrollport chrome; classification and credential controls stay readable; OFFICIAL/SECRET stores "
    "stay unmixed. Density must hold in all App area layout modes A–E (FR-UI-7). "
    "Lab tools (Heal/Desktop/Suites/Sandboxes full density) are this follow-on epic after Primary Track 3. "
    "Security density already shipped with Primary (KAN-318). "
    "Hard accept gate: no Lab HTML/CSS geometry until Designer accepts Lab wires (Accept Lab wires)."
)

FR_UI_7 = (
    "FR-UI-7: Dedicated App areas with layout modes overlay, stage, orb_hub, split, floating. "
    "Density and occlusion must hold in every mode."
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
                    'AND labels = "track3-lab" ORDER BY created DESC'
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
            fields["parent"] = {"key": parent_epic}
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201 and parent_epic and issue_type == "Story":
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


EPIC_SUMMARY = "TRACK3-LAB — Lab area density (FR-UI-10 follow-on)"

EPIC_BODY = f"""
## Intro
Apply FR-UI-10 enterprise density geometry to Lab App areas ({AREAS}) after Primary Track 3 (KAN-307) and TRACK4/5 grammar+craft. Same chrome budget as Primary; Lab wires Accept before geometry. Theme, orb, home/chat, and App nav stay locked.

## Who this is for
- Senior Test Engineer — denser Suites/Heal/Desktop/Sandboxes desks
- Developers — ui/desktop Lab sections only
- Designer — Lab wires in {WIRES}

## Problem / outcome
Primary density shipped; Lab still carries tall intro bands and Suites path/button-farm chrome. Grammar (FR-UI-11) and TRACK5 craft already landed — this epic is geometry/budget only.

## Requirements
{FR_UI_10}
{FR_UI_7}

## Scope
In: {AREAS}; ≤~120px chrome; .area-work scroll; Lab wires Accept; Lab A–E occlusion.
Out: Primary areas; Security (KAN-318); KAN-310 scaffold redo; TRACK4/5 craft redo; theme/orb/home/App nav; voice KAN-81; FR-MAN-2; real Playwright trace; auto-apply heal; silent sandbox remove; Gradio-first.

## Success criteria
Designer Accept Lab wires; four Lab areas meet chrome budget markers; Suites Done-gates Suites+Sandboxes story; Lab A–E clickability proven (CU/human) without soft-pass.

## Dependencies / risks
Relates Primary epic KAN-307. Risk: inventing geometry without Accept; re-polishing TRACK5; soft-passing A–E.

## Technical notes
ui/desktop/index.html, desktop.css, desktop.js; {WIRES}; markers per story. {CU}

## Mockups
{WIRES} (ASCII wires; light Studio — not a full mock pack)
"""

STORIES: List[Dict[str, str]] = [
    {
        "id": "1",
        "summary": "TRACK3-LAB: Lab wires Accept + chrome budget alignment",
        "test": "Test: TRACK3-LAB Lab wires Accept and chrome budget markers",
        "roadmap": "TRACK3-LAB-1",
        "body": f"""
## Intro
Active first story: Designer Accept of Lab wires in {WIRES}, then chrome-budget markers on {AREAS} without redoing KAN-310 scaffold.

## Who this is for
Designer (Accept gate); Senior Test Engineer; Build agents.

## User story
As the Designer, I want signed Lab density wires and shared chrome-budget markers on the four Lab areas, so that geometry stories cannot invent chrome or soft-pass “opened Lab.”

## Requirements
{FR_UI_10}
Wires source: {WIRES}. Reuse Primary stack. Do not reopen theme/orb/home/App nav. Do not redo sticky renames.

## Behaviour
- Lab ASCII wires for Suites, Sandboxes, Heal, Desktop live in {WIRES} §8 (Bridge may land docs).
- Stop for Designer phrase: Accept Lab wires. No Lab HTML/CSS geometry (Stories 2–4) before Accept.
- After Accept: markers prove surface + one toolbar + one status; no intro h3/About above toolbar; common-case stack ≤~120px; work scrolls in .area-work; TRACK5 Advanced stays closed by default.
- Do not re-apply KAN-310 class rename across Primary.

## Acceptance criteria
1. Given {WIRES} §8, When Designer has not Accepted, Then Stories 2–4 stay blocked for geometry HTML/CSS.
2. Given Designer replies Accept Lab wires, When Story 1 continues, Then chrome-budget markers exist on Heal, Desktop, Suites, and Sandboxes without inventing a second toolbar or sticky-named markers.
3. Given each Lab area, When inspecting chrome, Then there is no intro label band above the toolbar and About/Policy/Advanced sit under .area-work.
4. Given TRACK4/5 markers (scan craft, Lab disclosure, Heal no bulk Reject, evidence-first Trace not hooked), When this ships, Then they do not regress.
5. Given pytest for this story, When it runs after Accept+markers, Then it exits 0. {CU}

## {DOD}

## Out of scope
Suites/Sandboxes/Heal/Desktop area-specific density polish (Stories 2–3). Lab A–E occlusion (Story 4). Voice. FR-MAN-2. Trace runner.

## Dependencies
Council Bridge 2026-11-23. Relates epic TRACK3-LAB. Relates Primary KAN-307.

## Technical notes
Roadmap TRACK3-LAB-1. Files: {WIRES}; ui/desktop markers only after Accept.

## Mockups
{WIRES}
""",
        "test_body": f"""
## Intro
Verifies Lab wires Accept gate and chrome budget markers.

## Who this is for
Testers and Cursor agents.

## Test procedure
1. Confirm {WIRES} §8 Lab Accept checklist and Designer Accept Lab wires comment/evidence. Expected: Accept recorded before geometry Stories 2–4.
2. After markers land: run story pytest. Expected: exit 0; Lab areas have chrome-budget markers; no intro above toolbar.
3. Spot-check desktop_app.py → App → Suites: one toolbar band; Advanced holds Import. {CU}

## Acceptance criteria
Slim copy of parent AC 1–5.

## Evidence
Accept note + pytest command + pass count.
""",
    },
    {
        "id": "2",
        "summary": "TRACK3-LAB: Suites + Sandboxes Lab density",
        "test": "Test: TRACK3-LAB Suites and Sandboxes density markers",
        "roadmap": "TRACK3-LAB-2",
        "body": f"""
## Intro
Apply accepted Lab wires density to Suites (Done gate) and Sandboxes. Grammar and TRACK5 craft stay locked.

## Who this is for
Senior Test Engineer running Playwright suites and sandbox orchestration.

## User story
As a test engineer, I want Suites path/actions/status in one ≤~120px toolbar and Sandboxes enable/orchestrate compacted the same way, so that the suite list owns the height.

## Requirements
{FR_UI_10}
Wires: {WIRES} §8a–8b. Suites is the Done gate for this story.

## Behaviour
- Suites: Path + Discover/List/Run selected/Run all + one status in a single toolbar; Import/save path remains Advanced; first row visible without scrolling chrome away.
- Sandboxes: Enable / Save plugin / Action / Orchestrate / one status compacted to budget; Remove stays detail propose-then-confirm; Advanced closed Help only.
- No second filter strip; no sticky-named markers; theme/orb/home/App nav untouched.

## Acceptance criteria
1. Given Suites at ~1280×720, When measuring chrome above .area-work, Then the common-case stack is ≤~120px and path+actions+one status share one toolbar.
2. Given Suites Advanced, When first shown, Then Import/save path is inside closed Advanced — not a second chrome row.
3. Given Sandboxes, When the toolbar is shown, Then Enable/Save/Action/Orchestrate fit the budget and Remove confirm remains in detail.
4. Given TRACK5 scan craft on both areas, When this ships, Then quiet empty / Select a row / keyboard / disclosure do not regress.
5. Pytest markers exit 0. Suites AC blocks Done even if Sandboxes markers are easy. {CU}

## {DOD}

## Out of scope
Heal/Desktop (Story 3). A–E occlusion (Story 4). Auto-apply heal. Silent remove.

## Dependencies
After Story 1 Done + Designer Accept Lab wires.

## Technical notes
Roadmap TRACK3-LAB-2. ui/desktop Suites + Sandboxes sections.

## Mockups
{WIRES} §8a–8b
""",
        "test_body": f"""
## Intro
Verifies Suites + Sandboxes Lab density.

## Test procedure
1. Pytest markers exit 0.
2. desktop_app.py → Suites: one toolbar; Import in Advanced; first row visible.
3. Sandboxes: compact toolbar; Remove confirm in detail. {CU}

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest command + pass count.
""",
    },
    {
        "id": "3",
        "summary": "TRACK3-LAB: Heal + Desktop Lab density",
        "test": "Test: TRACK3-LAB Heal and Desktop density markers",
        "roadmap": "TRACK3-LAB-3",
        "body": f"""
## Intro
Apply accepted Lab wires density to Heal review and Desktop Lab. Confirm gates unchanged.

## Who this is for
Senior Test Engineer approving heals and running desktop smoke.

## User story
As a test engineer, I want Heal and Desktop chrome within the Primary budget so the diff and plugin detail own the height without weakening approve/reject confirms.

## Requirements
{FR_UI_10}
Wires: {WIRES} §8c–8d. Security stays out.

## Behaviour
- Heal: Filter + Refresh (+ bulk Approve when shown) + one status in one toolbar; Approve/Reject on focused detail fully visible; bulk Approve still confirm + files not written; no bulk Reject; no auto-apply.
- Desktop: Run smoke / Run demo steps + one status in one toolbar; Save stays in detail; Advanced closed for secondary fields.
- No intro above toolbar; TRACK5 evidence-first and scan craft preserved.

## Acceptance criteria
1. Given Heal, When chrome is inspected, Then one toolbar holds filter/refresh/bulk/status and Approve/Reject remain on focused detail.
2. Given Heal bulk Approve, When proposed, Then confirm still names count and files are not written; no bulk Reject; no auto-apply path.
3. Given Desktop, When chrome is inspected, Then smoke/demo + status fit ≤~120px stack and Save stays in detail.
4. Given TRACK5 markers, When this ships, Then they do not regress.
5. Pytest markers exit 0. {CU}

## {DOD}

## Out of scope
Suites/Sandboxes (Story 2). A–E (Story 4). Changing heal semantics. Voice.

## Dependencies
Prefer after Story 2. Requires Accept Lab wires.

## Technical notes
Roadmap TRACK3-LAB-3. ui/desktop Heal + Desktop sections.

## Mockups
{WIRES} §8c–8d
""",
        "test_body": f"""
## Intro
Verifies Heal + Desktop Lab density.

## Test procedure
1. Pytest markers exit 0.
2. Heal: one toolbar; Approve/Reject on detail; no bulk Reject.
3. Desktop: smoke/demo toolbar; Save in detail. {CU}

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest command + pass count.
""",
    },
    {
        "id": "4",
        "summary": "TRACK3-LAB: Lab occlusion verify A–E",
        "test": "Test: TRACK3-LAB Lab occlusion A–E verify",
        "roadmap": "TRACK3-LAB-4",
        "body": f"""
## Intro
Verify Lab density holds in every FR-UI-7 layout mode for {AREAS} only. Do not re-close Primary KAN-320.

## Who this is for
Designer demos; Senior Test Engineer; agents verifying clickability.

## User story
As a test engineer, I want Lab areas usable in overlay/stage/orb_hub/split/floating so chrome never covers the first work row or primary actions.

## Requirements
{FR_UI_10}
{FR_UI_7}

## Behaviour
- Per Lab area × modes A–E at ~1280×720 on desktop_app.py: title+Back; one toolbar clickable; first work row visible; scroll .area-work without chrome occlusion; Esc/Back home; compact ▦ only.
- Heal Approve/Reject and Sandboxes Remove confirm stay clickable when relevant.
- pytest markers first; clickability = CU or numbered human-hands. Never soft-pass “opened Lab.”

## Acceptance criteria
1. Given each of Heal, Desktop, Suites, Sandboxes in modes A–E, When the area is open, Then surface+toolbar stay fully visible and the first work row is visible without scrolling chrome away.
2. Given scroll of .area-work, When content moves, Then chrome bands do not slide over inputs.
3. Given clickability proof, When CU is unsafe, Then the test ticket records CU skipped — unsafe and the story stays open until human confirm — never soft-pass opened Lab.
4. Given Primary KAN-320, When this ships, Then Primary occlusion is not reopened as scope.
5. Pytest markers exit 0; CU/human evidence attached for clickability. {CU}

## {DOD}

## Out of scope
New density geometry. Voice. FR-MAN-2. Trace runner.

## Dependencies
After Stories 1–3 Done.

## Technical notes
Roadmap TRACK3-LAB-4. Extend or mirror tests/test_occlusion_verify_ae.py for Lab areas only.

## Mockups
{WIRES} + §9 A–E contract
""",
        "test_body": f"""
## Intro
Verifies Lab occlusion across A–E.

## Test procedure
1. Pytest Lab occlusion markers exit 0.
2. CU or numbered human-hands: each Lab area × A–E clickability. Expected: toolbar and first row usable; no soft-pass.
3. If unsafe: write CU skipped — unsafe; leave story open until human confirm.

## Acceptance criteria
Slim copy of parent AC.

## Evidence
Pytest + CU/human notes.
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
                        f"Roadmap {s['roadmap']}. Wires {WIRES}.",
                        "Do not mark Done until pytest / Accept evidence exists.",
                    ],
                )
            j.comment(
                story,
                [
                    f"Council+Designer Bridge 2026-11-23. Epic {epic}.",
                    f"Roadmap {s['roadmap']}. Lab wires: {WIRES}",
                    "Active Build: story 1 only until Done; Stories 2–4 after Accept Lab wires.",
                    "Parked: voice KAN-81/82, FR-MAN-2, CI, real Playwright trace deepen.",
                    "Relates Primary epic KAN-307 (do not reopen Primary children).",
                ],
            )

        j.link_relates(epic, "KAN-307")
        j.comment(
            epic,
            [
                "TRACK3-LAB Bridge 2026-11-23.",
                "Story 1: Lab wires Accept + chrome budget. Stories 2–4 after Accept.",
                f"Wires: {WIRES}",
                "After track: real Playwright trace deepen. Park voice / FR-MAN-2 / CI.",
            ],
        )
        j.comment(
            "KAN-307",
            [
                f"Lab follow-on epic seeded: {epic} (TRACK3-LAB Bridge 2026-11-23).",
                "Primary Track 3 stays Done; Lab density is the new epic.",
            ],
        )

        out = Path(__file__).resolve().parents[1] / "docs" / "ops" / "TRACK3_LAB_KEYS.json"
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
