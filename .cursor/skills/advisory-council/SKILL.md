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

1. Detect mode (Review / Creative / Full / Bridge). **Plain “review …” defaults to Full / whole-team** (all `council-*` + all `council-user-*`). Co-seat **Studio + Creative** when the topic is UI / Case detail / mockup-gated / CR layout.
2. Announce every seated role (do not thin-seat unless Designer names a lean roster).
3. **Field research (binding):** every seated role researches **current practice** in its domain (web or official docs) before Round 1 closes — test dashboards, exploratory tools, traces/heal, sandboxes, compliance (ISO/Cyber Essentials/SOC2/GDPR), agentic QA, **home/vibe BYOK**. Seat **`council-user-home-developer`** for market/PERSONAL/BYOK. Do **not** rely on repo Done-rows or training memory alone. Update/cite `docs/ops/ENTERPRISE_GAP_RESEARCH.md` when material.
4. **Requirement discovery (binding — Designer 2026-11-27):** each seat must surface candidate **missing requirements / AC holes / Done-gate traps** from its lens (or explicit “none + why”). Designer is one person — the room invents the gaps early so walkthroughs do not. Verdict must include **Requirements discovered this review**.
5. Round 1 — spawn specialists in parallel (Council + Studio seats when co-seated).
6. Round 2 — challenges (Scope Guardian + Security + Senior Test Engineer at minimum; + Visual Critic / Creative when Studio co-seated).
7. Round 3 — verdict template from ADVISORY_COUNCIL.md (include Research + Requirements discovered).
8. Ask to apply Doc / rules / Jira patches; confirm before Jira writes.
9. Never implement product features here. Point “next Build chat” at pick-up or a new story after Slice-0.

## CR bridge

Creative decisions that change product intent: `FUNCTIONAL_SPEC.md` first → KAN descriptions → ROADMAP/WORK_LOG → Build chat codes later.

## Horizon

Seat eventual company-wide users (QA, developers, POs, release, security) — not only today’s builders.
