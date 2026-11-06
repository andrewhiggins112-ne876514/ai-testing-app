# PROJECT_MEMORY.md
# Persistent memory for the AI Testing Application

Last updated: 2026-11-06 (neural glass polish toward mockup; aether left at prior)

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
- Classic orb styles stay pure canvas. **WebGL / Three.js is allowed** for the three new styles (mystic, aether, neural) only. Vendor Three.js under ui/vendor/ is acceptable for those styles.
- Jira writes are two-step confirm; no Jira account yet — do not solicit credentials until the user says one exists.
- **Local zero-token helpers (2026-11-06):**
  - `docs/prompts/NEXT_PROMPT.md` — edit and copy into a fresh Cursor chat.
  - `scripts/next_prompt.py` — run locally to print a suggested prompt from PROJECT_MEMORY.
  - Use these instead of waking the Grok guide bot for day-to-day prompt hand-off.
- **Ollama in Cursor (parked 2026-11-06):** possible via OpenAI Base URL override to localhost:11434, but unreliable for full Agent mode and requires tunnel for reliability. Revisit only when cloud tokens run out. App runtime already uses local Ollama.
- **Orb styles approved (2026-11-06):** Mystic (cyan filament), Aether (orange plasma), Neural (blue glass bubble). See docs/mockups/orb_styles.md. Widgets in mockups are future configurable panels. WebGL preferred for these three.

## Current State
Skeleton + substantial features exist:
- `agent/agent.py` — Ollama tool-calling loop with clarification rules and sessions
- `plugins/playwright_runner.py` — steps, click self-heal, screenshots/evidence path
- `plugins/jira_plugin.py` — list/create/transition/comment/epic link; writes need confirm
- `settings/store.py` — local settings under `%LOCALAPPDATA%\ai_testing_app\settings.json` (incl. orb)
- `main.py` — FastAPI `/chat` + `/health` + `/api/orb` + static `/ui`
- `desktop_app.py` — **native Windows window** (pywebview + Edge WebView2) hosting mystic shell at `/ui/desktop/`; Gradio remains available via `run_ui.py`
- `ui/desktop/` — full-window mystic orb on pure black `#000000`; shared **shell-surface** style for chat widget, both drawers, and chat input; **app drawer** + **screen drawer** (chat / orb / widget-settings icons); bottom chat bar; no top nav. **UI-6 partial:** edge-snap drawer toggles; free-drag widgets; Widget Settings (transparency + border/background colour) apply live to all shell surfaces; layout in `localStorage` (`desktop-shell-layout-v1`). See `docs/mockups/screenshots/widget_settings_desk7.png`.
- `ui/gradio_app.py` — Gradio UI + energy orb; **named presets** (UI-5); orb controls behind top-right gear panel (UI-6a)
- **Orb styles:** classic four on canvas; **`mystic` / `aether` / `neural` on WebGL** via `ui/orb_webgl.js` + vendored `ui/vendor/three.min.js` (particle counts capped; see `docs/mockups/orb_styles.md`). **Mystic** uses FBM / ridge-extracted filament fragment shaders (`FRAG_MYSTIC`), not ribbon meshes; soft atmospheric bloom replaces hard rim; equatorial streak removed; floor glow kept (see `docs/mockups/screenshots/mystic_final_*.png`). **Aether** remains prior fiery plasma pass (soft atmos, `FRAG_AETHER`, arcs/embers); a further mockup pass was tried and reverted (not clearly closer). **Neural** polished toward mockup: darker hollow void, cleaner glass rim (`FRAG_BUBBLE`), brighter white elliptical hero ring, fainter orbits, less pane mist; glow/turbulence live. **Desktop UI theme follows style:** mystic `#50cdff`, aether `#ff8a2b`, neural `#5ce1ff` (borders / shell glow / `--cyan`). **Live controls (2026-11-06):** slider `0` applies; glow mid=`1`; turbulence warps filaments (mystic/aether) and shell shimmer (neural); spin `0` stops swirl. Shots: `mystic_glow_*.png`, `aether_mid.png`, `neural_mid_v2.png`, `style_theme_switch.png`.
- `reports/exporter.py` — run export
- Tests under `tests/` for Jira, Playwright heal, orb config/presets, sessions, settings, reports
- Architecture notes + AGENTS.md + this file
- **Cursor ops:** `.cursor/rules`, agents (implementer/ui-orb on Grok 4.7; doc-keeper/verifier/explorer on Composer), skills, MCP template, `docs/ops/*`
- Settings keys: `orb_presets` (map), `orb_active_preset` (string), still under local app data only

Not yet done:
- Jira credentials in local store only when user has an account (none yet)
- UI-6 remainder: resizable panels; more mockup widgets as configurable panels (desktop drag/snap + transparency landed)
- Document ingestion → settings proposal
- Broader self-healing; security-level isolation (browser profiles + credential scopes)
- Desktop .exe testing; customisable reporting polish; multi-sandbox orchestration

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
- At the start of a coding session: “Read PROJECT_MEMORY.md and AGENTS.md, then continue from the Current State. Keep tool use targeted.”
- Or run: `python scripts/next_prompt.py` and copy the output.
- Or edit `docs/prompts/NEXT_PROMPT.md` and copy that.
- After meaningful progress, update the “Current State” and “Key Decisions” sections (or ask the agent to propose the update).
- If the agent starts drifting or burning tokens, point it back to the “Original Vision” section, AGENTS.md token rules, and `docs/ops/HOW_WE_WORK.md`.

## Next Recommended Steps (in order)
1. Wire Settings/Reports screens from the app drawer; refine hideable chat panel UX.
2. UI-6 resize + more mockup widgets as configurable panels (drag/snap already on desktop).
3. Broader self-healing / security isolation / document ingestion as roadmap allows.
