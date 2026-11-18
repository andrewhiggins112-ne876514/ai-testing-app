# Advisory Council Room

**Build tooling only — not product.** Lives under `.cursor/agents`, `.cursor/skills`, and `docs/ops`. It must **never** ship inside the desktop app, Gradio UI, FastAPI surface, or any end-user feature of the AI Testing Application.

A **separate Cursor Agent chat** for project review, creative pivots, and multi-persona debate while *we* build the project.
It does **not** replace the normal build workflow.

## Two chats (do not mix jobs)

| Chat | How you open it | What you say | What it does |
|------|-----------------|--------------|--------------|
| **Build (normal)** | Fresh IDE Agent chat (default / PM) | **“pick up where we left off”** | Unchanged: pull `main`, read WORK_LOG Active slice, implement that KAN story, verify, Jira close-out, commit/push |
| **Council Room** | Fresh IDE Agent chat → type **`/council`** (slash menu) then your ask | “review the project”, “I have a creative idea…”, “open the room on …” | Debate, gap analysis, CR shaping, docs/Jira/rules proposals — **no product feature coding** |

You can keep both chats. Build chat ignores council drama unless you (or council, after you agree) land decisions into docs/rules/Jira that the next pick-up will read.

## Product horizon (why the room is wide)

This app is **not finished**. End state: a **local-first “test all” tool** that software companies and their employees use daily — browser + desktop AUT, Jira/Xray, self-heal with human review, reports, OFFICIAL/SECRET isolation, conversational agent UX.

Council seats therefore include **future users and buyers**, not only people who help build the repo today.

## When to use which

| Situation | Chat |
|-----------|------|
| Next feature slice / bugfix / continue Active story | **Build** — “pick up where we left off” |
| Audit Jira ↔ repo, find gaps, backlog health | **Council** — Review mode |
| Rough vibe / creative idea / “what if we change direction” | **Council** — Creative mode |
| Decide to change AGENTS.md, `.cursor/rules`, skills, TEAM | **Council** (propose → you confirm → council or Build applies) |
| Implement the decided CR in code | **Build** after Slice-0 docs/Jira exist |

## Modes (auto-detect)

### Review mode
Triggers: “review the project”, “audit”, “find gaps”, Jira+repo health.

Seat: Facilitator + Delivery Auditor + Quality Auditor + Senior Test Engineer + Security Adviser  
(+ Test Manager / Developer / Release Manager when release or buyer impact is clear).

### Creative mode
Triggers: “creative idea”, “vibe”, “what if”, “deviate”, “change the path/setup”.

Seat: Facilitator + Creative Architect + Scope Guardian + Senior Test Engineer + Test Manager  
(+ Security if levels/telemetry/creds/heal auto-apply; + UX if chat/orb/nav; + Pragmatist if hardware/cost).

### Full room
Trigger: “open the council”, “full room”, “debate this with everyone”.

### Bridge to build
Trigger: “turn this into a CR / Jira / Slice 1”.

Order: update `docs/FUNCTIONAL_SPEC.md` (if product intent changed) → KAN epic/story/test text → ROADMAP/WORK_LOG notes → **stop**. Coding happens only in a **Build** chat via normal pick-up / new story.

## Room protocol (3 rounds)

1. **Positions** — each seated role speaks in its voice (short).
2. **Challenges** — Scope Guardian + Security + Primary User (and others as needed) push back.
3. **Verdict** — Facilitator writes the council output (below). You may interrupt any round.

### Verdict template

```text
## Council verdict
- Mode: review | creative | full | bridge
- Decision: ship-as-is insight | CR | park | need-you
- Vision fit: align | extend | conflict
- Who this serves (roles): …
- Top risks (max 5)
- Agreements
- Open disagreements (who vs who)
- Doc / rules updates proposed (paths)
- Jira actions proposed (keys or new titles + AC)
- IDE agent rules/skills: no change | propose patch (paths)
- Next Build chat: none | new story key | “pick up” after CR landed
- Explicitly NOT coding product features in this chat
```

