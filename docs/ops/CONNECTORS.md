# Connectors (MCP and integrations)

**Full walkthrough (IDE + Agent window):** [`IDE_CAPABILITIES.md`](IDE_CAPABILITIES.md)

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

If Cursor Atlassian MCP errors with **permission / API token** (common on this site):

- **Do not give up.** Use Jira REST + `%LOCALAPPDATA%\ai_testing_app\settings.json` instead.
- Helpers: `scripts/jira_kan_enrich.py`, `scripts/jira_kan_progress_sync.py`, `scripts/jira_kan_rebuild.py`.
- Full rules: `.cursor/skills/jira-safe/SKILL.md`.

## Add when ready (do not rush)

| Connector | When | How |
|-----------|------|-----|
| Cursor Cloud Agents | Overnight PR/CI style work | Dashboard GitHub install; same Premium pool — use sparingly |
| Cursor ↔ Jira ticket assign | Teams/Enterprise + Rovo | Skip for now as solo Premium |

## Product vs IDE

- **IDE MCP** helps *you* while coding.
- **App plugins** (`plugins/jira_plugin.py`) help *end users* of the testing agent and must stay local-first.

Disable unused MCP servers — each tool schema burns context tokens.
