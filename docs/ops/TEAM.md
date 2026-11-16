# Agent Team

Cursor **build** agents only — nothing here ships in the product app.

Two chat lanes. Do not mix their jobs.

## Lane A — Build (normal IDE work)

Open a **fresh default Agent chat** and say **“pick up where we left off”**.
Behaviour stays as today: pull `main`, read Active slice, implement, verify, Jira close-out, commit/push.

You talk to the **PM** in this lane. Coding agents are workers the PM invokes — not separate paste targets.

| Agent | File | Model | When |
|-------|------|--------|------|
| PM | (Build parent chat) | Grok 4.7 / Auto | Build lane — implement or delegate |
| implementer | `implementer.md` | Grok 4.7 | Backend / plugin / general code |
| ui-orb | `ui-orb.md` | Grok 4.7 | Gradio + orb |
| doc-keeper | `doc-keeper.md` | Grok 4.5 | Memory, roadmap, ops docs after a slice |
| verifier | `verifier.md` | Grok 4.5 | After implementation |
| explorer-cheap | `explorer-cheap.md` | Grok 4.5 | Discovery |
| architect | `architect.md` | Grok 4.7 | Multi-file / security design |

## Lane B — Advisory Council Room (review & creative)

Open a **fresh Agent chat**, type **`/council`**, then your review or creative ask.
(No separate Council button — Cursor exposes `.cursor/agents` via the **`/`** menu.)

Use for project review, creative pivots, multi-persona debate, and (after you agree) updates to docs, Jira, `AGENTS.md`, rules, and skills.

**Does not** replace pick-up. **Does not** implement product features.

Guide: `docs/ops/ADVISORY_COUNCIL.md` · Skill: `advisory-council`

| Agent | File | Model | When |
|-------|------|--------|------|
| council (Facilitator) | `council.md` | Grok 4.7 | **`/council` to open the room** |
| council-creative-architect | `council-creative-architect.md` | Grok 4.5 | Vibes / path deviations |
| council-delivery-auditor | `council-delivery-auditor.md` | Grok 4.5 | Jira↔repo / FR gaps |
| council-quality-auditor | `council-quality-auditor.md` | Grok 4.5 | Coverage / heal / regression |
| council-user-test-engineer | `council-user-test-engineer.md` | Grok 4.5 | ★ Primary daily user |
| council-user-test-manager | `council-user-test-manager.md` | Grok 4.5 | ★ Buyer / QA lead |
| council-user-developer | `council-user-developer.md` | Grok 4.5 | ★ Dev consuming bugs/evidence |
| council-user-product-owner | `council-user-product-owner.md` | Grok 4.5 | ★ PO/BA / AC author |
| council-user-release-manager | `council-user-release-manager.md` | Grok 4.5 | ★ Release / eng manager |
| council-security-adviser | `council-security-adviser.md` | Grok 4.7 | ★ Security / compliance |
| council-ux-partner | `council-ux-partner.md` | Grok 4.5 | Chat/orb UX |
| council-scope-guardian | `council-scope-guardian.md` | Grok 4.5 | Devil’s advocate / vision |
| council-platform-pragmatist | `council-platform-pragmatist.md` | Grok 4.5 | Home-PC / Windows limits |

★ = likely real users/buyers when the unfinished **“test all”** product ships to software companies.

## Billing reality

All Cursor agents stay on the **Grok** family (4.5 light / 4.7 heavy). Ollama is free only for the **product** runtime.

## Build skills

| Skill | Purpose |
|-------|---------|
| `slice-workflow` | How Build PM runs a slice |
| `run-local-stack` | Boot desktop / stack on Windows |
| `jira-safe` | Confirm gates; no secrets |
| `orb-slice` | Orb UI conventions |
| `update-memory` | After-slice PROJECT_MEMORY / ROADMAP |
| `advisory-council` | Council Room protocol |

## Constraint

Council and Build are **separate chats** you open. Within a chat, the lead may spawn subagents. Do not ask the human to paste prompts between browser Grok / AFK Pilot and Cursor.
