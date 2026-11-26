"""Seed research-addition + HOME/BYOK stories under GAP-CR / new HOME epic. Never prints tokens."""
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
LABELS_GAP = ["gap-cr", "enterprise-backlog", "research-2026-11-26"]
LABELS_HOME = ["home-market", "personal-level", "byok", "vibe-dev"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
)

GAP_EPIC_SUMMARY = (
    "GAP-CR — Enterprise gaps after OPERATE (charts, Manual float, stubs, compliance)"
)
HOME_EPIC_SUMMARY = "HOME-MARKET — Personal level + BYOK agents for home/vibe developers"


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
                "maxResults": 80,
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
        lab = search_label or labels[0]
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
1. Run focused pytest for this story (or design Accept if design-only).
   Expected: exit 0 or documented Accept.
2. Never soft-pass orb home. Never print secrets.

## Acceptance criteria
Mirror parent AC. {DOD}

## Evidence
Pytest command + pass count, or Accept comment for design stories.
"""


def story(
    summary: str,
    intro: str,
    user_story: str,
    requirements: str,
    ac: str,
    oos: str,
    tech: str,
) -> Dict[str, str]:
    body = f"""
## Intro
{intro}

## Who this is for
Home developers, Senior TE, Test Manager, Security — as relevant.

## User story
{user_story}

## Requirements
{requirements}

## Acceptance criteria
{ac}

## {DOD}

## Out of scope
{oos}

## Technical notes
{tech}

## Research
See docs/ops/ENTERPRISE_GAP_RESEARCH.md (enterprise + home/vibe sections).
"""
    return {"summary": summary, "body": body}


GAP_STORIES = [
    story(
        "GAP-CR: Release readiness summary panel (go/no-go + critical path)",
        "Decision-useful release panel: status, critical-path coverage, blockers, freshness — not vanity pass%.",
        "As a Release Manager, I want a go/no-go summary from local runs, so that I can decide without assembling markdown.",
        "FR-REP-1 deepen; Reports / HUD release pack.",
        "1. Given local suite history, When I open Release readiness, Then I see executed/passed/failed/skipped, critical failures, last-run freshness.\n2. Given critical-path tags or config, When shown, Then those flows are distinguished from peripheral tests.\n3. Drill-down links to case evidence. No cloud BI.",
        "Cloud analytics; fake green when data stale.",
        "ui/desktop Reports; reports/*; F3 pack deepen.",
    ),
    story(
        "GAP-CR: Flake and quarantine trend chart in Reports",
        "Industry treats flakiness as first-class; chart quarantine/flake over time from local data.",
        "As a Senior Test Engineer, I want flake trends, so that I prioritise quarantine fixes.",
        "FR-REP-1; FR-PLAN-2 quarantine/flake (KAN-181).",
        "1. Given flake scores/quarantine history, When Reports charts load, Then a flake/quarantine trend is visible.\n2. Empty data → quiet empty.\n3. Never invent flake without stored scores.",
        "Auto-delete flaky cases.",
        "plans/quarantine.py; Reports charts after KAN-384.",
    ),
    story(
        "GAP-CR: Heal proposal provenance + link to Playwright trace action",
        "Heal governance 2026: locator-only heal with before/after + trace evidence; human approve.",
        "As a Developer, I want heal proposals tied to trace evidence, so that I trust Approve.",
        "FR-HEAL-2; FR-TEST-4; never heal assertions.",
        "1. Given a pending heal, When opened, Then show old vs new locator and link/open related trace.zip when present.\n2. Approve still confirm-gated; assertions never proposed.\n3. Pytest for provenance fields.",
        "Auto-apply heal; assertion weaken.",
        "plugins/heal_policy.py; ui Heal detail; OPERATE open-trace.",
    ),
    story(
        "GAP-CR: Manual SBTM session report + debrief fields",
        "Session-based test management: charter coverage %, notes categories, debrief, new charter ideas.",
        "As a Manual Tester, I want a session report after Charter Frame, so that debrief matches industry exploratory practice.",
        "FR-MAN-1 deepen; SBTM patterns.",
        "1. Given ended session, When review opens, Then session report fields exist (coverage estimate, observations, open questions, new charters).\n2. Exportable locally; level-scoped.\n3. No keylog; video still opt-in later.",
        "FR-MAN-2 live circles; silent recording.",
        "plans/manual_session.py; Manual review UI.",
    ),
    story(
        "GAP-CR: Agent governance (token/tool budget + exportable session audit)",
        "Agentic QA buyers expect budgets and exportable tool-call audit — local-first.",
        "As a home or security-conscious user, I want agent budgets and an exportable audit of tool calls, so that runaway loops and opaque agent actions are visible.",
        "FR-AGENT-4/5; FR-SEC-2; agent governance research.",
        "1. Given Settings, When PERSONAL or allowed level, Then optional token/call budget is configurable and enforced.\n2. Given a session, When export audit, Then tool names/timestamps/outcomes export without secrets.\n3. SECRET keeps narrowed tools; no silent raise of budget.",
        "Cloud SIEM; removing confirm gates.",
        "agent/agent.py; settings/local_audit.py; Settings UI.",
    ),
    story(
        "GAP-CR: Expand compliance matrix with Cyber Essentials + SOC2 crosswalk",
        "Extend KAN-392 design matrix with UK Cyber Essentials controls and SOC 2 crosswalk — still not certification.",
        "As a Security adviser, I want CE + SOC2 mapped beside ISO themes, so that UK/home and enterprise buyers see the full gap list.",
        "FR-SEC-6.",
        "1. Given docs/design/COMPLIANCE_MATRIX.md, When reviewed, Then ISO themes, Cyber Essentials five controls, and SOC2 TSC crosswalk appear with shipped vs gap.\n2. No ISO/CE/SOC certified badge in product UI.\n3. Design Accept = Done for this story.",
        "Paying for certification audits in this story.",
        "docs/design/; Relates KAN-392.",
    ),
]

HOME_EPIC_BODY = f"""
## Intro
Serve home developers and vibe coders: add PERSONAL (lowest) security level and BYOK cloud agent providers (Grok/xAI, OpenAI, Anthropic, OpenRouter, OpenAI-compatible) while keeping OFFICIAL/SECRET isolation and local Ollama default. See docs/ops/ENTERPRISE_GAP_RESEARCH.md home section.

