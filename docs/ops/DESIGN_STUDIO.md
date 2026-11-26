# Design Studio (Lane C)

**Build tooling only — not product.** Lives under `.cursor/agents`, `.cursor/skills`, and `docs/ops` / `docs/mockups`. It must **never** ship inside the desktop app, Gradio UI, FastAPI surface, or any end-user feature.

A **separate Cursor Agent chat** for visual UI audit, layout mockups, UX research, creative continuity, and design→Jira handoff while *we* build the project.
It does **not** replace Build pick-up or the Advisory Council Room.

## Three chats (do not mix jobs)

| Chat | How you open it | What it does |
|------|-----------------|--------------|
| **Build (Lane A)** | Fresh IDE Agent → **“pick up where we left off”** | Implement Active KAN story; verify; Jira close-out; commit/push |
| **Council (Lane B)** | Fresh Agent → **`/council`** | Review, creative pivots, CRs, policy — **no product code** |
| **Design Studio (Lane C)** | Fresh Agent → **`/studio`** | Visual audit, mockups, research, Design Intent — **no product code** |

Name is **Design Studio** (not Layout Lab — Lab is product FR-UI-8 / TRACK3-LAB density).

## Why Lane C exists

Council debates intent; Build ships code. Studio owns **seeing** the native desktop UI and producing **layout grammar + mockups** so Build does not thrash on “looks wrong” loops.

**First mandate (Designer 2026-11-21):** theme, orb, and main/home UI are **good and locked**. Secondary App areas still read as row-soup (whole-row checkboxes, flat hierarchy). Studio redesigns **secondary layout systems**, not skin.

## Binding gates (Council-ratified)

1. **Advisory-only** — no product feature code; never set `WORK_LOG` Active; never treat Studio as Build pick-up.
2. **Bridge** — mockups → human confirm → `FUNCTIONAL_SPEC.md` CR if product intent/UX FR changes → KAN Story + linked `issuetype=test` → **Build** implements.
3. **Hard locks (default)** — theme tokens, orb styles, home/chat chrome, App nav model. Unlock only via explicit Designer CR (escalate to Council Creative if vision conflict).
4. **Lean default roster** — Lead + Visual Critic + Layout Designer + Code Mapper. Research / Continuity / Jira Shaper / Test Engineer / Security / Pragmatist / Scope on-demand. Prefer lighter models. One Studio topic per chat. Do not stack Council + Studio + Build Premium unless the Designer asks.
5. **Selection grammar** — checkbox = dedicated hit target; row click = open/navigate/focus; **ban whole-row toggle**.
6. **Density over pretty-empty** — power-user scannability (status · name · result · fail reason · evidence), not vanity dashboards.
7. **CU verify** — tiered: HTML/mockup markers first; short quiet Computer Use on native `desktop_app.py` only; pause Ollama; classic (non-WebGL) orb; document **CU skipped — unsafe**. Never soft-pass on “opened orb home.”
8. **Security** — synthetic placeholders in mockups; one security level at a time; no live secrets, `settings.json`, tokens, or real AUT data in chat/repo/Jira. Credential UI mockups show masked status only.
9. **Hard pause** — if Active-slice delivery slips, pause Studio until Build recovers (Designer call; not optional shrug).

## Modes (auto-detect)

| Mode | Triggers | Default seats |
|------|----------|---------------|
| **Audit** | “audit UI”, “what’s wrong with layouts”, screenshot pass | Lead, Visual Critic, Code Mapper |
| **Redesign** | “mockup”, “rework Settings/Suites…”, layout options | Lead, Critic, Layout Designer, Code Mapper (+ Test Engineer) |
| **Research** | “best practices”, “how do tools do X”, enterprise UX bar | Lead, Research Analyst (+ Critic) — **web/current docs required** |
| **Continuity** | “past creative”, “remember mockups”, reconcile ideas | Lead, Continuity Keeper (+ Creative from Council if vision fight) |
| **Bridge** | “turn into CR / Jira / stories” | Lead, Jira Shaper, Code Mapper (+ Delivery patterns from Council) |

## Room protocol

1. Name mode + seated roles; restate **frozen** surfaces.
2. **Round 1 — Evidence / positions** (screenshots or prior mockups before opinions). For Audit/Research on enterprise gaps: **also** web/current-tool research (TestRail/Xray/Explorer-class Manual, release dashboards) — see `docs/ops/ENTERPRISE_GAP_RESEARCH.md`.
3. **Round 2 — Challenges** (density, selection grammar, locks, security if Settings).
4. **Round 3 — Studio verdict** (template below).
5. Ask once whether to apply docs / Design Intent / Jira drafts. Confirm before Jira writes.

