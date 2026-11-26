"""Seed FULL-REVIEW 2026-11-26 gaps + HOME-5+ + OPERATE-3 fold-in + SEC heal/trace Bug.
Never prints tokens. Designer confirm: yes+spec patches.
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
LABELS = ["full-review-2026-11-26", "enterprise-backlog", "configurability-cr"]
LABELS_HOME = ["home-market", "personal-level", "byok", "vibe-dev", "full-review-2026-11-26"]
LABELS_QA = LABELS + ["qa-trust"]
LABELS_TM = LABELS + ["tm-depth"]
LABELS_INT = LABELS + ["integrate-ro"]
LABELS_PLUG = LABELS + ["plugin-pro"]

DOD = (
    "Definition of done: team DoD from FUNCTIONAL_SPEC section 7 "
    "(one behaviour change, pytest evidence on the linked test, story comment "
    "stating what the agent implemented, no secrets, WORK_LOG, PROJECT_MEMORY "
    "if behaviour changed)."
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
                "maxResults": 100,
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
                f"create {issue_type} {summary[:48]}: {r.status_code} {r.text[:220]}"
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

    def update_description(self, key: str, body: str) -> None:
        r = self._req(
            "PUT",
            f"/rest/api/3/issue/{key}",
            json={"fields": {"description": adf_from_lines(split_lines(body))}},
        )
        if r.status_code >= 300:
            self.failures.append(f"update desc {key}: {r.status_code} {r.text[:160]}")
        else:
            print(f"updated description {key}")


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
3. Where level gates apply: assert PERSONAL allows / OFFICIAL or SECRET refuses as Spec.

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
Senior TE, Test Manager, home/indie developer, Security — as relevant.

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

## Research / CR
Council Full Review 2026-11-26. Configurability CR: level-gate unsuitable features — do not delete.
docs/ops/ENTERPRISE_GAP_RESEARCH.md; docs/FUNCTIONAL_SPEC.md.
"""
    return {"summary": summary, "body": body}


def seed_pair(
    j: Jira,
    s: Dict[str, str],
    labels: List[str],
    epic: Optional[str],
    search_label: str,
    bucket: Dict[str, Any],
) -> None:
    story_key = j.create_issue(
        s["summary"], "Story", s["body"], labels, parent_epic=epic, search_label=search_label
    )
    test_key = j.create_issue(
        f"Test: {s['summary']}",
        "test",
        test_body(s["summary"]),
        labels + ["test"],
        search_label=search_label,
    )
    if story_key and test_key:
        j.link_relates(story_key, test_key)
    bucket[s["summary"][:52]] = {"story": story_key, "test": test_key}


