# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| TESTALL-A | Test-all alpha (A1–A9) — in-app plan/suite spine | now | Catalogue `docs/ops/test_all_catalogue.json`; first story A1; cut nothing |
| UI-6a | Orb settings behind top-right gear (clean chat dash) | done | Chatbot/input settings icons later |
| UI-6 | Movable/resizable panels | done | Desktop resize + persist (KAN-53); Gradio orb panel resize parity |
| OPS-1 | Cursor ops (rules, agents, skills, HOW_WE_WORK) | done | Merged to main via PR #1 |
| OPS-2 | Beginner Cursor setup + PM-owned workflow | done | Human talks only to PM; Grok guide bot retired |
| UI-5 | Orb presets (save/load/delete named configs) | done | Settings `orb_presets` + Gradio accordion controls |
| UI-ORB-W | WebGL styles mystic / aether / neural | done | Vendored Three.js; classic styles stay canvas |
| UI-DESK-1 | First native desktop window (pywebview mystic shell) | done | `desktop_app.py` + `ui/desktop/`; Gradio kept |
| UI-DESK-2 | Desktop dual drawers + full-void orb canvas | done | App/screen drawers; no top nav; soft cyan glass |
| UI-DESK-3 | Edge-snap drawer buttons + movable widgets | done | Shared shell surfaces; Widget Settings (opacity/border/bg) |
| UI-DESK-4 | Dedicated App area screens + agent HUD widgets | done | **KAN-103/104 Done** (desk22g) — area layouts A–E, HUD widgets, hub, overlap fix verified |

## Near term

| ID | Item | Depends | Notes |
|----|------|---------|-------|
| UI-CHAT | Minimal chat UX polish / Gradio Settings+Reports gaps | UI-6 | **done** — KAN-10 Settings/Reports polish (2026-11-15) |
| JIRA-R | Richer tickets (AC + test steps) | — | **done** (2026-11-15) — multi-audience template + enrich script |
| JIRA-B | Backlog structure (epics/stories/tests/bugs) | JIRA-R | **done** (2026-11-15) — KAN-20…29; Story→`test`+Relates; Task=dev; Bug=defects |
| PW-1 | Stronger step gen + screenshot evidence | — | **done** — **KAN-57** (test KAN-58) |
| PW-2 | Import/run existing Playwright suites | — | **done** — **KAN-59** (test KAN-60) |

## Mid term

| ID | Item | Notes |
|----|------|-------|
| SEC-1 | OFFICIAL / SECRET isolation | **done** — KAN-15; level-scoped creds + Playwright profiles + confirm gate |
| SEC-2 | GDPR delete + consent / no telemetry | **done** — KAN-69; `settings/privacy.py` + App Security Privacy |
| DOC-1 | Document ingestion → settings proposals | **done** — KAN-45; propose + consent before store |
| REP-1 | Customisable reporting | **done** — KAN-51; section toggles + exporter |
| HEAL-1 | Broader locator self-heal | **done** — KAN-14; click + fill heal; assertions stay red |
| HEAL-2 | Full FR-HEAL guardrails | **done** — KAN-49; `plugins/heal_policy.py` + runner hooks |
| HEAL-3 | Heal proposal review UI | **done** — KAN-75; App → Heal review + `/api/heal/*` (desk23) |

## Later

| ID | Item | Notes |
|----|------|-------|
| DESK-1 | Desktop `.exe` testing plugin | **done** — KAN-47; `plugins/desktop_runner.py` smoke + toggle |
| MULTI-1 | Multi-sandbox orchestration | **done** — KAN-55 stub + **KAN-95** real local records/status/prepare |
| VOICE-1 | Voice input | **KAN-81** / Test-all **G10** — deferred until mic; stays in product |
| SALES-1 | Installer / second PC | Test-all **G11** after alpha used |
| TESTALL-B…F | Failures, project plan, run policy, privacy, role widgets | later | After A9; F = HUD packs on **orb home** (not separate homes) |
| TESTALL-G | Plugins widen (desktop cases, API, a11y, …) | later | Stubs stay until deepened |
| TESTALL-H | Manual capture + pipelines + multi-PC share | future | Design-only until later council |

FR gap pass KAN-83…KAN-99 complete as **prototype baselines**. Active product track: Test-all A–H. Voice **KAN-81** deferred. Matrix: `docs/FUNCTIONAL_SPEC.md` §5. Catalogue: `docs/ops/test_all_catalogue.json`.

**Near/Mid “done” rows below are prototype baselines** — still in the product; deepen via Test-all, do not cut.

## Blocked / waiting on you

| ID | Blocker |
|----|---------|
| CRED-1 | Real credentials only in local settings store, never chat/repo |
| VOICE-MIC | Microphone before KAN-81 / G10 |

**Resolved (2026-11-15):** **JIRA-LIVE** — site `https://ai-testing-lab.atlassian.net`, project **KAN**. Token in local settings; agent Jira writes remain two-step confirm.

## Definition of done (every slice)

1. One logical behaviour change  
2. Test or manual check recorded  
3. Human review of meaningful diffs  
4. `PROJECT_MEMORY.md` Current State updated when behaviour changes  
5. No secrets in git  
6. Append `docs/ops/WORK_LOG.md` + Jira story comment  

## Next slice (PM-owned — human does not paste prompts)

**Test-all C2** — next after C1 (**KAN-159** report sections + heal review for a run). Alpha A1–A9 closed. Do **not** start **KAN-81** while deferred.  
**Shipped:** A1–A9 as before; **B1–B7** as before; **C1 KAN-157** Gradio Plans tab (same store + single-case run).

**Council CR (2026-11-16):** Test-all vision locked; 48-story catalogue seeded to Jira; cut nothing; one orb home + HUD widgets for roles.

Say **“pick up where we left off”** or run `python scripts/next_prompt.py`.
