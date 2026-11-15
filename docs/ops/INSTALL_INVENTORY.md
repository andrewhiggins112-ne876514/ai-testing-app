# Install inventory (what helps this project)

Legend: **H** = you must do (account/installer). **A** = PM/agent can do once local worker or IDE agent has PC access. **Later** = wait for a blocker.

| Item | Who | Status / notes |
|------|-----|----------------|
| Cursor Desktop | H | Installed |
| Git + GitHub repo access | H | Working |
| Python venv + requirements | H/A | Working |
| Ollama + 7B/8B model | H | Working — `D:\Program Files\Ollama`, models via Settings/`OLLAMA_MODELS` |
| Playwright Chromium | H/A | Per README |
| `scripts/restart_ui.cmd` | A shipped | Double-click UI restart |
| Cursor CLI + My Machines worker | H | Do next — see `MY_MACHINES.md` |
| Node.js LTS | H | Needed only for GitHub/Atlassian MCP (`npx`) |
| GitHub MCP + PAT env var | H | Prefer **GitHub plugin** MCP; workspace npx MCP disabled |
| Atlassian / Jira MCP | H | Site live; MCP may need scoped token; REST via local settings works |
| App Jira credentials in local settings | H | `%LOCALAPPDATA%\ai_testing_app\settings.json` — never in git; project **KAN** |
| Cursor Teams Jira @Cursor assign | Later | Not for solo Grok Premium |
| AFK Pilot / browser Grok guide | Retired | Do not re-enable daily paste loop |

## Jira epics / stories

- Site: `https://ai-testing-lab.atlassian.net` — project **KAN**.  
- Template: `docs/ops/JIRA_TICKET_TEMPLATE.md`. Enrich: `python scripts/jira_kan_enrich.py`.  
- Product path: `plugins/jira_plugin.py` (two-step confirm on writes).  
- Handoff: `docs/ops/WORK_LOG.md`.

## Approval requests (PM)

Say **yes** to any of these and we proceed in the next slice:

1. My Machines worker setup (you run the three PowerShell lines in `MY_MACHINES.md`).
2. Install Node.js LTS on the home PC (for MCP) if not already.
3. Create a fine-scoped GitHub PAT for MCP (optional).
