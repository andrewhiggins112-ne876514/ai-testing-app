"""Seed OPERATE + GAP-CR epics/stories/tests + Baseline comments. Never prints tokens.

Council Slice-0 2026-11-26 — Designer unpark OPERATE; apply CRs.
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
LABELS_OP = ["operate", "daily-loop", "fr-test-4", "fr-plan-4"]
LABELS_GAP = ["gap-cr", "enterprise-backlog"]
BASELINE_KEYS = [
    "KAN-372",
    "KAN-366",
    "KAN-359",
    "KAN-354",
    "KAN-347",
    "KAN-345",
    "KAN-320",
    "KAN-307",
]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

FR_TEST_4 = (
    "FR-TEST-4: Capture screenshots / evidence on failure and success where useful."
)
FR_PLAN_4 = (
    "FR-PLAN-4: A run stores result, evidence, duration, and failure class on the case. "
    "Heal proposals and report sections can attach to that run."
)
FR_REP_1 = (
    "FR-REP-1: Generate reports with metrics… Deepen (CR 2026-11-26): Reports area "
    "grows into a visual analytics surface (charts/graphs)."
)
FR_MAN_1 = (
    "FR-MAN-1: … Charter-only / snip-tool mode (CR 2026-11-26): usable without Jira "
    "and without AI; capture chrome draggable across the Windows desktop."
)
FR_PLAN_1 = (
    "FR-PLAN-1: … local JSON under %LOCALAPPDATA%\\ai_testing_app\\plans\\{LEVEL}\\; "
    "user-friendly full plan document view (CR 2026-11-26)."
)
FR_LEARN_1 = (
    "FR-LEARN-1: … Documents demo pack (synthetic functional spec + user guide) "
    "(CR 2026-11-26)."
)
FR_PLUG_4 = (
    "FR-PLUG-4: Deepen stubs into real or rich demo behaviour; varied synthetic "
    "fixtures until runners are real; never fake pass."
)
FR_SEC_6 = (
    "FR-SEC-6: Compliance roadmap (ISO/IEC 27001-aligned themes) — design matrix "
    "first; not a certification claim."
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

    def find_by_summary(self, summary: str, issue_type: str, label: str) -> Optional[str]:
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": (
                    f'project = {PROJECT} AND issuetype = "{issue_type}" '
                    f'AND labels = "{label}" ORDER BY created DESC'
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
        labels: List[str],
        parent_epic: Optional[str] = None,
        search_label: Optional[str] = None,
    ) -> Optional[str]:
        lab = search_label or (labels[0] if labels else "operate")
        existing = self.find_by_summary(summary, issue_type, lab)
        if existing:
            print(f"exists {issue_type}: {existing}")
            return existing
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf_from_lines(split_lines(body)),
            "labels": labels,
        }
        if parent_epic and issue_type == "Story":
            fields["parent"] = {"key": parent_epic}
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201 and parent_epic and issue_type == "Story":
            fields.pop("parent", None)
            r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201:
            self.failures.append(
                f"create {issue_type} {summary[:48]}: {r.status_code} {r.text[:200]}"
            )
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


def test_body(story_summary: str) -> str:
    return f"""
## Intro
Verifies {story_summary}.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run focused pytest for this story.
   Expected: exit 0.
2. Spot-check desktop_app.py only if AC requires visual proof; else marker/API OK.
   Expected: matches story AC; never soft-pass orb home.

## Acceptance criteria
Mirror parent story AC. {DOD}

## Evidence
Paste pytest command + pass count on close-out.
"""


OPERATE_EPIC = """
## Intro
Prove one daily test-all loop on a home-PC local demo AUT: connect → plan → run → fail → open Playwright trace → triage → report. Completes TRACE-DEEPEN value for daily use. See docs/ops/DAILY_LOOP.md.

## Who this is for
- Senior Test Engineer — operable golden path
- Designer — internal demo without employer AUT
- Developers — evidence + Plans case detail

## Problem / outcome
Layout baselines look Done; operate coherence is thin. Open-trace + golden path close the gap.

## Requirements
""" + FR_TEST_4 + "\n" + FR_PLAN_4 + """

## Scope
In: open-trace affordance; home-PC demo AUT fixture; golden path docs; Documents demo pack; loop-hit polish (Plans Run / Manual idle / evidence).
Out: voice; FR-MAN-2 circles; CI OAuth; H3 daemon; Reports charts (GAP-CR); theme/orb/home; employer AUT.

## Success criteria
15-min walkthrough on OFFICIAL with Open trace from failed case; pytest green; DAILY_LOOP pass criteria met.

