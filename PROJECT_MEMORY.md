# PROJECT_MEMORY.md
# Persistent memory for the AI Testing Application

Last updated: 2026-11-16 (KAN-93 jira_project default Done; Active → KAN-95)

## Original Vision
A local AI testing agent with a conversational interface. The user talks to it (text first, voice later) to request tests, configure environments, or interpret results. Everything else lives in secondary tabs or settings.

The tool should solve real testing pain for software companies:
- Generate and run tests from functional specs, Jira stories, or existing Playwright suites
- Self-heal when locators break
- Bi-directional Jira/Xray integration (read, create tests, pass/fail, create bugs)
- Test both large browser-based applications and desktop (.exe) applications
- Support UK security levels (OFFICIAL / SECRET) with isolation
- Stay local / on-prem capable (no mandatory API tokens)
- Customisable reporting for management
- Document ingestion that can propose settings (URLs, APIs, credentials) with confirmation

Long-term goal: dominate the testing space for companies that want a capable local/on-prem AI testing tool rather than another cloud SaaS.

## Key Decisions So Far
- Local-first on high-end laptops (home machine for development, work Dell XPS 15s as target).
- Python backend + FastAPI + Gradio UI.
- Ollama for the local LLM. This PC has `qwen2.5-coder:7b` (the default). `qwen3:8b` is still fine via `OLLAMA_MODEL` once pulled.
- Playwright as the first execution engine (browser headed by default; headless via App Settings / run override — KAN-83).
- Modular plugin architecture so features can be toggled and extended later.
- Security context switcher from day one (OFFICIAL / SECRET).
- Agent must clarify ambiguous requests and confirm side-effecting actions.
- Development machine: Windows home PC (i7-8700K, 32 GB RAM, GTX 1080 Ti, Ollama already installed). User is on Python 3.15 (venv notes also mention 3.13 — watch compatibility).
- **Primary IDE workflow is Cursor** (rules, skills, custom agents). Browser Grok + AFK Pilot copy-paste is retired to save Premium credits.
- **PM-owned workflow:** human speaks only in the PM chat. PM implements or delegates agents; human pulls/runs — no paste of coding prompts into other chats.
- Coding models: **prefer free / Auto / Composer** in Cursor. Escalate to stronger models only when needed. Product runtime stays on local Ollama (free).
- Token efficiency matters: prefer targeted reads, compact slices, avoid re-sending full file contents.
- Classic orb styles stay pure canvas. **WebGL / Three.js is allowed** for hero styles (mystic, aether, neural, apex). Vendor Three.js under ui/vendor/ is acceptable for those styles.
- Jira writes are two-step confirm. **Jira is live:** [ai-testing-lab.atlassian.net](https://ai-testing-lab.atlassian.net) project **KAN**; API token + email in local settings only.
- **Canonical paths:** repo `D:\Projects\ai_testing_app`; Ollama `D:\Program Files\Ollama` + `OLLAMA_MODELS`; settings `%LOCALAPPDATA%\ai_testing_app\`.
- **Product spec:** `docs/FUNCTIONAL_SPEC.md` (**canonical in repo**; Jira KAN inlines FR text — keep both in sync on user CRs). **Ticket template:** `docs/ops/JIRA_TICKET_TEMPLATE.md`. **Handoff:** `docs/ops/WORK_LOG.md` + `.cursor/rules/work-log-handoff.mdc`.
- **Local zero-token helpers:**
  - Say “pick up where we left off”, or `python scripts/next_prompt.py`, or copy `docs/prompts/NEXT_PROMPT.md`.
  - Prefer these over waking the Grok guide bot.
- **Ollama in Cursor (parked 2026-11-06):** possible via OpenAI Base URL override to localhost:11434, but unreliable for full Agent mode and requires tunnel for reliability. Revisit only when cloud tokens run out. App runtime already uses local Ollama.
- **Orb styles approved (2026-11-06):** Mystic (cyan filament), Aether (orange plasma), Neural (blue glass bubble), Apex (white-gold core + data streams). See docs/mockups/orb_styles.md. WebGL preferred for these four.
- **Desktop nav model (2026-11-15, KAN-102 CR):** Agent home = chat + orb primary. Mockup side panels = **toggleable HUD widgets** (Screen drawer), not App-area content. Each App nav area (Settings, Security, Reports, …) = **dedicated full-window surface** — not inline `app-section-*` in the App drawer. **App Settings** (connectors, Jira, creds) ≠ **Orb settings** (visual style/size/spin in Screen drawer). Orb-as-hub particle nav = optional later flourish. Plan: `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`.

## Current State
Skeleton + substantial features exist:
- `agent/agent.py` — Ollama tool-calling loop with clarification rules and sessions; **FR-AGENT-6 (KAN-61):** JSON-in-text tool fallback parser, `think: false` + `num_ctx`, grounded replies that never claim success on failed tool results; **FR-SEC-4 (KAN-71):** system prompt + tool-result untrusted fencing, `temperature: 0.2`, confirm args ignored for settings/delete (exact user yes/confirm only), SECRET-narrowed tool surface
- `agent/prompt_guard.py` — prompt-injection mitigations (wrap untrusted, injection heuristics, high-privilege refuse, SECRET filter)
- `plugins/heal_policy.py` — central FR-HEAL-1…5 guardrails (classify; refuse weaken/skip/timeout/AUT; locator-only pending review + audit); **KAN-75:** `list_pending_heals` / `approve_heal` / `reject_heal` rewrite audit `review_status` (no suite auto-commit)
- `plugins/playwright_steps.py` — generate happy + negative/edge drafts; assess/reject visibility-only flows (FR-TEST-6); used by agent `generate_playwright_steps` (KAN-57); **from Jira AC** via `generate_steps_from_jira` + `issue_key` (KAN-85)
- `plugins/playwright_runner.py` — steps (+ `expect_visible`), click + fill locator self-heal via heal_policy (assertions never healed), failure screenshots always + success via `playwright_success_evidence`; **persistent browser profile per security level** (KAN-15); **headed/headless** from `playwright_headless` setting or run override (KAN-83)
- `plugins/playwright_suite.py` — import/list/run existing Playwright projects via `npx playwright test` (KAN-59 / FR-TEST-5); settings `playwright_suite_path`; suite CLI `--headed` when product mode is headed (KAN-83)
- `plugins/desktop_runner.py` — Windows `.exe` smoke + structured steps (KAN-47/KAN-87); `wait_window`/`type_text`/… via ctypes; toggle `plugin_desktop_enabled`; does not fork Playwright
- `plugins/multi_sandbox.py` — multi-sandbox orchestration stub (KAN-55); toggle `plugin_multi_sandbox_enabled` default off; mock list/plan only
- `plugins/registry.py` — lightweight plugin manifests + `list_plugins()` (FR-PLUG-1/2); includes `test_framework` / frameworks list (FR-PLUG-3)
- `plugins/framework_switch.py` — test-framework preference stub (KAN-79); Playwright default/ready; Selenium/Cypress not-implemented on run
- `plugins/jira_plugin.py` — list/create/transition/comment/epic link; **read_issue** (KAN-85/KAN-89) returns summary/description/AC (ADF→text); `list_stories(include_description=…)` defaults project from settings **`jira_project`** when omitted (KAN-93 / FR-LEARN-4); httpx uses system CA via `_async_client`; **FR-JIRA-6 (KAN-91):** shared `_request` retries on 429 with `Retry-After` + inter-call spacing; 401/403/429 → human-readable `unauthorized`/`rate_limited` (no token echo); **create_bug** (KAN-63 / FR-JIRA-4) builds Symptom/Expected/Actual/Environment/Replication/Evidence from failed runs or report_path; product_bug only; Relates optional; **create_test** / **update_status** (KAN-65 / FR-JIRA-2/3) — issuetype **`test`** + Relates, Done when coverage evidence confirmed; writes need confirm. KAN types: Task=dev work under Story, `test`=verification, Bug=defects
- `settings/store.py` — local settings under `%LOCALAPPDATA%\ai_testing_app\`; shared UI prefs in `settings.json`; **OFFICIAL/SECRET isolation (KAN-15):** credentials in `levels\{LEVEL}\credentials.json`; Playwright profiles in `browser_profiles\{LEVEL}\`; level switch needs confirm; `plugin_desktop_enabled`; `plugin_multi_sandbox_enabled` (default false); `playwright_success_evidence` (default true); `playwright_headless` (default false = headed, KAN-83); `playwright_suite_path` (level-scoped); `telemetry_enabled` default false (FR-SEC-2); **`app_settings_status` / `save_app_settings` (KAN-73 + KAN-77 + KAN-79 + KAN-83 + KAN-93)** — non-secret App Settings payload; Jira URL + **`jira_project`** (FR-LEARN-4) + **`target_url` / `target_app_path` / `api_endpoint`** (FR-LEARN-2/3, level-scoped) + **`test_framework`** (FR-PLUG-3) + **`playwright_mode`/`playwright_headless`**; partial saves skip omitted fields
- `settings/privacy.py` — **GDPR (KAN-69 / FR-SEC-2):** inventory + confirm-gated `delete_local_data` for reports/screenshots/heal_audit/sessions/browser_profiles; credentials/settings.json never wiped here; consent note for extracted data
- `main.py` — FastAPI `/chat` + `/health` (includes `telemetry_enabled`) + `/api/orb` + `/api/report-sections` + `/api/security-level` + `/api/privacy` + `/api/privacy/delete` + `/api/app-settings` + `/api/jira-issue` (KAN-89) + `/api/heal/proposals` + `/api/heal/approve` + `/api/heal/reject` + `/api/desktop-plugin` + `/api/desktop-smoke` + `/api/plugins` + `/api/multi-sandbox-plugin` + `/api/multi-sandbox/orchestrate` + `/api/playwright-suite*` + static `/ui`
- `desktop_app.py` — **native Windows window** (pywebview + Edge WebView2) hosting mystic shell at `/ui/desktop/`; Gradio remains available via `run_ui.py`
- `ui/desktop/` — full-window orb on pure black; **shell-surface** chrome uses the active orb-style accent (`--cyan`, borders, glow, muted text) so mystic / aether / neural / apex recolor nav, area shells, HUD panels, and the layout picker. **App drawer** is a nav list (8 areas including **Heal review**). Choosing an area opens `#area-surface` in the persisted **App area layout** (`localStorage` `desktop-area-layout-v1`): `overlay`, `stage`, `orb_hub`, `split`, `floating`. Esc/Back closes it. Orb hub (layout `orb_hub`) expands particle spokes (SVG lines/nodes + accent glow) then opens the area as an overlay. Screen drawer owns orb settings plus **HUD widget toggles** (Security status / Reports mini — home-only movable panels; `desktop-hud-widgets-v1`). **UI-6 done:** edge-snap drawer toggles; free-drag widgets; resize handles; widget appearance in `desktop-shell-layout-v1`. **Settings (KAN-73 + KAN-77 + KAN-89 + KAN-93, desk29):** Jira URL + **Jira project key** + **Read Jira story** (issue key → description/AC) plus first-class **target URL / .exe path / messaging endpoint** on the area surface, with the layout picker. Hub polish **KAN-109** Done; **KAN-110** overlap fix Done (desk22g: seam-parked toggle, drawer above chat, chat left gutter). **Heal review (KAN-75, desk23):** App → Heal review lists `pending_review` locator diffs with Approve/Reject (`/api/heal/*`). **Reports (KAN-51):** App drawer → Reports; home HUD can show latest export summary via `/api/reports/latest-summary`. **Security (KAN-15/KAN-69):** App drawer → Security (level switch + Privacy & local data wipe with confirm). **Desktop (KAN-47):** App drawer → Desktop (plugin toggle + smoke). **Suites (KAN-59):** App drawer → Suites (discover/import/run Playwright project path). **Sandboxes (KAN-55):** App drawer → Sandboxes (multi-sandbox toggle default off + stub orchestrate). **Orb controls:** per-style mystic/aether/neural/apex settings in `localStorage` (`desktop-orb-styles-v1`); style switch loads that style’s colours/sliders; edits persist only to the active style. See `docs/mockups/screenshots/widget_settings_desk7.png`.
- `ui/gradio_app.py` — Gradio UI + energy orb; **named presets** (UI-5); orb controls behind top-right gear panel (UI-6a); gear panel **resizable** with size in `localStorage` (`gradio-orb-panel-size-v1`); **Settings/Reports polish (KAN-10):** human Settings labels + local-store summary (no secret echo); Reports picker (newest first) + details path; **section toggles (KAN-51)** on Reports tab; **Security (KAN-15):** Confirm level switch gate + profile path in summary; **Privacy GDPR (KAN-69)** delete-local-data + telemetry summary on Settings; **Target URL/exe/messaging (KAN-77)** on Settings; **Jira project key (KAN-93)** on Settings; **Test framework (KAN-79)** + **Playwright mode headed/headless (KAN-83)** on Settings; **Desktop plugin (KAN-47)** toggle + smoke on Settings; **Playwright suites (KAN-59)** discover/import/run on Settings; **Multi-sandbox (KAN-55)** toggle + orchestrate + plugin registry list on Settings
- **Orb styles:** classic four on canvas; **`mystic` / `aether` / `neural` / `apex` on WebGL** via `ui/orb_webgl.js` + vendored `ui/vendor/three.min.js` (particle counts capped; see `docs/mockups/orb_styles.md`). **Mystic** uses FBM / ridge-extracted filament fragment shaders (`FRAG_MYSTIC`), not ribbon meshes; soft atmospheric bloom replaces hard rim; equatorial streak removed; floor glow kept (see `docs/mockups/screenshots/mystic_final_*.png`). **Aether** mockup pass (`aether_mid_v4.png`): single orange-gold plasma sphere — solar core in `FRAG_AETHER` (no white blowout), unchanged flare filament motion, FBM fire wisps on paths plus high-frequency crest **flame licks** (additive colour/alpha on filaments only), thinner ribbon arcs, soft bloom; no MeshPhysical transmission; glow/turbulence live. Mystic/neural untouched. **Neural** glass-torus bubble (`neural_mid_v16.png`): same single thick hollow shell in `FRAG_BUBBLE`. The facing body is a translucent veil so the dark centre shows through the glass. Inner and outer rims carry a thin filament that travels along the ring: cyan, with white on the bright crests (same hot-lift idea as mystic). Turbulence warps that travel. Front-skin specular catch, far wall, no MeshPhysical transmission, dark void, soft `FRAG_NEURAL_ATMOS` bloom, sparkle field kept in the glass; glow/turbulence live. Mystic/aether untouched. **Apex** (`apex_v4.png`): white-gold core (`FRAG_APEX_CORE`) with soft core-only bloom unchanged; 8–10 full elliptical orbit streams (`sampleApexOrbit` + `FRAG_APEX_STREAM` hairline floor for legibility on black, thin width); sparse node points; group rotation only; no shell, rings, fire, or glass; thinking brightens core; glow/turbulence live; desktop accent `#e8d4a0`. Visual gate: `.cursor/rules/orb-visual.mdc`; `scripts/compare_orb.py`. **Desktop UI theme follows style:** mystic `#50cdff`, aether `#ff8a2b`, neural `#5ce1ff`, apex `#e8d4a0`; neural orb calm default matches mystic `#50cdff`. **Live controls (2026-11-06):** slider `0` applies; glow mid=`1`; turbulence warps filaments (mystic/aether) and shell shimmer (neural); spin `0` stops swirl. Shots: `mystic_glow_*.png`, `aether_mid_v4.png`, `neural_mid_v16.png`, `apex_v4.png`, `style_theme_switch.png`.
- `reports/exporter.py` + `reports/sections.py` — JSON/Markdown export with FR-REP-2 section toggles (`summary` / `stories` / `bugs` / `evidence`; local `report_sections`); **FR-REP-1 (KAN-67):** richer metrics — tests passed/failed + pass rate, stories covered by Jira key, bugs raised with counts by story and functional area
- Tests under `tests/` for Jira, Playwright heal, orb config/presets, sessions, settings, reports
- Architecture notes + AGENTS.md + this file
- **Cursor ops:** `.cursor/rules`, agents (implementer/ui-orb on Grok 4.7; doc-keeper/verifier/explorer on Composer), skills, MCP template, `docs/ops/*`
- Settings keys: `orb_presets` (map), `orb_active_preset` (string), still under local app data only
- **Jira KAN backlog (2026-11-15):** Ten FR-area epics **KAN-20…KAN-29** from `docs/FUNCTIONAL_SPEC.md`; stories/tests enriched via `scripts/jira_kan_enrich.py` (multi-audience template in `docs/ops/JIRA_TICKET_TEMPLATE.md`). Rebuild: `scripts/jira_kan_rebuild.py`.
- **Product spec:** `docs/FUNCTIONAL_SPEC.md`. **Work log:** `docs/ops/WORK_LOG.md` (pointer also at `D:\Projects\WORK_LOG.md`).
- **Ollama models:** `qwen2.5-coder:7b` (app default), `qwen3:8b`, `llama3.2`, plus optional 14b/16b — one loaded at a time on 1080 Ti.
- **IDE tooling verified (2026-11-15):** GitHub plugin OK; Jira via REST fallback (MCP API-token often blocked); **product UI = `desktop_app.py` + Computer Use** (not browser shell); IronBee for AUT/Gradio only; Supermemory authenticated; Context7 optional. See `AGENTS.md` tooling preferences.

Not yet done (open Stories; see FUNCTIONAL_SPEC §5 FR matrix):
- **KAN-75** Heal proposal review UI — **Done** (KAN-76; desk23 App → Heal review)
- **KAN-77** Target URL / exe / messaging endpoints — **Done** (KAN-78; desk24 App Settings)
- **KAN-79** Dynamic framework switching stub — **Done** (KAN-80; desk25 `test_framework`)
- **KAN-83** Playwright headed/headless — **Done** (KAN-84; desk26 `playwright_mode`)
- **KAN-103** Desktop nav area screens + HUD widgets — **Done** (KAN-104 verify; desk22g; Tasks KAN-106–110/112 Done)
- **KAN-81** Voice input — **deferred** until mic connected (do last; test KAN-82 stays open)
- **KAN-87** Desktop .exe structured steps — **Done** (KAN-88; desk27 `wait_window`/`type_text`; Bug KAN-116 close tree)
- **KAN-89** Read story/AC UX — **Done** (KAN-90; desk28 `read_issue` tool + `/api/jira-issue` + App Settings Read story)
- **KAN-91** Jira 429 backoff / auth errors — **Done** (KAN-92; `_request` Retry-After + readable messages)
- **KAN-93** jira_project default — **Done** (KAN-94; desk29 Settings field + `list_stories` default)
- Next Active: **KAN-95** multi-sandbox real orchestration (test KAN-96); then KAN-97…KAN-99 gap pass; **KAN-81** voice last
- Done Stories are baseline-only where commented (KAN-8/9/11/12/15/45/47/49/55) — remaining FR text lives on open tickets
- Cursor agents must raise Jira **Bug** tickets when defects are found during development (Relates to Story + test ticket; replication steps + Fix comment). KAN types: **Task**=dev (e.g. per-FR), **`test`**=verification, **Bug**=defects. See AGENTS.md / JIRA_TICKET_TEMPLATE. KAN-101 / KAN-113 overlap bugs Done with KAN-110 (desk22g).

## Important Context from Earlier Conversations
- User is a senior test engineer (~£40k) wanting automated income / ability to leave traditional work.
- Existing company has a large browser-based application + Atlassian Jira + GitHub repos. Strong potential internal guinea-pig.
- Some early chat content was lost (multiple sandboxes, full security spectrum, etc.) — those features remain desired as later plugins.
- Preference for local models over paid APIs where possible, especially for company use.
- GDPR and UK security classifications are non-negotiable.
- Token usage in long agent sessions burns Premium quickly — ops docs encode the fix.
- User is not a project manager; Cursor PM chat fills process blanks (roadmap, slices, advice).
- User is brand new to Cursor; follow `docs/ops/SETUP_FOR_BEGINNERS.md` one step at a time.
- **Grok guide bot — use sparingly.** Prefer the local helpers (`docs/prompts/NEXT_PROMPT.md` and `scripts/next_prompt.py`) for day-to-day work. Wake the bot only for permanent state updates.

## How to Use This File
- Prefer: say **“pick up where we left off”** — agents read `docs/ops/WORK_LOG.md` Active slice and start that Jira story.
- Or run: `python scripts/next_prompt.py` and copy the output.
- Or edit `docs/prompts/NEXT_PROMPT.md` and copy that.
- After meaningful progress: update Current State here, append WORK_LOG, comment on the Jira story.
- If the agent starts drifting or burning tokens, point it back to the “Original Vision” section, AGENTS.md token rules, and `docs/ops/HOW_WE_WORK.md`.

## Next Recommended Steps (in order)
1. **KAN-95** — Multi-sandbox real orchestration beyond stub (FR-PLUG-1; test KAN-96).
2. Continue open FR Stories in WORK_LOG / FUNCTIONAL_SPEC §5 order; **KAN-81** voice last (needs mic).
