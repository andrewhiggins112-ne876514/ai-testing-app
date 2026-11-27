# Functional Specification — AI Testing Application

**Version:** 1.1  
**Date:** 2026-11-16  
**Status:** Living — prototype toward test-all (CR 2026-11-16)  
**Sources:** Original vision, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, Council CR catalogue `docs/ops/test_all_catalogue.json`, codebase, research into common failure modes of vibe-coded / AI-agent applications.

---

## 1. Purpose and Vision

A **downloadable, local-first “test all” application** for **enterprise QA teams and home / indie / vibe developers**. A person installs it on Windows, enters connection details once (optional Jira, target URL / exe, documents, security level, LLM — local Ollama by default, optional BYOK cloud agents on **PERSONAL**), and does their testing work **inside the app**.

The **primary surface** is the desktop **orb + chat home** (one home for everyone). Role-specific needs (tester, manager, release, product owner) are **HUD widgets** on that home (Screen drawer), not separate homes. App areas (Plan/Suite, Settings, Heal, Reports, Security, Documents, Desktop, Suites, Sandboxes, …) are dedicated full-window surfaces opened from home.

**Primary artifacts** are the **in-app test plan and suite** (viewed and run in the application). An existing Playwright git repo can be **imported** as an input; it is not the primary UX. Pipelines / CI are a **separate later section**. Manual session recording (**Charter Frame**) is specified under FR-MAN-1 / `docs/design/H1_MANUAL_SESSION_CAPTURE.md` §9 — **MVP shipped** (KAN-277); remaining FR-MAN-1 completion is **Council Track 2** Build stories. Live on-screen AI circles are FR-MAN-2 (parked; DPIA).

The agent is the way in: clarify before acting; draft plans from **one Jira story or a whole Jira project** (epics, stories, tests, bugs) plus **uploaded documentation**; run a **single case** or a selected set; show failures, evidence, metrics; export management reports with chosen sections. Jira writes stay human-confirmed. Start with common practice (Playwright, Jira, browser apps), then widen via **plugins** (desktop AUT, other frameworks, sandboxes-as-env, voice, a11y, perf, …). **Cut nothing** already in the product — sequence and deepen; park means later phase/plugin.

**Maturity (2026-11-16):** the shipped tree is an honest **prototype** (baseline plugins + shell). Done KAN tickets are baselines toward this vision, not a finished product. Active product track: Test-all epics A–H in `docs/ops/test_all_catalogue.json`.

**Core value proposition**
- Connect once; work entirely in-app (plan → suite → run → evidence → report).
- Generate and run tests from specs, Jira (story or project), or imported Playwright suites.
- Self-heal broken locators without weakening assertions (human review).
- Bi-directional Jira integration (read, create tests, update status, raise bugs) with confirm on writes; Xray-shaped sync later if needed.
- **PERSONAL / OFFICIAL / SECRET** isolation; local / on-prem (Ollama default; no mandatory cloud; BYOK cloud LLMs only on PERSONAL).
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
| Home / indie / vibe developer *(CR 2026-11-26)* | Buy or download the app for personal projects; strong agent when needed; minimal setup | Enterprise-only UX; 7B local limits; no BYOK; forced OFFICIAL/SECRET framing; empty desks without fixtures |

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
- **FR-LEARN-1:** Accept functional specifications (text, Markdown, PDF) and extract expected behaviour / test ideas. **Deepen (CR 2026-11-26):** ship a **Documents demo pack** (synthetic functional spec + user guide, varied cases) installable into the active level so Documents → draft plan is demonstrable without empty uploads — never real customer/employer docs.
- **FR-LEARN-2:** Accept target application path (`.exe`) or URL.
- **FR-LEARN-3:** Accept additional endpoints / messaging URLs (e.g. RabbitMQ JSON payloads).
- **FR-LEARN-4:** Accept Jira URL + project key so the agent can read epics and stories.
- **FR-LEARN-5:** Document ingestion must propose settings (URLs, credentials, API endpoints) and require explicit user confirmation before storing them. No silent storage of extracted data.

### 3.3 Test Generation and Execution
- **FR-TEST-1:** Generate test cases / steps from functional specs and/or Jira stories.
- **FR-TEST-2:** Execute browser tests via Playwright (headed or headless). First-class support for Playwright; other frameworks as plugins later.
- **FR-TEST-3:** Execute desktop tests via a separate plugin (do not fork the Playwright runner).
- **FR-TEST-4:** Capture screenshots / evidence on failure and success where useful. **Deepen (CR 2026-11-27 — Designer after OPERATE-2 walkthrough; Council agreed 2026-11-27; Studio+Council pick 2026-11-27):** after a run, the person must see a **readable step-by-step action narrative** (what the runner did: goto / click / fill / expect… with pass/fail per step in plain language — not raw JSON soup). **Evidence is first-class for fails and passes:** at least one real screenshot (or clear “none captured” reason) for failed runs — **never a fabricated / placeholder green image**; **success evidence on by default for smoke / golden-path demos** and configurable off for other runs (many enterprises require proof of pass, not only fail). **Case aside (KAN-496):** status → plain steps → **one representative** captured page (or honest none) → Open Trace (external). **Plans deep view (KAN-498):** thumb expand and **More evidence** open an in-area stage (selectable steps, large PNG or honest empty, captured-pages strip only); Back to case returns; Cases list stays; no new App nav item. Forensic DOM/network/console stay in external Playwright Trace Viewer via Open Trace (OPERATE-1) — **do not embed** Trace Viewer; **do not** open traces via `trace.playwright.dev`. Evidence list/open respects the **active security level** (no cross-level paths). Theme/orb/home/App nav stay locked.
- **FR-TEST-5:** Support existing Playwright suites (import and run). Import can be shown as cases in the in-app suite (FR-PLAN-2); the external project files are not deleted; `npx` run remains available.
- **FR-TEST-6:** Negative tests and edge cases must be first-class. The agent must not optimise only for the happy path. Generated tests that only check visibility or nearby elements without asserting the actual expected outcome are incomplete.

