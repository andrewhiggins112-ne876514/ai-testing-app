"""Create FR-UI-11 Suites + Plans inherit Stories + linked tests. Never prints tokens."""
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

SUITES_STORY = (
    "Suites area — inherit FR-UI-11 layout grammar (scan table + detail)"
)
SUITES_TEST = "Test: Suites FR-UI-11 inherit (scan, checkbox cell, detail)"
PLANS_STORY = (
    "Plans Cases — inherit FR-UI-11 layout grammar (scan table + detail)"
)
PLANS_TEST = "Test: Plans Cases FR-UI-11 inherit (scan table, row→detail)"


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
        content.append(
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        )
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
    return {"type": "doc", "version": 1, "content": content}


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

    def _req(self, method: str, path: str, **kwargs) -> httpx.Response:
        for _ in range(6):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
        return r

    def find_by_summary(self, summary: str, issue_type: str) -> Optional[str]:
        # Prefer exact summary match via recent fr-ui-11 labelled issues
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": (
                    f'project = {PROJECT} AND issuetype = "{issue_type}" '
                    f'AND labels = "fr-ui-11" ORDER BY created DESC'
                ),
                "maxResults": 50,
                "fields": ["summary", "issuetype"],
            },
        )
        if r.status_code >= 300:
            return None
        for issue in r.json().get("issues") or []:
            fields = issue.get("fields") or {}
            if (fields.get("summary") or "").strip() == summary:
                return issue["key"]
        return None

    def create_issue(
        self, summary: str, issue_type: str, description_lines: List[str]
    ) -> Optional[str]:
        existing = self.find_by_summary(summary, issue_type)
        if existing:
            print(f"exists {issue_type}: {existing}")
            return existing
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf_from_lines(description_lines),
            "labels": ["fr-ui-11", "track4-layout", "studio-bridge", "inherit"],
        }
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201:
            self.failures.append(f"create {issue_type}: {r.status_code} {r.text[:300]}")
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
            self.failures.append(f"link {story}<->{test}: {r.status_code} {r.text[:160]}")
        else:
            print(f"linked Relates {story} <-> {test}")

    def comment(self, key: str, lines: List[str]) -> None:
        r = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf_from_lines(lines)},
        )
        if r.status_code >= 300:
            self.failures.append(f"comment {key}: {r.status_code}")
        else:
            print(f"commented {key}")


SUITES_STORY_BODY = """## Intro
Inherit the accepted FR-UI-11 Settings layout grammar on the Lab Suites area: compact scan table + detail pane with dedicated multi-select checkboxes. Structure only — theme, orb, home/chat, App nav stay locked. No Settings-style section rail (single collection).

## Who this is for
- Test engineers — scannable Playwright suite list without whole-row select traps
- Developers / agents — clear inherit of Settings template
- Designer — mockups accepted under docs/mockups/suites_plans_layout_inherit/

## User story
As a test engineer, I want Suites listed as a scan table with a dedicated select column and a detail pane, so that I can multi-select for Run selected without whole-row ambiguity and inspect a focused test.

## Requirements
FR-UI-11: Shared secondary-area layout grammar. Suites inherit: Status · Title · File · Last; checkbox column only for multi-select; row opens detail. Settings remains the system template (KAN-324 Done). Rejected: KPI/card dashboards; whole-row toggle.

## Behaviour
- Replace .suite-list-item button stack with scan table: Sel · Status · Title · File · Last.
- Checkbox cell ~28px; stopPropagation; drives multi-select for Run selected.
- Row click focuses detail (title, file, grep, last result, Run this test).
- Toolbar (path, Discover, List, Run selected, Run all) stays area chrome.
- Import/save path stays under Advanced — not list-row chrome.
- External project files never deleted. Gradio out of scope.

## Acceptance criteria
1. Given Suites open with listed tests, When viewing the list, Then a compact scan table shows Sel · Status · Title · File · Last.
2. Given a checkbox cell, When clicking it, Then only selection toggles (no whole-row select).
3. Given a row, When clicking outside the checkbox, Then detail pane focuses that test.
4. Given selected checkboxes, When Run selected, Then those tests are the run set.
5. Given HTML markers, When pytest runs, Then markers prove scan table, checkbox cell, detail pane.
6. Theme tokens, orb, home/chat, App nav unchanged; no new section rail.

## Definition of done
Team DoD from FUNCTIONAL_SPEC §7 (story comment + linked test Done + WORK_LOG + no secrets).

## Out of scope
Plans Cases inherit (follow-on); Lab density TRACK3-LAB; voice; FR-MAN-2; Settings redesign; Gradio; KPI dashboards.

## Dependencies
Mockups docs/mockups/suites_plans_layout_inherit/; Settings template KAN-324 Done; Spec FR-UI-11. Designer accepted 2026-11-22. Active Build should start with this story first.

## Technical notes
ui/desktop/index.html #app-section-suites; desktop.css .suite-list-item; desktop.js renderSuiteList. Markers: data-suite-layout-grammar / data-suite-scan / data-suite-detail. pytest first; CU only if visual; classic orb.

## Mockups
docs/mockups/suites_plans_layout_inherit/00-structure-wire.html
docs/mockups/suites_plans_layout_inherit/01-themed-suites.html
docs/mockups/suites_plans_layout_inherit/02-annotated-build-note.html
docs/mockups/suites_plans_layout_inherit/03-rejected-options.html
""".strip().split(
    "\n"
)

