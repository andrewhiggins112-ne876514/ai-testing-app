---
name: jira-safe
description: Safe Jira work for this app — local settings, confirmation gates, REST fallback when MCP fails. Use when editing jira_plugin or discussing Atlassian MCP.
---

# Jira safe handling

## Product path (preferred)

- Credentials only in local settings store (`jira_url`, `jira_api_token`, `jira_email` for Cloud).
- Site live: `https://ai-testing-lab.atlassian.net` project **KAN**.
- Reads OK when configured. Writes stay two-step confirm (`yes` / `confirm`) for the product agent.
- After a coding slice: **required** Jira close-out (not optional):
  1. Story comment stating **what the agent did** to complete the story (implementation + files + verify).
  2. Linked **test** ticket (`issuetype=test`, Relates): comment with unit-test evidence; mark **Done**.
  3. Mark story **Done** only after the story comment is posted.
  Prefer: `python scripts/jira_kan_slice_closeout.py --story KAN-XX --done "…" --files "…" --verify "…" --pytest-cmd "…" --mark-done`
- **KAN issue types:** Epic / Story / **Task** (dev work under a story — e.g. one Task per FR) / **`test`** (verification) / **Bug** (defects) / Subtask. Do not use Task for tests or bugs.
- **Bugs found during development (mandatory):** raise a **Bug**, Relates-link to Story + test ticket (create test if missing). Standing authorization. Symptom / expected vs actual / environment / numbered replication steps. When fixed: Fix comment + Done.
  See Bug section in `docs/ops/JIRA_TICKET_TEMPLATE.md`.
- Seed unfinished FR backlog: `python scripts/jira_kan_seed_backlog.py` (idempotent; `--dry-run` / `--close-orphan-tests`).
- Migrate legacy Task+labels: `python scripts/jira_kan_migrate_issue_types.py`.
- Never log tokens. Never commit settings.
- Ticket layout: `docs/ops/JIRA_TICKET_TEMPLATE.md`; enrich with `scripts/jira_kan_enrich.py`.

## Cursor agents: MCP failure → REST fallback (do not give up)

Atlassian MCP (`user-atlassian` / plugin) often fails with **“You don't have permission to connect via API token”** even when Jira is configured. That is **not** “no Jira access”.

**Required fallback:**

1. Use **Jira Cloud REST** with Basic auth from `%LOCALAPPDATA%\ai_testing_app\settings.json` (`jira_url` + `jira_email` + `jira_api_token`).
2. Prefer existing helpers (they never print the token):
   - `python scripts/jira_kan_slice_closeout.py` — **slice close-out**: agent completion comment + linked test Task evidence + Done
   - `python scripts/jira_kan_enrich.py` — descriptions
   - `python scripts/jira_kan_progress_sync.py` — comments + epic status
   - `python scripts/jira_kan_rebuild.py` — backlog structure
   - `python scripts/jira_kan_seed_backlog.py` — seed open Stories/tests from unfinished FRs
3. Or a short `httpx` script in `scripts/` following those patterns (`ssl.create_default_context()`, rate-limit backoff on 429).
4. **Never** echo/log the API token. **Never** paste credentials into chat.
5. Only stop if REST also fails (401/403 after valid settings) — then tell the human settings need fixing.

`getAccessibleAtlassianResources` succeeding does **not** mean search/create will work; always fall back to REST on MCP tool errors.

## Cursor MCP (optional, IDE only)

- Prefer API-token MCP over Marketplace OAuth when OAuth hangs after browser consent.
- Setup: `scripts/setup_atlassian_mcp_auth.ps1` → user `%USERPROFILE%\.cursor\mcp.json` only (secret stays out of git).
- Use a Rovo MCP **scoped** token (`agent-interface`); classic Jira tokens often 401 on `mcp.atlassian.com`.
- MCP is for coding assistance; the product must still work local-first without Cursor.
- Disable the server when unused (tool schemas cost tokens).

## When changing `plugins/jira_plugin.py`

- Keep confirmation gates.
- Add/extend focused tests under `tests/`.
- Prefer `/implementer` + `/verifier`.
