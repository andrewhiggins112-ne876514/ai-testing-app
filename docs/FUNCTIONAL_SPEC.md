# Functional Specification — AI Testing Application

**Version:** 1.0  
**Date:** 2026-11-15  
**Status:** Draft for review  
**Sources:** Original Grok share chats, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, current codebase structure, and research into common failure modes of vibe-coded / AI-agent applications of similar nature.

---

## 1. Purpose and Vision

A local-first, conversational AI testing agent that helps senior test engineers and small teams generate, execute, self-heal, and report on tests for both browser-based and desktop applications. The primary interface is a natural-language conversation (text first; voice later). Everything else (settings, reports, Jira, orb visualiser, plugins) lives in secondary panels or drawers.

**Core value proposition**
- Generate and run tests from functional specifications, Jira stories/epics, or existing Playwright suites.
- Self-heal broken locators without weakening the actual assertions.
- Bi-directional Jira/Xray integration (read, create tests, update status, raise bugs) with explicit human confirmation on writes.
- Support UK security classifications (OFFICIAL / SECRET) with isolation of credentials and browser profiles.
- Stay fully local / on-prem capable (Ollama + no mandatory cloud tokens).
- Customisable reporting.
- Document ingestion that proposes settings with confirmation.

**Long-term goal:** A capable local/on-prem alternative to cloud SaaS testing tools, aimed at organisations that cannot or will not send test data or credentials to the cloud.

---

## 2. Personas

| Persona | Goals | Pain points this app addresses |
|---------|-------|--------------------------------|
| Senior Test Engineer (primary) | Leave traditional work; build reliable automation quickly; keep everything local | Flaky tests, manual Jira updates, broken locators, cloud lock-in, GDPR/security constraints |
| QA Lead / Tech Lead | Visibility into coverage, bugs raised, progress against stories | Customisable reports, Jira linking, evidence |
| Solo / small-team developer | Fast feedback without standing up a full CI farm | Local execution, Playwright + desktop plugins |

---

## 3. Functional Requirements

### 3.1 Conversational Agent Core
- **FR-AGENT-1:** User talks to the agent in natural language to request tests, configure environments, interpret results, or ask clarifying questions.
- **FR-AGENT-2:** Agent must clarify ambiguous requests before acting (especially side-effecting actions).
- **FR-AGENT-3:** Agent maintains session context and can resume interrupted work.
- **FR-AGENT-4:** All tool calls that have side effects (file writes, Jira writes, credential changes, destructive commands, security-level changes) require explicit user confirmation. No “YOLO” mode for production-relevant actions.
- **FR-AGENT-5:** Agent must surface clear error logs when it fails due to its own code, bad input, or tool failure (never swallow errors silently).
- **FR-AGENT-6:** Tool-calling reliability requirements:
  - Prefer models known to emit structured tool calls reliably with Ollama (or implement a robust fallback parser for JSON-in-text tool calls).
  - Explicitly set sufficient context window and disable thinking mode when it interferes with tool calls.
  - Never claim a tool action succeeded unless the tool result is received and validated.

### 3.2 Learning Inputs
- **FR-LEARN-1:** Accept functional specifications (text, Markdown, PDF) and extract expected behaviour / test ideas.
- **FR-LEARN-2:** Accept target application path (`.exe`) or URL.
- **FR-LEARN-3:** Accept additional endpoints / messaging URLs (e.g. RabbitMQ JSON payloads).
- **FR-LEARN-4:** Accept Jira URL + project key so the agent can read epics and stories.
- **FR-LEARN-5:** Document ingestion must propose settings (URLs, credentials, API endpoints) and require explicit user confirmation before storing them. No silent storage of extracted data.

### 3.3 Test Generation and Execution
- **FR-TEST-1:** Generate test cases / steps from functional specs and/or Jira stories.
- **FR-TEST-2:** Execute browser tests via Playwright (headed or headless). First-class support for Playwright; other frameworks as plugins later.
- **FR-TEST-3:** Execute desktop tests via a separate plugin (do not fork the Playwright runner).
- **FR-TEST-4:** Capture screenshots / evidence on failure and success where useful.
- **FR-TEST-5:** Support existing Playwright suites (import and run).
- **FR-TEST-6:** Negative tests and edge cases must be first-class. The agent must not optimise only for the happy path. Generated tests that only check visibility or nearby elements without asserting the actual expected outcome are incomplete.

