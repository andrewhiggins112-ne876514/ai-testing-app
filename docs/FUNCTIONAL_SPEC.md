# Functional Specification — AI Testing Application

**Version:** 1.1  
**Date:** 2026-11-16  
**Status:** Living — prototype toward test-all (CR 2026-11-16)  
**Sources:** Original vision, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, Council CR catalogue `docs/ops/test_all_catalogue.json`, codebase, research into common failure modes of vibe-coded / AI-agent applications.

---

## 1. Purpose and Vision

A **downloadable, local-first “test all” application**. A tester installs it on Windows, enters connection details once (Jira, target URL / exe, documents, security level, Ollama model), and does their testing work **inside the app**.

The **primary surface** is the desktop **orb + chat home** (one home for everyone). Role-specific needs (tester, manager, release, product owner) are **HUD widgets** on that home (Screen drawer), not separate homes. App areas (Plan/Suite, Settings, Heal, Reports, Security, Documents, Desktop, Suites, Sandboxes, …) are dedicated full-window surfaces opened from home.

**Primary artifacts** are the **in-app test plan and suite** (viewed and run in the application). An existing Playwright git repo can be **imported** as an input; it is not the primary UX. Pipelines / CI are a **separate later section**. Manual session recording that updates tickets is **future** work (needs its own design pass).

The agent is the way in: clarify before acting; draft plans from **one Jira story or a whole Jira project** (epics, stories, tests, bugs) plus **uploaded documentation**; run a **single case** or a selected set; show failures, evidence, metrics; export management reports with chosen sections. Jira writes stay human-confirmed. Start with common practice (Playwright, Jira, browser apps), then widen via **plugins** (desktop AUT, other frameworks, sandboxes-as-env, voice, a11y, perf, …). **Cut nothing** already in the product — sequence and deepen; park means later phase/plugin.

**Maturity (2026-11-16):** the shipped tree is an honest **prototype** (baseline plugins + shell). Done KAN tickets are baselines toward this vision, not a finished product. Active product track: Test-all epics A–H in `docs/ops/test_all_catalogue.json`.

**Core value proposition**
- Connect once; work entirely in-app (plan → suite → run → evidence → report).
- Generate and run tests from specs, Jira (story or project), or imported Playwright suites.
- Self-heal broken locators without weakening assertions (human review).
- Bi-directional Jira integration (read, create tests, update status, raise bugs) with confirm on writes; Xray-shaped sync later if needed.
- UK OFFICIAL / SECRET isolation; local / on-prem (Ollama; no mandatory cloud).
- Customisable reporting and role HUD widgets on the shared orb home.
- Document ingestion that proposes settings **and** feeds plans, with confirmation.

**Long-term goal:** The most-used local/on-prem testing hub for testers, developers, and managers — a capable alternative to cloud SaaS testing tools.

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
- **FR-TEST-5:** Support existing Playwright suites (import and run). Import can be shown as cases in the in-app suite (FR-PLAN-2); the external project files are not deleted; `npx` run remains available.
- **FR-TEST-6:** Negative tests and edge cases must be first-class. The agent must not optimise only for the happy path. Generated tests that only check visibility or nearby elements without asserting the actual expected outcome are incomplete.

