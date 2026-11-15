# AGENTS.md
# Rules for any AI coding agent working on this project

## Core behaviour
- Read `docs/ops/WORK_LOG.md` **Active slice** first when the user says “pick up where we left off” / “continue”, then start that Jira story immediately.
- Otherwise read PROJECT_MEMORY.md (and AGENTS.md) at the start of any non-trivial session.
- Prefer Plan mode (or an explicit plan in chat) before editing more than one file.
- Keep changes small and reviewable. One logical improvement at a time.
- If a requirement is ambiguous, stop and ask rather than guessing.
- Never store real credentials in code or in this repository. Use the local settings store only.
- After every finished or paused slice: append `docs/ops/WORK_LOG.md`, update Active slice, and add a Jira comment on the story (what changed + how to verify).
- **User change requests (CRs):** When the human changes product intent, scope, AC, or behaviour (including informal “actually do X instead”), update **all** of: `docs/FUNCTIONAL_SPEC.md` (canonical), affected KAN epic/story/test descriptions (re-enrich or edit), `PROJECT_MEMORY.md` / `ROADMAP.md` / `docs/ops/WORK_LOG.md` as needed, and any mockups/rules that contradict the CR. Do not leave Jira or the spec stale relative to what the user just decided.

## Cursor workflow (PM-managed; replaces Grok browser + AFK Pilot)
- Primary home is **Cursor IDE**. Prefer a **fresh IDE Agent chat** per slice; say **“pick up where we left off”** (reads `docs/ops/WORK_LOG.md`).
- Do not ask the human to paste coding prompts into browser Grok / AFK Pilot / other tools.
- Ops docs: `docs/ops/HOW_WE_WORK.md`, `docs/ops/TEAM.md`, `docs/ops/ROADMAP.md`.
- Custom agents: `.cursor/agents/` — **Grok family only** (`implementer`/`ui-orb`/`architect` → 4.7; `doc-keeper`/`verifier`/`explorer-cheap` → 4.5). User pays Grok Premium; do not assign Composer/Claude/GPT/Copilot as “free”.
- Skills: `.cursor/skills/` (`jira-safe`, `slice-workflow`, `run-local-stack`, `orb-slice`, `update-memory`).
- Local Ollama is for the *product* runtime (actually free). Cursor coding agents are not free.
- Prefer short chats + WORK_LOG / Supermemory over re-explaining history in long threads.

## Token budget
Premium plan only. Do not assume more tokens can be bought. Token use in long agent threads is much higher than short chats.
- Do not re-read the entire codebase unless explicitly asked.
- When exploring, prefer targeted reads (specific files or functions) over broad directory dumps.
- After reading a file, summarise only what is relevant and do not re-send full contents in later turns unless necessary.
- Read only files you will change. Do not re-read files already in context. Project rules and memory are already loaded — do not re-read them repeatedly in the same session.
- No subagents, broad searches, or drive-by refactors unless asked.
- Keep tool outputs short. Prefer structured summaries over raw logs.
- Prefer one small diff and a short reply.
- Compact the session, or start a fresh one, after a logical chunk of work.

## Home PC limits
This development machine is DESKTOP-NAL5HLJ: Intel i7-8700K, 32 GB RAM at 2400 MHz, GTX 1080 Ti with 11 GB VRAM, 1.16 TB disk with about 900 GB free. It is a 2017 desktop, not a modern AI workstation.
- Prefer 7B–8B local models. Those fit in the 11 GB GPU. 14B is the ceiling and may spill onto the CPU. Do not pull 32B or larger models, and do not run two models at once.
- Leave RAM for Windows and one headed browser. Do not start extra browsers, stacks, or background jobs unless asked.
- Disk space is enough for one or two models. Do not download a collection of models.
- Jira is live: `https://ai-testing-lab.atlassian.net` project **KAN**. Credentials only in `%LOCALAPPDATA%\ai_testing_app\settings.json`. Product-agent Jira writes stay two-step confirm.
- **If Atlassian MCP fails** (“permission to connect via API token”): do **not** stop — use Jira REST via local settings or `scripts/jira_kan_*.py` (see `.cursor/skills/jira-safe/SKILL.md`). Never print the token.
- Repo path: `D:\Projects\ai_testing_app`. Ollama: `D:\Program Files\Ollama` with models under `OLLAMA_MODELS`.

## Safety and confirmation
- Always confirm before:
  - Changing security level handling
  - Writing or updating credentials
  - Creating or modifying Jira issues
  - Deleting data or files
  - Running destructive commands
- Do not enable auto-merge or unrestricted terminal permissions.
- Prefer adding a simple runnable example or test when changing core logic.

## Project constraints (do not violate)
- Local-first: the application must run on a Windows laptop without requiring cloud services.
- UK security classifications: OFFICIAL and SECRET levels must be supported from the start (isolation of credentials and browser profiles).
- GDPR: no telemetry by default; easy local data deletion; explicit consent before storing extracted data.
- Main interface is a conversational AI agent that clarifies before acting.
- Modular plugin design: new capabilities (desktop testing, richer reporting, multi-sandbox, etc.) should be addable without rewriting the core.

## Tech stack (current)
- Python 3.11+ (this PC is on 3.15 — watch for compatibility; D: venv uses 3.13)
- FastAPI
- Ollama (recommended start model: qwen3:8b; installed default often `qwen2.5-coder:7b`)
- Playwright (Python)
- Gradio UI with pure-canvas energy orb
- Local settings store
- Target OS: Windows (home development machine first, then work Dell XPS 15s)

## Cursor tooling preferences (verified 2026-11-15 — no login how-tos here)
- **Jira:** try **user-atlassian** first; expect frequent MCP API-token errors → **always** fall back to REST + local settings / `scripts/jira_kan_*.py` (never print tokens).
- **GitHub:** **plugin-github-github** only. Keep `.cursor/mcp.json` empty (do not revive workspace npx GitHub MCP).
- **UI verify:** **IronBee browser** MCP only for this app (not cursor-ide-browser). IronBee Node/Backend stay **off** unless the user asks.
- **Supermemory:** use when authenticated for cross-chat recall (`workspaceRoot` = repo root). If MCP add/search fails but CLI/auth works, still treat memories as available; do not block the slice.
- **Context7:** optional; Cloud Connected is enough; ignore Local Error·terminated.
- **Skip unless asked:** plugin-atlassian (duplicate), cursor-origin (GitHub remotes only), enabling IronBee Node/Backend.
- **Computer Use / native cursor tools:** OK for desktop/OS UI; prefer IronBee for in-app web.

## When stuck
- Re-read the “Original Vision” and “Key Decisions” sections of PROJECT_MEMORY.md.
- Prefer extending existing plugins over creating parallel systems.
- Re-read `docs/ops/HOW_WE_WORK.md` if the session drifts into multi-tool copy-paste habits.