QA_STORIES = [
    story(
        "QA: Heal policy regression harness (runner + agent)",
        "Pinned matrix that forbids assertion weaken, timeout inflate, skip/fixme, value change.",
        "As a Senior TE, I want heal regression pytest, so that Done heal policy cannot silently drift.",
        "FR-HEAL-1..3; FR-HEAL-5.",
        "1. Given forbidden heal fixtures, When harness runs, Then all allowed=false with correct reason.\n2. Locator-only proposals stay pending_review.\n3. CI fails on drift.",
        "Auto-apply heal.",
        "tests/test_heal_regression_matrix.py; plugins/heal_policy.py.",
    ),
    story(
        "QA: DAILY_LOOP journey pytest (API chain)",
        "Automate golden path after OPERATE fixtures: health→run→fail→trace→heal→report.",
        "As a Quality auditor, I want an API journey test, so that OPERATE is not human-only proof.",
        "DAILY_LOOP.md; FR-TEST/PLAN/REP.",
        "1. Given seeded demo plan, When test_daily_loop_journey runs, Then steps 1–6 complete with real trace.zip and exportable report.\n2. Exit 0; no CU required.",
        "Soft-pass orb home.",
        "tests/test_daily_loop_journey.py; after OPERATE-2.",
    ),
    story(
        "QA: Confirm-gated apply approved heal to plan case",
        "Approve alone does not mutate case; Apply confirm updates locator only.",
        "As a Senior TE, I want Apply after Approve, so that heal review is not theatre.",
        "FR-HEAL-2 deepen.",
        "1. Given pending locator heal, When Approve then Apply confirm, Then only selector updates; assertions unchanged.\n2. Cancel leaves plan JSON unchanged.\n3. Bulk Approve never auto-applies.",
        "Assertion edits; mutating imported PW files.",
        "plugins/heal_*; plans/store.py; Heal UI.",
    ),
    story(
        "QA: Post-heal re-run verification hook",
        "Link next run to heal_id; fail surfaces heal ineffective.",
        "As a STE, I want re-run proof after heal, so that green trust is earned.",
        "FR-HEAL-2/5.",
        "1. Given applied heal, When re-run completes, Then history links heal_id.\n2. Fail keeps red + heal-ineffective banner.\n3. No auto-heal on re-run.",
        "Silent assertion change.",
        "plans/run_case.py; Heal detail.",
    ),
    story(
        "QA: Failure evidence completeness gate",
        "Bundle declares screenshot_ok/trace_ok/console_captured; refuse full-evidence label when false.",
        "As a STE, I want honest evidence labels, so that triage is not lied to.",
        "FR-TEST-4.",
        "1. Given failed stepped run, When bundle written, Then completeness booleans present.\n2. Export refuses full-evidence if tracing on and trace_ok false.\n3. Captured console capped + redacted.",
        "Fake console from step-error echo alone as full.",
        "plans/evidence_bundle.py.",
    ),
    story(
        "QA: Pause-on-fail × trace integrity contract",
        "Continue/Stop after pause still yields valid trace.zip.",
        "As a STE, I want pause+trace to both work, so that OPERATE fail-usefully holds.",
        "FR-TEST-2; KAN-149; KAN-372.",
        "1. Given pause_on_fail + fail, When Continue then Stop (API), Then valid zip in bundle.\n2. Pytest without headed human.",
        "Embedded Trace SPA required.",
        "plans/pause_session.py; playwright_runner tracing.",
    ),
    story(
        "QA: Flake quarantine policy beyond chart",
        "Suggest-quarantine thresholds, parallel skip honesty, expiry on HUD — not chart pixels.",
        "As a STE, I want flake policy, so that quarantine is not guesswork.",
        "FR-PLAN-2; complements KAN-396.",
        "1. Given ≥N fails in window, When flake API, Then suggest_quarantine with reason template.\n2. Quarantined never runs in parallel batch.\n3. Expiry lists returned cases.",
        "Duplicate of flake chart story.",
        "plans/quarantine.py.",
    ),
    story(
        "QA: Imported Playwright project immutability guard",
        "Heal/apply paths never mutate external import root files.",
        "As a STE, I want import immutability tests, so that customer repos stay safe.",
        "FR-TEST-5; FR-HEAL-2.",
        "1. Given imported PW project, When heal approve/apply/bulk, Then mtime+hash unchanged.\n2. Pytest temp fixture project.",
        "Writing into customer repo.",
        "tests/test_import_immutability.py.",
    ),
    story(
        "QA: Verification debt ledger (marker vs human vs journey)",
        "Close-out must declare verification tier; marker-only cannot stand alone for clickability.",
        "As a Quality auditor, I want a debt ledger, so that Done does not mean clickable.",
        "NFR quality; Council CU policy.",
        "1. Given docs/ops/VERIFICATION_DEBT.md, When story closes, Then tier stated.\n2. Marker-only needs linked human script or journey id.\n3. Pytest docstring tier annotation for new data-* markers.",
        "Requiring CU for every API story.",
        "docs/ops/VERIFICATION_DEBT.md.",
    ),
    story(
        "QA: Gradio vs desktop Lab parity honesty matrix",
        "Publish desktop_full / gradio_stub matrix; banners for Lab stubs.",
        "As a buyer, I want Gradio honesty, so that I do not assume desktop parity.",
        "FR-UI-2.",
        "1. Given GRADIO_PARITY.md, When reviewed, Then each App area has a tier.\n2. Gradio Lab areas show stub banner.\n3. Drift pytest if desktop adds Lab control without matrix update.",
        "Implementing full Gradio Lab A–E.",
        "docs/ops/GRADIO_PARITY.md; tests/test_gradio_parity_honesty.py.",
    ),
]