SUITES_TEST_BODY = """## Intro
Verification for Suites FR-UI-11 inherit Story (Relates).

## Who this is for
Testers and coding agents verifying desktop Suites structure markers.

## Test procedure
1. Open desktop_app.py → App → Suites. Discover or List tests on a sample path.
   Expected: scan table with Sel · Status · Title · File · Last (or equivalent columns).
2. Click checkbox cell only on two rows.
   Expected: those rows selected for Run; row focus not required for select.
3. Click a row outside the checkbox.
   Expected: detail pane shows that test’s fields.
4. Run selected.
   Expected: run uses checkbox selection set.
5. Run pytest markers for Suites grammar (command on close-out).
   Expected: markers pass for scan, checkbox cell, detail.
6. Spot-check orb / home / App nav / theme unchanged.

## Acceptance criteria
Mirror parent Story AC 1–6.

## Evidence
pytest command + pass count; CU skipped — unsafe or quiet CU note if visual AC claimed.
""".strip().split(
    "\n"
)

PLANS_STORY_BODY = """## Intro
Inherit FR-UI-11 on Plans · Cases: replace #plan-cases text dump with a compact scan table; row fills the existing edit form in a detail pane. Plan section tabs stay FR-UI-9 chrome. Structure only — theme/orb/home/App nav locked.

## Who this is for
- Test engineers — scannable cases without opaque text dumps
- Developers / agents — inherit Settings/Suites grammar on Primary Plans
- Designer — mockups accepted under docs/mockups/suites_plans_layout_inherit/

## User story
As a test engineer, I want plan cases in a scan table with a detail editor beside them, so that I can scan Status/Id/Name/Tags/Last and edit without a text dump or whole-row enable toggles.

## Requirements
FR-UI-11: Plans — replace #plan-cases text dump with a scan table; row fills the existing edit form in the detail pane; Trace keeps row-opens-case. Selection grammar: Enabled/Archived/Quarantine in detail — not whole-row toggles. FR-UI-9 plan tabs remain.

## Behaviour
- renderPlanCases becomes a scan table: Status · Id · Name · Tags · Last.
- Rehome existing edit / quarantine / run controls into a detail pane beside the table (same fields — geometry change).
- Row click loads case into detail; does not toggle Enabled/Archived.
- Show archived remains a work/toolbar control.
- Do not redesign Trace / Coverage / History in this story.
- Gradio out of scope.

## Acceptance criteria
1. Given Plans · Cases with ≥1 case, When viewing the panel, Then cases appear in a compact scan table (not a plain text dump).
2. Given a case row, When clicking the row, Then detail pane loads that case’s edit fields.
3. Given Enabled/Archived controls, When toggling them, Then they live in detail (not whole-row hit targets).
4. Given Trace panel, When using existing row-opens-case, Then behaviour is unchanged by this story.
5. Given HTML markers, When pytest runs, Then markers prove scan table + detail pane (data-plan-cases-layout-grammar).
6. Theme tokens, orb, home/chat, App nav, plan tabs IA unchanged.

## Definition of done
Team DoD from FUNCTIONAL_SPEC §7.

## Out of scope
Suites inherit (prior story); Trace/Coverage/History redesign; Lab density; voice; FR-MAN-2; KPI dashboards.

## Dependencies
Mockups docs/mockups/suites_plans_layout_inherit/01b-themed-plans-cases.html; Suites inherit should ship first (or in parallel only if Designer prioritises). Spec FR-UI-11. Designer accepted 2026-11-22.

## Technical notes
ui/desktop/index.html #plan-panel-cases / #plan-cases; desktop.js renderPlanCases; desktop.css plan-cases-list. Markers: data-plan-cases-layout-grammar / data-plan-cases-scan / data-plan-case-detail. pytest first.

## Mockups
docs/mockups/suites_plans_layout_inherit/00-structure-wire.html
docs/mockups/suites_plans_layout_inherit/01b-themed-plans-cases.html
docs/mockups/suites_plans_layout_inherit/02-annotated-build-note.html
docs/mockups/suites_plans_layout_inherit/03-rejected-options.html
""".strip().split(
    "\n"
)

