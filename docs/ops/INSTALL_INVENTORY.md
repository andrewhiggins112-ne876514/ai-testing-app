# Install inventory (what helps this project)

Legend: **H** = you must do (account/installer). **A** = PM/agent can do once local worker or IDE agent has PC access. **Later** = wait for a blocker.

| Item | Who | Status / notes |
|------|-----|----------------|
| Cursor Desktop | H | Installed |
| Git + GitHub repo access | H | Working |
| Python venv + requirements | H/A | Working |
| Ollama + 7B/8B model | H | Working (free app runtime) |
| Playwright Chromium | H/A | Per README |
| `scripts/restart_ui.cmd` | A shipped | Double-click UI restart |
| Cursor CLI + My Machines worker | H | Do next — see `MY_MACHINES.md` |
| Node.js LTS | H | Needed only for GitHub/Atlassian MCP (`npx`) |
| GitHub MCP + PAT env var | H | Optional; IDE git is enough without it |
| Atlassian / Jira MCP | H Later | Needs a real Jira account first |
| App Jira credentials in local settings | H Later | `%LOCALAPPDATA%\ai_testing_app\settings.json` — never in git |
| Cursor Teams Jira @Cursor assign | Later | Not for solo Grok Premium |
| AFK Pilot / browser Grok guide | Retired | Do not re-enable daily paste loop |

## Jira epics / stories

Product path (preferred for the testing app): `plugins/jira_plugin.py` once you have an account and save URL/token locally.  
Coding-assist path: Atlassian MCP in Cursor after Node + account.

Until you say a Jira account exists, PM will **not** ask for tokens. We can still design epic/story structure offline in the roadmap.

## Approval requests (PM)

Say **yes** to any of these and we proceed in the next slice:

1. My Machines worker setup (you run the three PowerShell lines in `MY_MACHINES.md`).
2. Install Node.js LTS on the home PC (for MCP).
3. Create a fine-scoped GitHub PAT for MCP (optional).
4. When ready: create/use a Jira site and wire read-only list first, then epics/stories.
