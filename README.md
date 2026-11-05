# AI Testing Application

Local-first AI testing agent with a local chat UI.

## Quick start (on your laptop)

1. Install dependencies (PowerShell):
   ```powershell
   cd C:\Users\User\ai_testing_app
   py -3 -m pip install -r requirements.txt
   py -3 -m playwright install chromium
   ```

2. A local model must be present. This machine already has `qwen2.5-coder:7b`, which is the default. To use another model: `$env:OLLAMA_MODEL="qwen3:8b"` after `ollama pull qwen3:8b`.

3. Run the backend:
   ```powershell
   py -3 -m uvicorn main:app --reload
   ```

4. Health check:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```

Jira read-only settings live in `%LOCALAPPDATA%\ai_testing_app\settings.json` (not in git). Set `jira_url`, `jira_api_token`, and `jira_email` for Cloud. Then ask the agent to list stories for a project key.

## Structure
- `agent/` — core tool-calling agent
- `plugins/` — Playwright, Jira, etc.
- `settings/` — local config store
- `ui/` — Gradio UI + energy orb
- `main.py` — FastAPI server
- `docs/ops/` — how we work, team, roadmap, connectors (Cursor workflow)
- `.cursor/` — rules, agents, skills, MCP template

## Cursor workflow
Primary development is in Cursor (not browser Grok + AFK Pilot copy-paste). See `docs/ops/HOW_WE_WORK.md`. Prefer Composer/Auto for coding; Ollama stays local for the product runtime.

Security levels, full document ingestion, broader self-healing, and richer UI come next as plugins.