TM_STORIES = [
    story(
        "STORE-1: Built-in light DB (SQLite) for plans + security indexes",
        "Settings-selectable embedded SQLite per security level for light-to-medium local use when JSON volume hurts. JSON remains default + export.",
        "As a Senior TE or home user, I want a built-in light database, so that plans and audit queries stay fast on one PC without standing up a server.",
        "FR-STORE-1 light tier; FR-PLAN-1; FR-SEC-1; FR-SEC-2 wipe.",
        "1. Given Settings storage backend, When JSON selected, Then behaviour matches today.\n2. When light DB selected for a level, Then plans/history/milestones/audit indexes use level-scoped SQLite under app data; levels never share a file.\n3. GDPR wipe and backup/restore include DB files; secrets not in plaintext columns.\n4. Migrate JSON → light DB without silent loss; export packs still JSON/markdown.\n5. No network DB server required. Pytest isolation + wipe.\n6. Default new install may stay JSON; guided opt-in for large local suites.",
        "Mandatory company DB; mixing levels; removing JSON export.",
        "plans/store.py adapter; settings backend picker; sqlite3 stdlib.",
    ),
    story(
        "STORE-2: Company / enterprise DB connector for large-org test data",
        "Connect to the organisation’s PostgreSQL / SQL Server / Oracle (etc.) for enterprise-scale plans/executions/indexes. Buyer’s DB — not vendor SaaS. Level-scoped creds + confirm gates.",
        "As a Test Manager in a large organisation, I want the app to use our company database, so that enterprise-scale test management does not outgrow a laptop JSON/SQLite store.",
        "FR-STORE-1 enterprise tier; FR-CONN-1; FR-SEC-1/5; FR-AGENT-4 confirm.",
        "1. Given any security level, When Settings enables company DB and I save connection (host/db/user) in that level’s credentials, Then status shows set/missing never the secret; health check pings without echoing password.\n2. Given first connect and any schema migrate / bulk write, When triggered, Then explicit confirm required (no YOLO agent SQL).\n3. Given SECRET (or strict desk), When company DB is still at soft default off, Then UI offers enable — not a hard product ban; once enabled, connect works like OFFICIAL.\n4. Given VPN/DB down, When opening Plans, Then honest not_connected — never fake green.\n5. Levels never share connection or schema data (isolation of stores remains).\n6. Migrate/import from JSON or light DB documented; export packs still work.\n7. Pytest with mocked driver; never require real company DB in CI.",
        "Mandatory vendor cloud test DB; silent agent writes; mixing levels in one schema; printing connection passwords; hard-banning company DB on SECRET.",
        "settings credentials; db adapter plugin; Drivers optional deps; Relates STORE-1. Configurability CR: Settings first, not level ban.",
    ),
    story(
        "TM: Run execution fingerprint on every case/suite run",
        "Immutable env/browser/viewport/optional AUT_BUILD/GIT_SHA on runs.",
        "As a STE, I want fingerprints, so that audit asks what ran are answerable.",
        "FR-PLAN-4 deepen.",
        "1. Given a run, When stored, Then fingerprint fields present.\n2. Shown on case detail, compare, export pack.\n3. Pytest persistence.",
        "Uploading fingerprints to cloud BI.",
        "plans/store.py; run_case.py.",
    ),
    story(
        "TM: First-class release milestones + Plans critical-path strip",
        "Milestone objects + smoke/critical % in Plans chrome; Reports filter.",
        "As a Test Manager, I want milestones, so that go/no-go matches TestRail practice.",
        "FR-PLAN-5; FR-PLAN-2 deepen; FR-REP-1.",
        "1. Given create milestone, When suite run attaches milestone_id, Then Reports filter works.\n2. Plans shows critical/smoke executed % with click-through.\n3. Empty quiet; pytest.",
        "Vanity KPI heroes; cloud milestones.",
        "plans/milestones.py; ui Plans/Reports.",
    ),
    story(
        "TM: Bulk case operations (retag / move / enable-disable)",
        "Multi-select scan table actions with confirm + undo snapshot.",
        "As a STE, I want bulk retag, so that sprint prep is not one-by-one.",
        "FR-PLAN-2 deepen.",
        "1. Given multi-select, When Retag/Move/Enable/Disable, Then confirm + undo snapshot.\n2. Quarantine rules respected.\n3. Pytest.",
        "AI auto-tag all cases.",
        "ui Plans scan; plans/store.py.",
    ),
    story(
        "TM: Test-data row binding on runs",
        "Optional data_row_id / fixture key on run start; on fail + defect packet.",
        "As a STE, I want the data row on the fail, so that flake vs data bugs are separable.",
        "FR-PLAN-4 deepen.",
        "1. Given data row selected, When run fails, Then data_row_id on run + defect packet.\n2. Pytest.",
        "Production PII as fixtures.",
        "plans/run_case.py; fixtures.",
    ),
    story(
        "TM: Blocker→failing-step evidence hop + named sign-off",
        "One click from release/blocker to step evidence; optional sign-off record.",
        "As a Release Manager, I want one-hop evidence and sign-off, so that go/no-go meetings work.",
        "FR-REP-1 deepen; FR-PLAN-4.",
        "1. Given release blocker chip, When clicked, Then case detail focuses failing step + screenshot + trace.\n2. Optional sign-off: approver, time, blocker snapshot, export fragment.\n3. No auto-approve when green.",
        "Silent Jira status flip.",
        "Reports release panel; Plans case detail.",
    ),
    story(
        "TM: Defect aging gadget + trend",
        "Age buckets for linked bugs; stale label if Jira down.",
        "As a Test Manager, I want defect aging, so that open blockers are visible.",
        "FR-JIRA-4; FR-REP-1.",
        "1. Given linked bugs, When gadget loads, Then 0–7 / 8–30 / 31d+ buckets.\n2. Jira down → stale timestamp, not fake green.\n3. Pytest with fixtures.",
        "Auto-close bugs.",
        "Reports; jira read.",
    ),
    story(
        "CONN: Named connection profiles (save/load/switch)",
        "First-class profiles bundling Jira/target/env/model/BYOK slot per level.",
        "As a home or lab user, I want named profiles, so that desk switching is one action.",
        "FR-CONN-1 deepen.",
        "1. Save Home lab profile; switch updates Settings without cross-level bleed.\n2. Health per profile; secrets never echoed.\n3. Pytest CRUD + isolation.",
        "Sharing credentials across levels.",
        "settings/store; Settings UI.",
    ),
]

