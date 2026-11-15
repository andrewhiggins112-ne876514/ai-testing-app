"""
Enrich KAN backlog descriptions from docs/FUNCTIONAL_SPEC.md (no secrets in repo).
Reads Jira credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logs the token.

Usage:
  python scripts/jira_kan_enrich.py           # update issues
  python scripts/jira_kan_enrich.py --dry-run # print keys only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

REPO = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO / "docs" / "FUNCTIONAL_SPEC.md"
SCREENSHOTS = REPO / "docs" / "mockups" / "screenshots"
PROJECT = "KAN"
BACKOFF = 0.4
SKIP_KEYS = frozenset({f"KAN-{i}" for i in range(1, 8)} | {"KAN-17", "KAN-18", "KAN-19"})

EPIC_FR_PREFIX: Dict[str, str] = {
    "KAN-20": "FR-AGENT",
    "KAN-21": "FR-LEARN",
    "KAN-22": "FR-TEST",
    "KAN-23": "FR-HEAL",
    "KAN-24": "FR-JIRA",
    "KAN-25": "FR-REP",
    "KAN-26": "FR-SEC",
    "KAN-27": "FR-UI",
    "KAN-28": "FR-PLUG",
    "KAN-29": "FR-SET",
}

EPIC_OVERVIEW: Dict[str, str] = {
    "KAN-20": (
        "Natural-language agent loop with Ollama tool calling, session memory, clarification rules, "
        "and hard confirmation gates on side effects."
    ),
    "KAN-21": (
        "Ingest specs, URLs, desktop paths, and Jira pointers; propose settings diffs — never store without confirm."
    ),
    "KAN-22": (
        "Generate and run browser/desktop tests with Playwright-first execution and rich failure evidence."
    ),
    "KAN-23": (
        "Self-healing limited to locator strategy changes; assertions and expected values stay human-approved."
    ),
    "KAN-24": (
        "Bi-directional Jira/Xray: read backlog, create tests/bugs, transition with two-step confirm and rate-limit backoff."
    ),
    "KAN-25": (
        "Run metrics and exportable reports; user picks which sections appear in each export."
    ),
    "KAN-26": (
        "UK OFFICIAL/SECRET isolation, GDPR defaults, prompt-injection mitigations, secrets scoping."
    ),
    "KAN-27": (
        "Conversational-first UI: native desktop shell, WebGL hero orbs, drawers, movable widgets, layout persistence."
    ),
    "KAN-28": (
        "Plugin registry so desktop testing, reporting, sandboxes, and future capabilities ship without core rewrites."
    ),
    "KAN-29": (
        "Local settings store under %LOCALAPPDATA%\\ai_testing_app\\ for credentials, orb presets, and layout."
    ),
}

ATTACHMENTS: Dict[str, List[str]] = {
    "KAN-27": [
        "style_theme_switch.png",
        "mystic_final_calm.png",
        "aether_mid_v4.png",
        "neural_mid_v16.png",
        "apex_v4.png",
    ],
    "KAN-10": ["mystic.png", "widget_settings_desk7.png"],
    "KAN-41": [
        "mystic_desktop_drawers.png",
        "mystic_final_thinking.png",
        "style_theme_switch.png",
        "aether_mid_v4.png",
        "neural_mid_v16.png",
        "apex_v4.png",
    ],
    "KAN-42": [
        "mystic_final_calm.png",
        "mystic_glow_mid.png",
        "aether_mid_v4.png",
        "neural_mid_v16.png",
        "apex_v4.png",
        "style_theme_switch.png",
    ],
    "KAN-53": ["widget_settings_desk7.png", "movable_controls_desk5.png", "widget_transparency_desk6.png"],
    "KAN-54": ["widget_settings_desk7.png", "movable_controls_desk5.png"],
}


TEAM_DOD: List[str] = [
    "One logical behaviour change is delivered.",
    "A test or recorded manual check exists.",
    "Human has reviewed the meaningful diffs.",
    "PROJECT_MEMORY.md Current State is updated if behaviour changed.",
    "No secrets are in git.",
    "Side-effecting actions still require confirmation.",
    "Self-healing (if touched) still obeys the “how not what” rule and requires approval.",
    "Errors are logged and surfaced rather than swallowed.",
    "docs/ops/WORK_LOG.md has an entry for this slice.",
    "A Jira comment on this ticket summarises what shipped and how to verify.",
]

AUDIENCE_STORY: List[str] = [
    "Management — product outcome, scope boundary, and how we will know it worked.",
    "Developers — requirements, behaviour, and technical notes with file paths.",
    "Testers — acceptance criteria and linked test Task procedure.",
    "Cursor agents — self-contained FR text; do not open other docs to start coding.",
    "AI Testing App — FR-IDs and AC are machine-usable for later spec/Jira ingestion.",
]

AUDIENCE_EPIC: List[str] = [
    "Management — area outcome and success criteria across multiple stories.",
    "Developers — full FR list for this area (text inlined below).",
    "Testers — child stories each have Relates-linked test Tasks.",
    "Cursor agents — pick a child Story from this epic; do not implement the whole epic at once.",
    "AI Testing App — epic groups FR-* prefixes for coverage reporting.",
]

AUDIENCE_TEST: List[str] = [
    "Testers — follow Test procedure; record pass/fail and evidence.",
    "Developers — use Expected lines as a checklist before marking the parent Story Done.",
    "Management — this Task does not deliver features; it proves the parent Story.",
    "Cursor / AI Testing App — steps must stay executable without “see story” placeholders.",
]


@dataclass
class TicketBody:
    summary_context: str
    requirements: List[str]
    behaviour: str
    acceptance: List[str]
    out_of_scope: List[str]
    technical_notes: List[str]
    mockups: List[str]
    test_steps: Optional[List[Tuple[str, str]]] = None
    user_story: str = ""
    dependencies: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    kind: str = "story"  # epic | story | test


def _load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    url = (settings.get("jira_url") or "").rstrip("/")
    email = settings.get("jira_email") or ""
    token = settings.get("jira_api_token") or ""
    if not url or not token:
        raise SystemExit("Jira not configured in local settings")
    return url, (email, token)


def parse_frs(spec_text: str) -> Dict[str, str]:
    frs: Dict[str, str] = {}
    current: Optional[str] = None
    buf: List[str] = []
    for line in spec_text.splitlines():
        m = re.match(r"^- \*\*(FR-[A-Z]+-\d+):\*\*\s*(.*)", line)
        if m:
            if current:
                frs[current] = " ".join(buf).strip()
            current, first = m.group(1), m.group(2)
            buf = [first] if first else []
            continue
        if current and line.strip().startswith("- ") and not line.strip().startswith("- **FR-"):
            buf.append(line.strip()[2:])
        elif current and line.strip() and not line.startswith("#"):
            if line.strip().startswith("- "):
                buf.append(line.strip()[2:])
    if current:
        frs[current] = " ".join(buf).strip()
    return frs


def _text(s: str) -> Dict[str, Any]:
    return {"type": "text", "text": s}


def _strong(s: str) -> Dict[str, Any]:
    return {"type": "text", "text": s, "marks": [{"type": "strong"}]}


def _heading(level: int, title: str) -> Dict[str, Any]:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(title)]}


def _para(lines: str) -> Dict[str, Any]:
    inner = [_text(lines)] if lines else [_text("\u00a0")]
    return {"type": "paragraph", "content": inner}


def _para_parts(*parts: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "paragraph", "content": list(parts)}


def _wrap_words(text: str, width: int = 96) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current: List[str] = []
    length = 0
    for word in words:
        add = len(word) + (1 if current else 0)
        if current and length + add > width:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += add
    if current:
        lines.append(" ".join(current))
    return lines


def _requirement_list_item(req: str) -> Dict[str, Any]:
    stripped = req.strip()
    m = re.match(r"^(FR-[A-Z]+-\d+|NFR\s*—\s*[^:]+)\s*:\s*(.*)", stripped, re.DOTALL)
    if m:
        rid, body = m.group(1), m.group(2).strip()
        lines = _wrap_words(body, 96)
        paras: List[Dict[str, Any]] = [
            _para_parts(_strong(rid), _text(": "), _text(lines[0] if lines else ""))
        ]
        for extra in lines[1:]:
            paras.append(_para(extra))
        return {"type": "listItem", "content": paras}
    return {
        "type": "listItem",
        "content": [_para(line) for line in _wrap_words(stripped, 96)],
    }


def _bullet(items: Sequence[str]) -> Dict[str, Any]:
    cleaned = [item for item in items if item.strip()]
    if not cleaned:
        cleaned = ["(none for this ticket)"]
    return {
        "type": "bulletList",
        "content": [_requirement_list_item(item) for item in cleaned],
    }


def _plain_bullet(items: Sequence[str]) -> Dict[str, Any]:
    """Notes / mockups — one short line per bullet, no FR-ID formatting."""
    cleaned = [item for item in items if item.strip()]
    if not cleaned:
        cleaned = ["(none for this ticket)"]
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [_para(line) for line in _wrap_words(item, 96)],
            }
            for item in cleaned
        ],
    }


def _acceptance_block(items: Sequence[str]) -> List[Dict[str, Any]]:
    cleaned = [item for item in items if item.strip()]
    if not cleaned:
        cleaned = ["(none for this ticket)"]
    list_items: List[Dict[str, Any]] = []
    for item in cleaned:
        paras: List[Dict[str, Any]] = []
        for i, line in enumerate(_wrap_words(item, 96)):
            paras.append(_para(line))
        paras.append(_para(""))
        list_items.append({"type": "listItem", "content": paras})
    return [
        {
            "type": "orderedList",
            "attrs": {"order": 1},
            "content": list_items,
        }
    ]


def _test_procedure(steps: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for n, (action, expected) in enumerate(steps, 1):
        action_paras = [_para_parts(_strong(f"Step {n}. "), _text(_wrap_words(action, 92)[0]))]
        for line in _wrap_words(action, 92)[1:]:
            action_paras.append(_para(line))
        exp_paras = [_para_parts(_strong("Expected: "), _text(_wrap_words(expected, 92)[0]))]
        for line in _wrap_words(expected, 92)[1:]:
            exp_paras.append(_para(line))
        items.append({"type": "listItem", "content": action_paras + exp_paras + [_para("")]})
    return {"type": "orderedList", "attrs": {"order": 1}, "content": items}


def _behaviour_blocks(text: str) -> List[Dict[str, Any]]:
    chunks = [c.strip() for c in re.split(r"\s{2,}|\n\n+", text.strip()) if c.strip()]
    if len(chunks) <= 1 and len(text) > 320:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks, buf, n = [], [], 0
        for s in sentences:
            buf.append(s)
            n += len(s)
            if n > 200:
                chunks.append(" ".join(buf))
                buf, n = [], 0
        if buf:
            chunks.append(" ".join(buf))
    if not chunks:
        chunks = [text.strip() or "(none)"]
    return [_para(c) for c in chunks]


def validate_adf(adf: Dict[str, Any]) -> List[str]:
    problems: List[str] = []

    def walk(node: Dict[str, Any]) -> None:
        if node.get("type") == "bulletList" and not (node.get("content") or []):
            problems.append("empty bulletList")
        if node.get("type") == "orderedList" and not (node.get("content") or []):
            problems.append("empty orderedList")
        for child in node.get("content") or []:
            if isinstance(child, dict):
                walk(child)

    walk(adf)
    return problems


def body_to_adf(body: TicketBody) -> Dict[str, Any]:
    """Multi-audience layout — see docs/ops/JIRA_TICKET_TEMPLATE.md."""
    if body.kind == "epic":
        audience = AUDIENCE_EPIC
    elif body.kind == "test":
        audience = AUDIENCE_TEST
    else:
        audience = AUDIENCE_STORY

    content: List[Dict[str, Any]] = [
        *_behaviour_blocks(body.summary_context)[:3],
        _heading(2, "Who this is for"),
        _plain_bullet(audience),
    ]

    if body.user_story.strip():
        content.append(_heading(2, "User story"))
        content.extend(_behaviour_blocks(body.user_story))

    if body.kind == "epic" and body.success_criteria:
        content.append(_heading(2, "Success criteria (epic)"))
        content.extend(_acceptance_block(body.success_criteria))

    content.extend(
        [
            _heading(2, "Requirements"),
            _bullet(body.requirements),
            _heading(2, "Behaviour"),
            *_behaviour_blocks(body.behaviour),
        ]
    )

    if body.test_steps:
        content.append(_heading(2, "Test procedure"))
        content.append(_test_procedure(body.test_steps))
        if body.acceptance:
            content.append(_heading(2, "Acceptance criteria"))
            content.extend(_acceptance_block(body.acceptance))
    else:
        content.append(_heading(2, "Acceptance criteria"))
        content.extend(_acceptance_block(body.acceptance))

    if body.kind != "test":
        content.append(_heading(2, "Definition of done (team)"))
        content.extend(_acceptance_block(TEAM_DOD))

    content.extend(
        [
            _heading(2, "Out of scope"),
            _plain_bullet(body.out_of_scope),
            _heading(2, "Dependencies"),
            _plain_bullet(body.dependencies or []),
            _heading(2, "Technical notes"),
            _plain_bullet(body.technical_notes),
        ]
    )

    if any(m.strip() for m in body.mockups):
        content.append(_heading(2, "Mockups"))
        content.append(_plain_bullet(body.mockups))

    content.append(_heading(2, "Traceability"))
    content.append(
        _plain_bullet(
            [
                "Canonical product spec: docs/FUNCTIONAL_SPEC.md (FR text is copied into Requirements above — do not rely on “see spec”).",
                "Ticket layout: docs/ops/JIRA_TICKET_TEMPLATE.md",
                "Active handoff: docs/ops/WORK_LOG.md",
            ]
        )
    )
    return {"type": "doc", "version": 1, "content": content}


def epic_body(key: str, frs: Dict[str, str]) -> TicketBody:
    prefix = EPIC_FR_PREFIX[key]
    req = [
        f"{fr_id}: {text}"
        for fr_id, text in sorted(frs.items())
        if fr_id.startswith(prefix)
    ]
    nfr = [
        "NFR — Local-first: Windows laptop, Ollama default, no mandatory cloud for core agent loop.",
        "NFR — Security: explicit confirm on side effects; secrets only in local settings store.",
        "NFR — Reliability: surface errors; capture evidence on test failure; classify before heal.",
        "NFR — Performance: prefer 7B–8B models; one headed browser; Jira 429 backoff.",
        "NFR — Maintainability: one logical slice per change; update PROJECT_MEMORY when behaviour changes.",
    ]
    return TicketBody(
        summary_context=EPIC_OVERVIEW[key],
        requirements=req + nfr,
        behaviour=(
            f"This epic groups all backlog stories and test tasks that implement {prefix}-* "
            f"requirements. Child stories should be implementable without external wiki links; "
            f"each story carries its own acceptance criteria and technical notes."
        ),
        acceptance=[
            "Every child Story under this epic has a self-contained description with FR IDs inline.",
            "Test Tasks labelled `test` list concrete verification steps and expected evidence.",
            "Done stories reflect shipped code in the repository (main branch).",
        ],
        out_of_scope=[
            "Voice input (later roadmap).",
            "Cloud-only SaaS deployment assumptions.",
            "Automatic Jira writes without user confirmation.",
        ],
        technical_notes=[
            f"Canonical spec: repo `docs/FUNCTIONAL_SPEC.md` section 3 ({prefix}).",
            "Ticket template: docs/ops/JIRA_TICKET_TEMPLATE.md",
            "Handoff: docs/ops/WORK_LOG.md",
            "Backlog rebuild helper: `scripts/jira_kan_rebuild.py`.",
            "This enrichment run: `scripts/jira_kan_enrich.py`.",
        ],
        mockups=[
            "UI/orb mockups: `docs/mockups/orb_styles.md` and `docs/mockups/screenshots/` when relevant to child stories.",
        ],
        kind="epic",
        success_criteria=[
            f"Product capability for {prefix} is usable end-to-end on a Windows laptop without mandatory cloud APIs.",
            "Open gaps are tracked as child Stories with AC — not as silent omissions.",
            "Management can report coverage by counting Done child stories under this epic.",
        ],
        dependencies=["Local Ollama for agent stories.", "Jira Cloud project KAN for integration stories."],
    )


def story_bodies(frs: Dict[str, str]) -> Dict[str, TicketBody]:
    """Per-issue enriched bodies keyed by Jira issue key."""

    def fr(*ids: str) -> List[str]:
        return [f"{i}: {frs[i]}" for i in ids if i in frs]

    bodies: Dict[str, TicketBody] = {}

    bodies["KAN-8"] = TicketBody(
        summary_context="Shipped Ollama tool-calling agent with clarification, sessions, and confirmation on side effects.",
        requirements=fr("FR-AGENT-1", "FR-AGENT-2", "FR-AGENT-3", "FR-AGENT-4", "FR-AGENT-5", "FR-AGENT-6"),
        behaviour=(
            "User messages POST to `/chat` (FastAPI). `agent/agent.py` runs the Ollama loop, registers plugins as tools, "
            "keeps session context, asks clarifying questions when intent is ambiguous, and blocks Jira writes / "
            "credential / destructive actions until the user confirms. Tool results must be validated before success "
            "is reported to the user. Errors return structured messages — never silent failure."
        ),
        acceptance=[
            "Given an ambiguous test request, When the user sends chat, Then the agent asks a clarifying question before calling Playwright or Jira write tools.",
            "Given a pending Jira create, When the user has not said yes/confirm, Then no POST is sent to Jira.",
            "Given a resumed session id, When the user continues chatting, Then prior turn context is available to the agent.",
            "Given a tool exception, When the agent responds, Then the reply includes a clear error (no false success).",
        ],
        out_of_scope=["Voice input.", "Cloud LLM routing.", "Autonomous Jira writes."],
        technical_notes=[
            "`agent/agent.py` — main loop and tool registration.",
            "`main.py` — `POST /chat`, session handling.",
            "Tests: `tests/` covering sessions and agent behaviour where present.",
        ],
        mockups=["Conversational UI: desktop shell chat bar (`ui/desktop/`) or Gradio (`ui/gradio_app.py`)."],
    )

    bodies["KAN-9"] = TicketBody(
        summary_context="Playwright runner executes generated steps, captures evidence, and click self-heal stays locator-only.",
        requirements=fr("FR-TEST-2", "FR-TEST-4", "FR-TEST-6", "FR-HEAL-1"),
        behaviour=(
            "`plugins/playwright_runner.py` accepts step lists (navigate, click, fill, assert). Runs headed Playwright by default. "
            "On click failure, attempts alternate locators (role/text) without changing assertions. "
            "Screenshots and evidence paths returned on failure and when configured for success. "
            "Generated steps must include real assertions — not visibility-only checks near the target."
        ),
        acceptance=[
            "Given a valid URL and steps, When run is invoked, Then Playwright completes and returns status + evidence path.",
            "Given a broken CSS selector for click, When heal is enabled, Then an alternate locator is attempted and diff is describable.",
            "Given a step with assertion, When heal runs, Then expected values are unchanged (FR-HEAL-1).",
        ],
        out_of_scope=["Desktop .exe runner (separate plugin FR-TEST-3).", "Importing external Playwright suites (FR-TEST-5) — partial/future."],
        technical_notes=[
            "`plugins/playwright_runner.py`.",
            "Evidence under configured reports/temp paths.",
            "Tests: `tests/` playwright / heal markers.",
        ],
        mockups=[],
    )

    bodies["KAN-10"] = TicketBody(
        summary_context="Gradio dashboard: chat, orb, named presets (UI-5 done); resizable panels remain open under KAN-53.",
        requirements=fr("FR-UI-1", "FR-UI-3"),
        behaviour=(
            "`run_ui.py` launches Gradio (`ui/gradio_app.py`). Chat is primary; orb settings live behind top-right gear (UI-6a). "
            "Named orb presets persist via local settings (`orb_presets`, `orb_active_preset` in `settings/store.py`). "
            "Classic canvas orb styles plus WebGL styles when selected. Resizable/movable parity with desktop is tracked separately."
        ),
        acceptance=[
            "Given `python run_ui.py`, When the UI loads, Then chat and orb render without console errors.",
            "Given a saved preset name, When user loads preset, Then orb parameters restore from settings store.",
            "Given gear panel, When opened, Then orb controls are reachable without cluttering the chat layout.",
        ],
        out_of_scope=["Native pywebview shell (KAN-41).", "Full UI-6 resize (KAN-53)."],
        technical_notes=["`ui/gradio_app.py`.", "`settings/store.py` orb preset keys.", "FastAPI still serves `/ui` static."],
        mockups=[
            "mystic.png — Gradio orb reference (calm state, gear panel closed).",
            "widget_settings_desk7.png — desktop widget opacity/border panel for parity with Gradio.",
        ],
    )

    bodies["KAN-11"] = TicketBody(
        summary_context="Report exporter produces JSON and Markdown artifacts from run metadata.",
        requirements=fr("FR-REP-1", "FR-REP-3"),
        behaviour=(
            "`reports/exporter.py` serialises run results (pass/fail counts, story keys when provided, timestamps) "
            "to JSON and Markdown files suitable for management review. Customisable section toggles (FR-REP-2) are "
            "scoped to KAN-51 — current exporter is baseline export only."
        ),
        acceptance=[
            "Given a completed test run payload, When export is called, Then JSON and Markdown files are written to the reports path.",
            "Given export output, When a human opens Markdown, Then pass/fail summary is readable without the app running.",
        ],
        out_of_scope=["User-selectable section toggles (KAN-51 / FR-REP-2).", "Xray upload."],
        technical_notes=["`reports/exporter.py`.", "Invoked from agent tools / future reporting UI."],
        mockups=[],
    )

    bodies["KAN-12"] = TicketBody(
        summary_context="Jira plugin lists issues and performs writes only after explicit user confirmation.",
        requirements=fr("FR-JIRA-1", "FR-JIRA-2", "FR-JIRA-5", "FR-JIRA-6", "FR-JIRA-7"),
        behaviour=(
            "`plugins/jira_plugin.py` reads project issues via REST (email + API token from local settings). "
            "Create, transition, comment, and link operations stage a pending action until the user confirms "
            "with yes/confirm. Credentials never logged. HTTP 429 triggers backoff using Retry-After when present."
        ),
        acceptance=[
            "Given configured jira_url/email/token in local settings, When list_stories runs, Then KAN stories return with status.",
            "Given create_issue without confirm, When agent attempts write, Then confirmation_required is returned.",
            "Given 429 from Jira, When retrying, Then client waits per Retry-After before repeat.",
        ],
        out_of_scope=["Silent writes.", "Storing tokens in git or chat logs."],
        technical_notes=[
            "`plugins/jira_plugin.py`.",
            "Settings keys: jira_url, jira_email, jira_api_token in %LOCALAPPDATA%\\ai_testing_app\\settings.json.",
            "Tests: `tests/` jira plugin tests.",
        ],
        mockups=[],
    )

    bodies["KAN-13"] = TicketBody(
        summary_context="Automated pytest suite guards core plugins, orb config, sessions, settings, and reports.",
        requirements=fr("FR-PLUG-1", "FR-AGENT-5"),
        behaviour=(
            "`tests/` contains unit/integration tests for Jira plugin, Playwright heal paths, orb presets/config, "
            "sessions, settings store, and report exporter. CI/local run: `pytest` should pass on main for shipped behaviour."
        ),
        acceptance=[
            "Given a clean venv, When `pytest` runs from repo root, Then core tests pass (no secrets required in env).",
            "Given a failing assertion in a plugin, When tests run, Then failure surfaces with file/line — not swallowed.",
        ],
        out_of_scope=["Full E2E browser suite for every UI pixel.", "Load/performance testing."],
        technical_notes=["`tests/` directory.", "Use markers for browser tests where present."],
        mockups=[],
    )

    bodies["KAN-14"] = TicketBody(
        summary_context="Extend self-healing beyond click-only while enforcing FR-HEAL guardrails (open).",
        requirements=fr("FR-HEAL-1", "FR-HEAL-2", "FR-HEAL-3", "FR-HEAL-4", "FR-HEAL-5"),
        behaviour=(
            "Today: click self-heal in Playwright runner. Target: heal proposals for additional locator strategies, "
            "always showing a human-readable diff, classifying failure (product bug vs test defect vs env), and logging "
            "approver + evidence. System must refuse assertion weakening, value changes, fixme/skip to green, "
            "timeout inflation, or patching the app under test."
        ),
        acceptance=[
            "Given a failing assertion, When heal is suggested, Then proposal does not change expected values (FR-HEAL-1).",
            "Given a product bug classification, When heal is considered, Then suite stays red until bug is fixed.",
            "Given an approved heal, When applied, Then audit log records classification, evidence, approver (FR-HEAL-5).",
        ],
        out_of_scope=["Auto-merge healed tests without review.", "Modifying application source to pass tests."],
        technical_notes=["`plugins/playwright_runner.py` (current heal).", "Coordinate with KAN-49 guardrail enforcement story."],
        mockups=[],
    )

    bodies["KAN-15"] = TicketBody(
        summary_context="UK OFFICIAL/SECRET switcher exists; full credential and browser-profile isolation not yet shipped.",
        requirements=fr("FR-SEC-1", "FR-SEC-2", "FR-SEC-3", "FR-SEC-4", "FR-SEC-5"),
        behaviour=(
            "Security level selector must gate credential scopes and Playwright browser profiles. "
            "Changing level requires explicit confirmation (FR-SEC-3). No telemetry by default; GDPR deletion paths. "
            "Treat external content as untrusted; narrow high-privilege tools at higher levels (FR-SEC-4)."
        ),
        acceptance=[
            "Given OFFICIAL vs SECRET selection, When user switches, Then confirmation prompt appears before profiles/creds switch.",
            "Given SECRET level, When Playwright launches, Then isolated browser profile path is used (not yet implemented — story open).",
            "Given secrets in settings store, When UI renders, Then tokens are never echoed to client logs.",
        ],
        out_of_scope=["Formal accreditation paperwork.", "Multi-tenant cloud hosting."],
        technical_notes=["`settings/store.py` for level persistence.", "Future: Playwright profile dirs per level.", "Read `.cursor/rules/security-levels.mdc` before coding."],
        mockups=[],
    )

    bodies["KAN-16"] = TicketBody(
        summary_context="Local settings store holds credentials, orb presets, and app config — never committed to git.",
        requirements=fr("FR-SET-1", "FR-SET-2", "FR-JIRA-7", "FR-SEC-5"),
        behaviour=(
            "`settings/store.py` reads/writes `%LOCALAPPDATA%\\ai_testing_app\\settings.json`. "
            "Jira tokens, URLs, Ollama overrides, and orb presets live here. Document ingestion (future) must "
            "propose diffs and wait for confirm before write (FR-SET-2)."
        ),
        acceptance=[
            "Given fresh install, When app starts, Then settings file is created under LOCALAPPDATA only.",
            "Given repo grep for api tokens, When scanning tracked files, Then no real credentials appear in git.",
        ],
        out_of_scope=["Syncing settings to cloud.", "Encrypting disk at rest (OS-level concern)."],
        technical_notes=["`settings/store.py`.", "Agent loads settings for Jira/Ollama/orb."],
        mockups=[],
    )

    bodies["KAN-39"] = TicketBody(
        summary_context="FastAPI backend exposes chat, health, orb API, and static UI assets.",
        requirements=fr("FR-AGENT-3", "FR-UI-2"),
        behaviour=(
            "`main.py` serves `GET /health`, `POST /chat` (agent), orb configuration endpoints, and static `/ui` "
            "including desktop shell assets. Health returns ok when process is up; chat delegates to agent session."
        ),
        acceptance=[
            "Given server running, When GET /health, Then 200 with ok payload.",
            "Given valid chat body, When POST /chat, Then JSON reply from agent.",
            "Given browser GET /ui/desktop/, When loaded, Then static assets serve without 404 for bundled JS/CSS.",
        ],
        out_of_scope=["Gradio mount (separate run_ui.py).", "HTTPS termination (local dev HTTP)."],
        technical_notes=["`main.py`.", "Run: `uvicorn` per `run-local-stack` skill."],
        mockups=[],
    )

    bodies["KAN-41"] = TicketBody(
        summary_context="Native Windows desktop (pywebview) with full-void WebGL orbs mystic/aether/neural/apex and per-style persistence.",
        requirements=fr("FR-UI-2", "FR-UI-3", "FR-UI-5"),
        behaviour=(
            "`desktop_app.py` opens Edge WebView2 window to `/ui/desktop/`. Pure black void; app + screen drawers; "
            "bottom chat bar. Orbs render via `ui/orb_webgl.js` + vendored Three.js. Style switch updates theme accent "
            "(mystic #50cdff, aether #ff8a2b, neural #5ce1ff, apex #e8d4a0). Sliders (glow, turbulence, size, spin) "
            "persist per style in localStorage key `desktop-orb-styles-v1`. Widget settings (opacity, border, bg) apply "
            "live to shell surfaces. Particle caps per `docs/mockups/orb_styles.md`."
        ),
        acceptance=[
            "Given `python desktop_app.py`, When window opens, Then mystic orb renders on #000000 background.",
            "Given style switch to aether, When selected, Then accent colour and saved aether sliders load.",
            "Given glow/turbulence sliders, When moved, Then orb updates live and persists after reload for active style.",
        ],
        out_of_scope=["Gradio feature parity.", "Resizable panel handles (KAN-53)."],
        technical_notes=[
            "`desktop_app.py`, `ui/desktop/`, `ui/orb_webgl.js`, `ui/vendor/three.min.js`.",
            "Visual gate: `.cursor/rules/orb-visual.mdc`, `scripts/compare_orb.py`.",
        ],
        mockups=[
            "mystic_desktop_drawers.png — void shell with left app drawer and right screen drawer.",
            "mystic_final_thinking.png — mystic orb mid-animation (thinking state).",
            "style_theme_switch.png — style picker and per-style accent colours.",
            "aether_mid_v4.png / neural_mid_v16.png / apex_v4.png — hero WebGL styles at mid settings.",
            "docs/mockups/orb_styles.md — particle caps and renderer table.",
        ],
    )

    bodies["KAN-43"] = TicketBody(
        summary_context="Cursor ops: rules, skills, custom agents, and HOW_WE_WORK — enabling PM-owned slices.",
        requirements=fr("FR-PLUG-1"),
        behaviour=(
            "Repository ships `.cursor/rules`, `.cursor/skills`, `.cursor/agents`, `docs/ops/HOW_WE_WORK.md`, "
            "`AGENTS.md`, and IronBee DevTools rule for browser verification. Enables slice workflow without "
            "copy-paste to external bots."
        ),
        acceptance=[
            "Given new contributor, When they read docs/ops/HOW_WE_WORK.md, Then PM-owned flow is clear.",
            "Given slice-workflow skill, When PM starts feature, Then run-local-stack and verifier paths are documented.",
        ],
        out_of_scope=["Replacing Ollama runtime.", "Mandatory Cursor Cloud agents."],
        technical_notes=["`.cursor/` tree.", "`docs/ops/*`."],
        mockups=[],
    )

    bodies["KAN-45"] = TicketBody(
        summary_context="Ingest functional specs (text/Markdown/PDF) and propose settings URLs/credentials — store only after confirm.",
        requirements=fr("FR-LEARN-1", "FR-LEARN-2", "FR-LEARN-4", "FR-LEARN-5", "FR-SET-2"),
        behaviour=(
            "Pipeline accepts uploaded spec files, extracts behaviours and environment hints, and presents a structured "
            "settings diff (target URL, Jira project, optional cred placeholders). Nothing is written to "
            "`settings.json` until the user explicitly confirms. Extracted content treated as untrusted input (FR-SEC-4)."
        ),
        acceptance=[
            "Given a Markdown spec upload, When parsing completes, Then proposed test ideas/settings diff is shown in UI/chat.",
            "Given proposed creds, When user declines, Then settings file unchanged.",
            "Given user confirms, When merge runs, Then only approved keys are written locally.",
        ],
        out_of_scope=["Automatic test generation without review (FR-TEST-1 coordination later).", "OCR for scanned PDFs beyond baseline."],
        technical_notes=["New plugin module under `plugins/` (to implement).", "`settings/store.py` confirm gate."],
        mockups=[],
    )

    bodies["KAN-47"] = TicketBody(
        summary_context="Separate desktop .exe test plugin — do not fork Playwright runner.",
        requirements=fr("FR-TEST-3", "FR-PLUG-1", "FR-PLUG-2"),
        behaviour=(
            "Register a toggleable plugin that launches/smokes Windows desktop apps via documented harness "
            "(e.g. UI automation library TBD). Playwright runner remains browser-only. Plugin exposes agent tools "
            "with the same confirmation rules as other side effects."
        ),
        acceptance=[
            "Given plugin disabled in settings, When agent asked to test .exe, Then graceful message to enable plugin.",
            "Given sample .exe path, When smoke test runs, Then result + logs returned without modifying Playwright code.",
        ],
        out_of_scope=["Mac/Linux desktop.", "Bundling installers."],
        technical_notes=["New `plugins/desktop_*` module.", "Register in `agent/agent.py`."],
        mockups=[],
    )

    bodies["KAN-49"] = TicketBody(
        summary_context="Implement full FR-HEAL guardrails before trusting broad self-heal.",
        requirements=fr("FR-HEAL-1", "FR-HEAL-2", "FR-HEAL-3", "FR-HEAL-4", "FR-HEAL-5"),
        behaviour=(
            "Central policy module enforced by Playwright runner and any future heal UI: classify failures, "
            "generate locator-only diffs, block forbidden transforms (assertion weaken, fixme, timeout bump, AUT patch), "
            "require approver, append heal audit log."
        ),
        acceptance=[
            "Given heal prompt to change toHaveText to toBeVisible, When policy runs, Then operation is refused with reason.",
            "Given unclassified failure, When heal requested, Then classification step is mandatory.",
        ],
        out_of_scope=["ML-based auto-approval.", "Healing production application code."],
        technical_notes=["Coordinate with KAN-14.", "`plugins/playwright_runner.py` hooks."],
        mockups=[],
    )

    bodies["KAN-51"] = TicketBody(
        summary_context="User-selectable report sections on top of existing exporter (FR-REP-2 polish).",
        requirements=fr("FR-REP-1", "FR-REP-2", "FR-REP-3"),
        behaviour=(
            "Extend reporting UI/settings so users toggle sections (summary, per-story, bugs, evidence links). "
            "Persist choices locally. `reports/exporter.py` respects section config on JSON/Markdown export."
        ),
        acceptance=[
            "Given section toggles saved, When export runs, Then omitted sections are absent from Markdown/JSON.",
            "Given defaults, When first export, Then all core sections present.",
        ],
        out_of_scope=["PDF layout designer.", "Email scheduling."],
        technical_notes=["`reports/exporter.py`.", "Settings keys for report profile."],
        mockups=[],
    )

    bodies["KAN-53"] = TicketBody(
        summary_context="UI-6 remainder: resizable panels/widgets; layout persists with existing drag/snap desktop work.",
        requirements=fr("FR-UI-4", "FR-UI-5"),
        behaviour=(
            "Desktop shell already supports edge-snap drawers, free-drag widgets, widget opacity/border/background "
            "(localStorage `desktop-shell-layout-v1`). Add resize handles for panels/widgets; persist dimensions on change. "
            "Gradio should gain equivalent movable/resizable behaviour where feasible without full rewrite."
        ),
        acceptance=[
            "Given a panel selected, When user drags resize handle, Then width/height updates live.",
            "Given layout saved, When app reloads, Then positions and sizes restore.",
        ],
        out_of_scope=["Arbitrary user HTML widgets.", "Cloud layout sync."],
        technical_notes=["`ui/desktop/` layout JS.", "`ui/gradio_app.py` for Gradio parity."],
        mockups=[
            "widget_settings_desk7.png — widget opacity, border, and background controls.",
            "movable_controls_desk5.png — drag handles and snap targets on desktop shell.",
            "widget_transparency_desk6.png — semi-transparent chat/settings surfaces.",
        ],
    )

    bodies["KAN-55"] = TicketBody(
        summary_context="Design stub for multi-sandbox orchestration plugin (future parallel test environments).",
        requirements=fr("FR-PLUG-1", "FR-PLUG-2"),
        behaviour=(
            "Define plugin interface and registry entry for orchestrating multiple sandboxes (URLs, profiles, credentials). "
            "Initial slice: registry accepts plugin manifest, settings toggle, no-op or mock orchestration — enough for "
            "agent to list capability without rewriting core."
        ),
        acceptance=[
            "Given plugin registered, When settings list plugins, Then multi-sandbox entry appears with toggle default off.",
            "Given toggle off, When agent invokes sandbox orchestration, Then returns not-enabled message.",
        ],
        out_of_scope=["Full parallel Playwright grid.", "Kubernetes sandboxes."],
        technical_notes=["Plugin registry pattern in `agent/agent.py` / `plugins/`."],
        mockups=[],
    )

    user_stories: Dict[str, str] = {
        "KAN-8": "As a senior test engineer, I want to talk to a local agent in natural language so that I can request tests and clarify intent without leaving my laptop.",
        "KAN-9": "As a tester, I want Playwright steps to run with evidence and safe locator heals so that flaky selectors do not silently change assertions.",
        "KAN-10": "As a user, I want a Gradio chat + orb UI so that I can drive the agent without a browser-only workflow.",
        "KAN-11": "As a QA lead, I want JSON/Markdown run exports so that I can share results with management offline.",
        "KAN-12": "As a developer, I want Jira reads and confirmed writes so that backlog updates never happen silently.",
        "KAN-13": "As a maintainer, I want automated pytest coverage of core plugins so that regressions surface before merge.",
        "KAN-14": "As a tester, I want broader self-healing under strict guardrails so that locators can adapt without weakening assertions.",
        "KAN-15": "As a security-conscious user, I want OFFICIAL/SECRET isolation so that credentials and browser profiles never mix.",
        "KAN-16": "As a user, I want settings and secrets only in local app data so that nothing sensitive lands in git.",
        "KAN-39": "As a developer, I want a FastAPI backend with health and chat endpoints so that UI and agents share one local API.",
        "KAN-41": "As a user, I want a native desktop shell with WebGL hero orbs so that the product feels local and polished.",
        "KAN-43": "As a Cursor user, I want repo rules/skills/agents so that coding agents follow project constraints without re-prompting.",
        "KAN-45": "As a user, I want document ingestion that proposes settings so that I confirm before anything is stored.",
        "KAN-47": "As a tester, I want a desktop .exe testing plugin so that Windows apps can be tested without forking Playwright.",
        "KAN-49": "As a tester, I want enforced heal guardrails so that the suite cannot go green by weakening assertions.",
        "KAN-51": "As a QA lead, I want customisable report sections so that exports match stakeholder needs.",
        "KAN-53": "As a user, I want resizable panels on the desktop shell so that chat, orb, and widgets fit my workflow.",
        "KAN-55": "As a power user, I want a multi-sandbox plugin stub so that parallel environments can be toggled later without rewriting core.",
    }
    for key, body in bodies.items():
        body.kind = "story"
        body.user_story = user_stories.get(
            key,
            "As a product user, I want this slice delivered so that the AI testing app moves closer to the functional specification.",
        )
        if body.dependencies is None:
            body.dependencies = [
                "Repo at D:\\Projects\\ai_testing_app with working venv.",
                "Ollama models on D:\\Program Files\\Ollama\\models when the agent loop is needed.",
            ]

    return bodies


# Test task key -> parent story key
TEST_PARENT: Dict[str, str] = {
    "KAN-30": "KAN-8",
    "KAN-31": "KAN-9",
    "KAN-32": "KAN-10",
    "KAN-33": "KAN-11",
    "KAN-34": "KAN-12",
    "KAN-35": "KAN-13",
    "KAN-36": "KAN-14",
    "KAN-37": "KAN-15",
    "KAN-38": "KAN-16",
    "KAN-40": "KAN-39",
    "KAN-42": "KAN-41",
    "KAN-44": "KAN-43",
    "KAN-46": "KAN-45",
    "KAN-48": "KAN-47",
    "KAN-50": "KAN-49",
    "KAN-52": "KAN-51",
    "KAN-54": "KAN-53",
    "KAN-56": "KAN-55",
}


def _split_gwt(ac: str) -> Tuple[str, str]:
    ac = ac.strip()
    if " Then " in ac:
        given_when, then = ac.split(" Then ", 1)
        return (
            given_when.replace("Given ", "Given ", 1) if given_when.startswith("Given ") else given_when,
            then.strip(),
        )
    return (ac, "Criterion is satisfied on current main; attach pytest log, screenshot, or short recording.")


def test_body(parent_key: str, story: TicketBody) -> TicketBody:
    procedure = [_split_gwt(ac) for ac in story.acceptance]
    procedure.append(
        (
            "Record evidence (pytest output, screenshot path, or short screen recording for UI stories).",
            "Evidence is attached or linked in the test task comment.",
        )
    )
    procedure.append(
        (
            "Compare results against pass/fail rules for the parent story.",
            "Pass when all steps succeed on main (or document a known gap for open stories). "
            "Fail with defect classification: product bug vs test defect vs environment.",
        )
    )
    return TicketBody(
        summary_context=(
            f"Manual and automated verification for parent story {parent_key}. "
            "Follow the numbered procedure below; each step includes an expected result. "
            "Do not close with a generic “verified” comment — attach command output or screenshots."
        ),
        requirements=list(story.requirements),
        behaviour=(
            f"Validate shipped behaviour for {parent_key} using the parent story’s acceptance scenarios. "
            "Automate where pytest or IronBee browser tools already exist; otherwise run the desktop or API checks described in technical notes."
        ),
        acceptance=[
            "All procedure steps completed with evidence attached.",
            f"Parent story {parent_key} acceptance scenarios are satisfied or gaps are documented.",
        ],
        test_steps=procedure,
        out_of_scope=["Production deployment checks.", "Third-party Atlassian uptime."],
        technical_notes=story.technical_notes + [f"Parent story: {parent_key}."],
        mockups=story.mockups,
        kind="test",
        user_story=(
            f"As a tester, I want a step-by-step procedure for {parent_key} so that I can pass or fail "
            "the parent story without guessing intent."
        ),
        dependencies=[f"Parent story {parent_key} must be implementable or already Done."],
    )


class JiraClient:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.client = httpx.Client(
            timeout=90.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers={"Accept": "application/json"},
        )
        self.failures: List[str] = []

    def close(self) -> None:
        self.client.close()

    def _sleep(self) -> None:
        time.sleep(BACKOFF)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        for attempt in range(6):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code == 429:
                wait = float(r.headers.get("Retry-After", "2"))
                time.sleep(wait)
                continue
            return r
        return r

    def update_description(self, key: str, adf: Dict[str, Any]) -> bool:
        r = self._request(
            "PUT",
            f"/rest/api/3/issue/{key}",
            json={"fields": {"description": adf}},
            headers={"Content-Type": "application/json"},
        )
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"update {key}: {r.status_code} {r.text[:180]}")
            return False
        return True

    def list_attachments(self, key: str) -> List[str]:
        r = self._request("GET", f"/rest/api/3/issue/{key}", params={"fields": "attachment"})
        if r.status_code >= 300:
            return []
        return [a.get("filename", "") for a in (r.json().get("fields") or {}).get("attachment") or []]

    def attach_file(self, key: str, path: Path) -> bool:
        if not path.is_file():
            self.failures.append(f"attach {key}: missing file {path.name}")
            return False
        existing = set(self.list_attachments(key))
        if path.name in existing:
            return True
        with path.open("rb") as fh:
            r = self._request(
                "POST",
                f"/rest/api/3/issue/{key}/attachments",
                files={"file": (path.name, fh, "image/png")},
                headers={"X-Atlassian-Token": "no-check"},
            )
        self._sleep()
        if r.status_code >= 300:
            self.failures.append(f"attach {key} {path.name}: {r.status_code}")
            return False
        return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    frs = parse_frs(spec_text)
    stories = story_bodies(frs)

    plan: List[Tuple[str, TicketBody]] = []
    for ek in EPIC_FR_PREFIX:
        plan.append((ek, epic_body(ek, frs)))
    for sk, body in sorted(stories.items()):
        plan.append((sk, body))
    for tk, pk in sorted(TEST_PARENT.items()):
        if pk in stories:
            plan.append((tk, test_body(pk, stories[pk])))

    if args.dry_run:
        print(json.dumps({"count": len(plan), "keys": [k for k, _ in plan]}, indent=2))
        return 0

    base, auth = _load_creds()
    client = JiraClient(base, auth)
    updated = 0
    attached_issues: List[str] = []

    adf_problems: List[str] = []
    for key, body in plan:
        if key in SKIP_KEYS:
            continue
        adf = body_to_adf(body)
        problems = validate_adf(adf)
        if problems:
            adf_problems.append(f"{key}: {', '.join(problems)}")
            continue
        ok = client.update_description(key, adf)
        if ok:
            updated += 1

    for key, files in ATTACHMENTS.items():
        if key in SKIP_KEYS:
            continue
        any_att = False
        for name in files:
            p = SCREENSHOTS / name
            if client.attach_file(key, p):
                any_att = True
        if any_att:
            attached_issues.append(key)

    summary = {
        "updated_count": updated,
        "planned_count": len(plan),
        "attachments_uploaded_or_present": attached_issues,
        "adf_validation_skipped": adf_problems,
        "failures": client.failures,
        "format_notes": {
            "template": "docs/ops/JIRA_TICKET_TEMPLATE.md",
            "after": (
                "Who this is for; User story (As a/I want/so that); Requirements with bold FR-IDs; "
                "Behaviour paragraphs; numbered AC; team Definition of done; Dependencies; Technical notes; "
                "Mockups; Traceability. Test tasks keep Test procedure + Expected."
            ),
        },
        "sample_story": "KAN-53",
        "sample_url_hint": f"{base}/browse/KAN-53",
    }
    print(json.dumps(summary, indent=2))
    client.close()
    return 0 if not client.failures else 2


if __name__ == "__main__":
    sys.exit(main())