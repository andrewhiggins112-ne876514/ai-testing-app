# PROJECT_MEMORY.md
# Persistent memory for the AI Testing Application

Last updated: 2026-11-05 (Grok guide bot retired as daily driver; Cursor PM + repo memory)

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
- Coding models: prefer Composer / Auto in Cursor. Product runtime stays on local Ollama (free for inference).
- Token efficiency matters: prefer targeted reads, compact/fresh chats per slice, avoid re-sending full file contents.
- Pure canvas energy orb (no Three.js / CDN) for the Gradio UI centrepiece.
- Jira writes are two-step confirm; no Jira account yet — do not solicit credentials until the user says one exists.

## Current State
Skeleton + substantial features exist:
- `agent/agent.py` — Ollama tool-calling loop with clarification rules and sessions
- `plugins/playwright_runner.py` — steps, click self-heal, screenshots/evidence path
- `plugins/jira_plugin.py` — list/create/transition/comment/epic link; writes need confirm
- `settings/store.py` — local settings under `%LOCALAPPDATA%\ai_testing_app\settings.json` (incl. orb)
- `main.py` — FastAPI `/chat` + `/health`
- `ui/gradio_app.py` — Gradio UI + configurable energy orb (styles/shapes/sliders) through orb slice 4 (`8553d6a`)
- `reports/exporter.py` — run export
- Tests under `tests/` for Jira, Playwright heal, orb config, sessions, settings, reports
- Architecture notes + AGENTS.md + this file
- **Cursor ops (2026-11-05):** `.cursor/rules`, `.cursor/agents`, `.cursor/skills`, `.cursor/mcp.json` (GitHub template), `docs/ops/*`

Not yet done:
- Jira credentials in local store only when user has an account (none yet)
- Orb presets (UI-5) and movable panels (UI-6)
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
- **Grok guide bot — retired as daily driver (2026-11-05).** It kept architecture in Grok persistent memory and wrote short AFK Pilot paste-prompts. That loop is replaced by: this file + `docs/ops/ROADMAP.md` + Cursor PM chat + slice chats (Composer). Do not use it for daily next-prompt / AFK copy-paste. Optional: leave the bot open read-only for a week if you want to cross-check old journal notes, then ignore it. Source of truth is the repo, not Grok memory (its journal was last current at orb `8553d6a`, before Cursor ops).
- Kept from that bot’s standing rules: plan first for larger diffs; test before commit; no secrets in git/UI; settings/reports/screenshots under `%LOCALAPPDATA%`; no telemetry; Jira writes only after explicit yes; prefer the smaller/safer foundational option.

## How to Use This File
- At the start of a coding session: “Read PROJECT_MEMORY.md and AGENTS.md, then continue from the Current State. Keep tool use targeted.”
- After meaningful progress, update the “Current State” and “Key Decisions” sections (or ask the agent to propose the update).
- If the agent starts drifting or burning tokens, point it back to the “Original Vision” section, AGENTS.md token rules, and `docs/ops/HOW_WE_WORK.md`.

## Next Recommended Steps (in order)
1. Land Cursor ops (this change). Use PM chat for priorities; coding chats per slice.
2. Optional: set `GITHUB_PERSONAL_ACCESS_TOKEN` env for GitHub MCP; add Atlassian MCP only after a Jira account exists.
3. Slice **UI-5**: orb preset save/load named configs (`/ui-orb` + `/verifier`).
4. UI-6 movable panels; then richer Jira ticket bodies (still confirm-gated).
5. Playwright evidence improvements; then SEC-1 isolation when ready to confirm the design.