## Who this is for
- Home / indie / vibe developers (purchase or download)
- Security (must not weaken SECRET)
- Platform pragmatist (home PC + API cost)

## Problem / outcome
Product was framed enterprise-first; home buyers need stronger cloud agents via their own keys on a lower level without forcing company classification UX.

## Requirements
FR-SEC-1 (PERSONAL + OFFICIAL + SECRET); FR-CONN-1 LLM provider; FR-AGENT-*; FR-SEC-5 keys local only.

## Scope
In: PERSONAL level store; BYOK providers on PERSONAL only; Settings UX; health check; explicit outbound consent; Ollama remains default.
Out: Cloud keys on SECRET; silent telemetry; removing confirm gates; Cursor IDE keys as product runtime.

## Success criteria
Home user can switch to PERSONAL, save a Grok/xAI (or other) key, chat with that provider, and OFFICIAL/SECRET remain isolated with cloud LLM keys refused.

## Dependencies / risks
After OPERATE preferred; may parallel GAP-CR. Risk: accidental cloud send — mitigate with level gates + confirm on first cloud use.

## Technical notes
settings/store levels/; agent LLM client router; Security area; docs/ops/ENTERPRISE_GAP_RESEARCH.md.
{DOD}
"""

HOME_STORIES = [
    story(
        "HOME-1: PERSONAL security level (lowest) for home developers",
        "Add PERSONAL below OFFICIAL. Isolated store like other levels. Default for fresh home installs may be PERSONAL (confirm in AC).",
        "As a home developer, I want a PERSONAL security level, so that I am not forced into UK OFFICIAL/SECRET framing for hobby projects.",
        "FR-SEC-1 CR 2026-11-26; FR-SEC-3 confirm on switch.",
        "1. Given Security area, When levels listed, Then PERSONAL, OFFICIAL, SECRET appear with clear descriptions.\n2. Given switch to PERSONAL, When confirmed, Then settings/plans/creds use levels/PERSONAL/ isolation.\n3. Given SECRET data, When switching away, Then stores stay unmixed.\n4. Pytest for level enum + path isolation.",
        "Merging PERSONAL with OFFICIAL stores; cloud keys (HOME-2).",
        "settings/security; plans_dir; credentials paths; Security UI.",
    ),
    story(
        "HOME-2: BYOK cloud agent providers on PERSONAL only (Grok/xAI et al.)",
        "Bring-your-own-key: xAI/Grok, OpenAI, Anthropic, OpenRouter, generic OpenAI-compatible base URL. PERSONAL only. Ollama remains default and always available.",
        "As a vibe coder, I want to paste my Grok (or other) API key on PERSONAL, so that the in-app agent can use a stronger model than local 7B when I choose.",
        "FR-CONN-1 deepen; FR-AGENT-6; FR-SEC-5; hybrid local+BYOK research 2026.",
        "1. Given PERSONAL, When I save provider+key+model, Then status shows set/missing never the secret; health can ping without echoing key.\n2. Given OFFICIAL or SECRET, When I try to save/use cloud LLM keys, Then refused with clear copy.\n3. Given PERSONAL + cloud provider selected, When first chat that would outbound, Then confirm outbound once per session (or sticky consent in level settings).\n4. Given Ollama selected, When used, Then no cloud key required.\n5. Pytest for gate matrix PERSONAL vs OFFICIAL/SECRET.",
        "Bundled paid SaaS tokens; Cursor API keys; SECRET BYOK; YOLO confirm skip.",
        "agent LLM router; settings credentials level-scoped; Context7/httpx for provider calls.",
    ),
    story(
        "HOME-3: Home/vibe onboarding — demo AUT + fixtures without Jira",
        "First-run path for solo users: demo AUT, Documents pack, starter plan — Jira optional.",
        "As a home developer, I want a Jira-optional first hour, so that I can prove the app on my PC immediately.",
        "FR-UI-6 checklist; OPERATE-2/4 fixtures; vibe onboarding trends.",
        "1. Given fresh PERSONAL, When First-hour / Lab checklist runs, Then steps work without Jira configured.\n2. Demo docs + AUT seed available.\n3. Copy avoids enterprise-only assumptions.",
        "Removing enterprise features; forcing cloud signup.",
        "plans/starter.py; fixtures; checklist HUD; Relates OPERATE-2/4.",
    ),
    story(
        "HOME-4: Council seat + docs — home/vibe developer persona",
        "Ops: ensure Advisory Council seats home/indie persona on market reviews (agent file already added).",
        "As the Designer, I want Council to seat a home/vibe voice, so that enterprise-only reviews do not recur.",
        "ADVISORY_COUNCIL future-user seats; TEAM.md.",
        "1. Given docs/ops/ADVISORY_COUNCIL.md and TEAM.md, When reviewed, Then council-user-home-developer is listed and Review mode seats them for market/gap asks.\n2. Agent file .cursor/agents/council-user-home-developer.md exists.\n3. Design Accept / doc-only Done — no product UI required.",
        "Product feature coding.",
        "docs/ops; .cursor/agents; skill advisory-council.",
    ),
]


def main() -> int:
    keys_path = Path(__file__).resolve().parents[1] / "docs" / "ops" / "OPERATE_KEYS.json"
    prior = json.loads(keys_path.read_text(encoding="utf-8")) if keys_path.exists() else {}
    gap_epic = prior.get("gap_epic") or "KAN-383"

    base, auth = load_creds()
    j = Jira(base, auth)
    out: Dict[str, Any] = {
        "gap_epic": gap_epic,
        "research_stories": {},
        "home_epic": None,
        "home_stories": {},
    }
    try:
        # Resolve gap epic by summary if needed
        found = j.find_by_summary(GAP_EPIC_SUMMARY, "Epic", "gap-cr")
        if found:
            gap_epic = found
            out["gap_epic"] = gap_epic

        for s in GAP_STORIES:
            story_key = j.create_issue(
                s["summary"], "Story", s["body"], LABELS_GAP, parent_epic=gap_epic, search_label="gap-cr"
            )
            test_key = j.create_issue(
                f"Test: {s['summary']}",
                "test",
                test_body(s["summary"]),
                LABELS_GAP + ["test"],
                search_label="gap-cr",
            )
            if story_key and test_key:
                j.link_relates(story_key, test_key)
            out["research_stories"][s["summary"][:48]] = {"story": story_key, "test": test_key}

        home_epic = j.create_issue(
            HOME_EPIC_SUMMARY, "Epic", HOME_EPIC_BODY, LABELS_HOME, search_label="home-market"
        )
        out["home_epic"] = home_epic
        for s in HOME_STORIES:
            story_key = j.create_issue(
                s["summary"],
                "Story",
                s["body"],
                LABELS_HOME,
                parent_epic=home_epic,
                search_label="home-market",
            )
            test_key = j.create_issue(
                f"Test: {s['summary']}",
                "test",
                test_body(s["summary"]),
                LABELS_HOME + ["test"],
                search_label="home-market",
            )
            if story_key and test_key:
                j.link_relates(story_key, test_key)
            out["home_stories"][s["summary"][:48]] = {"story": story_key, "test": test_key}

        if gap_epic:
            j.comment(
                gap_epic,
                [
                    "Seeded research additions 2026-11-26 (release panel, flake chart, heal provenance,",
                    "SBTM report, agent governance, CE/SOC2 matrix expand).",
                    "HOME-MARKET epic seeded separately for PERSONAL + BYOK.",
                ],
            )
        if home_epic:
            j.comment(
                home_epic,
                [
                    "Designer CR: home/vibe developers + BYOK (Grok etc.) on PERSONAL only.",
                    "SECRET/OFFICIAL must refuse cloud LLM keys. Ollama remains default.",
                    "Council seat council-user-home-developer required on market reviews.",
                    "Sequence after OPERATE preferred; Active Build stays KAN-375 until HOME unparked.",
                ],
            )
            if gap_epic:
                j.link_relates(home_epic, gap_epic)

        out_path = Path(__file__).resolve().parents[1] / "docs" / "ops" / "GAP_RESEARCH_KEYS.json"
        out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")

        # Merge into OPERATE_KEYS for discoverability
        prior["gap_research"] = out
        keys_path.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
        print(f"updated {keys_path}")

        if j.failures:
            for f in j.failures:
                print(f"FAIL: {f}", file=sys.stderr)
            return 1
        return 0 if home_epic else 1
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