### 3.3a Connection, in-app plan / suite (test-all)
- **FR-CONN-1:** The person can save a connection profile: Jira site and project, target URL, optional desktop path and messaging endpoint, security level, optional documents, and the Ollama model to use. Stored only in the local level-scoped settings. Secrets never shown back in full. A health check reports whether Jira, Ollama, and the target are reachable without printing secrets.
- **FR-PLAN-1:** The app holds a **test plan** (intent, sources, links to Jira keys and documents) that the person can view and edit before a run.
- **FR-PLAN-2:** The app holds a **suite** of cases and runs them **inside the app**. The person can run one case or a selected set (e.g. by tag). Cases can be reordered, disabled, archived, tagged, and prioritised without deleting history.
- **FR-PLAN-3:** The agent may draft or update a plan from one Jira issue or, in the project-scale phase, from the connected Jira project (epics, stories, tests, bugs) plus uploaded documents. Drafts are batched with a visible cap. The person reviews the plan before execution. Jira writes stay on FR-JIRA-5.
- **FR-PLAN-4:** A run stores result, evidence, duration, and failure class on the case. Heal proposals and report sections can attach to that run. Traceability links case ↔ Jira key ↔ bugs ↔ known issues.
- **FR-CI-1 (later):** Pipelines and CI live in a **separate section** of the app. They do not replace the in-app suite as the place tests are authored and reviewed. Design before build (catalogue H2).
- **FR-MAN-1 (future):** A manual / exploratory session may be recorded and proposed as ticket updates after confirm. Requires a design pass before implementation (catalogue H1). Not in alpha.

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
- **FR-JIRA-1:** Read stories, epics, and acceptance criteria. Supports a single issue and, on the project-scale story, paged reads of the configured project with FR-JIRA-6 backoff.
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
- **FR-UI-1:** Conversational interface is primary on the **agent home screen** (chat + central orb). **One home for everyone** — there is no separate Tester/Manager/PO landing. App drawer and screen drawer are secondary shells for navigation and layout — not replacements for the home canvas.
- **FR-UI-2:** Native Windows desktop window (pywebview + Edge WebView2) is the preferred experience. Gradio remains available.
- **FR-UI-3:** Visual orb styles (Mystic, Aether, Neural, Apex and classic canvas styles) with per-style settings, live controls, and theme accent that follows the active style. **Orb settings** (style, size, spin, glow, colours) live in the **Screen drawer** only — not under App → Settings. The active style accent (CSS variables such as `--cyan`, border, glow, and muted text) also paints App nav, area surfaces (overlay, stage, split, floating), HUD chips, hub spokes, and the App Settings layout picker — not only the orb canvas. *(CR 2026-11-16 — layout modes × style theme.)*
- **FR-UI-4:** Movable / resizable panels and widgets (UI-6). Layout persists in localStorage.
- **FR-UI-5:** Widget settings (transparency, border, background) apply live to shell surfaces.
- **FR-UI-6:** **Agent-home HUD widgets** — optional toggleable widgets on the agent home screen (status chips, mini panels, role packs for tester / manager / release / coverage, checklist, etc.). Visibility and layout controls sit alongside existing Screen drawer toggles (chat output widget, orb visibility, widget chrome) — not as App → Settings list content. Widgets summarise and deep-link into App areas; they do not replace Plan/Suite, Reports, Heal, or Settings surfaces.
- **FR-UI-7:** **Dedicated area screens** — each App-nav area (Settings, Security, Reports, Documents, Desktop, Suites, Sandboxes, and future areas) opens its own **dedicated surface**. The App drawer is a navigation list only; it must **not** expand inline `app-section-*` blocks. **App area layout** (App Settings, not Orb settings) chooses how that surface appears, persisted in `localStorage` key `desktop-area-layout-v1`:
  - `overlay` — full-bleed glass over a dimmed home (mockup A)
  - `stage` — area stage with the orb scaled to a corner pip (mockup B)
  - `orb_hub` — orb click shows spokes, then the area opens as an overlay (mockup C)
  - `split` — docked panel beside the home orb; Esc closes it (mockup D)
  - `floating` — one movable area window; the orb stays full size (mockup E)
  Esc or Back returns home. Accents follow the active orb style (FR-UI-3). *(Product decision 2026-11-16 — configurable A–E, not a single mockup pick.)*

### 3.9 Plugins and Extensibility
- **FR-PLUG-1:** Modular plugin architecture. New capabilities (desktop testing, richer reporting, multi-sandbox, performance, security testing, etc.) are addable without rewriting the core.
- **FR-PLUG-2:** Plugins can be toggled.
- **FR-PLUG-3:** Dynamic framework switching via settings (Playwright default/ready; Selenium/Cypress selectable stubs return not-implemented on run — full runners later).

