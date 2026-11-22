"""Create FR-UI-11 rest-of-app Stories + linked tests. Never prints tokens.

Does not change WORK_LOG Active (KAN-329). Does not edit KAN-329.
Posts a proposed-addendum comment on test KAN-330 only.
"""
from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35
PROJECT = "KAN"
LABELS = ["fr-ui-11", "track4-layout", "studio-bridge", "rest-areas"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed). Do not set this story as WORK_LOG Active while KAN-329 is Active."
)

CU = (
    "CU policy: pytest and HTML/JS/CSS markers are the pass gate. "
    "Computer Use only if a step claims visual occlusion or clickability the markers cannot prove. "
    "If the desktop is unsafe, write exactly 'CU skipped — unsafe' on this test ticket. "
    "That sentence does not pass any step. Evidence that only says the area was opened is a fail."
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


def adf_from_lines(lines: List[str]) -> Dict[str, Any]:
    content: List[Dict[str, Any]] = []
    for line in lines:
        text = line if line.strip() else " "
        content.append({"type": "paragraph", "content": [{"type": "text", "text": text}]})
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
    return {"type": "doc", "version": 1, "content": content}


def lines(text: str) -> List[str]:
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
                    'AND labels = "rest-areas" ORDER BY created DESC'
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

    def create_issue(self, summary: str, issue_type: str, body: str) -> Optional[str]:
        existing = self.find_by_summary(summary, issue_type)
        if existing:
            print(f"exists {issue_type}: {existing}")
            return existing
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf_from_lines(lines(body)),
            "labels": LABELS,
        }
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201:
            self.failures.append(f"create {issue_type} {summary[:48]}: {r.status_code}")
            return None
        key = r.json().get("key")
        print(f"created {issue_type}: {key}")
        return key

    def link_relates(self, story: str, test: str) -> None:
        payload = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": story},
            "outwardIssue": {"key": test},
        }
        r = self._req("POST", "/rest/api/3/issueLink", json=payload)
        if r.status_code >= 300:
            self.failures.append(f"link {story}<->{test}: {r.status_code}")
        else:
            print(f"linked Relates {story} <-> {test}")

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


PAIRS: List[Dict[str, str]] = []

