# Connectors (MCP and integrations)

## Workspace `.cursor/mcp.json`

Kept **empty** so the broken `npx` GitHub MCP does not error. Prefer the **GitHub Cursor plugin** MCP (`plugin-github-github`).

Optional template (needs Node + user env `GITHUB_PERSONAL_ACCESS_TOKEN`): `.cursor/mcp.json.example` — copy into `mcp.json` only if you deliberately want the npx server.

## Atlassian / Jira MCP (Cursor IDE)

OAuth via the Marketplace Atlassian plugin is flaky on this Windows box (browser consent OK, IDE stays Authenticating). Prefer **API-token MCP**:

1. Org admin: enable API-token auth for Rovo MCP (`admin.atlassian.com` → Security → Rovo MCP server).
2. Create a **scoped** MCP token (agent-interface), not a classic Jira-only token:  
   https://id.atlassian.com/manage-profile/security/api-tokens?autofillToken&expiryDays=max&appId=mcp&selectedScopes=all
3. Run (does not print secrets; writes **user** `%USERPROFILE%\.cursor\mcp.json` only):
   ```powershell
   $env:ATLASSIAN_MCP_API_TOKEN = '<paste-scoped-token>'
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_atlassian_mcp_auth.ps1
   ```
   Success = `PROBE: mcp initialize POST -> HTTP 200`. A HEAD `400` alone is a false negative (script now uses initialize).
4. Disable/ignore Marketplace Atlassian plugin OAuth so it does not fight the direct MCP entry.
5. Fully quit and reopen Cursor. Confirm Tools & MCP shows `atlassian` connected without a browser prompt.

Never commit tokens. Product Jira stays on local settings + `plugins/jira_plugin.py` (separate from IDE MCP).

### Agent fallback when MCP is blocked

If Cursor Atlassian MCP errors with **permission / API token** (common on this site; verified 2026-11-15):

- **Do not give up.** Use Jira REST + `%LOCALAPPDATA%\ai_testing_app\settings.json` instead.
- Helpers: `scripts/jira_kan_enrich.py`, `scripts/jira_kan_progress_sync.py`, `scripts/jira_kan_rebuild.py`.
- Full rules: `.cursor/skills/jira-safe/SKILL.md`.

### Verified preferences (2026-11-15)

- GitHub: **plugin-github-github** (workspace npx MCP disabled).
- Product UI: run **`desktop_app.py`** and verify with **Computer Use** (native window). Do not open the desktop shell in a browser.
- IronBee browser: AUT pages or Gradio-only; Node/Backend off.
- Supermemory: authenticated for this machine; use when available.
- Context7: **build-time IDE only** (Council 2026-11-18 stale-advice gate). Required when inventing/changing FastAPI / Pydantic / Playwright / Gradio / pywebview / Ollama HTTP / httpx calls — version-matched to the **venv**, not “latest.” On error: use installed package / official docs; do not block the slice; do not invent APIs. **Product runtime never calls Context7.** See `AGENTS.md` and `.cursor/skills/context7-use/SKILL.md`.

### Context7 local API key (plugin has no token field)

Marketplace **Context7** plugin uses **OAuth only** (`/mcp/oauth`). Cloud can show Connected while local stays Error with no place to paste a key.

**Reliable local path:** API key HTTP MCP entry named `context7` in **user** `%USERPROFILE%\.cursor\mcp.json` (never the repo; workspace `.cursor/mcp.json` stays empty).

1. Create/copy a key at https://context7.com/dashboard — or run `npx ctx7 login` then `npx ctx7 setup --cursor --mcp -y` (merges into user MCP; preserves atlassian/supermemory).
2. Or paste key and run (does not print the key; **merges** into existing user MCP servers):
   ```powershell
   $env:CONTEXT7_API_KEY = '<paste-key>'
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_context7_mcp_auth.ps1
   ```
   Optional: store `context7_api_key` in `%LOCALAPPDATA%\ai_testing_app\settings.json` (local only) and re-run without the env var.
3. Fully quit and reopen Cursor. Tools & MCP: confirm **`context7`** is green. Plugin OAuth Local Error can be ignored if that entry works.
4. Probe success = script prints `PROBE: mcp initialize POST -> HTTP 200`.

## Add when ready (do not rush)

| Connector | When | How |
|-----------|------|-----|
| Cursor Cloud Agents | Overnight PR/CI style work | Dashboard GitHub install; same Premium pool — use sparingly |
| Cursor ↔ Jira ticket assign | Teams/Enterprise + Rovo | Skip for now as solo Premium |

## Product vs IDE

- **IDE MCP** helps *you* while coding.
- **App plugins** (`plugins/jira_plugin.py`) help *end users* of the testing agent and must stay local-first.

Disable unused MCP servers — each tool schema burns context tokens.