HOME_STORIES = [
    story(
        "HOME-5: First-run wizard (level → Ollama → skip Jira → demo)",
        "Linear wizard flow beyond HOME-3 fixtures — purchase-path UX.",
        "As a home developer, I want a first-run wizard, so that I win in under 15 minutes without Jira.",
        "FR-CONN-1; HOME-MARKET.",
        "1. Wizard completes PERSONAL path without Jira.\n2. Plain language; no forced UK employer framing.\n3. Pytest/flow markers.",
        "Forcing cloud signup.",
        "ui onboarding; Relates HOME-3 / OPERATE fixtures.",
    ),
    story(
        "HOME-6: Hybrid Ollama-default + BYOK escalate router (PERSONAL)",
        "Default local; escalate hard tasks to BYOK; HUD shows runtime.",
        "As a vibe coder, I want hybrid routing, so that routine stays local and hard work uses Grok when I choose.",
        "FR-CONN-1 hybrid router.",
        "1. PERSONAL settings: default Ollama; escalate rules for named tools/tasks.\n2. First cloud route confirms; HUD shows runtime.\n3. OFFICIAL/SECRET hide cloud routes.\n4. Pytest gate matrix.",
        "Cloud keys on OFFICIAL/SECRET.",
        "agent LLM router; Settings; HUD.",
    ),
    story(
        "HOME-7: Post-demo empty-desk recovery",
        "After clearing demo: re-run demo / blank plan / import PW.",
        "As a home user, I want recovery after clearing demo, so that Plans/Documents are not dead walls.",
        "FR-LEARN-1; FR-UI-6.",
        "1. After clear demo, guided choices work.\n2. Checklist HUD reflects state.\n3. Pytest.",
        "Deleting user plans without confirm.",
        "checklist HUD; fixtures.",
    ),
    story(
        "HOME-8: Home HUD stack health chips",
        "Ollama / model / BYOK / AUT chips with deep-link fix.",
        "As a home user, I want one-glance health, so that I know what to fix.",
        "FR-CONN-1 health.",
        "1. Chips show up/down without secrets.\n2. Click deep-links to Settings fix.\n3. Pytest markers.",
        "Echoing API keys.",
        "ui home HUD.",
    ),
    story(
        "HOME-9: PERSONAL portable project export (secrets stripped)",
        "Take plans/runs/evidence to another PC; level-match import.",
        "As a home user, I want portable export, so that I can move machines without cloud.",
        "FR-SEC-1; F6 deepen.",
        "1. Export zip strips secrets.\n2. Import refuses cross-level mismatch without confirm.\n3. Pytest.",
        "Network share daemon.",
        "export_packs; backup.",
    ),
    story(
        "HOME-10: BYOK paste-first UX + outbound scrub + call ledger",
        "Provider cards, paste-key, scrub gate, redacted ledger — PERSONAL.",
        "As a Security-conscious home user, I want scrubbed outbound BYOK, so that keys do not leak in prompts.",
        "FR-SEC-7; FR-CONN-1; SEC threat model.",
        "1. Paste-key providers; masked status; health ping.\n2. Pre-send scrub blocks/masks keys/JWTs with confirm.\n3. Ledger export without full prompts.\n4. OFFICIAL/SECRET refuse.\n5. Pytest.",
        "Product OAuth proxy storing refresh tokens insecurely.",
        "agent router; settings/local_audit; Security Audit.",
    ),
]