# --- 1 Plans remaining tabs ---
PAIRS.append(
    {
        "order": "1",
        "story_summary": "Plans remaining tabs — FR-UI-11 scan and compact forms (not Cases)",
        "test_summary": "Test: Plans remaining tabs FR-UI-11 markers (Coverage Trace History Draft Run)",
        "mock": "docs/mockups/secondary_areas_rest/01-themed-plans-tabs.html",
        "story": f"""
## Intro
Apply FR-UI-11 to Plans tabs other than Cases: Coverage, Trace, History, Draft, and Run setup. Cases stays KAN-329 / KAN-330. Structure only. Theme, orb, home/chat, and App nav stay locked.

## Who this is for
- Test engineers who scan coverage, trace, and history without reading a text dump
- Developers implementing inside #app-section-plans
- Designer — mockup 01-themed-plans-tabs.html

## User story
As a test engineer, I want Coverage, Trace, and History in scan tables, and Draft and Run as compact forms, so that I can find a gap or a run without a dump and without a whole-row toggle.

## Requirements
FR-UI-11 (rest-of-app inherit, 2026-11-22): Coverage and Trace are scan tables. Trace row opens the case. History uses dedicated A/B radio cells about 28px wide; row click focuses the run. Draft and Run setup are compact forms. Single booleans are compact checkboxes, not page-width .check-row. FR-UI-9 tabs stay (Draft, Cases, Coverage, Trace, History, Run). KAN-329 owns the Cases scan and editor. FR-UI-1 App nav stays the compact menu.

## Behaviour
- #plan-panel-coverage: table data-plan-coverage-scan with columns Story, Gap, Summary. No checkbox column. Row click fills a detail pane. Refresh does not create cases.
- #plan-panel-trace: table data-plan-trace-scan with columns Story, Cases, Last, Bugs, Known. Row click still opens that case (existing trace behaviour). No checkbox column.
- #plan-panel-history: table data-plan-history-scan with radio cells named for compare A and compare B inside td.hit (about 28px). Row click outside the radios focuses the run. Compare uses the two radios.
- #plan-panel-draft: data-plan-draft-form. Fields and actions stay a form. No scan table required.
- #plan-panel-run: data-plan-run-sections. #plan-pause-on-fail is a compact checkbox, not a label.check-row that spans the row. Schedule stays inside the existing details element.
- Do not remove #plan-tab-cases, #plan-panel-cases, or data-plans-cases-geometry.
- Do not add App-menu items for these tabs.

## Acceptance criteria
1. Given Plans Coverage with gap data, When the panel is shown, Then a table[data-plan-coverage-scan] lists Story, Gap, and Summary, and the panel contains no input[type=checkbox].
2. Given a Coverage row, When the row is clicked outside any control, Then the detail shows that story key. Fail if the row toggles a selection.
3. Given Trace, When a row is clicked, Then the case opens as it does today, and table[data-plan-trace-scan] is present with no checkbox column.
4. Given History with at least two runs, When a radio in the A cell or B cell is used, Then only that radio changes. Row click does not change A or B.
5. Given Run setup, When inspecting #plan-pause-on-fail, Then it is not inside label.check-row.
6. Given the Cases tab, When this story is implemented, Then #plan-tab-cases and #plan-panel-cases still exist.
7. Given pytest tests/test_plans_tabs_layout_grammar.py, When it runs, Then it exits 0 only if the markers in the test ticket are present. Theme, orb, home, and App nav files for those surfaces are unchanged.

## {DOD}

## Out of scope
Plans Cases layout (KAN-329). Settings and Suites restyle. TRACK3-LAB. KAN-81 voice. FR-MAN-2. KPI cards. New App nav items. Gradio layouts.

## Dependencies
Mockups docs/mockups/secondary_areas_rest/. Spec FR-UI-11 rest-of-app paragraph. Ship after KAN-329 so Cases markup is stable. Active slice stays KAN-329 until that story is Done.

## Technical notes
ui/desktop/index.html #plan-panel-coverage #plan-panel-trace #plan-panel-history #plan-panel-draft #plan-panel-run. desktop.js renderers that fill plan-coverage-*, plan-trace-matrix, plan-history-list. Marker on the plans section: data-plans-tabs-layout-grammar="1". Pytest parses HTML/JS/CSS the way tests/test_suite_layout_grammar.py does. {CU}

## Mockups
docs/mockups/secondary_areas_rest/00-structure-wire.html
docs/mockups/secondary_areas_rest/01-themed-plans-tabs.html
docs/mockups/secondary_areas_rest/02-annotated-build-note.html
docs/mockups/secondary_areas_rest/03-rejected-options.html
""",
        "test": f"""
## Intro
Verifies the Plans remaining-tabs story (Relates). Pass requires the pytest file and every marker below. "Opened Plans" is a fail.

## Who this is for
Testers and coding agents. Fail the ticket when a marker is missing. Do not debate taste.

## Test procedure
1. Run: python -m pytest tests/test_plans_tabs_layout_grammar.py -q
   Expected: exit code 0. Missing file = fail.
2. The test must read ui/desktop/index.html, desktop.css, and desktop.js. It must slice #app-section-plans only.
   Expected: assertions, not a screenshot.
3. Static markers that must be present or the test fails:
   data-plans-tabs-layout-grammar="1"
   data-plan-coverage-scan="1" and header cells Story, Gap, Summary
   data-plan-trace-scan="1" and header cells Story, Cases, Last, Bugs, Known
   data-plan-history-scan="1" and header cells for A and B
   data-plan-draft-form="1"
   data-plan-run-sections="1"
   id="plan-tab-cases" and id="plan-panel-cases" still present
4. The test must fail if #plan-panel-coverage or #plan-panel-trace contains type="checkbox".
5. The test must fail if #plan-pause-on-fail sits inside class check-row (search the Run panel slice).
6. The test must fail if desktop.js still assigns plan-coverage or plan-history results only via textContent on the old dump nodes with no row builder. Require a function that creates tr elements for coverage, trace, and history.
7. History radios: JS must call stopPropagation on the A/B radio click, and the radio must not live on the tr click handler.
8. desktop_app.py spot-check (after pytest is green): App, Plans, Coverage. Click a gap row, not a control.
   Expected: detail shows that story key. Clicking the row does not check a box (there is no box).
9. History tab: click the A radio on run 1 and the B radio on run 2, then click the time cell of run 1.
   Expected: A/B stay on the radios you set; detail focus moves to run 1.
10. {CU}

## Acceptance criteria
1. pytest tests/test_plans_tabs_layout_grammar.py exits 0.
2. Coverage and Trace tables have no checkbox.
3. History A/B are radio inputs inside a hit cell, and row click does not change them.
4. Cases tab ids are still in the HTML.
5. A comment that only says the Plans area opened does not pass this ticket.

## Evidence
Paste the pytest command and the pass count. No secrets. CU note only if a visual step was attempted.
""",
    }
)

