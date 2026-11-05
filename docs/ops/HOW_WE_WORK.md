# How We Work (Cursor replaces Grok + AFK Pilot)

**Goal:** one place for planning and coding, no copy-paste between tools, low token burn.

## Old loop (stop using)

1. Ask Grok in the browser for a prompt  
2. Paste into AFK Pilot in VS Code  
3. Paste results back to Grok  
4. Burn Premium credits on long, repeated context  

**Grok guide bot:** retired as daily driver (2026-11-05). It used to store memory in Grok and emit AFK Pilot paste-prompts. That role is now this repo (`PROJECT_MEMORY.md`, `ROADMAP.md`) + the Cursor PM chat. Do not paste its prompts into AFK Pilot anymore.

## New loop (default)

1. Talk to the **PM chat** in Cursor (this project chat or a fresh “PM” chat).  
2. PM scopes one **slice** (one logical change).  
3. Use **Plan mode** for anything that touches more than one file.  
4. Implement with **Composer / Auto** (cheap). Reserve frontier models for hard architecture only.  
5. Run `/verifier` (or ask for the verifier agent) after the slice.  
6. Update `PROJECT_MEMORY.md` Current State in the same PR when behaviour changes.  
7. **New chat** after each finished slice — do not keep week-long threads.

## Roles (who does what)

| Role | Where | Model preference | Job |
|------|--------|------------------|-----|
| You (human) | Cursor | — | Goals, approvals, Jira/security confirmations |
| PM | Parent Agent chat | Auto / Composer | Scope, prioritise, fill blanks, advise |
| Explorer | `/explorer-cheap` | Composer 2.5, readonly | Find files; short summaries only |
| Architect | `/architect` | Inherit (stronger when needed) | Design decisions; no drive-by coding |
| Implementer | `/implementer` or Agent mode | Composer 2.5 | One small diff |
| Verifier | `/verifier` | Composer 2.5, readonly | Tests + skepticism |
| UI Orb | `/ui-orb` | Composer 2.5 | Gradio + canvas orb slices only |

Product runtime LLM stays **Ollama on the home PC** (`qwen2.5-coder:7b` / `qwen3:8b`). That is separate from Cursor coding models.

## Token rules (non-negotiable)

- Prefer Ask/Plan before Agent when exploring.  
- One slice per chat when possible.  
- Do not re-read the whole repo; use explorer + targeted reads.  
- Skills load on demand — keep always-on rules short.  
- Disable unused MCP servers (every tool schema costs context).  
- No subagents in parallel unless slices are independent.

## Connectors

| Need | Use | Notes |
|------|-----|--------|
| Git / GitHub | Built-in + optional GitHub MCP | Token via env / Cursor secrets — never in repo |
| Atlassian / Jira (while coding) | Optional Atlassian MCP in Cursor | Only after you have an account; env-based auth |
| Jira inside the product | `plugins/jira_plugin.py` + local settings store | Product path; OFFICIAL/SECRET isolation later |
| AFK overnight PRs | Cursor Cloud Agent | Use sparingly; same credit pool |

See `.cursor/mcp.json` for the template. Do not commit real credentials.

## Session start phrase (paste into a new coding chat)

```text
Read PROJECT_MEMORY.md and AGENTS.md once. Continue from Current State.
One slice only. Prefer Composer. Confirm before credentials/Jira writes/deletes.
```

## Session end checklist

- [ ] Diff is one logical change  
- [ ] Tests for the changed behaviour pass (or new test added)  
- [ ] `PROJECT_MEMORY.md` Current State updated if behaviour changed  
- [ ] Chat closed / compacted — next slice = new chat  
