# Agent Team (PM-managed)

You talk only to the **PM**. Agents are workers the PM invokes — not separate chats you paste into.

## Roster

| Agent | File | Model | When |
|-------|------|--------|------|
| PM | (this parent chat) | Auto / stronger as needed | Always — your only conversation |
| implementer | `implementer.md` | Grok 4.7 | Backend / plugin / general code |
| ui-orb | `ui-orb.md` | Grok 4.7 | Gradio + orb |
| doc-keeper | `doc-keeper.md` | Composer 2.5 | Memory, roadmap, ops docs after a slice |
| verifier | `verifier.md` | Composer 2.5 | After implementation |
| explorer-cheap | `explorer-cheap.md` | Composer 2.5 | Discovery |
| architect | `architect.md` | Inherit | Multi-file / security design |

## Why these (including ones you didn’t ask for)

| Need | Agent |
|------|--------|
| Feature coding (you asked Grok) | implementer / ui-orb |
| Docs on a cheap model (you asked) | doc-keeper |
| Review on a cheap model (you asked) | verifier |
| Stop re-reading the whole repo | explorer-cheap |
| Hard design without burning Grok on exploration | architect |
| PM does ops/merges/small fixes directly | — no extra agent |

## Add later only if repeated pain

- **debugger** — flaky Playwright / Ollama loops  
- **security-isolation** — OFFICIAL/SECRET profile work  
- **release-notes** — only if doc-keeper isn’t enough  

## Skills (playbooks)

| Skill | Purpose |
|-------|---------|
| `slice-workflow` | How PM runs a slice without human paste |
| `run-local-stack` | Boot FastAPI / health on Windows |
| `jira-safe` | Confirm gates; no secrets |
| `orb-slice` | Orb UI conventions |
| `update-memory` | After-slice PROJECT_MEMORY / ROADMAP |

## Constraint

Cloud/PM agents **cannot** open a second chat inside your local IDE. They either edit the repo here or spawn in-run subagents. You still only talk to the PM; pull when told.
