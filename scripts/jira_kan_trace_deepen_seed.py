"""Seed TRACE-DEEPEN Story + linked test. Never prints tokens.

Pick-up after TRACK3-LAB: real Playwright trace.zip replaces trace.notice.txt.
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
LABELS = ["fr-test-4", "fr-plan-4", "trace-deepen", "b1-depth"]

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
    "Heal proposals and report sections can attach to that run. "
    "Traceability links case ↔ Jira key ↔ bugs ↔ known issues."
)

STORY_SUMMARY = "TRACE-DEEPEN: Real Playwright trace.zip on failure (replace notice)"
TEST_SUMMARY = "Test: TRACE-DEEPEN Playwright trace.zip evidence"


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
                    'AND labels = "trace-deepen" ORDER BY created DESC'
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
            "description": adf_from_lines(split_lines(body)),
            "labels": LABELS,
        }
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


STORY_BODY = f"""
## Intro
Deepen B1 failure evidence: Playwright runner writes a real trace.zip into the evidence bundle instead of the placeholder trace.notice.txt. Desktop evidence-first copy reflects whether a real trace exists.

## Who this is for
- Senior Test Engineer — open failure traces in Playwright Trace Viewer
- Developers — plugins/playwright_runner.py + plans/evidence_bundle.py
- Agents — roadmap TRACE-DEEPEN after TRACK3-LAB

## User story
As a Senior Test Engineer, I want failed plan-case runs to store a real Playwright trace.zip with screenshots and DOM snapshots, so that I can diagnose failures beyond a single PNG and a notice file.

## Requirements
{FR_TEST_4}
{FR_PLAN_4}

## Behaviour
- On stepped Playwright runs, start context tracing (screenshots + snapshots).
- On failure, stop tracing to a local zip under the app evidence/screenshots area; put the path on the playwright result as `trace`.
- On pass (or discarded tracing), do not leave a fake notice file claiming to be a trace.
- `write_failure_bundle` prefers a real zip from playwright.trace; never writes trace.notice.txt when a zip was captured. If tracing failed, omit or record a short capture-failed note — not a pretend trace.
- Desktop evidence-first slot: when evidence includes a .zip trace, show that a Playwright trace was captured (path text OK); when absent, say no trace for this run. Do not claim the old notice file is a Playwright trace. No fake “Open Trace” runner control.
- Marker `data-playwright-trace="1"` on run-bearing App sections that show the evidence slot. Cache-bust desk UI.
- Secrets stay out of traces where we already redact evidence indexes; do not invent OCR of screenshots.

## Acceptance criteria
1. Given a stepped Playwright run that fails, When the runner finishes, Then result.trace points to an existing .zip file produced by context.tracing.stop.
2. Given write_failure_bundle with that playwright payload, When the bundle is written, Then bundle.trace is the zip path, paths include the zip, and no new trace.notice.txt is created for that run.
3. Given a failure without a captured zip, When the bundle is written, Then it does not present trace.notice.txt as a Playwright trace.
4. Given desktop evidence-first UI, When a case/run has a .zip in evidence, Then the Trace line states a Playwright trace was captured; When not, Then it does not say runner capture is not hooked / notice file.
5. Given pytest for this story, When it runs, Then it exits 0. CU not required (API/marker AC).

## {DOD}

## Out of scope
Voice KAN-81; FR-MAN-2; CI; H3 share; Trace Viewer embedded UI; success-only always-on traces; Selenium/Cypress; Gradio-first; theme/orb/home.

## Dependencies
After TRACK3-LAB Done (KAN-359). Relates prior B1 evidence baseline KAN-143. Playwright Python async_api in plugins/playwright_runner.py.

## Technical notes
Roadmap TRACE-DEEPEN. Files: plugins/playwright_runner.py, plans/evidence_bundle.py, plans/run_case.py (pass-through), ui/desktop evidence-first copy, tests/test_playwright_trace_deepen.py (+ evidence bundle / evidence-first updates). Context7/installed: context.tracing.start/stop (screenshots=True, snapshots=True).

## Mockups
None — deepen existing evidence slot; DESIGN_INTENT “Real Playwright trace deepen”.
"""

TEST_BODY = f"""
## Intro
Verifies {STORY_SUMMARY}.

## Who this is for
Testers and coding agents.

## Test procedure
1. Run focused pytest for TRACE-DEEPEN (runner trace zip + failure bundle + UI marker/copy).
   Expected: exit 0; asserts real .zip on failure; no notice-as-trace; evidence-first copy updated.
2. Optional spot-check: desktop_app.py → Plans → failed case evidence Trace line mentions Playwright trace when zip present.
   Expected: no “not hooked” / “notice file is not a Playwright trace” as the only Trace story.

## Acceptance criteria
Mirror story AC 1–5. CU not required.

## Evidence
Paste pytest command + pass count on close-out. {DOD}
"""


def main() -> int:
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
                    "Seeded TRACE-DEEPEN (pick-up after TRACK3-LAB).",
                    "Implement next: real Playwright trace.zip; replace trace.notice.txt.",
                    f"Linked test: {test}.",
                    "Park: voice KAN-81, FR-MAN-2, CI.",
                ],
            )
            keys = {"story": story, "test": test, "roadmap": "TRACE-DEEPEN"}
            out = Path(__file__).resolve().parents[1] / "docs" / "ops" / "TRACE_DEEPEN_KEYS.json"
            out.write_text(json.dumps(keys, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {out}")
        if j.failures:
            for f in j.failures:
                print(f"FAIL: {f}", file=sys.stderr)
            return 1
        return 0 if story and test else 1
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
