# Cursor setup for beginners (Windows)

Do **one step at a time**. Reply to the PM chat when a step is done before starting the next.

After setup, work **only in Cursor**. Stop: browser Grok → copy → AFK Pilot → paste back.

---

## Step 1 — Merge PR #1 and get a real folder on your PC

**Goal:** a normal Windows folder with the repo (including `.cursor/` and `docs/ops/`) that Cursor can open.

### 1A — Merge the PR (browser)

1. Open: https://github.com/andrewhiggins112-ne876514/ai-testing-app/pull/1  
2. Optional: skim **Files changed**.  
3. **Merge pull request** → **Confirm merge**.  
4. Optional: **Delete branch**.

### 1B — Do you already have the folder? (optional check)

VS Code almost always opened a folder on disk somewhere. If you still use VS Code with this project:

1. Open the project in VS Code.  
2. **File → Open Folder…** shows the path, or right-click a file → **Reveal in File Explorer**.  
3. If you find it, you can use that path in 1D instead of cloning — then only `git pull` in 1E.

If you are not sure, **skip 1B and clone fresh (1C)**. That is the safe beginner path.

### 1C — Clone from GitHub (if no local folder)

1. Install Git for Windows if needed: https://git-scm.com/download/win (restart Cursor after install).  
2. Open **PowerShell** (Windows search → PowerShell).  
3. Prefer a simple location (change `User` if your Windows username differs):

```powershell
cd $HOME
git clone https://github.com/andrewhiggins112-ne876514/ai-testing-app.git ai_testing_app
cd ai_testing_app
git checkout main
git pull origin main
```

4. Your folder is now: `C:\Users\<YourWindowsUsername>\ai_testing_app`  
   (PowerShell: `pwd` prints the exact path.)

If `git clone` asks you to sign in to GitHub, complete the browser/login prompt, then re-run the clone if it failed.

### 1D — Open that folder in Cursor  ← resume here if you were stuck on “Open Folder”

1. Open **Cursor**.  
2. **File → Open Folder…**  
3. Browse to `ai_testing_app` (from 1B or 1C) → **Select Folder**.  
4. If Windows/Cursor asks about trusting the folder → **Yes / Trust**.  
5. Left sidebar should list files such as `AGENTS.md`, `PROJECT_MEMORY.md`, `main.py`.

### 1E — Confirm ops files are present

1. In Cursor: **Terminal → New Terminal** (or `` Ctrl+` ``).  
2. Run:

```powershell
git checkout main
git pull origin main
dir .cursor
dir docs\ops
```

3. Confirm you see:
   - `.cursor\rules`
   - `.cursor\agents`
   - `.cursor\skills`
   - `docs\ops\SETUP_FOR_BEGINNERS.md`

**Done when:** Cursor has the folder open and those paths exist. Tell the PM chat: `Step 1 done`.

**Note:** A separate **Grok bot app** (e.g. downloaded from a link inside Cursor) is not the same as this repo folder. We deal with that in **Step 4**. Do not use it for the daily AFK copy-paste loop meanwhile.

---

## Step 2 — Learn the Cursor panels (no coding yet)

1. Open Agent: **Ctrl+I**.  
2. Find **New Chat** (**+**) at the top of the chat panel.  
3. Find the **model** name at the bottom of the input — click it. Prefer **Auto** or **Composer**.  
4. Find the **mode** control (or press **Shift+Tab**): **Ask** / **Plan** / **Agent**.  
5. In the chat box type `/` — you should see skills and agents (e.g. `slice-workflow`, `verifier`, `ui-orb`).  
6. Sidebar **Customize → Rules** — project rules should list.  
7. **Customize → Skills** — project skills should list.

**Done when:** you can open a new chat, switch model/mode, and see `/` items. Tell PM: `Step 2 done`.

---

## Step 3 — Name this chat “PM” and do a dry run

1. Keep **this** conversation (or start one) as your **PM chat** — planning only, not big code edits.  
2. In a **new** chat (**+**), paste:
   ```text
   Read PROJECT_MEMORY.md and AGENTS.md once. In 5 bullets, what is Current State and what is the next roadmap slice? Do not edit files.
   ```
3. Mode: **Ask**. Model: **Auto** or **Composer**.  
4. Check the reply mentions orb slice 4 / UI-5 presets (or similar).  
5. Close that Ask chat (or leave it). Return to the PM chat.

**Done when:** Ask chat answered from project memory without editing. Tell PM: `Step 3 done`.

---

## Step 4 — Grok “guide bot” check-in (decide keep / replace)

You already have a live Grok bot that remembers project state and writes the next AFK prompt.

1. Open that Grok bot in the browser.  
2. Ask it: `Summarise your job in 5 bullets and paste your standing instructions if you can.`  
3. Copy its reply into the PM chat (this Cursor chat).  
4. PM will decide: keep as backup, rewrite for Cursor, or retire in favour of `PROJECT_MEMORY.md` + ROADMAP + PM chat.

**Do not** go back to daily AFK copy-paste while we decide.

**Done when:** instructions (or a clear summary) are pasted into PM chat. Tell PM: `Step 4 done` plus the paste.

---

## Step 5 — GitHub MCP (optional; skip if tired)

Only if you want Cursor to talk to GitHub via tools.

1. Create a GitHub **Personal Access Token** (fine-scoped). **Do not paste it into chat.**  
2. Windows search → **Edit the system environment variables** → **Environment Variables…**  
3. Under **User variables** → **New…**  
   - Name: `GITHUB_PERSONAL_ACCESS_TOKEN`  
   - Value: *(your token)*  
4. **File → Exit** Cursor completely, then reopen the project.  
5. **Customize → MCP** → enable **github**.  
6. If it errors: **View → Output** → **MCP Logs**.

**Done when:** github MCP shows connected, or you say `Step 5 skipped`.

---

## Step 6 — First real coding slice (only after Steps 1–3)

1. **New chat**. Model: **Composer** or **Auto**.  
2. Paste:
   ```text
   Read PROJECT_MEMORY.md and AGENTS.md once. Continue from Current State.
   Slice UI-5 only: orb preset save/load named configs.
   Prefer Composer. Use /ui-orb then /verifier.
   Confirm before credentials / Jira writes / deletes / security changes.
   ```
3. If it plans multi-file work: use **Plan**, approve, then **Agent**.  
4. After it finishes: run `/verifier` (type `/` and pick verifier).  
5. Come back to the **PM chat** with a short “what landed” note.

**Do not start Cursor Cloud Agents yet.** Local Agent chat only.

---

## Quick map

| Old habit | New habit |
|-----------|-----------|
| Grok browser plans | Cursor **PM chat** |
| Guide bot → next AFK prompt | `ROADMAP.md` + PM + slice paste |
| AFK Pilot edits | Cursor **Agent** chat (Composer) |
| Long one-thread everything | New chat per slice |
| Paste secrets into chats | Windows env / local settings store only |