PAIRS.append(
    {
        "order": "2",
        "story_summary": "Reports library — FR-UI-11 scan table and detail",
        "test_summary": "Test: Reports library FR-UI-11 markers (scan, detail, no section editor)",
        "mock": "docs/mockups/secondary_areas_rest/01b-themed-reports.html",
        "story": f"""
## Intro
Replace the Reports button list plus duplicate id dropdown with a compact scan table and the existing detail viewer. No section rail. Report section include/exclude stays in Settings.

## Who this is for
- Test engineers opening a saved report for the active security level
- Developers changing #app-section-reports
- Designer — 01b-themed-reports.html

## User story
As a test engineer, I want saved reports in a scan table, so that I can see when, title, level, and kind, and open markdown without a second dropdown.

## Requirements
FR-REP-4: Reports lists and opens saved reports (markdown, screenshot, raw JSON). Empty state explains that a run produces a report. A control deep-links to Settings Report. The Reports surface does not host the section-include editor.
FR-UI-11 rest inherit: scan + detail, no section rail, dedicated checkbox only if multi-select exists. This story has no multi-select. Row click opens the report. FR-REP-2 section choices stay under Settings (FR-SET-4).

## Behaviour
- Remove #rpt-library-list button options and #rpt-library-select as the openers.
- Add table data-rpt-scan columns When, Title, Level, Kind. Row click calls the existing load path for that report id.
- Keep #rpt-markdown, #rpt-screenshot, and #rpt-json in aside data-rpt-detail.
- Keep #rpt-open-settings. Export run / pack stays in Advanced or the toolbar, not on the row.
- Empty state is one sentence, not a hero.
- No checkbox column.

## Acceptance criteria
1. Given one saved report, When Reports is open, Then table[data-rpt-scan] shows When, Title, Level, and Kind.
2. Given a row, When it is clicked, Then the detail pane shows that report markdown.
3. Given the reports section HTML, When searched, Then #rpt-library-select is absent and there is no input[type=checkbox] in #app-section-reports.
4. Given Report settings, When the button is used, Then Settings opens on report blocks. The reports area has no section include/exclude editor.
5. pytest tests/test_reports_layout_grammar.py exits 0. Theme, orb, home, and App nav are unchanged.

## {DOD}

## Out of scope
Settings report-block editor. KPI dashboard. Section rail. Gradio. TRACK3-LAB geometry. New report metrics (FR-REP-1 already shipped).

## Dependencies
Mockup 01b. Spec FR-REP-4 and FR-UI-11. Build after or beside Plans tabs; not instead of KAN-329.

## Technical notes
ui/desktop/index.html #app-section-reports. desktop.js renderReportLibraryList. Marker data-reports-layout-grammar="1" on the section. data-rpt-scan and data-rpt-detail. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01b-themed-reports.html
docs/mockups/secondary_areas_rest/02-annotated-build-note.html
docs/mockups/secondary_areas_rest/03-rejected-options.html
""",
        "test": f"""
## Intro
Verifies the Reports library story. "Opened Reports" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_reports_layout_grammar.py -q
   Expected: exit code 0.
2. Slice #app-section-reports in index.html. Fail unless all of these are true:
   data-reports-layout-grammar="1"
   table[data-rpt-scan="1"] with headers When, Title, Level, Kind
   data-rpt-detail="1" containing id="rpt-markdown"
   id="rpt-open-settings" present
   id="rpt-library-select" absent
   id="rpt-library-list" absent (the old button list)
   zero input type=checkbox inside the reports slice
3. desktop.js must not contain class rpt-library-item after the change. It must build tr rows for the scan body.
4. desktop_app.py: App, Reports. Click a report row.
   Expected: markdown area text changes to that report. There is no second "Open by id" dropdown.
5. Click Report settings.
   Expected: Settings area opens. Reports HTML still has no include/exclude checkbox.
6. {CU}

## Acceptance criteria
1. pytest command above exits 0.
2. Duplicate select is gone.
3. No checkbox in the reports section.
4. Row click loads detail.
5. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. No report bodies that contain secrets. Synthetic or local OFFICIAL sample only.
""",
    }
)

PAIRS.append(
    {
        "order": "3",
        "story_summary": "Documents — FR-UI-11 proposal scan and uploads scan",
        "test_summary": "Test: Documents FR-UI-11 markers (Keep cell, uploads scan, confirm outside row)",
        "mock": "docs/mockups/secondary_areas_rest/01c-themed-documents.html",
        "story": f"""
## Intro
Turn document proposal diffs and the uploads list into scan tables. Keep is a dedicated checkbox cell. Confirm and Decline stay deliberate buttons.

## Who this is for
- Test engineers accepting a settings proposal from a spec
- Developers changing #app-section-documents
- Designer — 01c-themed-documents.html

## User story
As a test engineer, I want each proposed settings key in a row with its own Keep cell, so that I can accept some keys without the whole row being the checkbox.

## Requirements
FR-SET-2: document ingestion proposes settings; the user confirms before they are written.
FR-SEC-2: explicit consent before storing extracted data.
FR-UI-11: dedicated checkbox cell (~28px, stopPropagation); row click focuses; Confirm and Decline are not row chrome. In-area Propose | Uploads switch is inside the area, not a new App nav item.

## Behaviour
- Replace label.check-row.doc-diff-row with table data-doc-diff-scan columns Keep, Key, From, To. Keep is td.hit with the checkbox. Default checked state may stay on.
- Row click focuses that key in the detail. It does not toggle Keep.
- #doc-confirm and #doc-decline sit outside the table (detail or toolbar).
- Uploads: table data-doc-uploads-scan columns Name, Time, Level, Consent. Row opens detail. No document body in the table.
- Spec textarea stays. In-area tabs only.

## Acceptance criteria
1. Given a proposal with two keys, When it renders, Then table[data-doc-diff-scan] has a Keep checkbox per key inside td.hit.
2. Given a Keep checkbox, When it is clicked, Then only that checkbox toggles (stopPropagation). The tr click handler does not toggle it.
3. Given a row click on the key text, When handled, Then detail shows that key and the checkbox state is unchanged.
4. Given uploads, When listed, Then table[data-doc-uploads-scan] shows Name, Time, Level, Consent.
5. class check-row and class doc-diff-row are absent from #app-section-documents.
6. pytest tests/test_documents_layout_grammar.py exits 0.

## {DOD}

## Out of scope
Security wipe UI (separate story). Parsing rules. Home/chat. Gradio. Showing secret values in the diff (mask if a value looks like a token).

## Dependencies
Mockup 01c. FR-SET-2 confirm behaviour stays. Not Active while KAN-329 is Active.

## Technical notes
desktop.js renderDocProposal. Marker data-documents-layout-grammar="1". data-doc-diff-scan, data-doc-uploads-scan, data-doc-keep-stop on the checkbox listener. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01c-themed-documents.html
docs/mockups/secondary_areas_rest/02-annotated-build-note.html
""",
        "test": f"""
## Intro
Verifies the Documents story. "Opened Documents" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_documents_layout_grammar.py -q
   Expected: exit code 0.
2. Fail the test unless #app-section-documents contains:
   data-documents-layout-grammar="1"
   data-doc-diff-scan="1" with headers Keep, Key, From, To
   data-doc-uploads-scan="1" with headers Name, Time, Level, Consent
   id="doc-confirm" and id="doc-decline" outside the diff table element
3. Fail if the documents slice contains class="check-row" or class doc-diff-row.
4. desktop.js renderDocProposal must create td.hit checkboxes and the listener must include stopPropagation. Fail if it still sets row.className to check-row doc-diff-row.
5. desktop_app.py: paste a short synthetic spec (no secrets), Parse and propose. Click the Keep cell.
   Expected: only the box toggles. Click the key text.
   Expected: detail shows the key; the box does not toggle.
6. {CU}

## Acceptance criteria
1. pytest exits 0.
2. No check-row in the documents section.
3. Confirm and Decline are outside the scan row.
4. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. Do not paste spec text that contains credentials.
""",
    }
)

