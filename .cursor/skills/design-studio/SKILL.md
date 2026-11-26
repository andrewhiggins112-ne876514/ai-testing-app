---
name: design-studio
description: Run Design Studio (Lane C) for visual UI audit, mockups, research, and design→Jira bridge. Separate from Build pick-up and /council. No product feature code.
---

# Design Studio playbook

## Three-chat rule

| Chat | Entry | Job |
|------|-------|-----|
| Build | “pick up where we left off” | Coding slices |
| Council | `/council` | Review / creative / CRs — no product code |
| Studio | `/studio` | Visual audit / mockups / research — no product code |

If the human asks for Active-slice implementation here, redirect to a **Build** chat. If they need vision/FR debate, redirect or escalate to **Council**.

## Read first

`docs/ops/DESIGN_STUDIO.md` — modes, gates, verdict template, locks.  
`docs/mockups/DESIGN_INTENT.md` — continuity log.

## Memory

`search_memory` with `namespace` = `repo_ai_testing_app__bbdc87968dd0838c`. After accepted verdicts, `add_memory` a short Design Intent note (no secrets).

## Steps

1. Detect mode (Audit / Redesign / Research / Continuity / Bridge).
2. Restate **frozen**: theme, orb, home/chat, App nav (unless Designer unlocked).
3. Announce lean seats (default: Lead + Critic + Layout + Mapper).
4. Evidence first — native desktop screenshots or prior mockups. **For Audit/Research on gaps/enterprise:** also search current enterprise QA UX (reporting dashboards, Explorer-class Manual, plan readability, demo fixtures) — cite adopt/adapt/reject; see `docs/ops/ENTERPRISE_GAP_RESEARCH.md`.
5. Enforce selection grammar + density rules.
6. Verdict template from `DESIGN_STUDIO.md`.
7. Ask to apply docs / Intent / Jira drafts; confirm before Jira.
8. Never implement product UI. Bridge → Spec (if needed) → KAN → Build.

## Binding gates (do not weaken)

Advisory-only · Spec/Jira bridge · hard locks · lean roster · selection grammar · density · tiered CU · synthetic secrets · hard pause if Active-slice slips.

## First mandate

Secondary App areas layout rework (row-soup / whole-row checkboxes). Theme/orb/home stay.