## Dependencies / risks
After KAN-372. Home PC only — local fixture AUT. 7B agent flaky — grounded tools.

## Technical notes
docs/ops/DAILY_LOOP.md; plugins/playwright_runner.py; plans/evidence_bundle.py; ui/desktop evidence slot.
"""

STORIES_OP = [
    {
        "summary": "OPERATE-1: Open Playwright trace from failed case evidence",
        "body": f"""
## Intro
Failed case detail exposes a clear Open / Reveal / show-trace action for the real trace.zip from KAN-372.

## Who this is for
Senior TE, Developer, agents.

## User story
As a Senior Test Engineer, I want to open the Playwright trace from a failed case in one click (or Reveal in Explorer + documented show-trace), so that TRACE-DEEPEN is usable daily.

## Requirements
{FR_TEST_4}
{FR_PLAN_4}

## Behaviour
- When evidence includes a .zip Playwright trace, show an explicit control (Open / Reveal / copy path) — not text-only.
- Prefer launching `playwright show-trace` via desktop bridge or Reveal in Explorer; never embed a heavy Trace Viewer SPA in this story.
- Marker data-operate-open-trace=\"1\". Cache-bust desk UI.
- Level-scoped paths only; no secrets in UI.

## Acceptance criteria
1. Given a failed case with real trace.zip, When I open case evidence, Then an Open/Reveal control is present and actionable.
2. Given no zip, When I open evidence, Then the control is absent or disabled with honest empty copy.
3. Given pytest, When it runs, Then exit 0. CU not required.

## {DOD}

## Out of scope
Embedded Trace Viewer; voice; FR-MAN-2; Reports charts; employer AUT.

## Dependencies
KAN-372 TRACE-DEEPEN Done.

## Technical notes
ui/desktop evidence-first; desktop_app.py bridge; tests/test_operate_open_trace.py.
""",
    },
    {
        "summary": "OPERATE-2: Home-PC demo AUT fixture + golden-path seed",
        "body": f"""
## Intro
Ship a local demo AUT (static HTML or fixtures) + seed script so OPERATE runs without any employer browser app.

## Who this is for
Designer (home PC), Senior TE, agents.

## User story
As a Designer on a home PC, I want a local demo target URL and seeded smoke case, so that I can walk the daily loop without company VPN or AUT access.

## Requirements
{FR_PLAN_4}
{FR_TEST_4}