INT_STORIES = [
    story(
        "CI: Pipelines read-only shell + on-demand artifact ingest",
        "H2 phase 1: Pipelines area not_synced + import JUnit/JSON/trace folders.",
        "As a Release Manager, I want CI visibility without re-running 200 tests locally.",
        "FR-CI-1 deepen; H2_PIPELINES_SECTION.md.",
        "1. App→Pipelines list/detail; status not_synced honest.\n2. On-demand folder ingest links to cases by id/tag.\n3. No OAuth in this story; level-scoped JSON.\n4. Pytest.",
        "Live CI write-back without confirm.",
        "ui Pipelines; plans/pipelines_design.py.",
    ),
    story(
        "XRAY: Read-only import + offline export manifest",
        "Import Xray-shaped JSON to cases; F6 adds xray_manifest; no writes.",
        "As a TE in an Xray shop, I want read-only interchange, so that offline packs work.",
        "FR-REP-3; Jira/Xray section.",
        "1. Import sample → source=xray_readonly cases.\n2. Export pack includes xray_manifest.json.\n3. No Jira/Xray writes.\n4. Pytest round-trip.",
        "Full bi-directional sync (later optional plugin).",
        "export_packs; import parser.",
    ),
    story(
        "SHARE: Shared-folder outbox + confirm import (H3 phase 1)",
        "Redacted pack drop + confirm merge; refuse cross-level; no daemon.",
        "As a small team on LAN share, I want folder handoff without a cloud tenant.",
        "FR-SEC-1; H3 design.",
        "1. Export to share_outbox/ with level label + E3 redaction.\n2. Import confirm; refuse mix without confirm.\n3. No background watcher.\n4. Pytest.",
        "Network multi-tenant service.",
        "docs/design/H3_SHARED_USE_WITHOUT_CLOUD.md.",
    ),
]

