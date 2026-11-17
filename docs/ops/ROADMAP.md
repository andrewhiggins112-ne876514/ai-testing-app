# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| TESTALL-E | Test-all E privacy / audit / recovery | done | E1–E5 Done (**KAN-201** desk66); UI-LAB-MENU Done |
| TESTALL-F | Test-all F role HUD / UX — F1–F7 | done | F7 Done (**KAN-215** desk73); F6 Done (**KAN-213** desk72) |
| TESTALL-G | Test-all G widen as plugins — **G4** Seed data and fixtures | now | **KAN-223** (test **KAN-224**); G3 Done **KAN-221** desk76; G2 Done **KAN-219**; G1 Done **KAN-217**; voice G10 deferred with KAN-81 |
| UI-LAB-MENU | Lab tools back on desktop App menu | done | **KAN-260** Done (desk64) — Primary + Lab tools on ▦; hub kept |
| TESTALL-A | Test-all alpha (A1–A9) — in-app plan/suite spine | done | Catalogue A1–A9 shipped; cut nothing; deepen via later epics |
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
| UI-NAV-IA-1 | Reports area = library/viewer; section toggles → Report Settings | UI-DESK-4 + after KAN-159 | **done** — **KAN-247** / test **KAN-250** (desk41) |
| UI-NAV-IA-2 | Gradio menu button (no persistent top tab bar) | UI-NAV-IA-1 | **done** — **KAN-248** / test **KAN-251** |
| UI-NAV-IA-3 | Settings hub category switch (App / Report / …) | UI-NAV-IA-1 | **done** — **KAN-249** / test **KAN-252** (desk42); FR-SET-4 |
| UI-NAV-IA-4 | Desktop compact App menu (match Gradio ▦ panel) | UI-NAV-IA-2 | **done** — **KAN-253** / test **KAN-254** (desk44); then resume C4 |
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
| TESTALL-B…D | Failures, project plan, run policy | done | B1–B7, C1–C11, D1–D7 shipped (baselines; deepen later) |
| UI-LAB-MENU | Lab tools back on desktop App menu | done | **KAN-260** desk64 |
| TESTALL-F | Role widget packs on orb home | later | F = HUD packs on **orb home** (not separate homes); F6 assumes E3 redaction |
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

**G3** — Done (**KAN-221** Contract and mock responses; desk76). **G2** — Done (**KAN-219** API/messaging checks; desk75). **G1** — Done (**KAN-217** Desktop cases on same suite; desk74). **F7** — Done (**KAN-215** Home checklist; desk73). **F6** — Done (**KAN-213** Read-only export pack; desk72). **F5–F1** Done. **E5–E1** Done. **UI-LAB-MENU** — Done (**KAN-260** desk64). **Now** — **KAN-223** G4 Seed data and fixtures (test **KAN-224**). Alpha A1–A9 closed. Do **not** start **KAN-81** while deferred.
**Shipped:** A1–A9 as before; **B1–B7** as before; **C1 KAN-157**; **C2 KAN-159**; **UI-NAV-IA-1…4** (**KAN-247…249**, **KAN-253**); **C3 KAN-161**; **C4 KAN-163** coverage gaps (desk45); **C5 KAN-165** acceptance drift (desk46); **C6 KAN-167** traceability matrix (desk48); **C7 KAN-169** tags/priority/smoke/regression (desk49); **C8 KAN-171** import Playwright into suite (desk50); **C9 KAN-173** search plans/cases/failures (desk51); **C10 KAN-175** suite history/compare (desk52); **C11 KAN-177** archive case (desk53); **D1 KAN-179** sequential default + parallel cap (desk54); **D2 KAN-181** flake/quarantine (desk55); **D3 KAN-183** named environments (desk56); **D4 KAN-185** credential status (desk57); **D5 KAN-187** case step timeouts (desk58); **D6 KAN-189** local run-finish notices (desk59); **D7 KAN-191** duration on run/case + compare (desk60); **E1 KAN-193** document privacy for uploads (desk61); **E2 KAN-195** local side-effects audit (desk62); **E3 KAN-197** redact secrets in evidence/exports (desk63); **E4 KAN-199** lab backup/restore (desk65); **E5 KAN-201** offline last plan (desk66).

**Council CR (2026-11-16):** Test-all vision locked; catalogue seeded to Jira; cut nothing; one orb home + HUD widgets for roles.
**Council review (2026-11-17):** On track at E3; cut-nothing holds (reach gap = hub-only lab tools → **KAN-260** after E3); stale Now pointers refreshed here.

Say **“pick up where we left off”** or run `python scripts/next_prompt.py`.
