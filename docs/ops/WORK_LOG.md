# Work log — AI Testing Application

**Path:** `D:\Projects\ai_testing_app\docs\ops\WORK_LOG.md`  
**Rule:** Every coding/agent slice **must** append an entry here when the slice finishes (or is paused). Also add a **Jira comment** on the active story with the same summary.

## Active slice (agents: read this first)

| Field | Value |
|-------|--------|
| **Status** | ready |
| **Jira story** | [KAN-53](https://ai-testing-lab.atlassian.net/browse/KAN-53) — UI-6 resizable panels (remainder) |
| **Epic** | [KAN-27](https://ai-testing-lab.atlassian.net/browse/KAN-27) — UI and Desktop Experience |
| **Roadmap ID** | UI-6 |
| **Spec** | `docs/FUNCTIONAL_SPEC.md` FR-UI-4 |
| **Next action** | Implement resizable panels on desktop shell; keep Gradio; verify with screenshot |

When the user says **“pick up where we left off”** / **“continue”**: read this Active slice table, open the Jira story description, then start coding that story immediately (no long rediscovery).

---

## Entry format

```
### YYYY-MM-DD — KAN-XX — short title
- **Agent/chat:** …
- **Done:** …
- **Files:** …
- **Verify:** …
- **Jira:** comment on KAN-XX (yes/no)
- **Next:** next story key + one line
```

---

## Log

### 2026-11-15 — OPS — git sync prep + IDE capabilities walkthrough
- **Agent/chat:** Cursor PM chat
- **Done:** Added `docs/ops/IDE_CAPABILITIES.md` (MCP/plugin login steps for IDE + Agent window); emptied workspace `.cursor/mcp.json` (broken GitHub npx); ROADMAP IDE-1…6; commit/push of local drift pending in same slice.
- **Files:** `IDE_CAPABILITIES.md`, `.cursor/mcp.json`, `.cursor/mcp.json.example`, CONNECTORS, INSTALL, ROADMAP.
- **Verify:** Open IDE_CAPABILITIES; run Supermemory login when ready.
- **Jira:** n/a.
- **Next:** User: Supermemory login (IDE-2); then KAN-53.

### 2026-11-15 — OPS — document Jira MCP → REST fallback
- **Agent/chat:** Cursor PM chat
- **Done:** Instructed agents: when Atlassian MCP is blocked, use local-settings REST / `scripts/jira_kan_*.py` instead of giving up (`jira-safe`, CONNECTORS, AGENTS, work-log-handoff).
- **Files:** `.cursor/skills/jira-safe/SKILL.md`, `docs/ops/CONNECTORS.md`, `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`.
- **Verify:** skill section “MCP failure → REST fallback”.
- **Jira:** n/a (process).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — Jira progress comments + epic status sync
- **Agent/chat:** Cursor PM chat
- **Done:** Commented Done stories with completion notes; commented epics KAN-20…29 with Done/open child lists; transitioned epics (Done or In Progress from children); noted KAN-53 as Active slice. Helper: `scripts/jira_kan_progress_sync.py`.
- **Files:** `scripts/jira_kan_progress_sync.py`, WORK_LOG.
- **Verify:** Browse KAN-8 / KAN-20 / KAN-53 comments; epic statuses updated.
- **Jira:** yes — story + epic comments.
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — sync FUNCTIONAL_SPEC §5 done vs open
- **Agent/chat:** Cursor PM chat
- **Done:** Updated §5 Current State vs Target to 2026-11-15 (D: paths, KAN backlog done, open stories mapped to KAN keys; Active slice KAN-53).
- **Files:** `docs/FUNCTIONAL_SPEC.md`
- **Verify:** §5 no longer lists “richer Jira backlog” as open.
- **Jira:** statuses unchanged (MCP API token still blocked for live re-query this turn; statuses from last known enrich).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — CR sync rule for functional spec
- **Agent/chat:** Cursor PM chat
- **Done:** Documented that `docs/FUNCTIONAL_SPEC.md` is canonical in-repo; Jira inlines FRs. Agent instructions now require user CRs to update spec + related KAN tickets + memory/roadmap/work log.
- **Files:** `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/JIRA_TICKET_TEMPLATE.md`, `PROJECT_MEMORY.md`, `update-memory` skill.
- **Verify:** Instructions searchable for “User change requests (CRs)”.
- **Jira:** n/a (process only).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — handoff + multi-audience Jira template
- **Agent/chat:** Cursor PM chat
- **Done:** Added `docs/ops/JIRA_TICKET_TEMPLATE.md`, `docs/ops/WORK_LOG.md`, `.cursor/rules/work-log-handoff.mdc`; updated AGENTS/PROJECT_MEMORY/ROADMAP/HOW_WE_WORK/NEXT_PROMPT/next_prompt.py/slice-workflow; re-ran `jira_kan_enrich.py` with Who-this-is-for, User story, DoD, Dependencies, Traceability.
- **Files:** ops docs, agent rules/skills, `scripts/jira_kan_enrich.py`, `scripts/next_prompt.py`.
- **Verify:** `python scripts/next_prompt.py` prints KAN-53 Active slice; enrich exit 0.
- **Jira:** all active KAN descriptions refreshed (sample KAN-53).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — project move, Ollama move, KAN backlog + ticket enrichment
- **Agent/chat:** Cursor PM chat (this session)
- **Done:** Moved repo to `D:\Projects\ai_testing_app` (Python 3.13 venv); moved Ollama to `D:\Program Files\Ollama` with `OLLAMA_MODELS`; removed old C: copies; added `docs/FUNCTIONAL_SPEC.md`; rebuilt KAN epics KAN-20…29; enriched/reformatted ticket descriptions; models restored + `qwen3:8b`; Model location set to D: in Ollama Settings.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `scripts/jira_kan_rebuild.py`, `scripts/jira_kan_enrich.py`, path docs.
- **Verify:** `/health` OK; `ollama list` shows 5 models; KAN backlog browsable.
- **Jira:** backlog rebuilt/enriched (no per-story ship comments for this ops day).
- **Next:** KAN-53 UI-6 resizable panels.