PAIRS.append(
    {
        "order": "4",
        "story_summary": "Security area — FR-UI-11 rail, checkbox cells, masked status",
        "test_summary": "Test: Security FR-UI-11 markers (rail, Include cell, confirm, no secrets)",
        "mock": "docs/mockups/secondary_areas_rest/01d-themed-security.html",
        "story": f"""
## Intro
Give Security an in-area section rail and replace page-width check-rows with checkbox cells. Classification stays one level at a time. No secret values on the surface.

## Who this is for
- Test engineers switching level or wiping local artifacts
- Developers changing #app-section-security
- Designer — 01d-themed-security.html (synthetic OFFICIAL only)

## User story
As a test engineer, I want privacy wipe targets in a scan with a dedicated Include cell, so that I do not toggle a wipe flag by clicking the whole line, and I never see a token.

## Requirements
FR-SEC-1: OFFICIAL and SECRET isolate credentials and browser profiles.
FR-SEC-3: level switch takes effect only after confirmation.
FR-SEC-5: secrets never render in the UI.
FR-SEC-2: local delete with confirmation; telemetry off by default.
FR-UI-11: in-area rail (not a new App nav item) for Level, Privacy, Audit, Redaction, Backup. Include flags use a ~28px checkbox cell. Delete, restore, and level switch stay propose-then-confirm. TRACK3-LAB wire geometry is out of scope; use the existing area chrome.

## Behaviour
- Rail data-sec-rail with five section buttons. Default visible section may be Privacy or Level; Level controls remain reachable without scrolling past Advanced.
- Privacy targets: table data-sec-privacy-scan columns Include, Artifact. Checkbox in td.hit. Row click focuses the artifact name and does not toggle Include.
- #priv-propose then #priv-confirm (confirm starts disabled). Same pattern for #sec-propose / #sec-confirm and backup restore.
- Audit: table data-sec-audit-scan columns Time, Action, Ref. No document bodies.
- Redaction panel shows hit counts and a screenshot warning only. It must not echo a matched secret.
- Backup list: table data-sec-backup-scan. Include-settings and include-secrets are compact checkboxes in the detail. Secrets option stays off by default.
- Remove every label.check-row inside #app-section-security.

## Acceptance criteria
1. Given Security, When HTML is read, Then data-security-layout-grammar="1" and data-sec-rail="1" exist, and the rail has Level, Privacy, Audit, Redaction, Backup.
2. Given privacy rows, When the Include cell is clicked, Then only that checkbox changes. Row text click does not.
3. Given Confirm switch, Confirm delete, and Confirm restore, When the area first loads, Then those confirm buttons are disabled.
4. Given the security section source and rendered text, When scanned for api_token, jira_api_token, or a live Authorization value, Then none are present.
5. pytest tests/test_security_layout_grammar.py exits 0.
6. App nav still has a single Security item. No new Primary items.

## {DOD}

## Out of scope
Changing isolation rules. Mixing OFFICIAL and SECRET in one view. TRACK3-LAB density. Settings hub restyle. Pasting settings.json into the UI.

## Dependencies
Mockup 01d. FR-SEC-*. Not Active during KAN-329.

## Technical notes
ui/desktop/index.html #app-section-security. Keep existing button ids (sec-propose, sec-confirm, priv-propose, priv-confirm, backup-restore-propose, backup-restore-confirm). Marker data-sec-privacy-scan, data-sec-audit-scan, data-sec-backup-scan. Checkbox listener stopPropagation. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01d-themed-security.html
docs/mockups/secondary_areas_rest/02-annotated-build-note.html
Synthetic level label OFFICIAL only. Do not attach real Settings screenshots.
""",
        "test": f"""
## Intro
Verifies the Security layout story. "Opened Security" is a fail. Never paste tokens into the ticket.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_security_layout_grammar.py -q
   Expected: exit code 0.
2. Slice #app-section-security. Fail unless:
   data-security-layout-grammar="1"
   data-sec-rail="1" with buttons or tabs whose text includes Level, Privacy, Audit, Redaction, Backup
   data-sec-privacy-scan="1" headers Include, Artifact
   data-sec-audit-scan="1"
   data-sec-backup-scan="1"
   id="sec-confirm", id="priv-confirm", and id="backup-restore-confirm" exist and carry disabled on first paint in the HTML
3. Fail if the security slice contains class="check-row".
4. Fail if the security slice contains the substrings jira_api_token or api_token.
5. desktop.js privacy checkbox builder must use td.hit and stopPropagation.
6. desktop_app.py spot-check at OFFICIAL: open Security, Privacy. Click Include on one artifact.
   Expected: only that box changes. Click Confirm delete without proposing.
   Expected: confirm control stays disabled.
7. Do not photograph credential fields. {CU}

## Acceptance criteria
1. pytest exits 0.
2. No check-row in the security section.
3. Confirm buttons start disabled.
4. No secret substrings in the section HTML.
5. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. No settings.json, no tokens.
""",
    }
)

