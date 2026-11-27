"""Seed GAP-CR: readable run steps + pass/fail evidence gallery (Designer CR 2026-11-27).

For Council review — no product feature code in this script. Never prints tokens.
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
GAP_EPIC = "KAN-383"
LABELS = ["gap-cr", "evidence-ux", "fr-test-4", "operate-followon", "council-review"]
SUMMARY = "GAP-CR: Readable run steps + pass/fail evidence gallery"
TEST_SUMMARY = "test: Readable run steps + pass/fail evidence gallery"

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

FR_TEST_4 = (
    "FR-TEST-4: Capture screenshots / evidence on failure and success where useful. "
    "Deepen (CR 2026-11-27): readable step-by-step action narrative after a run; "
    "evidence first-class for fails and passes; success evidence on by default for "
    "smoke/golden-path; Case detail = steps + thumbnail/gallery + open-trace as one story."
)
FR_PLAN_4 = (
    "FR-PLAN-4: A run stores result, evidence, duration, and failure class. "
    "Deepen (CR 2026-11-27): ordered step outcomes retained for narrative timeline; "
    "screenshot + trace.zip linked on the same run."
)

STORY_BODY = f"""
## Intro
After the OPERATE-2 home-PC demo walkthrough, Case detail is not yet a scannable
story of what the test did. Testers and auditors need readable steps plus visible
evidence for fails and passes.

## Who this is for
Senior Test Engineer (daily), Test Manager / auditor (pass proof), Designer (home demo), Council.

## User story
As a Senior Test Engineer, I want each run to show clear step-by-step actions and
screenshots for pass and fail, so that I can explain results to colleagues and keep
audit-ready evidence without digging through raw JSON.

## Requirements
{FR_TEST_4}
{FR_PLAN_4}

## Behaviour
- Case detail (and optionally Reports run view) shows an ordered **step timeline**:
  human labels for goto/click/fill/expect with per-step pass/fail and short error text.
- Failed runs: screenshot thumbnail + open full + Open Playwright Trace (OPERATE-1).
- Passed runs: at least one success screenshot when `playwright_success_evidence` /
  smoke-golden defaults apply; never invent a fake green screenshot.