**Field research gate (binding — Designer 2026-11-26):** Do not limit “gaps” to row-soup leftovers. Compare App areas to **current enterprise QA UX** (reporting charts, Manual float capture, plan document readability, demo fixtures). Cite adopt/adapt/reject.

### Verdict template

```text
## Studio verdict
- Mode: audit | redesign | research | continuity | bridge
- Frozen: theme | orb | home/chat | app nav (confirm)
- Areas in scope: …
- Diagnosis (pattern failures; hit targets)
- Preferred layout direction (+ rejected options)
- Mockups: paths under docs/mockups/…
- Research: sources + adopt / adapt / reject (required for Audit/Research enterprise gap asks)
- Creative continuity: locked vs new (Design Intent)
- Code touch surface (files/areas; orb untouched)
- Jira proposed: stories + AC + test tickets (draft only until confirm)
- Risks (a11y, CU, density, SECURITY settings)
- Next: Bridge → Council if FR/vision change | Build pick-up after stories land
- Explicitly NOT implementing product UI in this chat
```

## Selection and layout grammar (standing)

- **Checkbox / select control** — small dedicated hit zone; label associated for a11y.
- **Row / list item** — primary click opens detail, focuses row, or navigates — does **not** toggle selection unless an explicit select-mode is on.
- **Multi-select** — toolbar appears when ≥1 selected; do not steal the row’s primary click.
- **Destructive / Approve–Reject** — deliberate controls, never whole-row chrome.
- Prefer section groups, master–detail, or compact tables over endless undifferentiated rows.
- Reuse existing theme tokens (Track 2 / KAN-297); change **structure**, not skin.

## Mockup ladder

1. Structure wire (HTML under `docs/mockups/<topic>/`).
2. Themed static mock (reuse shell tokens / existing mockup CSS where possible).
3. Annotated build note (click targets, frozen chrome, code surface hints).

Living log: `docs/mockups/DESIGN_INTENT.md`.

## Allowed writes (with confirm gates)

- `docs/mockups/**`, `docs/mockups/DESIGN_INTENT.md`
- `docs/ops/DESIGN_STUDIO.md`, `docs/ops/TEAM.md` cross-links, notes in `docs/ops/WORK_LOG.md` for **design decisions** only
- `.cursor/agents/studio*.md`, `.cursor/skills/design-studio/**`
- `docs/FUNCTIONAL_SPEC.md` only when Bridge + human accepted a UX/FR CR
- Jira KAN drafts/stories/tests per `jira-safe` (**confirm before writes**)

## Forbidden

- Product feature code (`desktop_app.py` behaviour, orb shaders, plugins, FastAPI product endpoints)
- Setting or stealing the Build Active slice
- Quietly unlocking home/orb/theme without Designer CR
- Live credentials or real Settings screenshots with secrets in chat/repo
- Naming this lane “Layout Lab”

## Studio vs Council Bridge

| Need | Lane |
|------|------|
| Pixel/layout options, visual audit, mockups | **Studio** |
| Vision conflict, FR invent, policy, multi-stakeholder debate | **Council** |
| Spec + KAN after accepted design CR | Studio Bridge **or** Council Bridge (same order: Spec → Jira → Build) |
| Implement mockup | **Build** only |

## How to start

1. New Cursor Agent chat.
2. Mode: Agent.
3. Type **`/studio`** and pick **studio**, then the ask (e.g. “Audit secondary areas for row-soup”).
4. Parent chat coordinates; may spawn `studio-*` seats.

Also works: “Use the Design Studio / studio agent and …”  
Skill: `/design-studio` or `.cursor/skills/design-studio/SKILL.md`.

## Files

| Path | Role |
|------|------|
| `.cursor/agents/studio.md` | Facilitator — **open this for the room** |
| `.cursor/agents/studio-*.md` | Specialist seats |
| `.cursor/skills/design-studio/SKILL.md` | Playbook |
| `docs/mockups/DESIGN_INTENT.md` | Creative continuity log |
| `docs/ops/TEAM.md` | Lane C roster |
| `docs/ops/ADVISORY_COUNCIL.md` | Cross-link (Lane B) |

## Supermemory

`search_memory` / `add_memory` with `namespace` = `repo_ai_testing_app__bbdc87968dd0838c`. After accepted verdicts, store short Design Intent notes (no secrets).