PAIRS.append(
    {
        "order": "5",
        "story_summary": "Heal review — detail Approve/Reject + toolbar bulk approve",
        "test_summary": "Test: Heal markers (scan Sel, detail actions, bulk toolbar, no row approve)",
        "mock": "docs/mockups/secondary_areas_rest/01e-themed-heal.html",
        "story": f"""
## Intro
Heal proposals move to a scan list. Detail holds Approve and Reject for the focused proposal. Bulk approve uses dedicated Sel checkboxes plus a toolbar control behind confirm. The row and the checkbox never approve by themselves.

## Who this is for
- Test engineers reviewing a locator heal
- Developers changing #app-section-heal and renderHealProposals
- Designer — 01e-themed-heal.html (CR 2026-11-22 bulk approve)

## User story
As a test engineer, I want to approve one heal from the detail or several via Approve selected, so that list clicks cannot silently accept locator changes and I can still clear a backlog in one confirm.

## Requirements
FR-HEAL-2: a proposed heal is presented for review (diff or clear description). No automatic commit to the suite.
FR-HEAL-1: heal may change how a locator works, not what is asserted, unless a human approves that wider change. This story does not add assertion editing.
FR-UI-11 (Designer CR 2026-11-22): scan columns Sel · Class · Locator · Run · When. Sel is a ~28px checkbox cell (stopPropagation) for multi-select only — never means approve. Row click focuses. Approve and Reject for the focused id are separate buttons in the detail (data-heal-actions). Toolbar data-heal-bulk shows Approve selected (N) when ≥1 selected; bulk runs behind confirm; same no-auto-commit rule. Bulk reject is out of scope.

## Behaviour
- Replace per-card .heal-approve / .heal-reject inside #heal-list with table data-heal-scan including a Sel column.
- One #heal-approve and one #heal-reject inside aside data-heal-detail, acting on the focused proposal id.
- One #heal-bulk-approve (or equivalent) inside data-heal-bulk; hidden or disabled when selection count is 0; confirm before calling approve for each selected id.
- Diff text stays in the detail. Filter by run stays in the toolbar.
- Empty state is one line.
- TRACK3-LAB chrome height is unchanged.

## Acceptance criteria
1. Given two pending heals, When the list renders, Then table[data-heal-scan] has a Sel checkbox column and no Approve/Reject button inside the table.
2. Given a row click, When handled, Then the detail shows that proposal diff and does not call approve or reject.
3. Given Approve in the detail, When pressed, Then only the focused proposal is approved and the suite file is not auto-committed (existing API rule).
4. Given Reject, When pressed, Then that proposal is not treated as accepted.
5. Given two rows selected via Sel cells, When Approve selected is confirmed, Then both selected proposals are approved and unselected rows are unchanged.
6. Given a Sel checkbox click, When handled, Then selection toggles and approve is not called.
7. #heal-list contains no element with class heal-approve or heal-reject.
8. pytest tests/test_heal_layout_grammar.py exits 0.

## {DOD}

## Out of scope
Bulk reject. Changing heal policy (FR-HEAL-3/4/5). Auto-commit. TRACK3-LAB. Orb/home.

## Dependencies
Mockup 01e. Existing /api/heal/approve and /api/heal/reject. Not Active during KAN-329.

## Technical notes
desktop.js renderHealProposals. Marker data-heal-layout-grammar="1", data-heal-scan, data-heal-detail, data-heal-actions, data-heal-bulk. Keep button ids heal-approve, heal-reject, heal-bulk-approve. Checkbox click stopPropagation. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01e-themed-heal.html
docs/mockups/secondary_areas_rest/03-rejected-options.html (whole-card / checkbox-as-approve rejected; toolbar bulk accepted)
""",
        "test": f"""
## Intro
Verifies Heal layout with detail actions and toolbar bulk approve. "Opened Heal review" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_heal_layout_grammar.py -q
   Expected: exit code 0.
2. Slice #app-section-heal. Fail unless:
   data-heal-layout-grammar="1"
   data-heal-scan="1" with headers Sel, Class, Locator, Run, When
   data-heal-detail="1"
   data-heal-actions="1" containing id="heal-approve" and id="heal-reject"
   data-heal-bulk="1" containing id="heal-bulk-approve" (or documented equivalent)
3. Fail if #heal-list HTML shell contains a button. Fail if desktop.js renderHealProposals appends Approve/Reject into the card/row.
4. The scan Sel column must use input type=checkbox inside a dedicated hit cell; clicking the checkbox must not approve.
5. There must be exactly one id="heal-approve", one id="heal-reject", and one bulk approve control in index.html.
6. desktop_app.py with synthetic pending proposals: click a row — detail updates; status must not say Approved until detail Approve or confirmed bulk Approve.
7. Select two rows via Sel, confirm Approve selected — both selected approve; soft-pass wording does not pass.
8. If no proposal exists, the static pytest still has to pass. Do not invent a pass from an empty list.
9. {CU}

## Acceptance criteria
1. pytest exits 0.
2. Approve and Reject are not inside the scan list body as per-row buttons.
3. Sel checkbox exists and does not approve on click.
4. Bulk approve control exists and requires selection + confirm path covered by pytest or numbered manual steps.
5. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. Do not paste customer AUT data.
""",
    }
)

