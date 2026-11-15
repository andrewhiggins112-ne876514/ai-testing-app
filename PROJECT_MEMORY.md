# PROJECT_MEMORY.md
# Persistent memory for the AI Testing Application

Last updated: 2026-11-15 (KAN-10 Gradio Settings/Reports polish shipped; Active → KAN-14)

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
- Playwright as the first execution engine (browser + headed).
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
- **Orb styles approved (2026-11-06):** Mystic (cyan filament), Aether (orange plasma), Neural (blue glass bubble), Apex (white-gold core + data streams). See docs/mockups/orb_styles.md. Widgets in mockups are future configurable panels. WebGL preferred for these four.

## Current State
Skeleton + substantial features exist:
- `agent/agent.py` — Ollama tool-calling loop with clarification rules and sessions
- `plugins/heal_policy.py` — central FR-HEAL-1…5 guardrails (classify; refuse weaken/skip/timeout/AUT; locator-only pending review + audit)
- `plugins/playwright_runner.py` — steps, click + fill locator self-heal via heal_policy (assertions never healed), screenshots/evidence path; **persistent browser profile per security level** (KAN-15)
- `plugins/desktop_runner.py` — Windows `.exe` smoke plugin (KAN-47); stdlib launch; toggle `plugin_desktop_enabled`; does not fork Playwright
- `plugins/jira_plugin.py` — list/create/transition/comment/epic link; writes need confirm
- `settings/store.py` — local settings under `%LOCALAPPDATA%\ai_testing_app\`; shared UI prefs in `settings.json`; **OFFICIAL/SECRET isolation (KAN-15):** credentials in `levels\{LEVEL}\credentials.json`; Playwright profiles in `browser_profiles\{LEVEL}\`; level switch needs confirm; `plugin_desktop_enabled`
- `main.py` — FastAPI `/chat` + `/health` + `/api/orb` + `/api/report-sections` + `/api/security-level` + `/api/desktop-plugin` + `/api/desktop-smoke` + static `/ui`
- `desktop_app.py` — **native Windows window** (pywebview + Edge WebView2) hosting mystic shell at `/ui/desktop/`; Gradio remains available via `run_ui.py`
- `ui/desktop/` — full-window mystic orb on pure black `#000000`; shared **shell-surface** style for chat widget, both drawers, and chat input; **app drawer** + **screen drawer** (chat / orb / widget-settings icons); bottom chat bar; no top nav. **UI-6 done:** edge-snap drawer toggles; free-drag widgets; **resize handles** (E/S/SE on widgets; drawer edge resize); Widget Settings (transparency + border/background colour) apply live to all shell surfaces; layout (position + size) in `localStorage` (`desktop-shell-layout-v1`). **Reports (KAN-51):** App drawer → Reports. **Security (KAN-15):** App drawer → Security (level switch + confirm). **Desktop (KAN-47):** App drawer → Desktop (plugin toggle + smoke). **Orb controls:** per-style mystic/aether/neural/apex settings in `localStorage` (`desktop-orb-styles-v1`); style switch loads that style’s colours/sliders; edits persist only to the active style. See `docs/mockups/screenshots/widget_settings_desk7.png`.
- `ui/gradio_app.py` — Gradio UI + energy orb; **named presets** (UI-5); orb controls behind top-right gear panel (UI-6a); gear panel **resizable** with size in `localStorage` (`gradio-orb-panel-size-v1`); **Settings/Reports polish (KAN-10):** human Settings labels + local-store summary (no secret echo); Reports picker (newest first) + details path; **section toggles (KAN-51)** on Reports tab; **Security (KAN-15):** Confirm level switch gate + profile path in summary; **Desktop plugin (KAN-47)** toggle + smoke on Settings
- **Orb styles:** classic four on canvas; **`mystic` / `aether` / `neural` / `apex` on WebGL** via `ui/orb_webgl.js` + vendored `ui/vendor/three.min.js` (particle counts capped; see `docs/mockups/orb_styles.md`). **Mystic** uses FBM / ridge-extracted filament fragment shaders (`FRAG_MYSTIC`), not ribbon meshes; soft atmospheric bloom replaces hard rim; equatorial streak removed; floor glow kept (see `docs/mockups/screenshots/mystic_final_*.png`). **Aether** mockup pass (`aether_mid_v4.png`): single orange-gold plasma sphere — solar core in `FRAG_AETHER` (no white blowout), unchanged flare filament motion, FBM fire wisps on paths plus high-frequency crest **flame licks** (additive colour/alpha on filaments only), thinner ribbon arcs, soft bloom; no MeshPhysical transmission; glow/turbulence live. Mystic/neural untouched. **Neural** glass-torus bubble (`neural_mid_v16.png`): same single thick hollow shell in `FRAG_BUBBLE`. The facing body is a translucent veil so the dark centre shows through the glass. Inner and outer rims carry a thin filament that travels along the ring: cyan, with white on the bright crests (same hot-lift idea as mystic). Turbulence warps that travel. Front-skin specular catch, far wall, no MeshPhysical transmission, dark void, soft `FRAG_NEURAL_ATMOS` bloom, sparkle field kept in the glass; glow/turbulence live. Mystic/aether untouched. **Apex** (`apex_v4.png`): white-gold core (`FRAG_APEX_CORE`) with soft core-only bloom unchanged; 8–10 full elliptical orbit streams (`sampleApexOrbit` + `FRAG_APEX_STREAM` hairline floor for legibility on black, thin width); sparse node points; group rotation only; no shell, rings, fire, or glass; thinking brightens core; glow/turbulence live; desktop accent `#e8d4a0`. Visual gate: `.cursor/rules/orb-visual.mdc`; `scripts/compare_orb.py`. **Desktop UI theme follows style:** mystic `#50cdff`, aether `#ff8a2b`, neural `#5ce1ff`, apex `#e8d4a0`; neural orb calm default matches mystic `#50cdff`. **Live controls (2026-11-06):** slider `0` applies; glow mid=`1`; turbulence warps filaments (mystic/aether) and shell shimmer (neural); spin `0` stops swirl. Shots: `mystic_glow_*.png`, `aether_mid_v4.png`, `neural_mid_v16.png`, `apex_v4.png`, `style_theme_switch.png`.
- `reports/exporter.py` + `reports/sections.py` — JSON/Markdown export with FR-REP-2 section toggles (`summary` / `stories` / `bugs` / `evidence`; local `report_sections`)
- Tests under `tests/` for Jira, Playwright heal, orb config/presets, sessions, settings, reports
- Architecture notes + AGENTS.md + this file
- **Cursor ops:** `.cursor/rules`, agents (implementer/ui-orb on Grok 4.7; doc-keeper/verifier/explorer on Composer), skills, MCP template, `docs/ops/*`
- Settings keys: `orb_presets` (map), `orb_active_preset` (string), still under local app data only
- **Jira KAN backlog (2026-11-15):** Ten FR-area epics **KAN-20…KAN-29** from `docs/FUNCTIONAL_SPEC.md`; stories/tests enriched via `scripts/jira_kan_enrich.py` (multi-audience template in `docs/ops/JIRA_TICKET_TEMPLATE.md`). Rebuild: `scripts/jira_kan_rebuild.py`.
- **Product spec:** `docs/FUNCTIONAL_SPEC.md`. **Work log:** `docs/ops/WORK_LOG.md` (pointer also at `D:\Projects\WORK_LOG.md`).
- **Ollama models:** `qwen2.5-coder:7b` (app default), `qwen3:8b`, `llama3.2`, plus optional 14b/16b — one loaded at a time on 1080 Ti.
- **IDE tooling verified (2026-11-15):** GitHub plugin OK; Jira via REST fallback (MCP API-token often blocked); **product UI = `desktop_app.py` + Computer Use** (not browser shell); IronBee for AUT/Gradio only; Supermemory authenticated; Context7 optional. See `AGENTS.md` tooling preferences.

Not yet done:
- **Next build slice:** [KAN-55](https://ai-testing-lab.atlassian.net/browse/KAN-55) Multi-sandbox orchestration plugin (see WORK_LOG Active slice)
- Desktop `.exe` testing (**KAN-47** — done 2026-11-15): `plugins/desktop_runner.py` + toggle
- OFFICIAL/SECRET isolation (**KAN-15** — done 2026-11-15): level-scoped credentials + Playwright profiles + confirm gate
- Document ingestion → settings proposals (**KAN-45** — done 2026-11-15): `plugins/doc_ingest.py` + confirm gate
- Full desktop Settings form beyond Security (optional UX follow-on)

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
1. **KAN-55** — Multi-sandbox orchestration plugin (Active slice).
2. Optional: fuller desktop Settings form beyond Security.
