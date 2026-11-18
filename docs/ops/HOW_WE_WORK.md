# How We Work (two Cursor chat lanes)

**Goal:** **No copy-paste** between browser Grok, AFK Pilot, and Cursor. Use the right chat for the job.

## Two chats

| Lane | Open | Say | Does |
|------|------|-----|------|
| **Build** | Fresh default Agent chat | **“pick up where we left off”** | Coding slices — unchanged (pull, Active story, implement, verify, Jira close-out, push) |
| **Council Room** | Fresh Agent chat → **`/council`** + your ask | “review…”, “creative idea…”, “open the room…” | Multi-persona review/creative debate; may update docs/Jira/rules after you agree — **no product feature coding** |

Full council guide: `docs/ops/ADVISORY_COUNCIL.md`. Roster: `docs/ops/TEAM.md`.

## Your job (human)

1. **Build:** fresh Agent chat → **“pick up where we left off”** (or `python scripts/next_prompt.py`).  
2. **Review / creative / path change:** fresh Agent chat → type **`/council`** then your ask.  
3. Confirm when asked (credentials, Jira writes, deletes, security, browser logins).  
4. You do **not** need to run git. Build chats **pull `main`** at pick-up and **commit + push** when a slice finishes. Optionally run **`desktop_app.py`** to look; agents verify that native window with **tiered** evidence (pytest/API first; Computer Use for visual/occlusion only — see `AGENTS.md` / tooling-use; pause Ollama during CU windows on the home PC). If Computer Use cannot confirm and you must check by hand, the agent should already have the app running, data/stubs seeded, and a short numbered step list for you — you only follow and confirm.  
5. Do **not** paste coding prompts into browser Grok / AFK Pilot.  
6. Workspace folder must be `D:\Projects\ai_testing_app`.

## Build PM job

- Scope slices, fill blanks, prioritise, advise.  
- Implement directly **or** dispatch build agents (same run — you never paste).  
- Report back: what landed, how to check the app, what’s next.  
- Never ask the human to `git pull` / commit / push.

## Build agent roster (`.cursor/agents/`)

| Agent | Model | Job |
|-------|--------|-----|
| implementer | Grok 4.7 | Feature/code slices |
| ui-orb | Grok 4.7 | Gradio / energy-orb slices |
| doc-keeper | Grok 4.5 | PROJECT_MEMORY / ROADMAP / ops docs |
| verifier | Grok 4.5 | Tests + skeptical review |
| explorer-cheap | Grok 4.5 | Find files; short summaries |
| architect | Grok 4.7 | Design-only trade-offs |
| **council** (+ `council-*`) | 4.7 / 4.5 | **Separate chat** — Advisory Council Room only |

Product runtime LLM stays **Ollama on the home PC** — that part is actually free.

**Grok guide bot:** retired as daily driver. Do not resume AFK paste loops.

## Model policy (Grok Premium only)

User pays **Grok Premium** only. Do **not** assume Composer/Claude/GPT/Copilot are free inside Cursor.

1. **All Cursor agents stay on the Grok family** (4.7 for coding/UI/architecture; 4.5 for docs/explore/verify to spare the pool).  
2. **Composer is not free** — it still uses the same Cursor/Grok weekly pool; we do not use it as a “free” option.  
3. **Claude / GPT / Copilot** are separate paid products inside Cursor Agent — do not assign them.  
4. **Ollama** = free for the *app* chat/runtime only, not for Cursor coding agents.  
5. Never parallelise agents unless slices are independent.  
6. GitHub MCP needs Node/`npx` — optional; IDE git is enough.

## Connectors

See `docs/ops/CONNECTORS.md`. Customize/MCP is in the **Agents** window, not the IDE window.

**Library docs:** before inventing third-party API calls, follow the Context7 / venv gate in `AGENTS.md` (Council 2026-11-18) — training memory is last resort.

## After each slice (PM checklist)

- [ ] One logical change  
- [ ] Tests or clear manual check  
- [ ] Memory/roadmap updated  
- [ ] `docs/ops/WORK_LOG.md` entry + Active slice advanced  
- [ ] Jira **story comment**: what the **agent did** to complete the story + files + verify  
- [ ] Linked **test** ticket (`issuetype=test` Relates): unit-test evidence comment + Done (create/link if missing)  
- [ ] Prefer `python scripts/jira_kan_slice_closeout.py --story KAN-XX … --mark-done`  
- [ ] **Bugs found during development (mandatory):** raise a **Bug** immediately (symptom + expected/actual + environment + numbered replication steps), Relates-link to Story + test ticket; when fixed, Fix comment then Done — never silently fix-only or leave the defect only in chat/WORK_LOG. **Task** = development work under a Story (e.g. per-FR); **`test`** = verification; **Bug** = defects  
- [ ] **Commit + `git push origin main`** (required; do not leave finished work unpushed)  
- [ ] Human told how to verify the app if useful — **never** told to `git pull` (next Agent chat pulls)  

## Continue next time

- **Build:** “pick up where we left off” → read WORK_LOG Active slice → implement that KAN story. Or: `python scripts/next_prompt.py`.  
- **Council:** **`/council`** → review or creative room (`docs/ops/ADVISORY_COUNCIL.md`).
