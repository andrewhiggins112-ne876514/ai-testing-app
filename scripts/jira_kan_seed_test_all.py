"""
Seed Test-all CR epics + Stories + test tickets from docs/ops/test_all_catalogue.json.

Idempotent by summary match. Credentials from local settings — never logged.

Usage:
  python scripts/jira_kan_seed_test_all.py --dry-run
  python scripts/jira_kan_seed_test_all.py
  python scripts/jira_kan_seed_test_all.py --comment-kan81
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "docs" / "ops" / "test_all_catalogue.json"
PROJECT = "KAN"
BACKOFF = 0.45

TEAM_DOD = [
    "One logical behaviour change is delivered.",
    "A test or recorded manual check exists.",
    "Human has reviewed the meaningful diffs.",
    "PROJECT_MEMORY.md Current State is updated if behaviour changed.",
    "No secrets are in git.",
    "Side-effecting actions still require confirmation.",
    "Self-healing (if touched) still obeys the how-not-what rule and requires approval.",
    "Errors are logged and surfaced rather than swallowed.",
    "docs/ops/WORK_LOG.md has an entry for this slice.",
    "A Jira story comment states what the agent implemented (files + verify).",
    "Linked test ticket (issuetype=test Relates) has evidence comment and is marked Done.",
]


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    levels = path.parent / "levels"
    level = str(data.get("security_level") or "OFFICIAL").upper()
    cred_path = levels / level / "credentials.json"
    if cred_path.exists():
        creds = json.loads(cred_path.read_text(encoding="utf-8-sig"))
        data = {**data, **creds}
    url = (data.get("jira_url") or "https://ai-testing-lab.atlassian.net").rstrip("/")
    email = data.get("jira_email") or ""
    token = data.get("jira_api_token") or ""
    if not token:
        raise SystemExit("Jira API token missing in local settings / level credentials")
    return url, (email, token)


def adf_from_lines(lines: List[str]) -> Dict[str, Any]:
    content: List[Dict[str, Any]] = []
    for line in lines:
        text = (line or "").rstrip()
        if not text:
            continue
        content.append(
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        )
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": "(none)"}]}]
    return {"type": "doc", "version": 1, "content": content}


def story_body(s: Dict[str, Any], epic_summary: str) -> str:
    ac = "\n".join(f"{i}. {a}" for i, a in enumerate(s["ac"], 1))
    oos = "\n".join(f"- {x}" for x in s.get("oos") or [])
    frs = "\n".join(f"- {f}" for f in s.get("fr") or [])
    dod = "\n".join(f"- {d}" for d in TEAM_DOD)
    return "\n".join(
        [
            "Intro",
            f"{s['code']}: {s['why']}",
            "",
            "Who this is for",
            f"Primary — {s['who']}.",
            "Cursor agents — self-contained AC; catalogue docs/ops/test_all_catalogue.json.",
            "",
            "User story",
            f"As a {s['who']}, I want {s['summary'].lower()} so that {s['why']}",
            "",
            "Requirements",
            frs or "- (see FR-PLAN / FR-CONN / FR-UI in FUNCTIONAL_SPEC)",
            "",
            "Behaviour",
            f"Band: {s['band']}. Epic: {epic_summary}. Cut nothing from the product; deepen or sequence only.",
            "One home for everyone: orb + chat. Role views are HUD widgets (Epic F). App areas are full-window work.",
            "",
            "Acceptance criteria",
            ac,
            "",
            "Definition of done",
            dod,
            "",
            "Out of scope",
            oos or "- (none listed)",
            "",
            "Dependencies",
            f"Catalogue code {s['code']}. Sequence: alpha A1–A9 first, then B→C→D→E→F→G; H is design-only.",
            "",
            "Technical notes",
            "- Primary shell: desktop_app.py + ui/desktop/",
            "- Local store: %LOCALAPPDATA%\\ai_testing_app\\",
            "- Spec: docs/FUNCTIONAL_SPEC.md (test-all CR 2026-11-16)",
            "- Catalogue: docs/ops/test_all_catalogue.json",
        ]
    )


def test_body(story_summary: str, ac: List[str]) -> str:
    steps: List[str] = []
    for i, a in enumerate(ac, 1):
        steps.append(f"Step {i}: Exercise — {a}")
        steps.append(f"Expected {i}: Criterion satisfied or gap documented.")
    return "\n".join(
        [
            "Intro",
            f"Verification for story: {story_summary}",
            "",
            "Who this is for",
            "Testers and Cursor agents.",
            "",
            "Test procedure",
            "\n".join(steps),
            "",
            "Acceptance criteria",
            "\n".join(f"- {a}" for a in ac),
            "",
            "Evidence",
            "Record pytest command + pass count and/or desktop Computer Use notes before Done.",
        ]
    )


def epic_body(e: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "Intro",
            e["intro"],
            "",
            "Who this is for",
            "Testers, managers, developers, release, security — eventual daily users of the test-all app.",
            "",
            "Problem / outcome",
            "Prototype baselines exist; this epic sequences coherence toward download-and-connect in-app plan/suite.",
            "",
            "Scope",
            f"In: stories tagged under this epic (band {e['band']}).",
            "Out: deleting Gradio, voice, sandboxes, desktop plugin, orb, layouts, or framework stubs.",
            "",
            "Success criteria",
            "Stories completed in sequence with linked test evidence; nothing existing removed.",
            "",
            "Dependencies / risks",
            "Home PC: one 7B–8B model, one headed browser. Confirm gates and OFFICIAL/SECRET isolation must survive.",
            "",
            "Technical notes",
            "docs/ops/test_all_catalogue.json ; docs/FUNCTIONAL_SPEC.md test-all CR",
        ]
    )


class Jira:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.client = httpx.Client(
            base_url=base,
            auth=auth,
            timeout=60.0,
            verify=ssl.create_default_context(),
        )
        self.failures: List[str] = []

    def close(self) -> None:
        self.client.close()

    def _req(self, method: str, path: str, **kwargs) -> httpx.Response:
        time.sleep(BACKOFF)
        r = self.client.request(method, path, **kwargs)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After") or "5")
            time.sleep(max(wait, 5))
            r = self.client.request(method, path, **kwargs)
        return r

    def search_summaries(self, jql: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        r = self._req(
            "GET",
            "/rest/api/3/search/jql",
            params={"jql": jql, "maxResults": 100, "fields": "summary"},
        )
        if r.status_code >= 300:
            # fallback older search
            r = self._req(
                "GET",
                "/rest/api/3/search",
                params={"jql": jql, "maxResults": 100, "fields": "summary"},
            )
        if r.status_code >= 300:
            self.failures.append(f"search: {r.status_code} {r.text[:200]}")
            return out
        for issue in r.json().get("issues") or []:
            summary = (issue.get("fields") or {}).get("summary") or ""
            out[summary.strip()] = issue["key"]
        return out

    def create_issue(
        self,
        summary: str,
        issue_type: str,
        description: str,
        parent: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Optional[str]:
        fields: Dict[str, Any] = {
            "project": {"key": PROJECT},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": adf_from_lines(description.split("\n")),
        }
        if parent:
            fields["parent"] = {"key": parent}
        if labels:
            fields["labels"] = labels
        r = self._req(
            "POST",
            "/rest/api/3/issue",
            json={"fields": fields},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 201:
            self.failures.append(
                f"create {issue_type} {summary[:60]}: {r.status_code} {r.text[:240]}"
            )
            return None
        return r.json().get("key")

    def link_relates(self, story: str, test_key: str) -> None:
        payload = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": story},
            "outwardIssue": {"key": test_key},
        }
        r = self._req(
            "POST",
            "/rest/api/3/issueLink",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 300:
            self.failures.append(f"link {story}<->{test_key}: {r.status_code} {r.text[:160]}")

    def comment(self, key: str, body: str) -> None:
        r = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf_from_lines(body.split("\n"))},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 300:
            self.failures.append(f"comment {key}: {r.status_code}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--comment-kan81", action="store_true")
    args = ap.parse_args()

    cat = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    epics = cat["epics"]
    stories = cat["stories"]

    if args.dry_run:
        print(f"DRY RUN: {len(epics)} epics, {len(stories)} stories (+ tests)")
        for e in epics:
            print(f"  Epic {e['id']}: {e['summary']}")
        for s in stories:
            print(f"  Story {s['code']}: {s['summary']} [{s['band']}]")
        return 0

    base, auth = load_creds()
    j = Jira(base, auth)
    created: Dict[str, str] = {}
    try:
        existing_epics = j.search_summaries(
            f'project = {PROJECT} AND issuetype = Epic AND summary ~ "Test-all" ORDER BY key ASC'
        )
        # broader story search in pages would be better; match by exact summary prefix
        existing_stories = j.search_summaries(
            f'project = {PROJECT} AND issuetype = Story AND summary ~ "Test-all" ORDER BY key ASC'
        )
        # Also match without relying on ~ if empty
        if not existing_stories:
            existing_stories = j.search_summaries(
                f"project = {PROJECT} AND issuetype = Story ORDER BY created DESC"
            )

        epic_keys: Dict[str, str] = {}
        for e in epics:
            summary = e["summary"]
            key = existing_epics.get(summary)
            if key:
                print(f"skip epic {summary} -> {key}")
                epic_keys[e["id"]] = key
                continue
            key = j.create_issue(summary, "Epic", epic_body(e), labels=["test-all", f"epic-{e['id'].lower()}"])
            if key:
                print(f"created epic {key}: {summary}")
                epic_keys[e["id"]] = key
                created[e["id"]] = key
            else:
                print(f"FAIL epic {e['id']}", file=sys.stderr)

        epic_by_id = {e["id"]: e for e in epics}
        first_story_key: Optional[str] = None

        for s in stories:
            summary = f"Test-all {s['code']} — {s['summary']}"
            # exact match preferred
            key = None
            for sum_text, k in existing_stories.items():
                if sum_text == summary:
                    key = k
                    break
            parent = epic_keys.get(s["epic"])
            if key:
                print(f"skip story {summary} -> {key}")
            else:
                body = story_body(s, epic_by_id[s["epic"]]["summary"])
                labels = ["test-all", s["code"].lower(), s["band"].split()[0].lower()]
                key = j.create_issue(summary, "Story", body, parent=parent, labels=labels)
                if not key:
                    print(f"FAIL story {s['code']}", file=sys.stderr)
                    continue
                print(f"created story {key}: {summary}")
                existing_stories[summary] = key

            if s["code"] == "A1" and first_story_key is None:
                first_story_key = key

            test_summary = f"Test: {summary}"
            # find existing test
            test_key = None
            for sum_text, k in list(existing_stories.items()):
                if sum_text == test_summary:
                    test_key = k
                    break
            if test_key:
                print(f"skip test {test_summary} -> {test_key}")
            else:
                td = test_body(summary, s["ac"])
                test_key = j.create_issue(
                    test_summary, "test", td, labels=["test", "test-all", s["code"].lower()]
                )
                if test_key:
                    print(f"created test {test_key}")
                    j.link_relates(key, test_key)
                else:
                    print(f"FAIL test {s['code']}", file=sys.stderr)

        if args.comment_kan81:
            j.comment(
                "KAN-81",
                "\n".join(
                    [
                        "Council CR 2026-11-16 — Test-all backlog",
                        "Voice remains in the product story as later plugin G10.",
                        "Do not pick up while Active slice is deferred / until mic exists.",
                        "Next Build work starts at Test-all A1 (local plan/suite/case/run model).",
                        "Catalogue: docs/ops/test_all_catalogue.json",
                    ]
                ),
            )
            print("commented KAN-81")

        if first_story_key:
            print(f"FIRST_ALPHA_STORY={first_story_key}")
        if j.failures:
            print("FAILURES:", file=sys.stderr)
            for f in j.failures:
                print(f"  {f}", file=sys.stderr)
            return 1
        return 0
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