### 3.4 Self-Healing (Critical Guardrails)
- **FR-HEAL-1:** Self-healing may only change *how* an element is located (locator strategy, role-based selector, etc.). It must never change *what* is asserted or the expected values without explicit human approval.
- **FR-HEAL-2:** Any proposed heal must be presented for review (diff or clear description). No automatic commit of healed tests to the main suite without approval.
- **FR-HEAL-3:** The system must refuse to:
  - Weaken assertions (e.g. change `toHaveText` to `toBeVisible`).
  - Alter expected values.
  - Skip or `test.fixme()` a test solely to make the suite green.
  - Raise timeouts or add retries solely to hide flakiness.
  - Patch the application under test instead of the test.
- **FR-HEAL-4:** Failures must be classified (product bug vs test defect vs intended change vs environment) before any heal is proposed. Real product bugs stay red.
- **FR-HEAL-5:** All heals are logged with classification, evidence, and approver.

### 3.5 Jira / Xray Integration
- **FR-JIRA-1:** Read stories, epics, and acceptance criteria.
- **FR-JIRA-2:** Create linked test tickets (with structured description / steps where possible).
- **FR-JIRA-3:** Update test ticket status to Done when criteria are covered.
- **FR-JIRA-4:** Create user-friendly bug tickets when defects are found.
- **FR-JIRA-5:** All write operations are two-step confirm (agent proposes → user confirms). No silent writes.
- **FR-JIRA-6:** Respect Jira rate limits. Implement backoff on 429, respect `Retry-After`, and avoid burst patterns that trigger per-issue or points quotas. Surface clear messages when rate-limited.
- **FR-JIRA-7:** Credentials live only in the local settings store. Never in chat history, repo, or logs. Support API token + email (Cloud).

### 3.6 Reporting
- **FR-REP-1:** Generate reports with metrics such as tests passed/failed, stories covered (by Jira key), bugs raised per story or functional area, progress, etc.
- **FR-REP-2:** Reports are customisable — user chooses which sections to include or exclude.
- **FR-REP-3:** Reports can be exported (current exporter exists; polish later).

### 3.7 Security and Isolation
- **FR-SEC-1:** Support UK security classifications OFFICIAL and SECRET from the start via isolation of credentials and browser profiles.
- **FR-SEC-2:** No telemetry by default. Easy local data deletion. Explicit consent before storing extracted data (GDPR).
- **FR-SEC-3:** Security-level switcher is available and changes take effect only after confirmation.
- **FR-SEC-4:** Prompt-injection mitigations:
  - Treat all external content (uploaded specs, Jira descriptions, web pages, tool outputs) as untrusted.
  - Narrow tool surface by default. High-privilege tools (file system outside workspace, network, shell) require confirmation or are disabled in higher security levels.
  - Prefer models and configurations that reduce injection success on smaller local models.
- **FR-SEC-5:** Secrets never leave the local settings store or are written to client-side code / logs.

### 3.8 UI and Desktop Experience
- **FR-UI-1:** Conversational interface is primary. Secondary controls live in drawers / panels.
- **FR-UI-2:** Native Windows desktop window (pywebview + Edge WebView2) is the preferred experience. Gradio remains available.
- **FR-UI-3:** Visual orb styles (Mystic, Aether, Neural, Apex and classic canvas styles) with per-style settings, live controls, and theme accent that follows the active style.
- **FR-UI-4:** Movable / resizable panels and widgets (UI-6). Layout persists in localStorage.
- **FR-UI-5:** Widget settings (transparency, border, background) apply live to shell surfaces.

### 3.9 Plugins and Extensibility
- **FR-PLUG-1:** Modular plugin architecture. New capabilities (desktop testing, richer reporting, multi-sandbox, performance, security testing, etc.) are addable without rewriting the core.
- **FR-PLUG-2:** Plugins can be toggled.
- **FR-PLUG-3:** Future: dynamic framework switching (Playwright first; others later) via settings.