## Supermemory (Build + Council tooling)

v5 hosted MCP (plugin 1.3.1+). Use `search_memory` / `add_memory` with `namespace` = `repo_ai_testing_app__bbdc87968dd0838c`. Do not use legacy `supermemory_search` / `supermemory_add` / `container` / `workspaceRoot`. Details: `.cursor/rules/tooling-use.mdc`, `docs/ops/CONNECTORS.md`.

## Allowed writes in Council (with confirm gates)

- Spec / ops docs: `docs/FUNCTIONAL_SPEC.md`, `PROJECT_MEMORY.md`, `docs/ops/*`, mockup notes
- Agent ops: `AGENTS.md`, `.cursor/rules/*`, `.cursor/agents/*`, `.cursor/skills/*`, `docs/ops/TEAM.md`
- Jira KAN: stories/epics/tests/bugs per `jira-safe` (confirm before writes; REST fallback)
- Work log notes that record a **decision** or park an idea (do not steal the Active coding slice unless you explicitly re-prioritise)

## Forbidden in Council

- Implementing product features (plugins, `desktop_app` behaviour, orb shaders, FastAPI feature endpoints)
- Quietly changing the Build pick-up path or Active slice without a clear CR verdict you accepted
- Asking you to paste prompts into other tools

## Future-user seats (eventual company-wide tool)

| Seat | Likely real-world user? | Cares about |
|------|-------------------------|-------------|
| Senior Test Engineer | Yes — daily driver | Suite maintenance, heal trust, Playwright/desktop reality |
| Test Manager / Head of QA | Yes — buyer/champion | ROI, governance, release readiness, auditability |
| Software Developer | Yes — consumer of bugs/evidence | Clear failures, repro, not flaky noise |
| Product Owner / BA | Yes — story author | AC → tests, readable coverage |
| Release / Eng Manager | Yes — gatekeeper | Reports, risk, go/no-go |
| Security / Compliance | Yes — blocker or enabler | OFFICIAL/SECRET, GDPR, local-first, audit logs |
| Manual / exploratory tester | Yes — later | Guided runs, evidence, low-code flows |
| Support / Ops | Maybe | Desktop `.exe` checks, environments |
| Creative Architect, Delivery/Quality Auditors, Scope Guardian, UX Partner, Platform Pragmatist | Build-time advisors | Spec quality, gaps, vision, UX, home-PC limits |

## How to start the room

There is **no “Council” button** in the Agents window. Custom agents are **slash subagents**, not a mode in the Agent/Ask/Plan dropdown.

1. Open a **new** Cursor Agent chat (IDE **Ctrl+I**, or Agents window → **New Chat**).
2. Leave mode on **Agent**.
3. In the input, type **`/council`** and pick **council** from the slash menu (or type it fully).
4. On the same line (or next), say what you want, e.g.:
   - `/council Review the project against Jira and the FR matrix.`
   - `/council Creative idea: …`
   - `/council Full room — should we add voice before more Jira polish?`
5. Press Enter. The parent chat stays the coordinator; **council** runs as the room facilitator and may call other `council-*` seats.

**Also works:** plain English — “Use the council subagent and review …”  
**Optional skill:** `/advisory-council` then your ask (same playbook).

If `/council` does not appear: confirm `.cursor/agents/council.md` exists on `main`, then reload the window (**Ctrl+Shift+P** → “Developer: Reload Window”).

Build chat stays: new Agent chat → **“pick up where we left off”** (no `/council`) → same as always.

## Files

| Path | Role |
|------|------|
| `.cursor/agents/council.md` | Facilitator — **open this for the room** |
| `.cursor/agents/council-*.md` | Specialist seats (subagents / referenced voices) |
| `.cursor/skills/advisory-council/SKILL.md` | Playbook when council triggers fire |