PAIRS.append(
    {
        "order": "6",
        "story_summary": "Manual area — session scan and compact start checks",
        "test_summary": "Test: Manual area FR-UI-11 markers (session scan, compact checks, charter untouched)",
        "mock": "docs/mockups/secondary_areas_rest/01f-themed-manual.html",
        "story": f"""
## Intro
Lay out the Manual area library and start form with FR-UI-11 grammar. Charter Frame and the orb home stay as they are.

## Who this is for
- Test engineers starting a charter and reopening a session
- Developers changing #app-section-manual only
- Designer — 01f-themed-manual.html

## User story
As a test engineer, I want past sessions in a scan table and the start options as compact checks, so that I can open a session without a whole-row toggle and without a new home screen.

## Requirements
FR-MAN-1: a manual session starts only on explicit Start. Capture is the Charter Frame. Notes and opt-in stills. Agent assist and armed mist default off. End, review, propose, then Confirm or Cancel. Manual is a Primary area. Esc/Back returns to orb home. Plans keeps Start manual on this case.
FR-UI-11 for the area (not the frame): session library scan columns When, Charter, Link, Stage. Row click opens that session in the detail/review. #manual-ticket-bound, #manual-assist, and #manual-mist are compact checkboxes, not label.check-row, inside #app-section-manual.
The Confirm dock (#manual-confirm-row) stays outside .area-work.
Do not edit #charter-frame-root structure, ids, or its dock checkboxes in this story. FR-MAN-2 stays parked. Home/chat stays locked.

## Behaviour
- Replace #manual-session-list ul rows with table data-manual-session-scan.
- Start form keeps charter textarea and Start session.
- Compact checks use data-manual-compact-check.
- Propose buttons stay deliberate. Confirm/Cancel stay on the dock.

## Acceptance criteria
1. Given sessions for the active level, When Manual is open, Then table[data-manual-session-scan] shows When, Charter, Link, Stage.
2. Given a session row, When clicked, Then that session is focused for review. The row does not start a capture and does not confirm a Jira write.
3. Given the manual section, When searched, Then label.check-row is absent inside #app-section-manual, and the three start inputs above use data-manual-compact-check.
4. Given #manual-confirm-row, When compared to .area-work, Then the dock is not inside .area-work.
5. Given #charter-frame-root, When this story lands, Then ids charter-frame-root, charter-end, charter-note-add, and charter-still-add still exist.
6. pytest tests/test_manual_layout_grammar.py exits 0.

## {DOD}

## Out of scope
FR-MAN-2 circles. Restyling the Charter Frame dock. Orb home. Changing Jira confirm rules (FR-JIRA-5). TRACK3-LAB.

## Dependencies
Mockup 01f. FR-MAN-1 shipped behaviour. Not Active during KAN-329.

## Technical notes
ui/desktop/index.html #app-section-manual. Marker data-manual-layout-grammar="1". Do not change the charter-frame block at the top of index.html except if a test proves an id was accidentally removed — then restore it. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01f-themed-manual.html
docs/mockups/secondary_areas_rest/02-annotated-build-note.html
""",
        "test": f"""
## Intro
Verifies Manual area grammar and that Charter Frame ids survived. "Opened Manual" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_manual_layout_grammar.py -q
   Expected: exit code 0.
2. Slice only #app-section-manual. Fail unless:
   data-manual-layout-grammar="1"
   data-manual-session-scan="1" headers When, Charter, Link, Stage
   data-manual-compact-check="1" on the ticket, assist, and mist controls
   no class="check-row" inside this slice
   id="manual-start" present
   id="manual-confirm-row" present and the slice shows it after the area-work close (not nested in area-work). The test may assert the confirm dock element is a sibling following the work container, matching today's order.
3. Separately read the charter block. Fail if any of these ids are missing: charter-frame-root, charter-end, charter-note-add, charter-still-add, charter-frame-dock.
4. desktop.js session renderer must build tr rows, not only li.manual-session-row click-to-toggle.
5. desktop_app.py: App, Manual. Click a session row if one exists.
   Expected: review/detail for that session. Capture frame does not open until Start session.
6. Do not require Computer Use of the frame overlay. {CU}

## Acceptance criteria
1. pytest exits 0.
2. No check-row inside the manual section.
3. Charter frame ids still exist.
4. Confirm dock remains outside the scrolling work.
5. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count.
""",
    }
)

