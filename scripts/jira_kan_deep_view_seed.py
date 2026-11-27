"""Seed Plans deep-view Story + test; tighten KAN-496/497 comments. Never prints tokens.

Designer accept Council 2026-11-27 — thumb also expands (deep-view door).
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
EPIC = "KAN-383"
OPTION_A = "KAN-496"
OPTION_A_TEST = "KAN-497"
LABELS = ["gap-cr", "evidence-ux", "fr-test-4", "deep-view", "council-accepted"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

FR_TEST_4 = (
    "FR-TEST-4 (deepen): Case aside shows one representative captured page or none-captured "
    "reason with step narrative and external Open Trace. A separate Plans deep-view surface "
    "(own story; no new App nav) may show per-step captured pages; entry via More evidence "
    "and thumb expand; DOM/network/console stay in Open Trace; no Trace Viewer embed; "
    "no trace.playwright.dev."
)
FR_PLAN_4 = (
    "FR-PLAN-4 (deepen): ordered step outcomes on the run; may store per-step screenshot refs; "
    "aside still shows one representative shot."
)

STORY_SUMMARY = "Plans deep view — per-step captured pages for a run"
TEST_SUMMARY = "test: Plans run-evidence deep view (frames 05–07)"

STORY_BODY = f"""
## Intro
Additional Plans surface for one case run: selectable steps, large captured page or honest
empty, strip of captured pages only. Entered from the Option A Case aside. Separate from
KAN-496 (aside-only Build).

## Who this is for
Senior Test Engineer (path through shots), Software Developer (fail page at the fail step),
Home developer (optional after the aside demo).

## User story
As a Senior Test Engineer, I want a deeper evidence page for one run with per-step captured
pages, so that I can walk the path of a fail or smoke pass without embedding Trace Viewer
or leaving the Cases list permanently.

## Requirements
{FR_TEST_4}
{FR_PLAN_4}

## Behaviour
- Entry: **More evidence** on the Option A aside (including when the slot is None captured).
- Entry: **thumb expand** opens the same deep view focused on that shot (Designer accept
  2026-11-27 — thumb also expands). Open Trace remains a different hit.
- In-area Plans surface; Cases tab stays; **Back to case** returns to the same case/run.
- Header: case name, Pass/Fail, duration, failure class or tag, Back to case, Open Trace
  (external OPERATE-1).
- Step list matches the aside; choosing a step focuses that step's page on the stage.
- Stage: real PNG or None captured + reason; never a green stand-in.
- Strip: captured page files only, labelled by step; omit steps with no file; one-PNG and
  zero-PNG runs must work; do not unpack trace.zip to invent images; no network/console/DOM tiles.
- Same success-shot setting as the aside. Fail shots still show when present.
- Level-scoped files only; GDPR wipe removes what this surface can open; review-before-share note.

## Acceptance criteria
1. Given a focused case with a last run, When I choose More evidence, Then an in-area deep
   view opens and Back to case returns to the same case.
2. Given a representative thumb on the aside, When I activate thumb expand, Then deep view
   opens focused on that shot (Designer: thumb also expands).
3. Given a step with no PNG, When I select that step, Then the stage shows None captured
   with reason and no green stand-in; the strip omits that step.
4. Given a run with one PNG only, When deep view opens, Then one strip chip appears and
   other steps show honest empty on the stage.
5. Given a zero-PNG fail with trace.zip, When deep view opens, Then steps + empty stage +
   reason show and Open Trace still works externally.
6. Given success shots off, When deep view opens a non-smoke pass, Then pass PNGs stay hidden.
7. Given the deep view, When I look for Trace Viewer / network / console / DOM tiles /
   hosted trace.playwright.dev / a new App nav item, Then none are present.

## {DOD}

## Out of scope
KAN-496 aside narrative (already separate); Trace Viewer embed; hosted trace.playwright.dev;
new App nav item; Reports restyle; screenshot-every-step capture policy; run history picker;
heal actions; theme/orb/home.

## Dependencies
KAN-496 Option A aside behaviour present (or elevated by Designer). Mockups:
docs/mockups/run_evidence_ux/05-deep-view-fail.html, 06-deep-view-pass.html,
07-deep-view-entry.html. Frame 04 remains rejected as Cases replacement.

## Technical notes
ui/desktop Case aside entry controls + Plans in-area deep surface; run record per-step
screenshot refs (FR-PLAN-4); Open Trace = existing OPERATE-1. Relates KAN-496 / KAN-497 /
epic KAN-383.
"""

TEST_BODY = f"""
## Intro
Verifies {STORY_SUMMARY}. Relates to that Story.

## Who this is for
Testers + coding agents.

