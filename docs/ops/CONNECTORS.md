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
4. **Disable or ignore** the Marketplace **Atlassian** plugin OAuth (“Needs login” / “failed to exchange tokens”). That plugin is a **different** server from your user `atlassian` entry. OAuth token exchange is known-broken on this machine (`401 after successful authentication` in MCP logs).
5. Fully quit and reopen Cursor. In Tools & MCP, trust the entry named **`atlassian`** that came from `%USERPROFILE%\.cursor\mcp.json` (API token / Basic) — **not** the plugin that asks for browser login.

### Which MCP status to trust (this PC)

| What you see in Tools & MCP | Source | Trust? |
|-----------------------------|--------|--------|
| **`context7`** (stdio / no browser login) | User `mcp.json` | **Yes** — agents use `user-context7` |
| **Context7** plugin “Local Error” / terminated / Needs auth | Marketplace OAuth | **Ignore** — turn off if it confuses you |
| **`atlassian`** (no browser login) | User `mcp.json` API token | **Yes** — agents use `user-atlassian` |
| **Atlassian** plugin Needs login / token exchange fail | Marketplace OAuth | **Ignore** — do not use for setup |

Verified 2026-11-18 from Cursor MCP logs: `user-context7` connected via stdio; `user-atlassian` connected via HTTP API token; both plugin OAuth paths fail.

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

Marketplace **Context7** plugin uses **OAuth only** (`/mcp/oauth`). Cloud can show Connected while local stays Error with **no place to paste a key**. That is expected — do **not** hunt for a token box on the plugin.

**Where your API key goes (you must supply it once):**

| Place | Path / action | Notes |
|-------|----------------|-------|
| **Preferred** | PowerShell env, then run setup script | `$env:CONTEXT7_API_KEY = 'ctx7sk-...'` then `.\scripts\setup_context7_mcp_auth.ps1` |
| **Durable local** | `%LOCALAPPDATA%\ai_testing_app\settings.json` key `context7_api_key` | Same store as other local secrets; never commit |
| **Written by script** | `%USERPROFILE%\.cursor\mcp.json` server name **`context7`** | User-only MCP file; **not** the repo; workspace `.cursor/mcp.json` stays empty |

Get a key: https://context7.com/dashboard (starts with `ctx7sk-`).

```powershell
$env:CONTEXT7_API_KEY = 'ctx7sk-...'   # paste YOUR key
powershell -ExecutionPolicy Bypass -File .\scripts\setup_context7_mcp_auth.ps1
```

Default transport is **local stdio** (`npx @upstash/context7-mcp`) — avoids Cursor `streamableHttp … terminated` noise common on this Windows box. Use `-Http` only if you want the remote URL again.

After the script: **fully quit and reopen Cursor** → Tools & MCP → enable **`context7`** (stdio). Ignore plugin OAuth Local Error / terminated logs on the Marketplace server.

**Honest note:** an earlier agent session used `npx ctx7 login` (browser device code) which could place a key without you pasting one into chat. If you want **your** dashboard key instead, run the commands above — the script overwrites the `context7` entry.

## Add when ready (do not rush)

| Connector | When | How |
|-----------|------|-----|
| Cursor Cloud Agents | Overnight PR/CI style work | Dashboard GitHub install; same Premium pool — use sparingly |
| Cursor ↔ Jira ticket assign | Teams/Enterprise + Rovo | Skip for now as solo Premium |

## Product vs IDE

- **IDE MCP** helps *you* while coding.
- **App plugins** (`plugins/jira_plugin.py`) help *end users* of the testing agent and must stay local-first.

Disable unused MCP servers — each tool schema burns context tokens.