PAIRS.append(
    {
        "order": "7",
        "story_summary": "Desktop Lab — FR-UI-11 single-target scan and detail",
        "test_summary": "Test: Desktop Lab FR-UI-11 markers (enabled cell, scan, detail save)",
        "mock": "docs/mockups/secondary_areas_rest/01g-themed-desktop.html",
        "story": f"""
## Intro
Show the desktop plugin target as one scan row plus a detail pane. The enable flag is a checkbox cell. This is layout grammar, not TRACK3-LAB density.

## Who this is for
- Test engineers running a desktop smoke against a configured exe
- Developers changing #app-section-desktop
- Designer — 01g-themed-desktop.html

## User story
As a test engineer, I want the exe path and last smoke on a scan row, with Enable only in its cell, so that clicking the path does not toggle the plugin.

## Requirements
FR-UI-11: scan columns Enabled, Status, Path, Last smoke. Enabled is td.hit (~28px) and stopPropagation. Row click focuses the detail. Save, path override, Run smoke, and Run demo stay as buttons, not row toggles.
FR-UI-8: Desktop stays a Lab tools area. Do not add App nav items.
TRACK3-LAB: do not change area chrome heights or invent a density pass.

## Behaviour
- Replace the status paragraph plus label.check-row#desk-enabled with table data-desk-scan (one row is valid).
- Detail holds #desk-exe and #desk-save.
- Toolbar keeps #desk-smoke and #desk-steps.
- Empty path still renders the row with an em dash, not a hero card.

## Acceptance criteria
1. Given Desktop, When shown, Then table[data-desk-scan] has headers Enabled, Status, Path, Last smoke.
2. Given the Enabled checkbox, When clicked, Then only that checkbox changes. Clicking the path cell does not.
3. label.check-row is absent inside #app-section-desktop.
4. #desk-smoke, #desk-steps, and #desk-save still exist.
5. pytest tests/test_desktop_layout_grammar.py exits 0.

## {DOD}

## Out of scope
TRACK3-LAB. Implementing a fuller desktop runner. Orb/home. Gradio.

## Dependencies
Mockup 01g. Not Active during KAN-329.

## Technical notes
ui/desktop/index.html #app-section-desktop. Marker data-desktop-layout-grammar="1" and data-desk-scan="1". {CU}

## Mockups
docs/mockups/secondary_areas_rest/01g-themed-desktop.html
""",
        "test": f"""
## Intro
Verifies the Desktop Lab story. "Opened Desktop" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_desktop_layout_grammar.py -q
   Expected: exit code 0.
2. Slice #app-section-desktop. Fail unless:
   data-desktop-layout-grammar="1"
   data-desk-scan="1" headers Enabled, Status, Path, Last smoke
   id="desk-enabled" inside td class hit (or equivalent hit cell)
   id="desk-smoke", id="desk-steps", id="desk-save", id="desk-exe" present
   no class="check-row" in the slice
3. JS that toggles enable must stopPropagation on the checkbox and must not bind enable to the tr click.
4. desktop_app.py: App, Desktop. Click the path text.
   Expected: detail focuses; enabled state unchanged. Click the Enabled cell.
   Expected: only the checkbox changes.
5. {CU}

## Acceptance criteria
1. pytest exits 0.
2. Enable hit is the cell, not a page-width label.
3. Run and Save ids remain.
4. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. Do not paste a real customer exe path if it identifies a private system; a local sample path is enough.
""",
    }
)