## Test procedure
1. From a shot run aside → More evidence → Expected: deep view; Back to case returns.
2. From aside thumb expand → Expected: deep view focused on that shot.
3. From zero-PNG fail aside → More evidence → Expected: steps + empty stage + reason;
   Open Trace external when zip exists.
4. Select a step with no PNG → Expected: honest empty stage; no strip chip for that step.
5. One-PNG run → Expected: one strip chip only.
6. Success-shots-off non-smoke pass → Expected: pass PNGs hidden in deep view.
7. Confirm no Trace embed, no network/console/DOM tiles, no new App nav, Cases list reachable.

## Acceptance criteria
Copy of parent AC 1–7.

## Evidence
pytest command + pass count; optional CU/human confirm for visual deep view.
"""

OPTION_A_COMMENT = """h2. Designer accept Council (2026-11-27) — Option A aside only

*Decision:* Accept Council verdict. *KAN-496* / *KAN-497* = Case aside Option A (frames 01–03) only.

*AC (aside):*
# Status → plain-language steps → one representative shot or None captured + reason → Open Trace external.
# Failed step shows error sentence; never fake/placeholder green image.
# Representative rule: fail page for the failing step when that PNG exists; else None captured even if earlier steps have shots.
# Success shots default on for smoke/golden; configurable off; shots-off uses honest empty.
# Thumbnail for *this* story opens the one PNG (in-panel or file). Open Trace is a different hit.
# Persist ordered steps + representative path/none + trace.zip; store per-step PNG refs if the runner wrote them — aside does not render the strip.
# Level-scoped paths; review-before-share note; no Trace Viewer embed; no trace.playwright.dev.

*Out of KAN-496:* More evidence, thumb-expand into deep view, multi-shot strip, deep-view stage (those land on the *separate* deep-view Story). Frame 04 as Cases replacement stays rejected.

*Mockups:* docs/mockups/run_evidence_ux/01–03. Spec FR-TEST-4 / FR-PLAN-4 updated.
"""

DEEP_VIEW_COMMENT = """h2. Designer accept Council (2026-11-27) — deep view + thumb expands

*Decision:* Deep view is a *separate* Story under epic *KAN-383* (not folded into KAN-496).

*Doors:* More evidence *and* thumb expand (Designer override — thumb also expands into deep view focused on that shot). Open Trace remains external / different hit.

*Mockups:* 05-deep-view-fail, 06-deep-view-pass, 07-deep-view-entry. Soft-vetoes: no Trace embed, no hosted viewer, no second evidence cache, no screenshot-every-step default capture.
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

    def close(self) -> None:
        self.client.close()

    def _url(self, path: str) -> str:
        return f"{self.base}{path}"

    def get(self, path: str) -> Dict[str, Any]:
        r = self.client.get(self._url(path))
        r.raise_for_status()
        time.sleep(BACKOFF)
        return r.json()

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        r = self.client.post(self._url(path), json=body)
        if r.status_code >= 400:
            raise SystemExit(f"HTTP {r.status_code} {path}: {r.text[:500]}")
        time.sleep(BACKOFF)
        return r.json() if r.content else {}

    def put(self, path: str, body: Dict[str, Any]) -> None:
        r = self.client.put(self._url(path), json=body)
        if r.status_code >= 400:
            raise SystemExit(f"HTTP {r.status_code} {path}: {r.text[:500]}")
        time.sleep(BACKOFF)

    def find_by_summary(self, summary: str, issue_type: str) -> Optional[str]:
        token = "Plans deep view" if "deep view" in summary.lower() else "run-evidence deep view"
        jql = (
            f'project = {PROJECT} AND issuetype = "{issue_type}" '
            f'AND summary ~ "\\"{token}\\"" ORDER BY created DESC'
        )
        data = self.post(
            "/rest/api/3/search/jql",
            {"jql": jql, "maxResults": 20, "fields": ["summary"]},
        )
        for issue in data.get("issues") or []:
            if (issue.get("fields") or {}).get("summary") == summary:
                return issue["key"]
        return None

    def create(self, itype: str, summary: str, description: str, parent_epic: Optional[str] = None) -> str:
        type_name = "Story" if itype.lower() == "story" else ("test" if itype.lower() == "test" else itype)
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": type_name},
            "description": adf(description.strip().split("\n")),
            "labels": LABELS,
        }
        if parent_epic and type_name == "Story":
            fields["parent"] = {"key": parent_epic}
        try:
            created = self.post("/rest/api/3/issue", {"fields": fields})
        except SystemExit:
            fields.pop("parent", None)
            created = self.post("/rest/api/3/issue", {"fields": fields})
        return created["key"]

    def link_relates(self, a: str, b: str) -> None:
        self.post(
            "/rest/api/3/issueLink",
            {
                "type": {"name": "Relates"},
                "inwardIssue": {"key": a},
                "outwardIssue": {"key": b},
            },
        )

    def comment(self, key: str, text: str) -> None:
        # api/2 wiki body
        r = self.client.post(
            self._url(f"/rest/api/2/issue/{key}/comment"),
            json={"body": text},
        )
        if r.status_code >= 400:
            raise SystemExit(f"HTTP {r.status_code} comment {key}: {r.text[:500]}")
        time.sleep(BACKOFF)

    def set_description(self, key: str, description: str) -> None:
        self.put(
            f"/rest/api/3/issue/{key}",
            {"fields": {"description": adf(description.strip().split("\n"))}},
        )


