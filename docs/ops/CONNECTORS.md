# Connectors (MCP and integrations)

## Already templated

`.cursor/mcp.json` includes **GitHub MCP** using `${env:GITHUB_PERSONAL_ACCESS_TOKEN}`.

**Prerequisite:** Node.js LTS must be installed so `npx` works in a normal PowerShell (`node -v` and `npx -v`). Without Node, enabling github MCP fails with `'npx' is not recognized`. That is optional — git in the Cursor IDE terminal is enough for day-to-day work.

On the home PC (only if you want MCP):
1. Install Node.js LTS from https://nodejs.org (default options). Close and reopen Cursor.
2. Create a fine-scoped GitHub PAT (repo as needed).
3. Set `GITHUB_PERSONAL_ACCESS_TOKEN` in Windows User environment variables — **not** in the repo.
4. Restart Cursor. Enable the server under **Agents window → Customize → MCP** only when you need it.
5. If it fails, leave the toggle **off** and keep using IDE git.

## Add when ready (do not rush)

| Connector | When | How |
|-----------|------|-----|
| Atlassian / Jira MCP | After you have a Jira account | Prefer Cursor Marketplace “Atlassian”; auth via OAuth/env — never paste tokens into chat or `mcp.json` |
| Cursor Cloud Agents | Overnight PR/CI style work | Dashboard GitHub install; same Premium pool — use sparingly |
| Cursor ↔ Jira ticket assign | Teams/Enterprise + Rovo | Skip for now as solo Premium |

## Product vs IDE

- **IDE MCP** helps *you* while coding.
- **App plugins** (`plugins/jira_plugin.py`) help *end users* of the testing agent and must stay local-first.

Disable unused MCP servers — each tool schema burns context tokens.
