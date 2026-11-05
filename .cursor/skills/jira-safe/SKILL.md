---
name: jira-safe
description: Safe Jira work for this app — local settings, confirmation gates, no secrets in git. Use when editing jira_plugin or discussing Atlassian MCP.
---

# Jira safe handling

## Product path (preferred)

- Credentials only in local settings store (`jira_url`, `jira_api_token`, `jira_email` for Cloud).
- Reads OK when configured. Writes stay two-step confirm (`yes` / `confirm`).
- Do not ask for URL/token until the user says a Jira account exists.
- Never log tokens. Never commit settings.

## Cursor MCP (optional, IDE only)

- Use env-based auth in `.cursor/mcp.json` — no secrets in the file.
- MCP is for coding assistance; the product must still work local-first without Cursor.
- Disable the server when unused (tool schemas cost tokens).

## When changing `plugins/jira_plugin.py`

- Keep confirmation gates.
- Add/extend focused tests under `tests/`.
- Prefer `/implementer` + `/verifier`.