PLUG_STORIES = [
    story(
        "PLUG: axe-core a11y sidecar (opt-in, evidence on case_run)",
        "Replace shallow HTML heuristics with axe-core; attach violations to case_run.",
        "As a STE, I want real a11y scans, so that Lab a11y is not theatre.",
        "FR-PLUG-4; FR-PLUG-1.",
        "1. Opt-in case runs axe; violations on evidence.\n2. Sequential recommended; functional result unchanged.\n3. Pytest fixture with known violation.",
        "Claiming WCAG certification.",
        "plugins/a11y_*; @axe-core.",
    ),
    story(
        "PLUG: Lighthouse perf sidecar (opt-in, level/settings gated)",
        "Local LHR JSON + budgets; refuse when parallel hot; configurable not deleted.",
        "As a STE, I want Lighthouse when I opt in, so that perf budgets are real.",
        "FR-PLUG-1/4/5.",
        "1. Opt-in stores LHR on case_run.\n2. Honesty mutex with parallel/Manual/Ollama.\n3. Pytest stubbed LHR.",
        "Cloud APM default.",
        "plugins/perf_*.",
    ),
    story(
        "LAB: Sandbox honesty + ephemeral TTL + optional Docker plugin",
        "Local profile copy + TTL; Docker optional plugin when present — level-gated.",
        "As a STE, I want TTL prepare and optional Docker, so that isolation matches industry without fake farms.",
        "FR-PLUG-1 configurability CR.",
        "1. UI copy: local browser profile on this PC.\n2. Optional TTL → not_ready.\n3. Docker plugin toggled; unavailable → honest disable; SECRET may refuse remote.\n4. Pytest TTL.",
        "Defaulting cloud device farm as product sandbox.",
        "plugins/multi_sandbox.py.",
    ),
    story(
        "PW: UI Mode / Inspector launch + pause-before-step + rerun from N",
        "Detached UI Mode when idle; pause-before-step; headed rerun from step N — configurable.",
        "As a STE, I want PW debug parity, so that in-app runner matches Playwright practice.",
        "FR-TEST-2; FR-PLAN-2 deepen.",
        "1. Idle-only UI Mode/Inspector launch; mutex with active suite.\n2. Pause before step N; Continue/Stop.\n3. Rerun from N records parent run id.\n4. Pytest command builders.",
        "Requiring embedded Trace SPA (optional advanced setting later).",
        "desktop_app bridge; playwright_runner.",
    ),
    story(
        "AGENT: Chat recipes dry-run + mid-run steer with approve-next-tool",
        "Recipes preview then confirm; pause/skip/insert; approve-next-tool for sensitive tools — audited; cloud on PERSONAL only.",
        "As a STE, I want recipes and steer, so that the agent is controllable like KaneAI HITL without SaaS lock-in.",
        "FR-AGENT-4/7 deepen.",
        "1. Recipe dry-run shows cases/env/parallel → confirm.\n2. Mid-run skip/stop-after/insert on pause or between steps; audit log.\n3. Approve-next-tool for money/auth/destructive.\n4. Cloud steer refused on OFFICIAL/SECRET.\n5. Pytest state machine.",
        "YOLO without confirm; assertion heal via steer.",
        "agent/agent.py; pause_session; Settings budgets.",
    ),
    story(
        "MAN: Session→case draft + env snapshot + stakeholder PDF",
        "Review-gated case draft; start snapshot; PDF export — video remains opt-in after DPIA.",
        "As a Manual tester, I want Explorer-class session outcomes without silent suite writes.",
        "FR-MAN-1 deepen.",
        "1. End session → proposed steps → Save confirm.\n2. Start stamps OS/monitors/AUT/level.\n3. PDF notes+stills+debrief with redaction.\n4. Pytest.",
        "Silent video; FR-MAN-2 circles.",
        "plans/manual_session.py; Manual UI.",
    ),
    story(
        "SEC: Compliance evidence export pack + level tool manifest",
        "Zip evidence mapping (not certified); Security UI tool allow/block per level.",
        "As Security/procurement, I want evidence files and a tool manifest, so that buyers see controls without fake badges.",
        "FR-SEC-6 deepen.",
        "1. Export pack: matrix excerpt, audit sample, GDPR inventory; UI says not certified.\n2. Tool manifest matches prompt_guard; pytest drift.\n3. Packs exclude foreign-level secrets.",
        "ISO/CE/SOC certified badge.",
        "docs/design/COMPLIANCE_MATRIX.md; Security UI.",
    ),
    story(
        "RUN: Configurable parallel workers with honesty panel",
        "Raise/lower parallel via settings; warn on contention; SECRET may cap — capability not deleted.",
        "As a power user on a strong PC, I want more than 2 workers when safe, with honesty on home PCs.",
        "FR-PLUG-5.",
        "1. Settings parallel max configurable; soft default conservative.\n2. Suite run shows slots + shared-profile warnings.\n3. SECRET policy may refuse above N.\n4. Pytest.",
        "Silent raise without warning.",
        "plans/parallel.py; Settings.",
    ),
]

OPERATE3_BODY = f"""
## Intro
Polish the golden-path surfaces plus Studio fold-in S1–S3 (Designer 2026-11-26): Plans Run disclosure, Manual idle, evidence affordance, case-detail triage strip, run→report link, App-menu Heal pending badge. Not a full TRACK6 home redesign. Theme/orb/home/App nav locked.

## Who this is for
Designer, Senior TE.

## User story
As a Senior Test Engineer walking the daily loop, I want Plans Run, Manual idle, evidence, triage, report handoff, and Heal awareness to be scannable, so that the operate path does not hide next actions.

## Requirements
FR-UI-9 progressive disclosure for Run setup; FR-MAN-1 idle clarity; evidence-first consistency with OPERATE-1; Studio notes S1–S3.

## Behaviour
- Plans → Run: collapse secondary forms behind disclosure sections (env/sandbox/schedule).
- Manual idle: separate library scan from Start charter.
- Evidence slot matches OPERATE-1 affordance.
- Case detail: horizontal Triage strip (failure class / heal pending / defect packet) under evidence header on fail.
- After export: Open report for this run link (`data-operate-run-report`).
- App menu ▦: Heal pending badge/count when pending heals exist.
- Theme/orb/home/App nav locked.

## Acceptance criteria
1. Given Plans Run, When opened, Then primary run actions visible without scrolling past all advanced forms.
2. Given Manual idle, When opened, Then library and Start are visually separated.
3. Given failed case detail, When opened, Then triage strip is visible and clickable.
4. Given a report for the run, When link clicked, Then Reports opens that entry.
5. Given pending heals, When App menu opens, Then Heal item shows pending affordance.
6. Markers + pytest; CU skipped if unsafe.

## {DOD}

## Out of scope
Screen drawer HUD wall; Gradio parity; FR-MAN-2; floating OS snip (GAP-CR); theme/orb/home redo.

## Technical notes
ui/desktop Plans/Manual/Heal menu only; Studio mockups optional.
"""