### 3.3a Connection, in-app plan / suite (test-all)
- **FR-CONN-1:** The person can save a connection profile: optional Jira site and project, target URL, optional desktop path and messaging endpoint, security level, optional documents, and the **agent LLM** to use. **Default agent runtime is local Ollama** (model picker). **Deepen (CR 2026-11-26 — home/vibe):** on **PERSONAL** only, the person may **BYOK** (bring your own key) for cloud agent providers — at minimum **xAI/Grok**, OpenAI, Anthropic, OpenRouter, and a generic OpenAI-compatible base URL + model id. Keys are level-scoped, never shown in full, never committed. **OFFICIAL and SECRET refuse cloud LLM keys and refuse routing prompts to cloud LLMs.** First outbound cloud agent call on PERSONAL requires explicit confirm (or sticky level consent). Health check reports Jira / Ollama / cloud-provider reachability without printing secrets. Jira remains optional for home onboarding.
- **FR-PLAN-1:** The app holds a **test plan** (intent, sources, links to Jira keys and documents) that the person can view and edit before a run. Plans are stored as **local JSON files** under `%LOCALAPPDATA%\ai_testing_app\plans\{PERSONAL|OFFICIAL|SECRET}\` — **not** an internal SQL database. **Deepen (CR 2026-11-26):** provide a **user-friendly full plan document view** (readable narrative of intent, cases, tags, last results — not only scan-table + form fields).
- **FR-PLAN-2:** The app holds a **suite** of cases and runs them **inside the app**. The person can run one case or a selected set (e.g. by tag). Cases can be reordered, disabled, archived, tagged, and prioritised without deleting history.
- **FR-PLAN-3:** The agent may draft or update a plan from one Jira issue or, in the project-scale phase, from the connected Jira project (epics, stories, tests, bugs) plus uploaded documents. Drafts are batched with a visible cap. The person reviews the plan before execution. Jira writes stay on FR-JIRA-5.
- **FR-PLAN-4:** A run stores result, evidence, duration, and failure class on the case. Heal proposals and report sections can attach to that run. Traceability links case ↔ Jira key ↔ bugs ↔ known issues. **Deepen (CR 2026-11-27):** the stored run must retain **ordered step outcomes** (action, status, short human label, error snippet) so Case detail and Reports can show a narrative timeline; evidence paths (screenshot, trace.zip) stay linked on the same run. The run **may also store per-step screenshot refs** (path or none). The Case aside still shows **one** representative shot (or honest none); the deep-view story reads the per-step list.
- **FR-CI-1 (later):** Pipelines and CI live in a **separate section** of the app. They do not replace the in-app suite as the place tests are authored and reviewed. **H2 design (KAN-243):** `docs/design/H2_PIPELINES_SECTION.md` — what a pipeline record shows, what it will not do, secrets stay local; **no CI integration ships until a later Build story**.
- **FR-MAN-1:** A manual / exploratory session starts only on explicit Start (charter). Capture is a calm resizable **snip-style Charter Frame** over a free screen region (B1); **window/monitor snap** is part of FR-MAN-1 completion (not MVP). Evidence: timestamped notes (default on) + **opt-in** stills inside the frame (annotate-still supported); page URL/title when a headed AUT context is already known; no keylog, clipboard, mic, or silent video. **Agent assist** is a session toggle (recommended default **off**) so testers can record without AI; when on, AI must keep **real local unpublished** step/bug drafts (Ollama) — never silent Jira; UI must not pretend note-echo is AI. **Armed mist** (light mist inside the frame) is a separate toggle (recommended default **off**) so visuals never block testing. Jira: story key when ticket-bound; test ticket optional (C3). **Charter-only / snip-tool mode (CR 2026-11-26):** the Frame must be usable **without** a Jira key and **without** AI assist — like a snipping tool (still / optional short recording later). The capture chrome must be **draggable across the Windows desktop** (not trapped inside the main pywebview client area). Linking to Jira/AI remains available but optional. **Manual** is a Primary App area and Plans offers a deep-link (A3). End → review → propose bug/comment/step-update → **two-step confirm** (FR-JIRA-5); Confirm/Cancel always clickable. Session library + level-scoped GDPR wipe include Manual sessions. OFFICIAL/SECRET isolation as H1 §5. Design: `docs/design/H1_MANUAL_SESSION_CAPTURE.md` (KAN-241 design-Done; **MVP Done KAN-277**; **completion = Council Track 2 Build stories**). *(Council CR 2026-11-18 Track 1; Council CR 2026-11-18 Track 2.)*
- **FR-MAN-2 (parked):** Live / sparse on-screen assist (click-through circles citing AC/spec, event-driven region analysis). Requires DPIA + separate stories after FR-MAN-1 **completion** ships. Not Cursor Computer Use mist as product chrome. See H1 §10.

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
- **FR-REP-1:** Generate reports with metrics such as tests passed/failed, stories covered (by Jira key), bugs raised per story or functional area, progress, etc. **Baseline today:** metrics appear in markdown/JSON exports and HUD chips. **Deepen (CR 2026-11-26):** the Reports area must grow into a **visual analytics surface** (charts/graphs for pass-fail trends, coverage, duration, failure classes, bugs-by-story) suitable for a test-all / enterprise desk — not markdown-only. Charts consume local run data only; no telemetry cloud.
- **FR-REP-2:** Reports are customisable — user chooses which sections to include or exclude. Section include/exclude is **Report Settings** (FR-SET-4), applied to the next JSON/Markdown export — not the primary content of the Reports area. *(CR 2026-11-17 — content vs settings.)*
- **FR-REP-3:** Reports can be exported (current exporter exists; polish later). Export remains available alongside in-app charts.
- **FR-REP-4:** The **Reports** area lists and opens saved reports for the active security level (markdown detail, screenshot, raw JSON as available). Empty state explains how a run produces a report. A deep link opens Settings → Report. The Reports surface does **not** host the section-include editor. *(CR 2026-11-17.)* **Deepen (CR 2026-11-26):** detail view adds chart panels fed by the same local report/run JSON; markdown remains a section, not the only view.

### 3.7 Security and Isolation
- **FR-SEC-1:** Support three isolated levels via credentials, browser profiles, plans, and settings scopes: **PERSONAL** (lowest — home / indie / vibe), **OFFICIAL** (UK workplace baseline), **SECRET** (highest). Stores must never mix. **PERSONAL** may use BYOK cloud agent providers (FR-CONN-1). **OFFICIAL** and **SECRET** keep local Ollama as the only agent LLM path (no cloud LLM keys). SECRET keeps the narrowest tool surface (FR-SEC-4). *(CR 2026-11-26 — home market + prior OFFICIAL/SECRET baseline.)*
- **FR-SEC-2:** No telemetry by default. Easy local data deletion. Explicit consent before storing extracted data (**GDPR** / UK data-protection baseline). Cloud BYOK on PERSONAL is **user-initiated outbound**, not product telemetry.
- **FR-SEC-6 (compliance roadmap, CR 2026-11-26):** Beyond GDPR + classification isolation, plan and progressively evidence controls for enterprise **and** serious home buyers — **ISO/IEC 27001**-aligned themes, **UK Cyber Essentials**, and a **SOC 2** crosswalk (access control, audit logging, encryption at rest for secrets, change/confirm gates, backup/restore, secure configuration, no-telemetry stance). **Not** a certification claim. Matrix design = first deliverable (`docs/ops/ENTERPRISE_GAP_RESEARCH.md`).
- **FR-SEC-3:** Security-level switcher is available and changes take effect only after confirmation. Switching into PERSONAL shows that cloud BYOK becomes available; switching into OFFICIAL/SECRET warns that cloud LLM keys will not be used.
- **FR-SEC-4:** Prompt-injection mitigations:
  - Treat all external content (uploaded specs, Jira descriptions, web pages, tool outputs) as untrusted.
  - Narrow tool surface by default. High-privilege tools (file system outside workspace, network, shell) require confirmation or are disabled in higher security levels.
  - Prefer models and configurations that reduce injection success on smaller local models.
- **FR-SEC-5:** Secrets never leave the local settings store or are written to client-side code / logs.

### 3.8 UI and Desktop Experience
- **FR-UI-1:** Conversational interface is primary on the **agent home screen** (chat + central orb). **One home for everyone** — there is no separate Tester/Manager/PO landing. App menu and screen drawer are secondary shells for navigation and layout — not replacements for the home canvas. App areas open from a **compact App menu**: `▦` button toggles a small App panel (nav list only) with two groups — **Primary** (Chat, Settings, Plans, **Manual**, Reports, Documents) and **Lab tools** (Security, Heal review, Desktop, Suites, Sandboxes; FR-UI-8); choosing an item closes the panel and opens the dedicated area surface (FR-UI-7). **Manual** owns Charter Frame session UX (FR-MAN-1); Esc/Back returns to orb home — Manual is not a second landing. Plans keeps a **Start manual on this case** deep-link. A **tall persistent App side drawer** and a **persistent top tab bar** are not app navigation. *(CR 2026-11-17 menu button; CR 2026-11-17b — desktop matches Gradio compact menu; CR 2026-11-17c Lab tools; Council CR 2026-11-18 Manual Primary A3.)*
- **FR-UI-2:** Native Windows desktop window (pywebview + Edge WebView2) is the **primary product UI**. The app is intended for desktop use, not as a browser product. Gradio (`run_ui.py`) remains a secondary lab/dev shell and must follow the same **compact menu-button navigation** and **content-vs-settings** split (FR-UI-7, FR-SET-4, FR-REP-4). Gradio does **not** have to implement desktop area layouts A–E. *(CR 2026-11-17b — desktop-first.)*
- **FR-UI-3:** Visual orb styles (Mystic, Aether, Neural, Apex and classic canvas styles) with per-style settings, live controls, and theme accent that follows the active style. **Orb settings** (style, size, spin, glow, colours) live in the **Screen drawer** only — not under App → Settings. The active style accent (CSS variables such as `--cyan`, border, glow, and muted text) also paints App nav, area surfaces (overlay, stage, split, floating), HUD chips, hub spokes, and the App Settings layout picker — not only the orb canvas. *(CR 2026-11-16 — layout modes × style theme.)*
- **FR-UI-4:** Movable / resizable panels and widgets (UI-6). Layout persists in localStorage.
- **FR-UI-5:** Widget settings (transparency, border, background) apply live to shell surfaces.
- **FR-UI-6:** **Agent-home HUD widgets** — optional toggleable widgets on the agent home screen (status chips, mini panels, role packs for tester / manager / release / coverage, checklist, etc.). Visibility and layout controls sit alongside existing Screen drawer toggles (chat output widget, orb visibility, widget chrome) — not as App → Settings list content. Widgets summarise and deep-link into App areas; they do not replace Plan/Suite, Reports, Heal, or Settings surfaces.
- **FR-UI-7:** **Dedicated area screens** — each App-nav area (Settings, Security, Reports, Documents, Desktop, Suites, Sandboxes, Plans, Manual, Heal review, and future areas) opens its own **dedicated surface**. The App menu panel is a **compact navigation list only**; it must **not** expand inline `app-section-*` blocks and must **not** remain a full-height side rail while an area is open. **App area layout** (App Settings, not Orb settings) chooses how that surface appears, persisted in `localStorage` key `desktop-area-layout-v1`:
  - `overlay` — full-bleed glass over a dimmed home (mockup A)
  - `stage` — area stage with the orb scaled to a corner pip (mockup B)
  - `orb_hub` — orb click shows spokes, then the area opens as an overlay (mockup C)
  - `split` — docked panel beside the home orb; Esc closes it (mockup D)
  - `floating` — one movable area window; the orb stays full size (mockup E)
  Esc or Back returns home. Accents follow the active orb style (FR-UI-3). *(Product decision 2026-11-16 — configurable A–E, not a single mockup pick.)* An area surface shows that area’s **content** (lists, viewers, run results, proposals). **Configuration** for the area lives under Settings categories (FR-SET-4), with a deep link from the area. *(CR 2026-11-17.)*
- **FR-UI-8:** **Lab tools navigation** — Security, Heal review, Desktop, Suites, and Sandboxes remain dedicated area surfaces and must be reachable from home in **every** App area layout (not only when layout is `orb_hub`). Default placement: a **Lab tools** group inside the compact App menu under the Primary group (still a popover, not a tall rail). Orb-hub spokes may mirror these as accelerators when layout is `orb_hub`. Gradio need not expose every Lab tool. *(CR 2026-11-17c; KAN-260.)*
- **FR-UI-9 (Plans IA + area chrome):** Plans area uses progressive disclosure — default landing is **Cases** for the open plan (not Draft/Schedule). **Area chrome** (plan picker, open/refresh/search, one-line status, and the same pattern on Suites / Reports / Manual / Lab) is a **non-overlapping header** outside the scrollport (or equivalent geometry): primary fields, section tabs, and primary buttons — including Confirm/Cancel — must stay fully visible and clickable; chrome must **not** cover the work surface. `position: sticky` inside a scrolling `.area-body` is **not** required and must not be used if it occludes content. Sections/tabs: Draft & import; Cases; Coverage & drift; Traceability; History; Run setup. One **Add case ▾** menu (not a button farm). Lab knobs (env manage, sandbox manage, schedule detail) live under Settings / Lab / collapsed Run setup — not the forever-scroll. *(Council CR 2026-11-18 Track 1 D1; Council CR 2026-11-18 Track 2 — non-overlap.)* **Note:** Track 2 tokens (**KAN-297**) wired type/spacing variables only — they do **not** satisfy visual density redesign (that is **FR-UI-10**).
- **FR-UI-10 (Enterprise area density — Track 3):** Primary App areas (Settings, Plans, Manual, Reports, Documents) use **accepted Track 3 wires** for real geometry — not token-only CSS. Shared non-scrolling chrome stack: surface bar + one toolbar + optional section tabs; common-case chrome ≤ ~120px; work content scrolls in `.area-work`. Filter/search live in that one toolbar (no second filter strip; class/marker names must not say sticky). Plans · Cases matches the enterprise Cases wire (Cases default; one Add case ▾). Manual Confirm/Cancel stay fully visible on their dock. Settings and Security use the same outside-scrollport chrome; classification and credential controls stay readable; OFFICIAL/SECRET stores stay unmixed. Density must hold in **all** App area layout modes A–E (overlay, stage, orb_hub, split, floating — FR-UI-7). Source density note: `docs/design/ENTERPRISE_LAYOUT_NOTE.md`; wires pack: `docs/design/TRACK3_AREA_WIRES.md`. **Hard accept gate:** no HTML/CSS geometry Build until Designer accepts the Slice-0 wires pack. Orb home, compact ▦ App menu, system fonts, orb accents (FR-UI-3) unchanged. Lab tools (Security chrome alignment may ship with Settings; Heal/Desktop/Suites/Sandboxes full density) are follow-on epic **KAN-359** (TRACK3-LAB Bridge 2026-11-23) after Primary Track 3 — Lab wires in `docs/design/TRACK3_AREA_WIRES.md` §8; Designer `Accept Lab wires` before Lab geometry. *(Council CR 2026-11-18 Track 3 — Designer confirm: wire accept yes; Primary-first yes; verify all A–E; Lab Bridge 2026-11-23.)*
- **FR-UI-11 (Secondary area layout grammar — Studio 2026-11-21):** Inside dedicated App areas (FR-UI-7), list-heavy work surfaces use a shared **layout grammar** — **structure, not skin**. Theme tokens, orb styles, home/chat chrome, and App nav stay locked. **Grammar:** (1) **In-area section rail** (or equivalent section tabs inside the area chrome — not new App nav items) for Settings sections such as Layout, Connections, Environments, Model & runner, Report blocks, Credentials; Security remains its own App area. (2) **Compact scan table** for collections — scannable columns (e.g. Status · Name · Target); multi-select uses a **dedicated checkbox cell** (~28px; click stops on the control); **row click focuses / opens detail** — never toggles selection via the whole row. (3) **Detail pane** holds fields and primary save; **destructive** actions (delete env, clear credential) sit in the detail behind confirm — not on list-row chrome. Single booleans are compact section checkboxes, not page-width `.check-row` toggles. **Settings is the system template** (mockups: `docs/mockups/settings_layout_grammar/`). **Inheritance (shipped TRACK4-LAYOUT):** Suites — Sel · Status · Title · File · Last + detail (no section rail). Plans · Cases — scan table; row fills the existing edit form in the detail pane; plan tabs stay FR-UI-9; Coverage / Trace / History (A/B radio cells) / Draft / Run follow the same grammar. Reports — When · Title · Level · Kind + detail (no checkboxes). Documents — Propose | Uploads tabs; Keep cell; Confirm/Decline outside the scan. Security — in-area rail (Level · Privacy · Audit · Redaction · Backup); Include cell; propose-then-confirm. Heal — Sel · Class · Locator · Run · When; Approve/Reject on focused detail; bulk Approve selected behind confirm (no bulk Reject). Manual — session scan; compact start checks; Confirm dock outside `.area-work`; Charter Frame untouched. Desktop Lab — Enabled · Status · Path · Last smoke (Enabled is the hit cell). Sandboxes Lab — Id · Label · URL · Ready; Remove behind confirm in detail. Mockups: `docs/mockups/suites_plans_layout_inherit/`, `docs/mockups/secondary_areas_rest/`. **Still deferred (not this FR’s TRACK4 scope):** TRACK3-LAB Lab density; voice (KAN-81/82); FR-MAN-2. Rejected: KPI/card dashboards; “tighter single scroll” without hierarchy/hit-target fixes. Density for power users; no pretty-empty heroes. *(Studio CR 2026-11-21 — Designer accepted Intent + Bridge; TRACK4 inheritance Done through KAN-345 / desk118; Studio+Council catch-up 2026-11-22.)*
  - **FR-UI-11 enhancement (TRACK5-LAYOUT — Studio+Council Bridge 2026-11-22):** After TRACK4 grammar, every secondary App area also provides: (a) a **quiet empty** one-line state (no KPI/hero cards; no secrets in copy); (b) an unfocused detail placeholder **“Select a row”** (primary Save/Run/Confirm not armed as if focused); (c) a **keyboard scan contract** — Up/Down move the focused row, Enter focuses detail, Esc returns to the scan; shortcuts **never** confirm Jira, approve/reject heal, delete, restore, or remove; Space toggles only when focus is on the checkbox cell; (d) **one scroll per pane** with the scan header sticky inside the scan scroller (`.area-work` must not add a third scroll fighting the split); (e) **Plans** residual compact booleans (Show archived, Enabled, Archived, Pause on fail) and case-detail **sections** (Edit / Run / Quarantine / Known issue) with Save/Run pinned; (f) **Documents** tab-scoped toolbar (Propose = Parse; Uploads = Refresh); Confirm/Decline stay off the scan row; (g) **Heal** Approve-selected confirm names the count and states files are not written — **no bulk Reject**; (h) **Lab** detail disclosure for secondary fields on Desktop / Suites / Sandboxes (not TRACK3-LAB density); (i) optional Suites/Reports **filter in the existing toolbar only**. **Phase 2 (later story):** evidence-first detail slot on run-bearing rows; Trace copy must state runner capture is not hooked — do not fake a Playwright trace. Mockups: `docs/mockups/layout_enhancement_pack/`. Theme/orb/home/App nav stay locked.

### 3.9 Plugins and Extensibility
- **FR-PLUG-1:** Modular plugin architecture. New capabilities (desktop testing, richer reporting, multi-sandbox, performance, security testing, etc.) are addable without rewriting the core. **Sandboxes (clarified CR 2026-11-26):** product sandboxes are **local / internal** environment records + isolated browser profile dirs under the app data tree (prepare/status/orchestrate on this PC). They are **not** cloud device farms or third-party hosted sandboxes. External/remote sandbox providers remain a future plugin if ever needed — never pretend local records are remote farms.
- **FR-PLUG-4 (new — stub deepen, CR 2026-11-26):** Every framework/plugin stub that remains in the product (Selenium, Cypress, a11y, perf, …) must be **deepened into real or rich demo behaviour** over time — not left as eternal `not_implemented`. Until a runner is real, the UI may keep an honest stub **only if** Lab/fixtures supply **good, varied synthetic test data** so desks are not empty walls. Prefer deepen; never fake pass.
- **FR-PLUG-2:** Plugins can be toggled.
- **FR-PLUG-3:** Dynamic framework switching via settings (Playwright default/ready; Selenium/Cypress selectable stubs return not-implemented on run — full runners later). UI must label stubs honestly (`not implemented` / never pass), **disable Run** for non-ready frameworks, and **never default** the Plans framework control to Selenium/Cypress. Cut nothing — deepen runners later. *(Council CR 2026-11-18 stub honesty.)*

### 3.10 Settings and Local Store
- **FR-SET-1:** All user settings, credentials, orb presets, and layout live under the local app data directory (`%LOCALAPPDATA%\ai_testing_app\`). Never committed to git.
- **FR-SET-2:** Document ingestion proposes settings; user must confirm before they are written.
- **FR-SET-3:** **App Settings** (connectors, Jira URL / project, Ollama model, test framework, Playwright headed/headless, **App area layout**, credential *status*) is the **App** category on the Settings hub — separate from **Orb settings** (FR-UI-3) in the Screen drawer / gear. Secrets never render. The layout control lists overlay, stage, orb hub, split, and floating. App Settings is **not** every area’s toggles dumped into one scroll. *(CR 2026-11-17.)*
- **FR-SET-4:** **Settings hub** — one Settings surface with navigation that stays on Settings. Prefer the **FR-UI-11 in-area section rail** (Layout, Connections, Environments, Model & runner, Report blocks, Credentials) over a flat App/Report tab plus undifferentiated `h4` stack; Report section include/exclude for the next export remains under Settings (FR-REP-2), not the Reports area. Security level confirm and GDPR local-data delete stay on the **Security** area (may be linked from Settings). Plugin / suite / sandbox enable flags may move into further sections in follow-on stories. Selection and destructive controls follow FR-UI-11 grammar. *(CR 2026-11-17; Studio CR 2026-11-21 — layout grammar.)*

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
- Isolation for PERSONAL / OFFICIAL / SECRET; cloud LLM BYOK gated to PERSONAL only.

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

**Still open / next:** Layout Tracks 1–5 + TRACK3-LAB + TRACE-DEEPEN + OPERATE-1..4 Done as **baselines**. Run-evidence CR Done: Option A **KAN-496**/497 + deep view **KAN-498**/499. Reports charts **KAN-384**/385 Done. Manual OS float snip **KAN-386**/387 Done (**desk140**). **Active track = GAP-CR KAN-388** plan document view. **CR backlog (seeded):** plan document view (**FR-PLAN-1**), stub deepen (**FR-PLUG-4**), compliance matrix (**FR-SEC-6**); research adds. FR-MAN-2 live circles parked (DPIA). Voice **KAN-81** deferred (mic). Full CI OAuth / H3 network share / Xray stay later — read-only shells may precede.

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
| FR-TEST-3 | Done (smoke + steps + suite cases) | **Done** KAN-47 smoke; **KAN-87** steps; **KAN-217** desktop-typed cases on same suite |
| FR-TEST-4, FR-TEST-6 | Baseline shipped (evidence + negatives/quality); run-evidence UI deepen **shipped** | **Done** KAN-57 baseline; **KAN-496**/497 Option A; **KAN-498**/499 deep view (**desk136**) |
| FR-TEST-5 | Shipped baseline import/run; in-suite import deepen | **Done** **KAN-59**; Test-all **C8** **KAN-171** |
| FR-CONN-1 | Partial (test-all) | **A2** health **KAN-127**; **A3** model **KAN-129**; **D3** named envs **KAN-183**; **D4** credential status **KAN-185**; **E5** offline last plan **KAN-201** Done |
| FR-PLAN-1…2 | Partial (A1+A5+A6+C11+E5) | **KAN-125** store + **KAN-133** edit/disable/reorder + **KAN-135** starter/empty home + **KAN-177** archive; run UI A7; **KAN-201** offline search/matrix |
| FR-PLAN-3…4 | Partial (A4+C3–C10); FR-PLAN-4 ordered steps + deep view **shipped** | **KAN-131** one story; **KAN-161** project-wide draft; **KAN-163** coverage gaps; **KAN-165** AC drift; **KAN-167** C6 matrix; **KAN-169** C7 tags; **KAN-171** C8 import; **KAN-173** C9 search; **KAN-175** C10 history; **KAN-177** C11 archive Done; **KAN-496** ordered steps + aside; **KAN-498** deep view reads per-step / evidence PNG refs |
| FR-CI-1 | Design done (KAN-243); CI not shipped | Test-all **H2** → `docs/design/H2_PIPELINES_SECTION.md` |
| FR-MAN-1 | Design Done (KAN-241) + MVP **KAN-277**; completion = Track 2 | MVP test **KAN-278**; Track 2 stories complete FR-MAN-1; FR-MAN-2 parked |
| FR-MAN-2 | Parked (live assist / circles; needs DPIA) | H1 §10 — after FR-MAN-1 **completion** |
| FR-SEC-1 (H3 share) | Isolation shipped (KAN-15); multi-PC share **design** done | Test-all **H3** **KAN-245** → `docs/design/H3_SHARED_USE_WITHOUT_CLOUD.md` (no network service) |
| FR-HEAL-1,3,4,5 (+ locator heal) | Shipped policy + click/fill | **Done** KAN-14, **KAN-49** |
| FR-HEAL-2 | Shipped review UI (approve/reject; no auto-commit) | **Done** **KAN-75** |
| FR-JIRA-1 | Shipped (list + read_issue + UX) | **Done** KAN-12 list; **KAN-85** `read_issue`/gen; **KAN-89** agent tool + `/api/jira-issue` + App Settings Read story |
| FR-JIRA-2, FR-JIRA-3 | Shipped (create_test + update_status confirm) | **Done** **KAN-65** |
| FR-JIRA-4 | Shipped (create_bug + confirm) | **Done** KAN-63 |
| FR-JIRA-5, FR-JIRA-7 | Shipped confirm + local creds + write audit | **Done** KAN-12, **KAN-16**, **KAN-99** |
| FR-JIRA-6 | Shipped (429 Retry-After backoff + readable auth/rate-limit errors) | **Done** **KAN-91** |
| FR-REP-1 | **Baseline** metrics in export/HUD; charts deepen **Done** | **Done baseline** **KAN-67**; charts **KAN-384**/385 (**desk137**) |
| FR-REP-2 | Shipped (placement → Report Settings under FR-SET-4) | **Done** KAN-51; UI move **Done** **KAN-247** / **KAN-249** |
| FR-REP-3 | Baseline export Done; deepen E3 + F6 pack | **Done** KAN-11 baseline; **deepen E3** **KAN-197** (desk63); **F6** read-only pack **KAN-213** (desk72) |
| FR-REP-4 | Reports library/viewer **Baseline**; chart panels in detail **Done** | **Done baseline** **KAN-247**; charts **KAN-384**/385 (**desk137**) |
| FR-SEC-1, FR-SEC-3 | OFFICIAL/SECRET isolation **Baseline**; **PERSONAL + BYOK open** | **Done** KAN-15/16; HOME-MARKET epic for PERSONAL/BYOK |
| FR-SEC-5 | Baseline secrets scoping Done; deepen E3 | **Done** KAN-15/16 baseline; **deepen E3** **KAN-197** (evidence/export redaction — Done desk63) |
| FR-SEC-2 | Done (GDPR baseline) | **KAN-69** |
| FR-SEC-4 | Done | **KAN-71** |
| FR-SEC-6 | Compliance roadmap (ISO27001-aligned themes) | **Open** — design matrix after OPERATE |
| FR-PLUG-4 | Stub deepen + rich fixtures | **Open** — after OPERATE; no eternal empty stubs |
| FR-UI-1…5 | Baseline shipped; UI-1 compact desktop App menu | **Done** KAN-10/41/53/73; Voice **KAN-81** deferred; compact desktop menu **KAN-253** (desk44) |
| FR-UI-6 | Baseline Security + Reports + Lab checklist; role packs later | **Done** **KAN-103** / **KAN-107** / **KAN-104** + **KAN-135** empty-lab checklist; Test-all **F1–F7** |
| FR-UI-7 | Dedicated surfaces + layout A–E + hub + overlap fix; content vs config | **Done** shell **KAN-103** / **KAN-104**; content-vs-config **KAN-247…249** |
| FR-UI-8 | Lab tools group on compact App menu (every layout) | **Done** **KAN-260** (desk64; test **KAN-262**) |
| FR-UI-9 | Plans IA + non-overlapping area chrome | IA tidy **Done** **KAN-265**; chrome non-overlap **Done** **KAN-281** (desk92); layout tokens **Done** **KAN-297** (desk99) — tokens ≠ visual redesign |
| FR-UI-10 | Enterprise area density (real geometry; Primary first; all A–E) | **Primary Done** — **KAN-308…320** + Bug **KAN-323** desk106. **Lab density Done** — epic **KAN-359**; Stories **KAN-360/362/364/366** (+ bugs **368**/370); human A–E **desk131**; Security with Primary **KAN-318** |
| FR-UI-11 | Secondary area layout grammar (rail + scan table + detail; Settings template) | **Grammar Done** — Settings **KAN-324** … Sandboxes Lab **KAN-345**. **Enhancement TRACK5 Done** — Phase 1 **KAN-348…352**; Phase 2 evidence-first **KAN-354** (**desk125** / **KAN-355**). Lab **density** is TRACK3-LAB (**KAN-359**), not this FR’s TRACK4/5 scope |
| FR-UI-1 Manual | Primary **Manual** area (A3) | **Done** — **KAN-275** (desk90; test **KAN-276**); Charter Frame still **KAN-277** |
| FR-MAN-1 implement | Charter Frame MVP + Track 2 completion | MVP **Done** **KAN-277**; completion stories under Track 2 epic; design **KAN-241** |
| FR-PLUG-3 honesty | Stub labels / disable Run / Playwright default | **Done** — **KAN-267** (test **KAN-268**) |
| FR-SET-3 | Shipped — App Settings vs Orb settings; App category on Settings hub | **Done** Task **KAN-108**; hub **KAN-249** |
| FR-SET-4 | Settings hub with category switch (App / Report / …) | **Done** — **KAN-249** (desk42) |
| FR-PLUG-1 | Shipped registry + local multi-sandbox orchestration | **Done** KAN-55 stub + **KAN-95** (test **KAN-96**) |
| FR-PLUG-2 | Shipped toggles | **Done** KAN-47/55 toggles |
| FR-PLUG-3 | Stub + plan-case select (Playwright default; Selenium/Cypress not-implemented, never pass) | **Done** **KAN-79** + **KAN-233** G9 (test **KAN-234**) |
| FR-SET-1 | Shipped local store | **Done** KAN-16 |

**Open product track:** Test-all Stories A1–H3 (see catalogue / Jira epics “Test-all A–H”). Voice **KAN-81** / **KAN-82** deferred. FR gap pass KAN-83…KAN-99 is **Done** as baselines.

**Recently done** — prototype baselines (not product-complete). See matrix and WORK_LOG.

---

## 6. Open Items and Dependencies

| Item | Status | Notes |
|------|--------|-------|
| Jira account | **Live** | [ai-testing-lab.atlassian.net](https://ai-testing-lab.atlassian.net), project **KAN**. Credentials in local settings only; agent writes still two-step confirm. |
| Real credentials | Local store only | Never in chat or repo |
| Test-all in-app plan/suite | **Active CR** | Catalogue A–H designs complete; **Track 1** Plans IA + Charter Frame (Council 2026-11-18); voice deferred |
| Nav IA — Reports data / menu / Settings hub | **Shipped** KAN-247…249 | Gradio + desktop compact menu |
| Desktop compact App menu (match Gradio) | **Shipped** KAN-253 / **KAN-257** | Compact `▦`; Lab tools restored **KAN-260** |
| Coverage gaps (C4) | **Shipped** KAN-163 (desk45) | No-case / all-disabled lists; filter; no auto-create |
| Acceptance drift (C5) | **Shipped** KAN-165 (desk46) | Stale on summary/AC change; Keep/Refresh; runs preserved |
| Traceability matrix (C6) | **Shipped** KAN-167 (desk48) | Story → cases → last result → bugs → known; not_loaded never pass; export section |
| Tags / smoke / regression (C7) | **Shipped** KAN-169 (desk49) | Case tags+priority; sequential run-by-tag; suite_run stores tag; untagged = not_selected |
| Import Playwright into suite (C8) | **Shipped** KAN-171 (desk50) | Project → plan cases (`source=playwright`); npx Suites unchanged; single-case suite run; external files never deleted |
| Search plans / cases / failures (C9) | **Shipped** KAN-173 (desk51) | Matches plan name, case name, Jira key, tag, failure class; active level only; hit opens case |
| Suite history / compare two runs (C10) | **Shipped** KAN-175 (desk52) | Past runs: time, duration, pass/fail, tag; compare changed results; known labelled; level-local |
| Duration on run and case (D7) | **Shipped** KAN-191 (desk60) | Case + suite store duration; compare shows duration change; local only, no upload |
| Archive case without deleting history (C11) | **Shipped** KAN-177 (desk53) | Soft-archive hides from runs/default list; Show archived filter; evidence kept; unarchive restores |
| Sequential default + parallel cap (D1) | **Shipped** KAN-179 (desk54) | Default parallel=1; max 2 visible; suite_run stores count; refuse above cap |
| E3 redact secrets in evidence/exports | **Shipped** KAN-197 (desk63) | Pattern + stored-token redact; hit count; screenshot warn; not a wipe |
| Lab tools in App menu | **Shipped** KAN-260 (desk64) | Primary + Lab tools on ▦; orb hub kept |
| Voice input | Deferred | **KAN-81**; mic; later G10 |
| Model tool-calling reliability | **Done** baseline | **KAN-61** |
| Self-healing guardrails (policy) | **Done** (KAN-49) | Review UI **Done** (KAN-75) |
| Security isolation | **Done** (KAN-15) | GDPR **KAN-69**; prompt-injection **KAN-71** |
| Document ingestion | **Done** baseline (KAN-45) | Privacy uploads **Done** E1 (**KAN-193** desk61) |

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