PLANS_TEST_BODY = """## Intro
Verification for Plans Cases FR-UI-11 inherit Story (Relates).

## Who this is for
Testers and coding agents verifying Plans · Cases structure markers.

## Test procedure
1. Open desktop_app.py → App → Plans → Cases with a plan that has cases.
   Expected: scan table (Status · Id · Name · Tags · Last) — not a numbered text dump.
2. Click a case row.
   Expected: detail pane shows that case’s edit fields.
3. Toggle Enabled or Archived in detail.
   Expected: controls are in detail; row click alone does not toggle them.
4. Open Trace tab briefly.
   Expected: existing row-opens-case behaviour still works (no regression required beyond smoke).
5. Run pytest markers for Plans Cases grammar (command on close-out).
   Expected: markers pass.
6. Spot-check orb / home / App nav / plan tabs unchanged.

## Acceptance criteria
Mirror parent Story AC 1–6.

## Evidence
pytest command + pass count; CU note or CU skipped — unsafe if visual AC claimed.
""".strip().split(
    "\n"
)


def main() -> None:
    base, auth = load_creds()
    j = Jira(base, auth)
    out: Dict[str, Any] = {"failures": []}
    try:
        suites = j.create_issue(SUITES_STORY, "Story", SUITES_STORY_BODY)
        suites_test = j.create_issue(SUITES_TEST, "test", SUITES_TEST_BODY)
        if suites and suites_test:
            j.link_relates(suites, suites_test)
            j.comment(
                suites,
                [
                    "Studio Bridge 2026-11-22: Designer accepted Suites/Plans FR-UI-11 inherit.",
                    "Mockups: docs/mockups/suites_plans_layout_inherit/",
                    "Active Build should implement this story first (before Plans Cases).",
                    f"Linked test: {suites_test}",
                ],
            )
        plans = j.create_issue(PLANS_STORY, "Story", PLANS_STORY_BODY)
        plans_test = j.create_issue(PLANS_TEST, "test", PLANS_TEST_BODY)
        if plans and plans_test:
            j.link_relates(plans, plans_test)
            j.comment(
                plans,
                [
                    "Studio Bridge 2026-11-22: Designer accepted Suites/Plans FR-UI-11 inherit.",
                    "Implement after Suites inherit story is Done (preferred order).",
                    f"Linked test: {plans_test}",
                ],
            )
        out = {
            "suites_story": suites,
            "suites_test": suites_test,
            "plans_story": plans,
            "plans_test": plans_test,
            "failures": j.failures,
        }
        print(json.dumps(out, indent=2))
    finally:
        j.close()


if __name__ == "__main__":
    main()