BUG_BODY = f"""
## Symptom
Heal audit log and Playwright trace.zip storage appear to use global paths under %LOCALAPPDATA%/ai_testing_app/ (heal_audit.jsonl, traces/) rather than level-scoped stores. Plans/sessions are level-scoped; heal/trace evidence may leak across PERSONAL/OFFICIAL/SECRET switches.

## Expected
Heal proposals, audit lines, and trace.zip paths are isolated per active security level. Switching levels must not show another level's heal/trace. GDPR wipe respects per-level heal/trace. FR-HEAL-5 deepen / FR-SEC-1.

## Actual
Council Quality Auditor report (2026-11-26): heal_log_path and traces look global; cross-level visibility risk.

## Environment
Windows desktop app; security levels PERSONAL/OFFICIAL/SECRET; local settings store. Never paste secrets.

## Replication steps
1. Set level SECRET; produce a failed run with heal proposal and/or trace.zip.
2. Switch to OFFICIAL (confirm).
3. Open Heal review and evidence/trace affordances.
4. Observe whether SECRET heal/trace entries remain visible or share paths.
5. Note paths under %LOCALAPPDATA%/ai_testing_app/ (no secrets in ticket).

## {DOD} when fixed
Fix comment with root cause, files, pytest proving level isolation; transition Bug Done.
"""


