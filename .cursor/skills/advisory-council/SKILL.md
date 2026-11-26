---
name: advisory-council
description: Run the Advisory Council Room for project review or creative pivots. Separate from Build pick-up. Use when user opens council agent or asks to review/audit/brainstorm path changes.
---

# Advisory Council playbook

## Two-chat rule

| Chat | Entry | Job |
|------|-------|-----|
| Build | Default Agent + “pick up where we left off” | Coding slices — **unchanged** |
| Council | Agent **`council`** | Review, creative debate, docs/Jira/rules — **no product feature code** |

If the human asks for Active-slice implementation inside Council, redirect them to a Build chat.

## Read first

`docs/ops/ADVISORY_COUNCIL.md` — modes, seats, verdict template, future-user roster.

## Memory (optional, same as Build)

If recalling past council/build decisions: `search_memory` with `namespace` = `repo_ai_testing_app__bbdc87968dd0838c`. After a verdict the human accepts into durable policy, `add_memory` a short note (no secrets). Supermemory is v5 hosted MCP — do not use `supermemory_search` / `workspaceRoot` / `container`.

## Steps

1. Detect mode (Review / Creative / Full / Bridge).
2. Announce seated roles.
3. **If Review/Full and the ask is gaps / enterprise / what’s missing:** run **field research** (web or official docs) for seated domains before Round 1 closes — test dashboards, exploratory tools, traces/heal, sandboxes, compliance (ISO/Cyber Essentials/SOC2/GDPR), agentic QA. Do **not** rely on repo Done-rows or training memory alone. Update/cite `docs/ops/ENTERPRISE_GAP_RESEARCH.md` when material. Verdict must include Research adopt/adapt/reject.
4. Round 1 — spawn or role-play `council-*` specialists (parallel when useful).
5. Round 2 — challenges (Scope Guardian + Security + Senior Test Engineer at minimum for Creative).
6. Round 3 — verdict template from ADVISORY_COUNCIL.md.
7. Ask to apply Doc / rules / Jira patches; confirm before Jira writes.
8. Never implement product features here. Point “next Build chat” at pick-up or a new story after Slice-0.

## CR bridge

Creative decisions that change product intent: `FUNCTIONAL_SPEC.md` first → KAN descriptions → ROADMAP/WORK_LOG → Build chat codes later.

## Horizon

Seat eventual company-wide users (QA, developers, POs, release, security) — not only today’s builders.
