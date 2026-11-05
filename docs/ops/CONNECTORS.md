# Connectors (MCP and integrations)

## Already templated

`.cursor/mcp.json` includes **GitHub MCP** using `${env:GITHUB_PERSONAL_ACCESS_TOKEN}`.

On the home PC:
1. Create a fine-scoped GitHub PAT (repo as needed).
2. Set the env var in Windows User environment variables — **not** in the repo.
3. Restart Cursor. Enable the server under Customize → MCP only when you need it.

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
