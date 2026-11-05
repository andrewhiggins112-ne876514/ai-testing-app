# Cursor setup for beginners (Windows)

Do **one step at a time**. Reply to the PM chat when a step is done before starting the next.

After setup, work **only in Cursor**. Stop: browser Grok → copy → AFK Pilot → paste back.

---

## Step 1 — Merge PR #1 and pull onto your PC

**Goal:** get the new `.cursor/` folder and `docs/ops/` onto your machine.

1. In a browser, open: https://github.com/andrewhiggins112-ne876514/ai-testing-app/pull/1  
2. Open **Files changed** and skim (optional).  
3. Click **Merge pull request** → **Confirm merge**.  
4. Optional: **Delete branch**.  
5. Open **Cursor** → **File → Open Folder…** → select your local `ai-testing-app` folder → **Trust** if asked.  
6. Open a terminal in Cursor: **Terminal → New Terminal** (or `` Ctrl+` ``).  
7. Run:
   ```powershell
   git checkout main
   git pull origin main
   ```
8. In the left file list, confirm you see:
   - `.cursor\rules`
   - `.cursor\agents`
   - `.cursor\skills`
   - `docs\ops\HOW_WE_WORK.md`

**Done when:** those folders/files exist locally. Tell the PM chat: `Step 1 done`.

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

## Step 4 — Grok “guide bot” check-in — DONE

**Decision (2026-11-05): retire as daily driver.**  
Cursor PM chat + `PROJECT_MEMORY.md` + `ROADMAP.md` replace it. Optional read-only cross-check for one week, then ignore.

Send the bot this freeze message (optional but tidy):

```text
Thanks — daily guide duty moves to Cursor + PROJECT_MEMORY.md. Please stop giving AFK Pilot prompts unless I explicitly ask for an archive lookup.
```

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