### 3.10 Settings and Local Store
- **FR-SET-1:** All user settings, credentials, orb presets, and layout live under the local app data directory (`%LOCALAPPDATA%\ai_testing_app\`). Never committed to git.
- **FR-SET-2:** Document ingestion proposes settings; user must confirm before they are written.
- **FR-SET-3:** **App Settings** (connectors, Jira URL, credentials status, **App area layout**, configuration for other areas) is a **dedicated App area screen** — separate from **Orb settings** (FR-UI-3) in the Screen drawer. App → Settings is main application configuration, not orb visual controls. The layout control lists overlay, stage, orb hub, split, and floating.

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

**Maturity:** Prototype (2026-11-16). Baseline plugins and desktop shell exist; in-app plan/suite and the daily test-all path are the active CR track (`docs/ops/test_all_catalogue.json`, epics A–H).

**Already present (prototype baselines)**
- Ollama tool-calling agent with clarification and sessions (default `qwen2.5-coder:7b`; also `qwen3:8b` / `llama3.2` on D:).
- Playwright runner with click + fill locator self-heal (assertions never auto-healed), heal proposals/audit log, and evidence.
- Step generation + quality (KAN-57): `generate_playwright_steps` / `playwright_steps.py` builds happy + negative drafts with `expect_text`/`expect_url`; visibility-only drafts flagged/rejected; failure screenshots always; success evidence via `playwright_success_evidence`.
- Jira plugin (list/create/transition/comment; writes need confirm) against live project **KAN**; write audit; 429 backoff; jira_project default; read_issue.
- Local settings store (`%LOCALAPPDATA%\ai_testing_app\`); OFFICIAL/SECRET isolation; GDPR wipe.
- FastAPI backend + Gradio UI + native desktop window with WebGL hero orbs (mystic/aether/neural/apex); HUD widgets; App area layouts.
- Reports exporter with customisable sections (summary / stories / bugs / evidence; KAN-51).
- Desktop `.exe` plugin, multi-sandbox local records, framework switch stub, document ingest, busy/cancel UX.
- Cursor ops (rules, agents, skills), Advisory Council Room, `docs/ops/WORK_LOG.md` handoff, multi-audience KAN backlog (epics KAN-20…29 + Test-all A–H).
- Tests for core pieces.
- Repo on `D:\Projects\ai_testing_app`; Ollama on `D:\Program Files\Ollama`.

**Still open / next:** Test-all catalogue — alpha **A2–A9** (A1 plan model shipped **KAN-125**). Voice **KAN-81** deferred (mic; later plugin G10). Cut nothing; sequence plugins in epics G–H.

Rule: a Done Story covers only what it actually shipped (baseline). New FR-CONN / FR-PLAN / FR-CI / FR-MAN work lives on Test-all Stories. Seed via `scripts/jira_kan_seed_test_all.py`.

### FR → ticket coverage matrix

| FR | Implementation status | Primary ticket(s) |
|----|----------------------|-------------------|
| FR-AGENT-1…5 | Shipped (chat/sessions/clarify/confirm/errors + busy/long-run UX) | **Done** KAN-8; **Done** **KAN-97** |
| FR-AGENT-6 | Shipped (JSON-in-text fallback + grounded replies) | **Done** **KAN-61** |
| FR-LEARN-1, FR-LEARN-5, FR-SET-2 | Shipped (ingest propose+confirm) | **Done** KAN-45 |
| FR-LEARN-2, FR-LEARN-3 | Shipped (Settings + API + agent; level-scoped) | **Done** **KAN-77** |
| FR-LEARN-4 | Shipped (jira_project default + Settings field) | **Done** **KAN-93** |
| FR-TEST-1 | Shipped (chat/spec + from Jira AC) | **Done** KAN-57; **Done** **KAN-85** |
| FR-TEST-2 | Done (headed + headless setting) | **Done** KAN-9 baseline; **KAN-83** headless mode |
| FR-TEST-3 | Done (smoke + structured steps) | **Done** KAN-47 smoke; **KAN-87** steps (`wait_window`/`type_text`/…) |
| FR-TEST-4, FR-TEST-6 | Shipped (evidence + negatives/quality) | **Done** KAN-57 |
| FR-TEST-5 | Shipped baseline import/run; in-suite import deepen | **Done** **KAN-59**; Test-all **C8** |
| FR-CONN-1 | Open (test-all) | Test-all **A2**, **A3**, **D3**, **D4** |
| FR-PLAN-1…2 | Partial (A1 model) | **KAN-125** store + API; edit/run UI later A5/A7 |
| FR-PLAN-3…4 | Open (test-all) | Test-all epic **A** then **B–C** |
| FR-CI-1 | Future (design) | Test-all **H2** |
| FR-MAN-1 | Future (design) | Test-all **H1** |
| FR-HEAL-1,3,4,5 (+ locator heal) | Shipped policy + click/fill | **Done** KAN-14, **KAN-49** |
| FR-HEAL-2 | Shipped review UI (approve/reject; no auto-commit) | **Done** **KAN-75** |
| FR-JIRA-1 | Shipped (list + read_issue + UX) | **Done** KAN-12 list; **KAN-85** `read_issue`/gen; **KAN-89** agent tool + `/api/jira-issue` + App Settings Read story |
| FR-JIRA-2, FR-JIRA-3 | Shipped (create_test + update_status confirm) | **Done** **KAN-65** |
| FR-JIRA-4 | Shipped (create_bug + confirm) | **Done** KAN-63 |
| FR-JIRA-5, FR-JIRA-7 | Shipped confirm + local creds + write audit | **Done** KAN-12, **KAN-16**, **KAN-99** |
| FR-JIRA-6 | Shipped (429 Retry-After backoff + readable auth/rate-limit errors) | **Done** **KAN-91** |
| FR-REP-1 | Shipped (stories covered + bugs by story/area) | **Done** **KAN-67** |
| FR-REP-2 | Shipped | **Done** KAN-51 |
| FR-REP-3 | Shipped baseline export | **Done** KAN-11 |
| FR-SEC-1, FR-SEC-3, FR-SEC-5 | Shipped isolation + confirm + secrets scoping | **Done** KAN-15, **KAN-16** |
| FR-SEC-2 | Done | **KAN-69** |
| FR-SEC-4 | Done | **KAN-71** |
| FR-UI-1…5 | Baseline shipped | **Done** KAN-10/41/53/73; Voice **KAN-81** deferred (mic; last) |
| FR-UI-6 | Baseline Security + Reports widgets; role packs later | **Done** **KAN-103** / **KAN-107** / **KAN-104**; Test-all **F1–F7** |
| FR-UI-7 | Dedicated surfaces + layout A–E + hub + overlap fix | **Done** **KAN-103** / **KAN-104** (desk22g) |
| FR-SET-3 | Shipped — App Settings screen vs Orb settings (Screen drawer) | **Done** Task **KAN-108** under KAN-103 |
| FR-PLUG-1 | Shipped registry + local multi-sandbox orchestration | **Done** KAN-55 stub + **KAN-95** (test **KAN-96**) |
| FR-PLUG-2 | Shipped toggles | **Done** KAN-47/55 toggles |
| FR-PLUG-3 | Stub shipped (Playwright default; others not-implemented) | **Done** **KAN-79** (test **KAN-80**) |
| FR-SET-1 | Shipped local store | **Done** KAN-16 |

**Open product track:** Test-all Stories A1–H3 (see catalogue / Jira epics “Test-all A–H”). Voice **KAN-81** / **KAN-82** deferred. FR gap pass KAN-83…KAN-99 is **Done** as baselines.

**Recently done** — prototype baselines (not product-complete). See matrix and WORK_LOG.

---

## 6. Open Items and Dependencies

| Item | Status | Notes |
|------|--------|-------|
| Jira account | **Live** | [ai-testing-lab.atlassian.net](https://ai-testing-lab.atlassian.net), project **KAN**. Credentials in local settings only; agent writes still two-step confirm. |
| Real credentials | Local store only | Never in chat or repo |
| Test-all in-app plan/suite | **Active CR** | Catalogue A–H; alpha A1–A9 first |
| Voice input | Deferred | **KAN-81**; mic; later G10 |
| Model tool-calling reliability | **Done** baseline | **KAN-61** |
| Self-healing guardrails (policy) | **Done** (KAN-49) | Review UI **Done** (KAN-75) |
| Security isolation | **Done** (KAN-15) | GDPR **KAN-69**; prompt-injection **KAN-71** |
| Document ingestion | **Done** baseline (KAN-45) | Deepen via FR-PLAN-3 / E1 |

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
10. The linked **test** ticket (`issuetype=test`, Relates) has verification evidence (e.g. pytest command + result) and is marked Done.

---

## 8. References

- Original vision chats (share links provided by user)
- `PROJECT_MEMORY.md` and `docs/ops/ROADMAP.md` in the repository
- Research summaries on vibe-coding failure modes, self-healing risks, Ollama tool-calling issues, and Jira rate limits (incorporated into NFRs and guardrails above)

---

*This specification is intended to be living. It is the **canonical product spec in the repo** (`docs/FUNCTIONAL_SPEC.md`). Jira KAN tickets inline FR text from here — they are not a second source of truth. When the human issues a change request (CR), update this file first, then refresh related KAN tickets (and `PROJECT_MEMORY.md` / `ROADMAP.md` / `WORK_LOG.md` as needed) so agents, testers, and the app never read stale requirements.*