### 3.10 Settings and Local Store
- **FR-SET-1:** All user settings, credentials, orb presets, and layout live under the local app data directory (`%LOCALAPPDATA%\ai_testing_app\`). Never committed to git.
- **FR-SET-2:** Document ingestion proposes settings; user must confirm before they are written.

---

## 4. Non-Functional Requirements

### 4.1 Local-First and Privacy
- Must run on a Windows laptop without requiring cloud services or API tokens for core functionality.
- Ollama is the default local LLM. No mandatory outbound calls for the agent loop.
- GDPR: no telemetry by default; easy deletion of local data; explicit consent for any extracted data storage.

### 4.2 Security and Trustworthiness
- Explicit confirmation on all side-effecting actions (see FR-AGENT-4, FR-JIRA-5, FR-SEC-3).
- Self-healing guardrails (FR-HEAL-*).
- Prompt-injection and tool-calling reliability requirements (FR-AGENT-6, FR-SEC-4).
- Secrets never in repo, chat, or client code.
- Isolation for OFFICIAL / SECRET.

### 4.3 Reliability and Observability
- Clear error logging for agent, tool, and test failures. No silent swallows.
- Evidence (screenshots, logs) captured on test failure.
- Classification of test failures before any healing.
- Logging of all heals and Jira writes.

### 4.4 Performance and Resource Awareness
- Target the development machine constraints (i7-8700K, 32 GB RAM, GTX 1080 Ti). Prefer 7B–8B models. Do not assume large models or dual-model operation.
- Leave headroom for Windows + one headed browser.
- Jira calls respect rate limits and back off cleanly.

### 4.5 Maintainability and Anti-Vibe-Coding Rules
- Small, reviewable changes. One logical behaviour change per slice.
- Tests (or recorded manual checks) required for meaningful changes.
- Human review of meaningful diffs before merge.
- Update `PROJECT_MEMORY.md` Current State when behaviour changes.
- Prefer extending existing plugins over parallel systems.
- No secrets in git.
- Architecture must remain modular so future features do not require rewrites.

### 4.6 Error Handling and User Experience
- Agent must surface failures clearly rather than claim success.
- Rate-limit and authentication errors from Jira must be human-readable.
- UI must remain usable when the agent is thinking or a long test is running.

---

## 5. Current State vs Target

**Already present (as of 2026-11-15)**
- Ollama tool-calling agent with clarification and sessions (default `qwen2.5-coder:7b`; also `qwen3:8b` / `llama3.2` on D:).
- Playwright runner with click + fill locator self-heal (assertions never auto-healed), heal proposals/audit log, and evidence.
- Step generation + quality (KAN-57): `generate_playwright_steps` / `playwright_steps.py` builds happy + negative drafts with `expect_text`/`expect_url`; visibility-only drafts flagged/rejected; failure screenshots always; success evidence via `playwright_success_evidence`.
- Jira plugin (list/create/transition/comment; writes need confirm) against live project **KAN**.
- Local settings store (`%LOCALAPPDATA%\ai_testing_app\`).
- FastAPI backend + Gradio UI + native desktop window with WebGL hero orbs (mystic/aether/neural/apex).
- Reports exporter with customisable sections (summary / stories / bugs / evidence; KAN-51).
- Cursor ops (rules, agents, skills), `docs/ops/WORK_LOG.md` handoff, multi-audience KAN backlog (epics KAN-20…29).
- Tests for core pieces.
- Repo on `D:\Projects\ai_testing_app`; Ollama on `D:\Program Files\Ollama`.

**Still open / next** (track in KAN; Active slice = **KAN-59**)

Rule: a Done Story covers only what it actually shipped. Remaining FR text must stay on open Stories (seed/reconcile via `scripts/jira_kan_seed_backlog.py`). Done parents have gap comments where needed.

### FR → ticket coverage matrix

| FR | Implementation status | Primary ticket(s) |
|----|----------------------|-------------------|
| FR-AGENT-1…5 | Shipped (chat/sessions/clarify/confirm/errors baseline) | **Done** KAN-8; busy UX remainder **KAN-97** |
| FR-AGENT-6 | Shipped (JSON-in-text fallback + grounded replies) | **Done** **KAN-61** |
| FR-LEARN-1, FR-LEARN-5, FR-SET-2 | Shipped (ingest propose+confirm) | **Done** KAN-45 |
| FR-LEARN-2, FR-LEARN-3 | Open (settings keys exist; first-class UI/agent use incomplete) | **KAN-77** |
| FR-LEARN-4 | Open | **KAN-93** |
| FR-TEST-1 | Partial (chat/spec step gen) | **Done** KAN-57; from Jira AC **KAN-85** |
| FR-TEST-2 | Partial (headed only today) | **Done** KAN-9 baseline; headless **KAN-83** |
| FR-TEST-3 | Partial (smoke only) | **Done** KAN-47 smoke; expand **KAN-87** |
| FR-TEST-4, FR-TEST-6 | Shipped (evidence + negatives/quality) | **Done** KAN-57 |
| FR-TEST-5 | Shipped | **Done** **KAN-59** |
| FR-HEAL-1,3,4,5 (+ locator heal) | Shipped policy + click/fill | **Done** KAN-14, **KAN-49** |
| FR-HEAL-2 | Open (audit log only; no review UI) | **KAN-75** |
| FR-JIRA-1 | Partial (list summary only) | **Done** KAN-12 list; read AC **KAN-89** |
| FR-JIRA-2, FR-JIRA-3 | Shipped (create_test + update_status confirm) | **Done** **KAN-65** |
| FR-JIRA-4 | Shipped (create_bug + confirm) | **Done** KAN-63 |
| FR-JIRA-5, FR-JIRA-7 | Shipped confirm + local creds | **Done** KAN-12, **KAN-16**; write audit **KAN-99** |
| FR-JIRA-6 | Open (no product 429 backoff) | **KAN-91** |
| FR-REP-1 | Shipped (stories covered + bugs by story/area) | **Done** **KAN-67** |
| FR-REP-2 | Shipped | **Done** KAN-51 |
| FR-REP-3 | Shipped baseline export | **Done** KAN-11 |
| FR-SEC-1, FR-SEC-3, FR-SEC-5 | Shipped isolation + confirm + secrets scoping | **Done** KAN-15, **KAN-16** |
| FR-SEC-2 | Done | **KAN-69** |
| FR-SEC-4 | Done | **KAN-71** |
| FR-UI-1…5 | Mostly shipped; Settings panel + voice open | **Done** KAN-10/41/53; Settings **KAN-73**; Voice **KAN-81** |
| FR-PLUG-1 | Partial (registry + stubs) | **Done** KAN-55 stub; real sandboxes **KAN-95** |
| FR-PLUG-2 | Shipped toggles | **Done** KAN-47/55 toggles |
| FR-PLUG-3 | Open | **KAN-79** |
| FR-SET-1 | Shipped local store | **Done** KAN-16 |

**Open Stories (To Do):** KAN-57…KAN-81 (first seed), KAN-83…KAN-99 (FR gap pass). Each has a linked `test` Task (KAN-58…KAN-100).

**Recently done (2026-11-15)** — baseline only; see matrix for remainder  
Gradio Settings/Reports (**KAN-10**); UI-6 (**KAN-53**); heal (**KAN-14**/**KAN-49**); report sections (**KAN-51**); doc ingest (**KAN-45**); OFFICIAL/SECRET (**KAN-15**); desktop smoke (**KAN-47**); multi-sandbox stub (**KAN-55**).

---

## 6. Open Items and Dependencies

| Item | Status | Notes |
|------|--------|-------|
| Jira account | **Live** | [ai-testing-lab.atlassian.net](https://ai-testing-lab.atlassian.net), project **KAN** (QA Testing). Credentials in local settings only; agent writes still two-step confirm. |
| Real credentials | Local store only | Never in chat or repo |
| Model tool-calling reliability | Open | **KAN-61** |
| Self-healing guardrails (policy) | **Done** (KAN-49) | Review UI still **KAN-75** |
| Security isolation | **Done** (KAN-15) | GDPR delete **Done** (KAN-69); prompt-injection **Done** (KAN-71) |
| Document ingestion | **Done** (KAN-45) | LEARN-2/3/4 remain open Stories |

---

## 7. Acceptance Criteria (High-Level)

A slice is done when:
1. One logical behaviour change is delivered.
2. A test or recorded manual check exists.
3. Human has reviewed the meaningful diffs.
4. `PROJECT_MEMORY.md` Current State is updated if behaviour changed.
5. No secrets are in git.
6. Side-effecting actions still require confirmation.
7. Self-healing (if touched) still obeys the “how not what” rule and requires approval.
8. Errors are logged and surfaced rather than swallowed.
9. A Jira **story comment** states what the **agent did** to complete the story (implementation + files + verify).
10. The linked **test Task** (`label=test`, Relates) has verification evidence (e.g. pytest command + result) and is marked Done.

---

## 8. References

- Original vision chats (share links provided by user)
- `PROJECT_MEMORY.md` and `docs/ops/ROADMAP.md` in the repository
- Research summaries on vibe-coding failure modes, self-healing risks, Ollama tool-calling issues, and Jira rate limits (incorporated into NFRs and guardrails above)

---

*This specification is intended to be living. It is the **canonical product spec in the repo** (`docs/FUNCTIONAL_SPEC.md`). Jira KAN tickets inline FR text from here — they are not a second source of truth. When the human issues a change request (CR), update this file first, then refresh related KAN tickets (and `PROJECT_MEMORY.md` / `ROADMAP.md` / `WORK_LOG.md` as needed) so agents, testers, and the app never read stale requirements.*