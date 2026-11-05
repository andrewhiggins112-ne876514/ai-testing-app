# Agent Team

Custom agents live in `.cursor/agents/`. Invoke with `/name` or by asking the parent to delegate.

## Roster

### pm (you talk here — no separate file required)
Parent chat. Owns priorities, blank-filling, risk call-outs, and when to open a new slice chat. Does **not** dump entire files into context.

### explorer-cheap
Readonly searcher. Returns paths + 1–2 line summaries. Prefer for “where is X?” before reading files in the parent.

### architect
Design-only. Produces a short plan, trade-offs, and file touch list. Does not implement unless explicitly asked after approval.

### implementer
Applies one approved slice. Small diff, matches existing plugin patterns, no drive-by refactors.

### verifier
Readonly skeptic. Runs or cites tests, checks AGENTS.md constraints, reports gaps. Never “looks good” without evidence.

### ui-orb
Scoped to `ui/gradio_app.py` + orb settings. Presets, styles, panels — not backend/Jira unless the slice requires a tiny hook.

## When to add a new agent

Add only if a job repeats weekly and keeps polluting the parent chat. Candidates later:

- **doc-keeper** — PROJECT_MEMORY / ROADMAP updates only  
- **playwright-healer** — locator self-heal experiments  
- **security-isolation** — OFFICIAL/SECRET profile work  

Do **not** create vague agents (“helps with coding”). Routing fails and tokens rise.

## Model policy (keep Premium alive)

1. Default coding: **Composer / Auto**  
2. Explore + verify: **Composer 2.5** (subagent `model: composer-2.5`)  
3. Hard architecture only: stronger model for `/architect` briefly  
4. Product inference: **local Ollama** — free for runtime, not Cursor credits  
5. Never run two heavy local models; never pull 32B+ on the home PC  

## Bots vs agents

| Kind | Meaning here |
|------|----------------|
| Agent | Cursor chat/subagent with tools |
| Bot / skill | On-demand playbook (`.cursor/skills/*/SKILL.md`) |
| Product agent | The app’s own Ollama tool-calling loop in `agent/agent.py` |

Skills: `run-local-stack`, `slice-workflow`, `jira-safe`, `orb-slice`.
