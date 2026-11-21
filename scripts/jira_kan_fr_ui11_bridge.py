"""Create FR-UI-11 Settings layout grammar Story + linked test. Never prints tokens."""
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

STORY_SUMMARY = (
    "Settings area — apply FR-UI-11 layout grammar (rail + scan table + detail)"
)
TEST_SUMMARY = "Test: Settings FR-UI-11 layout grammar (rail, checkbox cell, detail)"


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
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": (
                    f'project = {PROJECT} AND issuetype = "{issue_type}" '
                    f'AND summary ~ "layout grammar" ORDER BY created DESC'
                ),
                "maxResults": 20,
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
            "labels": ["fr-ui-11", "track4-layout", "studio-bridge"],
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


STORY_BODY = """## Intro
Implement the accepted Design Studio Settings layout grammar (FR-UI-11) on the native desktop Settings area. Structure only — theme, orb, home/chat, and App nav stay locked.

## Who this is for
- Test engineers — scannable Settings without whole-row checkbox traps
- Developers / agents — clear layout template before Suites/Plans inherit
- Designer — mockups accepted under docs/mockups/settings_layout_grammar/

## User story
As a test engineer, I want Settings organised as an in-area section rail, compact scan tables, and a detail pane with dedicated selection hit targets, so that I can scan and edit without accidental whole-row toggles or flat section soup.

## Requirements
FR-UI-11: Shared secondary-area layout grammar — in-area section rail + compact scan table + detail pane. Checkbox = dedicated ~28px cell (click stops on control). Row click focuses/opens detail — never whole-row toggle. Destructive actions in detail behind confirm. Settings is the system template. Security remains its own App area.

FR-SET-4: Settings hub prefers FR-UI-11 section rail over flat App/Report tab + undifferentiated h4 stack. Report include/exclude stays under Settings. Security confirm/GDPR delete stay on Security area.

## Behaviour
- In-area section rail: Layout, Connections, Environments, Model & runner, Report blocks, Credentials (not new App nav).
- Environments / Report blocks as compact scan tables; dedicated checkbox cells; row focuses detail.
- Delete env / clear credential in detail behind confirm — not on list-row chrome.
- Reuse KAN-297 tokens and .area-chrome-toolbar / .area-work. Gradio out of scope.

## Acceptance criteria
1. Given Settings open on desktop, When viewing work surface, Then in-area section rail lists Layout, Connections, Environments, Model & runner, Report blocks, Credentials.
2. Given Environments or Report blocks list, When clicking checkbox cell, Then only that control toggles (no whole-row toggle).
3. Given a collection row, When clicking row outside checkbox, Then detail pane focuses that item.
4. Given environment in detail, When looking for Delete, Then it is in detail (with confirm), not on list-row chrome.
5. Given HTML markers, When pytest runs, Then markers prove rail, dedicated checkbox cell, row-focus detail, delete not on list row.
6. Theme tokens, orb, home/chat, App nav unchanged.

## Definition of done
Team DoD from FUNCTIONAL_SPEC §7 (story comment + linked test Done + WORK_LOG + no secrets).

## Out of scope
Suites/Plans inheritance; Security full redesign; Gradio Settings; orb/theme/home/nav; KPI dashboards.

## Dependencies
Mockups docs/mockups/settings_layout_grammar/; Spec FR-UI-11 + FR-SET-4 CR 2026-11-21. Active Build currently deferred — implement when Designer sets this story Active.

## Technical notes
ui/desktop/index.html #app-section-settings; desktop.css; desktop.js. Pytest: test_settings_security_density.py / test_settings_hub.py. pytest first; CU only if visual; classic orb; no live secret screenshots.

## Mockups
docs/mockups/settings_layout_grammar/00-structure-wire.html
docs/mockups/settings_layout_grammar/01-themed-preferred.html
docs/mockups/settings_layout_grammar/02-annotated-build-note.html
docs/mockups/settings_layout_grammar/03-rejected-options.html
""".strip().split(
    "\n"
)

TEST_BODY = """## Intro
Verification for Settings FR-UI-11 layout grammar Story (Relates).

## Who this is for
Testers and coding agents verifying desktop Settings structure markers.

## Test procedure
1. Open desktop_app.py → App → Settings.
   Expected: in-area section rail (or equivalent section nav) visible inside Settings chrome.
2. Open Environments (or Report blocks) section with ≥1 row.
   Expected: compact scan table; checkbox is a dedicated cell.
3. Click checkbox cell only.
   Expected: selection toggles; row does not act as whole-row toggle for unrelated focus steal.
4. Click row outside checkbox.
   Expected: detail pane focuses that item’s fields.
5. Inspect Delete / clear-credential controls.
   Expected: in detail pane behind confirm — not on list-row chrome.
6. Run pytest markers for Settings grammar (command recorded on close-out).
   Expected: markers pass for rail, checkbox cell, row-focus, delete placement.
7. Confirm orb / home / App nav / theme tokens unchanged (spot-check).

## Acceptance criteria
Mirror parent Story AC 1–6.

## Evidence
pytest command + pass count; optional quiet CU note or CU skipped — unsafe for live Settings secrets.
""".strip().split(
    "\n"
)


def main() -> None:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        story = j.create_issue(STORY_SUMMARY, "Story", STORY_BODY)
        test = j.create_issue(TEST_SUMMARY, "test", TEST_BODY)
        if story and test:
            j.link_relates(story, test)
            j.comment(
                story,
                [
                    "Studio Bridge 2026-11-21: Spec FR-UI-11 + Design Intent accepted.",
                    "Mockups: docs/mockups/settings_layout_grammar/",
                    "Do not implement while Active Build is deferred unless Designer sets this story Active.",
                    f"Linked test: {test}",
                ],
            )
        print(json.dumps({"story": story, "test": test, "failures": j.failures}, indent=2))
    finally:
        j.close()


if __name__ == "__main__":
    main()