## Behaviour
- Add repo fixture page(s) and document how to point Settings target_url at them (file:// or local static server).
- Seed optional OFFICIAL plan with smoke-tagged case against the fixture (synthetic only).
- Update DAILY_LOOP.md with exact start commands.
- Never require employer credentials.

## Acceptance criteria
1. Given fixture + seed, When target_url points at the demo AUT, Then a smoke case can run headed and produce pass or intentional fail.
2. Given DAILY_LOOP.md, When followed, Then steps name the home-PC AUT only.
3. Pytest covers seed/fixture presence.

## {DOD}

## Out of scope
Company AUT; cloud hosting; voice.

## Technical notes
fixtures/operate_demo/; scripts/seed_operate_demo.py; docs/ops/DAILY_LOOP.md.
""",
    },
    {
        "summary": "OPERATE-3: Loop-hit UI polish (Plans Run, Manual idle, evidence)",
        "body": f"""
## Intro
Polish only the three surfaces the golden path hits: Plans Run tab disclosure, Manual idle library vs Start, evidence affordance consistency. Not a full TRACK6 home redesign.

## Who this is for
Designer, Senior TE.

## User story
As a Senior Test Engineer walking the daily loop, I want Plans Run and Manual idle to stop being vertical soup, so that the operate path is scannable.

## Requirements
FR-UI-9 progressive disclosure for Run setup; FR-MAN-1 idle clarity; evidence-first consistency with OPERATE-1.

## Behaviour
- Plans → Run: collapse secondary forms behind disclosure sections (env/sandbox/schedule).
- Manual idle: separate library scan from Start charter (wire-aligned).
- Evidence slot matches OPERATE-1 affordance.
- Theme/orb/home/App nav locked.

## Acceptance criteria
1. Given Plans Run, When opened, Then primary run actions visible without scrolling past all advanced forms.
2. Given Manual idle, When opened, Then library and Start are visually separated.
3. Markers + pytest; CU skipped if unsafe.

## {DOD}

## Out of scope
Screen drawer HUD wall; Gradio parity; FR-MAN-2; floating OS snip (GAP-CR).

## Technical notes
ui/desktop Plans/Manual only; Studio mockups optional.
""",
    },
    {
        "summary": "OPERATE-4: Documents demo pack (spec + user guide fixtures)",
        "body": f"""
## Intro
Install synthetic functional-spec + user-guide documents into the active level so Documents → draft plan is demonstrable.

## Who this is for
Designer POC, PO, agents.

## User story
As a Designer, I want stub documents that look like a real spec and user guide, so that document-driven planning proves the Documents area works.

## Requirements
{FR_LEARN_1}

## Behaviour
- Ship markdown fixtures (functional spec excerpt + user guide) under fixtures/operate_docs/.
- Seed/upload into OFFICIAL Documents with consent flags for synthetic data.
- Draft-from-document path produces editable cases (no silent Jira).
- Varied content (happy path + edge notes).

## Acceptance criteria
1. Given seed, When Documents Lists Uploads, Then both demo docs appear for OFFICIAL.
2. Given Parse/draft, When confirmed, Then a plan gains cases sourced from the docs.
3. Pytest + no employer/customer text.

## {DOD}

## Out of scope
Real company docs; silent settings writes.

## Technical notes
plugins/doc_uploads.py; plans/draft.py; fixtures/operate_docs/.
""",
    },
]

GAP_EPIC = """
## Intro
Enterprise / test-all gaps raised in Council 2026-11-26 after OPERATE unpark. Sequence after OPERATE stories. Not voice / FR-MAN-2 circles.

## Who this is for
Designer, Test Manager, Security adviser, Senior TE.

## Problem / outcome
Baselines leave Reports text-only, Manual trapped in-window, empty Documents, eternal stubs, plan JSON-only views, GDPR-only compliance story.

## Requirements
""" + "\n".join([FR_REP_1, FR_MAN_1, FR_PLAN_1, FR_PLUG_4, FR_SEC_6, FR_LEARN_1]) + """

## Scope
In: charts; floating snip; plan document view; stub deepen + fixtures; ISO27001-aligned matrix design.
Out: OPERATE-1..4 (separate epic); certification audit; cloud sandboxes; theme/orb.

## Success criteria
Each child story Done with AC; product still local-first; stubs never fake pass.

## Technical notes
FUNCTIONAL_SPEC CR 2026-11-26; ROADMAP GAP-CR.
"""

STORIES_GAP = [
    {
        "summary": "GAP-CR: Reports visual analytics (charts/metrics)",
        "body": f"""
## Intro
Reports area gains charts/graphs for pass-fail, coverage, duration, failure class — not markdown-only.

## User story
As a Test Manager, I want charts in Reports, so that I can read readiness without exporting raw markdown.

## Requirements
{FR_REP_1}

## Acceptance criteria
1. Given local run data, When I open a report detail, Then at least pass/fail and coverage charts render from local JSON.
2. Given empty data, When opened, Then quiet empty — no fake metrics.
3. No telemetry cloud. {DOD}

## Out of scope
Cloud BI; changing Report Settings placement.
""",
    },
    {
        "summary": "GAP-CR: Manual floating snip tool (OS-level, no ticket required)",
        "body": f"""
## Intro
Charter Frame becomes a draggable Windows-desktop snipping tool; Jira/AI optional.

## User story
As a Manual Tester, I want to drag the capture frame anywhere on screen and snip without a Jira key or AI, so that Manual works like a snipping tool and can still link later.

## Requirements
{FR_MAN_1}

## Acceptance criteria
1. Given Start without story key and assist off, When I drag the frame outside the main app window, Then it remains usable for still capture.
2. Given a still, When I end session, Then evidence stores level-scoped locally.
3. No keylog/clipboard/mic. FR-MAN-2 circles still parked. {DOD}

## Out of scope
Live AI circles; Cursor Computer Use mist as product.
""",
    },
    {
        "summary": "GAP-CR: User-friendly full plan document view",
        "body": f"""
## Intro
Readable narrative view of a full test plan beyond scan-table + forms. Storage remains local JSON.

## User story
As a Senior Test Engineer, I want to read the full plan like a document, so that I can review intent and cases without editing forms.

## Requirements
{FR_PLAN_1}

## Acceptance criteria
1. Given an open plan, When I open Plan document view, Then intent, cases, tags, last results render as readable content.
2. Given storage, When inspected, Then files remain under plans/{{LEVEL}}/*.json — no new required SQL DB.
3. {DOD}
""",
    },
    {
        "summary": "GAP-CR: Deepen all stubs + varied synthetic Lab fixtures",
        "body": f"""
## Intro
Deepen Selenium/Cypress/a11y/perf stubs toward real or rich demo behaviour; supply varied synthetic test data so desks are not empty.

## User story
As a Senior Test Engineer, I want stubs deepened (or rich fixtures while deepening), so that Lab areas prove the product instead of empty honest errors only.

## Requirements
{FR_PLUG_4}

## Acceptance criteria
1. Given each listed stub plugin, When opened in Lab/Settings, Then either a real deepen slice exists or varied synthetic rows demonstrate the desk.
2. Given a non-ready runner, When Run is attempted, Then never_pass / disabled Run remains honest.
3. Phased stories OK; this story seeds the epic checklist. {DOD}
""",
    },
    {
        "summary": "GAP-CR: Compliance matrix design (ISO27001-aligned themes)",
        "body": f"""
## Intro
Design-only matrix mapping ISO/IEC 27001-aligned control themes to FR-SEC-* and gaps. Not certification.

## User story
As a Security adviser, I want a compliance matrix, so that enterprise buyers see GDPR + classification is not the whole story and gaps are explicit.

## Requirements
{FR_SEC_6}

## Acceptance criteria
1. Given docs/design/COMPLIANCE_MATRIX.md (or equivalent), When reviewed, Then themes (access, audit, crypto-at-rest for secrets, confirm gates, backup, no-telemetry) map to shipped vs gap.
2. Given product UI, When unchanged in this story, Then no false “ISO certified” badge.
3. {DOD} for design story — pytest N/A; human Accept on matrix.

## Out of scope
Paying for certification; inventing extra UK classification tiers without CR.
""",
    },
]


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    keys: Dict[str, Any] = {"roadmap": "OPERATE", "stories": {}, "gap_stories": {}}
    try:
        epic = j.create_issue(
            "OPERATE — Daily test-all loop + open-trace",
            "Epic",
            OPERATE_EPIC,
            LABELS_OP,
            search_label="operate",
        )
        keys["epic"] = epic
        for s in STORIES_OP:
            story = j.create_issue(
                s["summary"], "Story", s["body"], LABELS_OP, parent_epic=epic, search_label="operate"
            )
            test = j.create_issue(
                f"Test: {s['summary']}",
                "test",
                test_body(s["summary"]),
                LABELS_OP + ["test"],
                search_label="operate",
            )
            if story and test:
                j.link_relates(story, test)
            short = s["summary"].split(":")[0].strip()
            keys["stories"][short] = {"story": story, "test": test}

        gap_epic = j.create_issue(
            "GAP-CR — Enterprise gaps after OPERATE (charts, Manual float, stubs, compliance)",
            "Epic",
            GAP_EPIC,
            LABELS_GAP,
            search_label="gap-cr",
        )
        keys["gap_epic"] = gap_epic
        for s in STORIES_GAP:
            story = j.create_issue(
                s["summary"],
                "Story",
                s["body"],
                LABELS_GAP,
                parent_epic=gap_epic,
                search_label="gap-cr",
            )
            test = j.create_issue(
                f"Test: {s['summary']}",
                "test",
                test_body(s["summary"]),
                LABELS_GAP + ["test"],
                search_label="gap-cr",
            )
            if story and test:
                j.link_relates(story, test)
            keys["gap_stories"][s["summary"][:40]] = {"story": story, "test": test}

        if epic:
            j.comment(
                epic,
                [
                    "Council Slice-0 2026-11-26 — Designer unpark OPERATE.",
                    "Home-PC demo AUT only (no employer browser). See docs/ops/DAILY_LOOP.md.",
                    "Active Build starts at OPERATE-1 open-trace.",
                    "GAP-CR epic holds charts / Manual float / stubs / compliance — after OPERATE.",
                    "Park: voice KAN-81, FR-MAN-2 live circles.",
                ],
            )

        baseline_lines = [
            "Baseline label (Council 2026-11-26): this Done story shipped a prototype baseline,",
            "not enterprise-complete test-all. Further deepen lives on OPERATE / GAP-CR.",
            "Truth labels: Done = baseline unless a later story says otherwise.",
        ]
        for k in BASELINE_KEYS:
            j.comment(k, baseline_lines)

        out = Path(__file__).resolve().parents[1] / "docs" / "ops" / "OPERATE_KEYS.json"
        out.write_text(json.dumps(keys, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")

        # Point WORK_LOG reader at concrete keys if OPERATE-1 exists
        op1 = keys["stories"].get("OPERATE-1") or {}
        if op1.get("story"):
            print(f"ACTIVE_STORY={op1['story']} TEST={op1.get('test')}")

        if j.failures:
            for f in j.failures:
                print(f"FAIL: {f}", file=sys.stderr)
            return 1
        return 0 if epic and keys["stories"].get("OPERATE-1", {}).get("story") else 1
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