PAIRS.append(
    {
        "order": "8",
        "story_summary": "Sandboxes Lab — FR-UI-11 scan table and detail remove",
        "test_summary": "Test: Sandboxes FR-UI-11 markers (scan, row focus, remove confirm)",
        "mock": "docs/mockups/secondary_areas_rest/01h-themed-sandboxes.html",
        "story": f"""
## Intro
Replace the sandbox hint paragraph with a scan table and a detail pane. Remove is confirmed from the detail. Layout grammar only; TRACK3-LAB density stays deferred.

## Who this is for
- Test engineers managing up to four local sandboxes
- Developers changing #app-section-sandboxes
- Designer — 01h-themed-sandboxes.html

## User story
As a test engineer, I want each sandbox on a scan row, so that I can open one and remove it only from a confirm control in the detail.

## Requirements
FR-UI-11: columns Id, Label, URL, Ready. No checkbox column. Row click focuses the detail. #ms-remove moves behind a confirm control in the detail (propose then confirm, or a disabled confirm until Remove is pressed). Enable multi-sandbox (#ms-enabled) is a compact checkbox in the toolbar, not label.check-row.
FR-UI-8: Sandboxes stays one Lab item.
Local configured environments, max 4. No cloud farms. TRACK3-LAB geometry is out of scope.

## Behaviour
- Table data-ms-scan replaces the single #ms-list sentence. A status line may remain for the plugin summary.
- Detail shows id, label, URL, Save, and Remove… with Confirm remove disabled until Remove is pressed.
- Toolbar keeps the action select and #ms-run.
- Clicking a row does not remove and does not toggle enable.

## Acceptance criteria
1. Given two sandboxes, When the area is open, Then table[data-ms-scan] shows Id, Label, URL, Ready and has no checkbox inputs.
2. Given a row click, When handled, Then detail fields show that sandbox and nothing is deleted.
3. Given Remove, When pressed once, Then a confirm control enables. The sandbox is not removed until confirm.
4. #ms-enabled is not inside label.check-row.
5. pytest tests/test_sandboxes_layout_grammar.py exits 0.

## {DOD}

## Out of scope
TRACK3-LAB. Raising the max of 4. Cloud device farms. Orb/home. Gradio.

## Dependencies
Mockup 01h. Not Active during KAN-329.

## Technical notes
ui/desktop/index.html #app-section-sandboxes. desktop.js renderSandboxList. Marker data-sandboxes-layout-grammar="1", data-ms-scan="1", data-ms-detail="1". Add id ms-remove-confirm disabled by default. {CU}

## Mockups
docs/mockups/secondary_areas_rest/01h-themed-sandboxes.html
docs/mockups/secondary_areas_rest/03-rejected-options.html
""",
        "test": f"""
## Intro
Verifies the Sandboxes story. "Opened Sandboxes" is a fail.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run: python -m pytest tests/test_sandboxes_layout_grammar.py -q
   Expected: exit code 0.
2. Slice #app-section-sandboxes. Fail unless:
   data-sandboxes-layout-grammar="1"
   data-ms-scan="1" headers Id, Label, URL, Ready
   data-ms-detail="1"
   id="ms-run" and id="ms-enabled" present
   id="ms-remove" and id="ms-remove-confirm" present
   ms-remove-confirm has disabled in the initial HTML
   no input type=checkbox inside the scan table
   no class="check-row" in the slice
3. desktop.js must render sandbox rows as tr elements. The tr click must not call remove.
4. desktop_app.py: App, Sandboxes. Click a row.
   Expected: detail shows that id. Click Remove once.
   Expected: confirm becomes enabled and the row is still listed. Do not click confirm unless you are on synthetic data you can recreate.
5. {CU}

## Acceptance criteria
1. pytest exits 0.
2. Scan has no checkbox.
3. Remove does nothing until confirm.
4. No check-row in the section.
5. Soft-pass wording does not pass.

## Evidence
Pytest command and pass count. Synthetic sandbox URLs only.
""",
    }
)


KAN330_COMMENT = [
    "Studio 2026-11-22 — proposed addendum for this test. Do not weaken story KAN-329.",
    "Do not pull Coverage, Trace, History, Draft, or Run redesign into KAN-329. Those are separate rest-area stories.",
    "Gaps: this test does not name a pytest file, does not list fail-if-missing markers, treats Trace as a soft smoke, and does not ban a soft-pass.",
    "Proposed extra steps (append; keep the existing steps):",
    "A. Add or extend tests/test_plan_cases_layout_grammar.py. Exit 0 required.",
    "B. Fail unless #plan-panel-cases (or the cases panel slice) contains data-plan-cases-layout-grammar, data-plan-cases-scan, and data-plan-case-detail.",
    "C. Fail unless scan headers include Status, Id, Name, Tags, and Last (or the story's exact column set if the story text names them).",
    "D. Fail if Enabled or Archived inputs sit inside the scan tbody. They belong in the detail.",
    "E. If a checkbox exists on the scan, its listener must call stopPropagation and the tr click must not toggle it.",
    "F. Evidence that only says Plans was opened is a fail.",
    "G. CU policy: pytest and markers first. CU only for a visual/occlusion step. If unsafe, write CU skipped — unsafe. That note is not a pass.",
    "This comment is a proposed edit. The story description was not changed.",
]


def main() -> None:
    base, auth = load_creds()
    jira = Jira(base, auth)
    created: List[Dict[str, str]] = []
    try:
        for pair in PAIRS:
            story = jira.create_issue(pair["story_summary"], "Story", pair["story"])
            test = jira.create_issue(pair["test_summary"], "test", pair["test"])
            if story and test:
                jira.link_relates(story, test)
                jira.comment(
                    story,
                    [
                        "Studio verdict 2026-11-22 — Redesign + Bridge. Not Active Build.",
                        "Frozen: theme tokens, orb styles, home/chat, App nav (areas + Screen drawer).",
                        "Settings and Suites looks stay the accepted baseline. Plans Cases stays KAN-329 / KAN-330.",
                        f"Build order slot: {pair['order']} after KAN-329.",
                        f"Mockup: {pair['mock']}",
                        "Pack: docs/mockups/secondary_areas_rest/ (wire, themed, annotated, rejected).",
                        "Preferred: FR-UI-11 scan or compact form. Checkbox or radio is a dedicated cell. Row click focuses or opens. Heal Approve/Reject and Manual Charter Frame are contrasts — see the story.",
                        "Testing: linked test names the pytest file, markers, numbered desktop_app.py steps, and CU skipped — unsafe. Opened-area is a fail.",
                        f"Linked test: {test}",
                        "Active slice remains KAN-329. Do not start this story from pick-up until that story is Done and the log moves.",
                    ],
                )
            created.append(
                {
                    "order": pair["order"],
                    "story": story or "",
                    "test": test or "",
                    "summary": pair["story_summary"],
                }
            )
        jira.comment("KAN-330", KAN330_COMMENT)
        print(json.dumps({"created": created, "failures": jira.failures}, indent=2))
    finally:
        jira.close()


if __name__ == "__main__":
    main()
