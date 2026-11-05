# How We Work (PM-managed Cursor team)

**Goal:** you speak in **one place** (this PM chat). The PM does work directly or delegates to agents. **No copy-paste** between browser Grok, AFK Pilot, and other Cursor coding chats.

## Your job (human)

1. Tell the PM what you want (goals, preferences, approvals).  
2. Confirm when asked (credentials, Jira writes, deletes, security).  
3. On your PC when told: `git pull`, run the app, say if the UI looks wrong.  
4. Do **not** paste prompts into other AIs unless the PM explicitly asks (rare).

## PM job (this chat)

- Scope slices, fill blanks, prioritise, advise.  
- Implement work directly **or** dispatch agents (same run — you never paste).  
- Merge to `main` when push access allows.  
- Report back: what landed, what to pull/run, what’s next.

## Agent roster (`.cursor/agents/`)

| Agent | Model | Job |
|-------|--------|-----|
| implementer | Grok 4.7 | Feature/code slices |
| ui-orb | Grok 4.7 | Gradio / energy-orb slices |
| doc-keeper | Grok 4.5 | PROJECT_MEMORY / ROADMAP / ops docs |
| verifier | Grok 4.5 | Tests + skeptical review |
| explorer-cheap | Grok 4.5 | Find files; short summaries |
| architect | Grok 4.7 | Design-only trade-offs |

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

## After each slice (PM checklist)

- [ ] One logical change  
- [ ] Tests or clear manual check  
- [ ] Memory/roadmap updated  
- [ ] Merged / pushed when possible  
- [ ] Human told: `git pull` + how to verify  
