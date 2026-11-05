# AGENTS.md
# Rules for any AI coding agent working on this project

## Core behaviour
- Read PROJECT_MEMORY.md at the start of any non-trivial session.
- Prefer Plan mode (or an explicit plan in chat) before editing more than one file.
- Keep changes small and reviewable. One logical improvement at a time.
- If a requirement is ambiguous, stop and ask rather than guessing.
- Never store real credentials in code or in this repository. Use the local settings store only.

## Cursor workflow (replaces Grok browser + AFK Pilot)
- Primary home is Cursor. Do not instruct the user to copy-paste prompts between browser Grok and VS Code.
- Ops docs: `docs/ops/HOW_WE_WORK.md`, `docs/ops/TEAM.md`, `docs/ops/ROADMAP.md`.
- Custom agents: `.cursor/agents/` (`explorer-cheap`, `architect`, `implementer`, `verifier`, `ui-orb`).
- Skills: `.cursor/skills/` (`slice-workflow`, `run-local-stack`, `jira-safe`, `orb-slice`).
- Default coding model: Composer / Auto. Local Ollama is for the *product*, not for burning Cursor credits on coding.

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
- There is no Jira account yet. Do not block other work on a live Jira call, and do not ask for a URL or token until the user says an account exists.

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
- Python 3.11+ (this PC is on 3.15 — watch for compatibility)
- FastAPI
- Ollama (recommended start model: qwen3:8b; installed default often `qwen2.5-coder:7b`)
- Playwright (Python)
- Gradio UI with pure-canvas energy orb
- Local settings store
- Target OS: Windows (home development machine first, then work Dell XPS 15s)

## When stuck
- Re-read the “Original Vision” and “Key Decisions” sections of PROJECT_MEMORY.md.
- Prefer extending existing plugins over creating parallel systems.
- Re-read `docs/ops/HOW_WE_WORK.md` if the session drifts into multi-tool copy-paste habits.