OPTION_A_DESC = f"""
## Intro
Case aside Option A only: readable run steps + one representative shot or honest empty +
Open Trace. Deep view is a *separate* Story.

## Who this is for
Senior Test Engineer (daily fail reading), Home developer (smoke demo), Software Developer.

## User story
As a Senior Test Engineer, I want the Case aside to show plain steps and one real shot
(or why none), so that I understand the last run without JSON or Trace Viewer.

## Requirements
{FR_TEST_4}
{FR_PLAN_4}

## Behaviour
Studio frames 01–03. Vertical story in existing Plans → Cases aside. Thumbnail opens the
one PNG for this story. More evidence / thumb-expand deep view are out of this story.

## Acceptance criteria
1. Given a smoke pass, When Case detail opens, Then ordered plain steps + success shot
   (or honest none) are visible; no fake green image.
2. Given an intentional fail, When Case detail opens, Then failed step shows the error and
   the fail page (or None captured if that step has no PNG).
3. Given none captured, When Case detail opens, Then reason is shown and Open Trace still
   works when zip exists.
4. Given success shots off on a non-smoke pass, When Case detail opens, Then honest empty
   (not a green card).
5. Thumbnail opens the one PNG; Open Trace is a different external control.
6. Pytest/markers cover narrative + representative rule + honest empty; no More evidence /
   deep-view strip required for Done.

## {DOD}

## Out of scope
Deep view (05–07); More evidence; thumb-expand into multi-shot; Trace embed; Reports charts;
theme/orb/home; OPERATE-3 absorb.

## Dependencies
OPERATE-1..4 Done. Mockpack docs/mockups/run_evidence_ux/01–03 Accepted.
"""

OPTION_A_TEST_DESC = f"""
## Intro
Verifies KAN-496 Option A Case aside only.

## Who this is for
Testers + coding agents.

## Test procedure
1. Smoke pass → steps + pass evidence or honest none.
2. Intentional fail → error sentence + fail shot or None captured for that step.
3. Honest empty → reason; Open Trace if zip exists.
4. Shots-off non-smoke → honest empty.
5. Thumb opens PNG; Open Trace external; no deep-view / More evidence required for Done.

## Acceptance criteria
Copy of KAN-496 AC 1–6.

## Evidence
pytest command + pass count.
"""


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        story = j.find_by_summary(STORY_SUMMARY, "Story")
        if not story:
            story = j.create("story", STORY_SUMMARY, STORY_BODY, parent_epic=EPIC)
            print(f"created story {story}")
        else:
            j.set_description(story, STORY_BODY)
            print(f"updated story {story}")

        test_key = j.find_by_summary(TEST_SUMMARY, "test")
        if not test_key:
            test_key = j.create("test", TEST_SUMMARY, TEST_BODY)
            print(f"created test {test_key}")
        else:
            j.set_description(test_key, TEST_BODY)
            print(f"updated test {test_key}")

        for a, b in (
            (story, OPTION_A),
            (story, OPTION_A_TEST),
            (story, EPIC),
            (test_key, story),
        ):
            try:
                j.link_relates(a, b)
                print(f"relates {a} ↔ {b}")
            except SystemExit as e:
                print(f"link skip {a}-{b}: {e}")

        j.set_description(OPTION_A, OPTION_A_DESC)
        j.set_description(OPTION_A_TEST, OPTION_A_TEST_DESC)
        print(f"tightened {OPTION_A} / {OPTION_A_TEST}")

        j.comment(OPTION_A, OPTION_A_COMMENT)
        j.comment(OPTION_A_TEST, OPTION_A_COMMENT)
        j.comment(story, DEEP_VIEW_COMMENT)
        j.comment(test_key, DEEP_VIEW_COMMENT)
        print("comments posted")
        print(f"KEYS story={story} test={test_key}")
    finally:
        j.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