- Empty evidence states are honest (\"none captured\" + why), never soft-pass.
- OPERATE-3 may keep a light evidence-affordance polish; this story is the deeper UX.
- Theme/orb/home/App nav locked. Studio mockups before Build if Council agrees.

## Acceptance criteria
1. Given a finished smoke pass on the demo AUT, When Case detail opens, Then steps
   are listed in order in plain language and a success screenshot (or honest none) is visible.
2. Given a finished intentional-fail run, When Case detail opens, Then failed step is
   highlighted, screenshot + open-trace controls are visible without leaving the panel.
3. Given raw run JSON alone, When a tester opens Case detail, Then they do not need
   to read JSON to understand what ran.
4. Markers + pytest for DOM contract; CU only if visual/occlusion AC; skip unsafe honestly.

## {DOD}

## Out of scope
Embedded Trace Viewer SPA; theme/orb redesign; full Reports charts (separate GAP-CR);
FR-MAN-2; voice.

## Dependencies
OPERATE-1 open-trace Done; OPERATE-2 demo AUT Done; TRACK5 evidence-first baseline.
Council Review/Creative on this CR before Build expands beyond OPERATE-3 light polish.

## Technical notes
plans/run_case.py step persistence; plugins/playwright_runner.py success evidence;
ui/desktop Case detail; docs/ops/DAILY_LOOP.md; Studio mockups under docs/mockups if agreed.
Relates OPERATE-3 KAN-379 (do not silently absorb full scope into OPERATE-3).
"""

TEST_BODY = f"""
## Intro
Verifies {SUMMARY}.

## Who this is for
Testers + coding agents.

## Test procedure
1. Run OPERATE golden path smoke → Expected: Case detail shows ordered steps + pass evidence.
2. Run intentional-fail → Expected: failed step highlighted + screenshot + open-trace.
3. Confirm no raw-JSON-only requirement for understanding the run.
4. pytest markers for step timeline + evidence slot.

## Acceptance criteria
Copy of parent AC 1–4.

## Evidence
pytest command + pass count; optional CU/human confirm for visual gallery.
"""


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


def adf(lines: List[str]) -> Dict[str, Any]:
    content = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": line if line.strip() else " "}],
        }
        for line in lines
    ]
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
                    f'AND summary ~ "Readable run steps" ORDER BY created DESC'
                ),
                "maxResults": 20,
                "fields": ["summary"],
            },
        )
        if r.status_code >= 300:
            self.failures.append(f"search: {r.status_code}")
            return None
        for issue in r.json().get("issues") or []:
            if (issue.get("fields") or {}).get("summary") == summary:
                return issue["key"]
        return None

    def create(
        self,
        summary: str,
        issue_type: str,
        body: str,
        *,
        parent: Optional[str] = None,
    ) -> Optional[str]:
        existing = self.find_by_summary(summary, issue_type)
        if existing:
            print(f"exists {issue_type}: {existing}")
            return existing
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf(body.strip().split("\n")),
            "labels": LABELS,
        }
        if parent and issue_type == "Story":
            fields["parent"] = {"key": parent}
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201 and parent and issue_type == "Story":
            fields.pop("parent", None)
            r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code != 201:
            self.failures.append(f"create {summary[:40]}: {r.status_code} {r.text[:200]}")
            return None
        key = r.json().get("key")
        print(f"created {issue_type}: {key}")
        return key

    def link(self, a: str, b: str) -> None:
        r = self._req(
            "POST",
            "/rest/api/3/issueLink",
            json={
                "type": {"name": "Relates"},
                "inwardIssue": {"key": a},
                "outwardIssue": {"key": b},
            },
        )
        if r.status_code >= 300:
            self.failures.append(f"link {a}<->{b}: {r.status_code}")

    def comment(self, key: str, lines: List[str]) -> None:
        self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf(lines)},
        )


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    keys_path = Path(__file__).resolve().parents[1] / "docs" / "ops" / "GAP_RESEARCH_KEYS.json"
    try:
        story = j.create(SUMMARY, "Story", STORY_BODY, parent=GAP_EPIC)
        test = j.create(TEST_SUMMARY, "test", TEST_BODY)
        if story and test:
            j.link(story, test)
            j.link(story, "KAN-379")
            j.link(story, "KAN-377")
            j.link(story, GAP_EPIC)
            j.comment(
                story,
                [
                    "CR 2026-11-27 (Designer after OPERATE-2 confirm): seeded for Council review.",
                    "Spec updated: FR-TEST-4 + FR-PLAN-4 deepen in docs/FUNCTIONAL_SPEC.md.",
                    "Do not Build-implement until Council agree / Slice-0. OPERATE-3 stays light polish only.",
                    "Next: open /council with this story.",
                ],
            )
            j.comment(
                "KAN-379",
                [
                    "CR 2026-11-27: deeper readable steps + pass/fail evidence gallery seeded under GAP-CR",
                    f"({story}). OPERATE-3 remains light evidence-affordance only — do not absorb full CR.",
                ],
            )
        # Merge keys file
        data: Dict[str, Any] = {}
        if keys_path.exists():
            data = json.loads(keys_path.read_text(encoding="utf-8"))
        research = data.setdefault("research_stories", data.get("research_stories") or {})
        if not isinstance(research, dict):
            # file shape: top-level research under gap_research
            pass
        # GAP_RESEARCH_KEYS uses research_stories at top in some shapes; OPERATE_KEYS nests.
        # Write a dedicated pointer file for this CR.
        out = {
            "cr": "2026-11-27-run-evidence-ux",
            "summary": SUMMARY,
            "story": story,
            "test": test,
            "epic": GAP_EPIC,
            "relates": ["KAN-379", "KAN-377", GAP_EPIC],
            "status": "awaiting_council",
        }
        out_path = keys_path.parent / "CR_RUN_EVIDENCE_UX_KEYS.json"
        out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        # Also append into GAP_RESEARCH_KEYS research_stories if present
        root = data
        if "research_stories" in data:
            data["research_stories"][SUMMARY[:48]] = {"story": story, "test": test}
        elif "gap_research" in data and isinstance(data["gap_research"], dict):
            rs = data["gap_research"].setdefault("research_stories", {})
            rs[SUMMARY[:48]] = {"story": story, "test": test}
        else:
            data.setdefault("extra_gap_stories", {})[SUMMARY[:48]] = {
                "story": story,
                "test": test,
            }
        keys_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": not j.failures, "story": story, "test": test, "failures": j.failures}))
        return 0 if story and test and not j.failures else 1
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