def main() -> int:
    keys_path = Path(__file__).resolve().parents[1] / "docs" / "ops" / "OPERATE_KEYS.json"
    gap_keys = Path(__file__).resolve().parents[1] / "docs" / "ops" / "GAP_RESEARCH_KEYS.json"
    prior = json.loads(keys_path.read_text(encoding="utf-8")) if keys_path.exists() else {}
    gap_prior = json.loads(gap_keys.read_text(encoding="utf-8")) if gap_keys.exists() else {}
    home_epic = gap_prior.get("home_epic") or prior.get("gap_research", {}).get("home_epic") or "KAN-406"
    operate_epic = prior.get("epic") or "KAN-374"
    operate3 = (prior.get("stories") or {}).get("OPERATE-3", {}).get("story") or "KAN-379"
    operate3_test = (prior.get("stories") or {}).get("OPERATE-3", {}).get("test") or "KAN-380"

    base, auth = load_creds()
    j = Jira(base, auth)
    out: Dict[str, Any] = {
        "home_epic": home_epic,
        "operate3": operate3,
        "epics": {},
        "qa_stories": {},
        "tm_stories": {},
        "home_stories": {},
        "int_stories": {},
        "plug_stories": {},
        "bug_heal_trace_level": {},
    }

    try:
        # OPERATE-3 fold-in
        j.update_description(operate3, OPERATE3_BODY)
        j.comment(
            operate3,
            [
                "Designer CR 2026-11-26: fold Studio S1–S3 into OPERATE-3 —",
                "triage strip, run→report link, Heal pending badge — in addition to",
                "Plans Run / Manual idle / evidence polish. Theme/orb/home locked.",
                "Active Build remains KAN-375 until OPERATE-1 Done.",
            ],
        )
        j.comment(
            operate3_test,
            [
                "AC expanded: triage strip, run→report link, Heal badge — verify with OPERATE-3 story.",
            ],
        )

        qa_epic = j.create_issue(
            "QA-TRUST — Heal/evidence/journey quality (FULL-REVIEW)",
            "Epic",
            f"""
## Intro
Quality trust after OPERATE: heal apply loop, level isolation (Bug), journey pytest, evidence gates, flake policy, Gradio honesty, verification debt.

## Scope
In: QA-* stories listed in seed. Out: stealing Active KAN-375.

## Configurability
Capabilities stay level-gated; do not delete for SECRET. {DOD}
""",
            LABELS_QA,
            search_label="qa-trust",
        )
        out["epics"]["QA-TRUST"] = qa_epic

        tm_epic = j.create_issue(
            "TM-DEPTH — Milestones, fingerprints, bulk ops, release hop (FULL-REVIEW)",
            "Epic",
            f"""
## Intro
Test management depth: first-class milestones, fingerprints, bulk ops, data rows, evidence hop + sign-off, defect aging, named connection profiles.

## Requirements
FR-PLAN-2/4/5, FR-CONN-1, FR-REP-1 deepen. {DOD}
""",
            LABELS_TM,
            search_label="tm-depth",
        )
        out["epics"]["TM-DEPTH"] = tm_epic

        int_epic = j.create_issue(
            "INTEGRATE-RO — Pipelines shell, Xray RO, shared-folder (FULL-REVIEW)",
            "Epic",
            f"""
## Intro
Read-only integrations first: H2 Pipelines shell + artifact ingest, Xray RO pack, H3 folder outbox. OAuth/bi-sync later as optional plugins. {DOD}
""",
            LABELS_INT,
            search_label="integrate-ro",
        )
        out["epics"]["INTEGRATE-RO"] = int_epic

        plug_epic = j.create_issue(
            "PLUGIN-PRO — axe/Lighthouse/sandbox/PW debug/agent steer/Manual deepen (FULL-REVIEW)",
            "Epic",
            f"""
## Intro
Deepen plugins and runtime: axe, Lighthouse, sandbox TTL+optional Docker, PW UI Mode/from-step, agent recipes+steer+approve-next-tool, Manual session→case/PDF, compliance evidence pack, configurable parallel.

## Configurability CR
Level-gate unsuitable features; do not hard-reject legitimate test-all capabilities. {DOD}
""",
            LABELS_PLUG,
            search_label="plugin-pro",
        )
        out["epics"]["PLUGIN-PRO"] = plug_epic

        for s in QA_STORIES:
            seed_pair(j, s, LABELS_QA, qa_epic, "qa-trust", out["qa_stories"])
        for s in TM_STORIES:
            seed_pair(j, s, LABELS_TM, tm_epic, "tm-depth", out["tm_stories"])
        for s in HOME_STORIES:
            seed_pair(j, s, LABELS_HOME, home_epic, "home-market", out["home_stories"])
        for s in INT_STORIES:
            seed_pair(j, s, LABELS_INT, int_epic, "integrate-ro", out["int_stories"])
        for s in PLUG_STORIES:
            seed_pair(j, s, LABELS_PLUG, plug_epic, "plugin-pro", out["plug_stories"])

        # Bug: heal/trace level isolation
        bug_key = j.create_issue(
            "Bug: Heal audit + Playwright traces not level-isolated (SEC leakage)",
            "Bug",
            BUG_BODY,
            LABELS_QA + ["security", "heal"],
            search_label="qa-trust",
        )
        bug_test = j.create_issue(
            "Test: Heal audit + Playwright traces level isolation",
            "test",
            test_body("Heal/trace level isolation"),
            LABELS_QA + ["test"],
            search_label="qa-trust",
        )
        if bug_key and bug_test:
            j.link_relates(bug_key, bug_test)
        # Relates to OPERATE-1 / heal provenance when present
        for rel in ("KAN-375", "KAN-398", qa_epic):
            if bug_key and rel:
                j.link_relates(bug_key, rel)
        out["bug_heal_trace_level"] = {"bug": bug_key, "test": bug_test}

        if home_epic:
            j.comment(
                home_epic,
                [
                    "FULL-REVIEW seed: HOME-5..10 under this epic (wizard, hybrid router,",
                    "post-demo recovery, HUD health, portable export, BYOK scrub/ledger).",
                    "Configurability CR: PERSONAL-gated cloud features stay available — not deleted.",
                    "Active Build remains KAN-375.",
                ],
            )
        if qa_epic:
            j.comment(
                qa_epic,
                [
                    "Includes Bug for heal/trace level isolation (SEC leakage).",
                    "Sequence after KAN-375 preferred for journey test.",
                ],
            )

        out_path = Path(__file__).resolve().parents[1] / "docs" / "ops" / "GAP_FULL_REVIEW_KEYS.json"
        out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")

        prior["full_review"] = out
        keys_path.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
        print(f"updated {keys_path}")

        if gap_prior:
            gap_prior["full_review"] = out
            gap_keys.write_text(json.dumps(gap_prior, indent=2) + "\n", encoding="utf-8")
            print(f"updated {gap_keys}")

        if j.failures:
            for f in j.failures:
                print(f"FAIL: {f}", file=sys.stderr)
            return 1
        return 0
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
