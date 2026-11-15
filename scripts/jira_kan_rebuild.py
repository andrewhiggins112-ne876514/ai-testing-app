"""
One-shot KAN backlog rebuild from docs/FUNCTIONAL_SPEC.md (run locally only).
Reads Jira credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logs the token.
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

PROJECT = "KAN"
DONE_ID = "41"
BACKOFF = 0.35
PROBE_KEYS = ("KAN-17", "KAN-18", "KAN-19")

EPICS = [
    ("Conversational Agent Core", "FR-AGENT-*"),
    ("Learning Inputs and Document Ingestion", "FR-LEARN-*"),
    ("Test Generation and Execution", "FR-TEST-*"),
    ("Self-Healing Guardrails", "FR-HEAL-*"),
    ("Jira and Xray Integration", "FR-JIRA-*"),
    ("Reporting", "FR-REP-*"),
    ("Security and Isolation", "FR-SEC-*"),
    ("UI and Desktop Experience", "FR-UI-*"),
    ("Plugins and Extensibility", "FR-PLUG-*"),
    ("Settings and Local Store", "FR-SET-*"),
]

# existing story key -> new epic area index (0..9)
REMAP = {
    "KAN-8": 0,
    "KAN-9": 2,
    "KAN-10": 7,
    "KAN-11": 5,
    "KAN-12": 4,
    "KAN-13": 8,
    "KAN-14": 3,
    "KAN-15": 6,
    "KAN-16": 9,
}

DONE_STORIES = {
    "KAN-8",
    "KAN-9",
    "KAN-11",
    "KAN-12",
    "KAN-13",
    "KAN-16",
}

NEW_DONE = [
    (
        0,
        "FastAPI backend — /chat, /health, /api/orb",
        "FR-AGENT-3",
        "FastAPI `main.py` exposes chat, health, orb API, and static UI.",
        [
            "GET /health returns ok",
            "POST /chat accepts messages and returns agent reply",
            "Static /ui served",
        ],
    ),
    (
        7,
        "Native desktop shell + WebGL hero orbs",
        "FR-UI-2, FR-UI-3",
        "pywebview desktop window; mystic/aether/neural/apex WebGL orbs; per-style settings.",
        [
            "desktop_app.py opens mystic shell",
            "Style switch updates theme accent",
            "Orb sliders persist per style in localStorage",
        ],
    ),
    (
        8,
        "Cursor ops — rules, agents, skills, HOW_WE_WORK",
        "FR-PLUG-1",
        "`.cursor/rules`, custom agents, skills, `docs/ops/*` workflow.",
        [
            "AGENTS.md and slice workflow documented",
            "Skills: run-local-stack, slice-workflow present",
        ],
    ),
]

OPEN_BACKLOG = [
    (
        1,
        "Document ingestion → settings proposals",
        "FR-LEARN-1, FR-LEARN-5",
        "Ingest specs/PDFs; propose URLs/credentials; confirm before store.",
        ["User uploads spec", "Agent proposes settings diff", "Nothing stored without confirm"],
    ),
    (
        2,
        "Desktop .exe testing plugin",
        "FR-TEST-3",
        "Separate desktop runner plugin; do not fork Playwright.",
        ["Plugin toggled in settings", "Sample .exe smoke path documented"],
    ),
    (
        3,
        "Enforce self-healing guardrails (how not what)",
        "FR-HEAL-1..FR-HEAL-5",
        "Full guardrails from FUNCTIONAL_SPEC §3.4 before broad heal.",
        ["Heal proposal shows locator diff only", "Assertion weaken refused in tests"],
    ),
    (
        5,
        "Customisable reporting polish",
        "FR-REP-2",
        "User-selectable report sections on top of exporter.",
        ["Report config persisted locally", "Export respects section toggles"],
    ),
    (
        7,
        "UI-6 resizable panels (remainder)",
        "FR-UI-4",
        "Resize handles; layout persists with drag/snap desktop work.",
        ["Panel resize updates layout", "Reload restores layout"],
    ),
    (
        8,
        "Multi-sandbox orchestration plugin",
        "FR-PLUG-1",
        "Future plugin slot; design stub only.",
        ["Plugin registry accepts sandbox plugin"],
    ),
]

OLD_EPIC_RETIRE = {
    "KAN-5": "Replaced by area epics (Agent, Test, Security, …) — see KAN backlog from FUNCTIONAL_SPEC.",
    "KAN-6": "Replaced by FR-TEST / FR-HEAL / FR-REP epics.",
    "KAN-7": "Replaced by FR-SEC epic and security stories.",
}

OBSOLETE = {
    "KAN-1": "Early scaffolding. See Done stories under Conversational Agent Core and Test epics.",
    "KAN-2": "Superseded by KAN-8 and FastAPI/agent Done stories.",
    "KAN-3": "Superseded by structured Story → Task(test) hierarchy.",
    "KAN-4": "Superseded by pytest suite story KAN-13 and Playwright runner KAN-9.",
}


def _load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    url = (settings.get("jira_url") or "").rstrip("/")
    email = settings.get("jira_email") or ""
    token = settings.get("jira_api_token") or ""
    if not url or not token:
        raise SystemExit("Jira not configured in local settings")
    return url, (email, token)


def adf(text: str) -> Dict[str, Any]:
    blocks = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        blocks.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line}],
            }
        )
    if not blocks:
        blocks = [{"type": "paragraph", "content": [{"type": "text", "text": "(none)"}]}]
    return {"type": "doc", "version": 1, "content": blocks}


def story_description(
    summary: str,
    description: str,
    acceptance: List[str],
    trace: str,
    out_of_scope: str = "See FUNCTIONAL_SPEC for full FR list.",
    mockups: str = "Repo: docs/mockups/, docs/FUNCTIONAL_SPEC.md",
) -> str:
    ac = "\n".join(f"- {a}" for a in acceptance)
    return (
        f"Summary\n{summary}\n\n"
        f"Description\n{description}\n\n"
        f"Acceptance Criteria\n{ac}\n\n"
        f"Mockups/refs\n{mockups}\n\n"
        f"Out of scope\n{out_of_scope}\n\n"
        f"Traceability\n{trace}"
    )


class JiraClient:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.auth = auth
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.client = httpx.Client(
            timeout=45.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers=self.headers,
        )
        self.failures: List[str] = []

    def close(self) -> None:
        self.client.close()

    def _sleep(self) -> None:
        time.sleep(BACKOFF)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        for attempt in range(5):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code == 429:
                wait = float(r.headers.get("Retry-After", "2"))
                time.sleep(wait)
                continue
            return r
        return r

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
            "description": adf(description),
        }
        if parent:
            fields["parent"] = {"key": parent}
        if labels:
            fields["labels"] = labels
        r = self._request("POST", "/rest/api/3/issue", json={"fields": fields})
        self._sleep()
        if r.status_code != 201:
            self.failures.append(f"create {issue_type} {summary[:40]}: {r.status_code} {r.text[:200]}")
            return None
        return r.json().get("key")

    def update_issue(self, key: str, fields: Dict[str, Any]) -> bool:
        r = self._request("PUT", f"/rest/api/3/issue/{key}", json={"fields": fields})
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"update {key}: {r.status_code} {r.text[:200]}")
            return False
        return True

    def comment(self, key: str, body: str) -> None:
        r = self._request(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf(body)},
        )
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"comment {key}: {r.status_code}")

    def transition(self, key: str, transition_id: str = DONE_ID) -> None:
        r = self._request(
            "POST",
            f"/rest/api/3/issue/{key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"transition {key}: {r.status_code} {r.text[:120]}")

    def link_relates(self, story: str, task: str) -> None:
        payload = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": story},
            "outwardIssue": {"key": task},
        }
        r = self._request("POST", "/rest/api/3/issueLink", json=payload)
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"link {story}<->{task}: {r.status_code}")


def main() -> int:
    base, auth = _load_creds()
    j = JiraClient(base, auth)

    epic_keys: List[str] = []
    created_stories = 0
    created_tests = 0
    closed: List[str] = []

    # 1) Epics
    for title, trace in EPICS:
        desc = story_description(
            title,
            f"Epic for {trace} per docs/FUNCTIONAL_SPEC.md §3.",
            ["Epic visible on KAN board", "Child stories use this epic as parent"],
            trace,
        )
        key = j.create_issue(f"[Epic] {title}", "Epic", desc)
        if key:
            epic_keys.append(key)

    if len(epic_keys) != len(EPICS):
        print(json.dumps({"error": "epic_create_incomplete", "epic_keys": epic_keys, "failures": j.failures}))
        j.close()
        return 1

    epic_by_area = {i: epic_keys[i] for i in range(len(epic_keys))}

    # Retire probe issues
    for pk in PROBE_KEYS:
        j.comment(pk, "Probe issue from backlog rebuild script — closing.")
        j.transition(pk)
        closed.append(pk)

    # 2) Remap KAN-8..16
    enrichments = {
        "KAN-8": (
            "Ollama tool-calling agent with clarification and sessions.",
            ["Clarifies ambiguous requests", "Sessions persist", "Side effects require confirm"],
            "FR-AGENT-1..FR-AGENT-5",
        ),
        "KAN-9": (
            "Playwright runner: steps, click self-heal, screenshots.",
            ["Headed Playwright run works", "Click heal attempts alternate locator", "Evidence path returned"],
            "FR-TEST-2, FR-TEST-4",
        ),
        "KAN-10": (
            "Gradio UI with energy orb and presets.",
            ["Gradio launches via run_ui.py", "Orb presets save/load"],
            "FR-UI-1, FR-UI-3",
        ),
        "KAN-11": (
            "Report export JSON + Markdown.",
            ["Exporter produces artifacts under reports path"],
            "FR-REP-3",
        ),
        "KAN-12": (
            "Jira list/create/transition/comment with two-step confirm on writes.",
            ["list_stories works", "create requires user confirm"],
            "FR-JIRA-1, FR-JIRA-5",
        ),
        "KAN-13": (
            "pytest suite for core plugins and orb.",
            ["pytest passes for jira/playwright/orb/settings tests"],
            "FR-PLUG-1",
        ),
        "KAN-14": (
            "Broader self-healing improvements.",
            ["Beyond click heal — guardrails enforced per spec"],
            "FR-HEAL-1",
        ),
        "KAN-15": (
            "UK OFFICIAL/SECRET isolation.",
            ["Security level switcher exists", "Isolation not complete"],
            "FR-SEC-1",
        ),
        "KAN-16": (
            "Local settings store; no secrets in repo.",
            ["settings under LOCALAPPDATA", "No credentials in git"],
            "FR-SET-1, FR-JIRA-7",
        ),
    }

    for key, area_idx in REMAP.items():
        epic = epic_by_area[area_idx]
        desc_parts = enrichments[key]
        desc = story_description(key + " — " + desc_parts[0], desc_parts[0], desc_parts[1], desc_parts[2])
        j.update_issue(key, {"parent": {"key": epic}, "description": adf(desc)})
        if key in DONE_STORIES:
            j.transition(key)
        test_key = j.create_issue(
            f"Test: {key} acceptance",
            "test",
            story_description(
                f"Verify {key}",
                "Automated / manual verification steps for parent story.",
                desc_parts[1],
                desc_parts[2],
            ),
            labels=["test"],
        )
        if test_key:
            created_tests += 1
            j.link_relates(key, test_key)
    # 3) New Done stories
    new_done_keys: List[str] = []
    for area, summary, trace, body, ac in NEW_DONE:
        desc = story_description(summary, body, ac, trace)
        sk = j.create_issue(summary, "Story", desc, parent=epic_by_area[area])
        if sk:
            created_stories += 1
            new_done_keys.append(sk)
            j.transition(sk)
            tk = j.create_issue(
                f"Test: {summary[:50]}",
                "test",
                story_description("Verification", "Run manual/automated checks.", ac, trace),
                labels=["test"],
            )
            if tk:
                created_tests += 1
                j.link_relates(sk, tk)

    # 4) Open backlog stories
    open_keys: List[str] = []
    for area, summary, trace, body, ac in OPEN_BACKLOG:
        desc = story_description(summary, body, ac, trace)
        sk = j.create_issue(summary, "Story", desc, parent=epic_by_area[area])
        if sk:
            created_stories += 1
            open_keys.append(sk)
            tk = j.create_issue(
                f"Test: {summary[:50]}",
                "test",
                story_description("Verification steps", body, ac, trace),
                labels=["test"],
            )
            if tk:
                created_tests += 1
                j.link_relates(sk, tk)

    # KAN-14 stays To Do (broader heal not shipped); KAN-15 To Do

    # 5) Obsolete + old epics
    retire_comment = "New epics: " + ", ".join(epic_keys)
    for key, msg in OLD_EPIC_RETIRE.items():
        j.comment(key, msg + "\n\n" + retire_comment)
        j.transition(key)
        closed.append(key)

    for key, msg in OBSOLETE.items():
        j.comment(key, msg)
        j.transition(key)
        closed.append(key)

    # Mark KAN-10 as partial — already transitioned Done; comment only
    j.comment(
        "KAN-10",
        "Gradio + orb presets shipped. Resizable panels tracked under UI-6 open story.",
    )

    summary = {
        "epic_keys": epic_keys,
        "new_done_story_keys": new_done_keys,
        "open_story_keys": open_keys,
        "stories_created": created_stories,
        "test_tasks_created": created_tests,
        "closed_keys": closed,
        "remapped": list(REMAP.keys()),
        "failures": j.failures,
    }
    print(json.dumps(summary, indent=2))
    j.close()
    return 0 if not j.failures else 2


if __name__ == "__main__":
    sys.exit(main())