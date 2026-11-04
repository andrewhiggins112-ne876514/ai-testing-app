# PROJECT_MEMORY.md
# Persistent memory for the AI Testing Application

Last updated: 2026-11-04 (skeleton boots on Windows; Jira list_stories is read-only)

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
- Python backend + FastAPI.
- Ollama for the local LLM. This PC has `qwen2.5-coder:7b` (the default). `qwen3:8b` is still fine via `OLLAMA_MODEL` once pulled.
- Playwright as the first execution engine (browser + headed).
- Modular plugin architecture so features can be toggled and extended later.
- Security context switcher from day one (OFFICIAL / SECRET).
- Agent must clarify ambiguous requests and confirm side-effecting actions.
- Development machine: Windows home PC (i7-8700K, 32 GB RAM, GTX 1080 Ti, Ollama already installed). User is on Python 3.15.
- VS Code + Grok agent (AFK Pilot / Sixth AI or similar) for ongoing coding, with human review of every meaningful change.
- Token efficiency matters: prefer targeted reads, compact often, avoid re-sending full file contents.

## Current State
Skeleton exists and has been generated:
- `agent/agent.py` — Ollama tool-calling loop with clarification rules
- `plugins/playwright_runner.py` — basic headed Playwright execution
- `plugins/jira_plugin.py` — read-only `list_stories` via Jira REST. Writes stay blocked.
- `settings/store.py` — local settings under `%LOCALAPPDATA%\ai_testing_app\settings.json`
- `main.py` — FastAPI `/chat` endpoint
- Architecture document written
- AGENTS.md and PROJECT_MEMORY.md added for agent guidance
- Python 3.15: dependencies installed and `/health` responded on this PC

Not yet done:
- Jira credentials are read from the local store, but none are saved in the repo. Cloud uses `jira_email` + `jira_api_token`. Server/DC PAT uses `jira_api_token` only.
- Document ingestion → settings proposal
- Self-healing on locator failures
- Security level isolation (browser profiles + credential scopes)
- Minimal local chat UI
- Desktop .exe testing
- Customisable reporting
- Multi-sandbox orchestration

## Important Context from Earlier Conversations
- User is a senior test engineer (~£40k) wanting automated income / ability to leave traditional work.
- Existing company has a large browser-based application + Atlassian Jira + GitHub repos. Strong potential internal guinea-pig.
- Some early chat content was lost (multiple sandboxes, full security spectrum, etc.) — those features remain desired as later plugins.
- Preference for local models over paid APIs where possible, especially for company use.
- GDPR and UK security classifications are non-negotiable.
- Token usage in the VS Code agent is much higher than in chat. Efficiency rules are in AGENTS.md.

## How to Use This File
- At the start of a coding session, tell the agent: “Read PROJECT_MEMORY.md and AGENTS.md, then continue from the Current State. Keep tool use targeted.”
- After meaningful progress, update the “Current State” and “Key Decisions” sections (or ask the agent to propose the update).
- If the agent starts drifting or burning tokens, point it back to the “Original Vision” section and the token rules in AGENTS.md.

## Next Recommended Steps (in order)
1. Skeleton runs on this PC. Jira `list_stories` is wired, but there is no Jira account yet. Do not ask for credentials until one exists.
2. Add AGENTS.md and this file to the project root. Done.
3. Read-only `list_stories` is wired. Writes stay blocked until a later confirmed change.
4. Improve Playwright runner with basic step generation and screenshot evidence.
5. Add a simple local chat UI (Gradio is fastest).
6. Implement security-level isolation for browser contexts.
