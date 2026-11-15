# Cursor IDE capabilities & setup walkthrough

Use this to reduce long-chat amnesia and token burn: short chats + WORK_LOG handoff + the right MCP/plugins.

**Repo:** `D:\Projects\ai_testing_app`  
**Prefer:** Agent **IDE** chat (this window) for coding; Agent window for MCP/plugin toggles when needed.

---

## Why this matters for you

Long PM chats forget earlier decisions and burn Premium tokens. Prefer:

1. Say **“pick up where we left off”** (reads `docs/ops/WORK_LOG.md`).
2. Keep slices small; start a **fresh Agent chat** after each logical chunk.
3. Use **Supermemory** (once logged in) for cross-session recall instead of re-pasting history.
4. Use **GitHub / Atlassian MCP** for live repo/Jira instead of re-explaining state.

---

## Live connector preference (home PC)

| Prefer | Avoid / secondary |
|--------|-------------------|
| **user-atlassian** (Jira) | `plugin-atlassian-atlassian` until needed |
| **plugin-github-github** | Workspace `.cursor/mcp.json` GitHub npx (disabled; was erroring) |
| **IronBee DevTools browser** for app UI | `cursor-ide-browser` for app verification |
| Local Jira REST + `scripts/jira_kan_*.py` if MCP API-token fails | Giving up on Jira |

IronBee for this project: **Browser ON** · Node OFF · Backend OFF.

---

## Walkthrough A — Agent window (MCP / plugins)

### Open MCP settings

1. Open **Cursor**.
2. Open the **Agents** UI (Agent sidebar / Agents panel — not only the editor chat).
3. Go to **Tools & MCP** (or **Customize → MCP** / **Plugins** depending on your Cursor build).
4. You should see servers such as Atlassian, GitHub, Supermemory, IronBee, etc.

### A1. Supermemory (cross-chat memory) — do this first

**Status:** tools present but need login.

1. In a terminal (PowerShell):

   ```powershell
   cursor-supermemory login
   ```

2. Complete the browser login when prompted.
3. Back in Cursor: **Agents → Tools & MCP** → confirm **Supermemory** shows connected / authenticated.
4. Optional check: in a new Agent chat ask “search supermemory for ai_testing_app handoff” — it should not error on auth.
5. Agents already have an always-on Supermemory rule; after login, they can `supermemory_search` / `add` without you pasting old chats.

### A2. Atlassian / Jira

**Prefer connected `user-atlassian`.**

1. Agents → Tools & MCP → **Atlassian** / **user-atlassian**.
2. If it asks to authenticate, complete OAuth or API-token flow.
3. Quick test in Agent chat: “List my Atlassian resources” or “search Jira project KAN”.
4. If you see **“don’t have permission to connect via API token”** on search/create:
   - Do **not** treat Jira as unavailable.
   - Agents must use **REST** via `%LOCALAPPDATA%\ai_testing_app\settings.json` or `scripts/jira_kan_*.py` (see `jira-safe` skill).
5. Leave **plugin-atlassian** unauthenticated if `user-atlassian` already works (avoids duplicate schemas / token cost).

Optional Rovo MCP token setup (if OAuth flaky): `docs/ops/CONNECTORS.md` + `scripts/setup_atlassian_mcp_auth.ps1`.

### A3. GitHub

**Prefer `plugin-github-github`.**

1. Agents → Tools & MCP → **GitHub** → Sign in / connect.
2. Confirm account `andrewhiggins112-ne876514` (or your current login).
3. Test: “List PRs on ai-testing-app” or “get me for GitHub”.
4. Workspace file `.cursor/mcp.json` is now **empty** so the broken `npx` GitHub MCP does not compete. Optional template: `.cursor/mcp.json.example` (needs Node + `GITHUB_PERSONAL_ACCESS_TOKEN` user env) — only if you insist on the npx server.

### A4. IronBee DevTools (browser)

1. Install/enable the **IronBee DevTools** Cursor extension if not already.
2. Extension settings: `ironbeeDevTools.platform.browser.enable` = **true**.
3. Leave Node/Backend **off** unless you need them (saves MCP noise).
4. Agents are ruled to use IronBee for verifying this app’s UI — not Cursor’s built-in browser.

### A5. Context7 (library docs)

**Status:** often errors until reconnected.

1. Agents → Tools & MCP → **Context7** → reconnect / re-auth / toggle off→on.
2. If still failing: disable it (agents can use Context7 when available; otherwise WebSearch/docs in-repo).
3. Not required for day-to-day product coding.

### A6. cursor-origin (Cursor-hosted repos)

Only if you use Origin-hosted remotes. If MCP shows error and you use **GitHub** remotes only, ignore Origin.

### A7. Computer Use

Usually available as **cursor-computer-use**. No extra login. Use for desktop Ollama Settings UI, etc. Prefer IronBee for in-app web UI.

---

## Walkthrough B — IDE (editor) side

### B1. Open the correct folder

1. **File → Open Folder** → `D:\Projects\ai_testing_app` (not any old C: path).
2. Confirm status bar / Explorer root is D:.
3. New Agent chats inherit this workspace (MCP + rules + skills).

### B2. Rules & skills (no login)

Already in repo:

- Always-on: `work-log-handoff`, `00-core-efficiency`, IronBee, Supermemory rule (when plugin on), etc.
- Skills: `jira-safe`, `slice-workflow`, `run-local-stack`, `orb-slice`, `update-memory`.

You do not configure these in the UI beyond keeping the folder open.

### B3. Start a cheap coding chat

1. **Ctrl+L** / Agent chat in the IDE.
2. Paste output of:

   ```powershell
   cd D:\Projects\ai_testing_app
   .\venv\Scripts\python.exe scripts\next_prompt.py
   ```

   Or type: **pick up where we left off**.
3. Prefer Auto/Composer for small slices; escalate only when stuck.

### B4. Local app Jira (product), separate from MCP

1. Settings file: `%LOCALAPPDATA%\ai_testing_app\settings.json`  
   Keys: `jira_url`, `jira_email`, `jira_api_token` (never commit).
2. Product agent writes still two-step confirm.
3. Cursor coding agents may use the same file for REST when MCP fails.

### B5. Ollama (product runtime)

1. App: `D:\Program Files\Ollama`.
2. Settings → **Model location** = `D:\Program Files\Ollama\models`.
3. Default model for app: `qwen2.5-coder:7b`.

---

## Needs attention checklist

| Item | Action | IDE / Agent window |
|------|--------|--------------------|
| Supermemory | `cursor-supermemory login` | Both (login CLI; verify in Agents MCP) |
| Context7 | Reconnect or disable | Agents → MCP |
| Workspace GitHub MCP | Disabled in `.cursor/mcp.json` | Prefer GitHub plugin |
| plugin-atlassian | Optional | Skip if user-atlassian works |
| IronBee Node/Backend | Keep off unless needed | Extension settings |
| cursor-origin | Ignore unless using Origin remotes | Agents → MCP |

---

## After setup — recommended workflow

1. Fresh Agent IDE chat per slice.  
2. “Pick up where we left off” → implement KAN story.  
3. Log WORK_LOG + Jira comment.  
4. Commit when asked.  
5. Supermemory: save important decisions when you say “remember this”.  

Related: `docs/ops/CONNECTORS.md`, `docs/ops/HOW_WE_WORK.md`, `docs/ops/WORK_LOG.md`, `.cursor/skills/jira-safe/SKILL.md`.
