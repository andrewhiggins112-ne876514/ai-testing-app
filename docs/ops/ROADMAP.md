# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| OPERATE | Daily test-all loop + open-trace (home-PC demo AUT) | done (baseline) | Epic **KAN-374**; OPERATE-4 **KAN-381**/382 Done (`fixtures/operate_docs/`); OPERATE-3 **KAN-379**/380 Done (**desk134**); OPERATE-2 **KAN-377**/378 Done; OPERATE-1 **KAN-375**/376 Done — `docs/ops/DAILY_LOOP.md` |
| TRACK1-IA | Plans IA + stub honesty + other area tidy | done | Epic **KAN-264**; **KAN-265/267/269/271/273** Done (desk89 Lab areas tidy) |
| TRACK1-H1 | Manual shell + Charter Frame MVP | done | **KAN-275** Manual shell (desk90); **KAN-277** Charter Frame MVP (desk92; test **278**); design KAN-241 §9; FR-MAN-2 parked |
| TRACK2-CHROME | Non-overlapping area chrome (FR-UI-9) | done | **KAN-281** / **KAN-282** desk92; Bug **KAN-280** fixed |
| TRACK2-MAN | FR-MAN-1 completion (trustworthy loop → …) | done | **KAN-283/285/287/289/291/293** Done (desk99 propose/confirm harden) |
| TRACK2-UX | Enterprise layout note → tokens | done | **KAN-295** note accepted; **KAN-297**/**KAN-298** tokens desk99; Track 2 complete |
| TRACK3-UX | Enterprise area density (FR-UI-10) — Primary geometry | done | Epic **KAN-307** Primary Done (**KAN-320**/321 + **KAN-323** desk106); Lab follow-on |
| TRACK3-LAB | Lab area density (Heal/Desktop/Suites/Sandboxes) | done | Epic **KAN-359** Done; Stories **360/362/364/366** + bugs **368**/370; human A–E **desk131** |
| TRACE-DEEPEN | Real Playwright trace (replace notice file) | done | **KAN-372**/373 (**desk132**) — real `trace.zip` on failure; notice file removed — **Baseline** |
| TRACK4-LAYOUT | Secondary area layout grammar (FR-UI-11) — Settings template first | done | Settings **KAN-324** … Sandboxes Lab **KAN-345** (**desk118** / test **KAN-346**) — rest-of-App inherit complete — **Baseline** |
| TRACK5-LAYOUT | FR-UI-11 structure pack — all secondary areas (empty / keyboard / scroll + Plans/Docs/Heal/Lab craft) | done | Phase 1 **KAN-348…352**; Phase 2 **KAN-354** evidence-first (**desk125** / test **KAN-355**) — **Baseline** |
| OPERATE-POLISH | Loop-hit UI + triage strip / run→report / Heal badge (OPERATE-3) | done | **KAN-379**/380 Done (**desk134**) — Run disclosure, Manual idle split, triage strip; not a new full layout track |
| GAP-CR | Enterprise CRs: charts, Manual float, stubs, plan doc, compliance + research adds (release panel, flake, heal, SBTM, agent gov) + **readable run steps / pass-fail evidence** (CR 2026-11-27) | now | Epic **KAN-383**; **KAN-496**/497 Option A aside; **KAN-498**/499 deep view (thumb expands) — Build 496 first |
| HOME-MARKET | PERSONAL level + BYOK agents (Grok etc.) + home onboarding | later | Epic seeded 2026-11-26; after OPERATE unless unparked; SECRET/OFFICIAL refuse cloud LLM keys |
| FR-MAN-2 | Live assist / circles | later | Parked until DPIA (H1 §10); distinct from Manual float-snip CR |
| TESTALL-E | Test-all E privacy / audit / recovery | done | E1–E5 Done (**KAN-201** desk66); UI-LAB-MENU Done |
| TESTALL-F | Test-all F role HUD / UX — F1–F7 | done | F7 Done (**KAN-215** desk73); F6 Done (**KAN-213** desk72) |
| TESTALL-H | Test-all H future workplace — designs **complete** (H1–H3) | done | **H3** Done **KAN-245**; H2 **KAN-243**; H1 **KAN-241** design; implement via TRACK1-H1 |
| UI-LAB-MENU | Lab tools back on desktop App menu | done | **KAN-260** Done (desk64) — Primary + Lab tools on ▦; hub kept |
| TESTALL-A | Test-all alpha (A1–A9) — in-app plan/suite spine | done | Catalogue A1–A9 shipped; cut nothing; deepen via later epics |
| UI-6a | Orb settings behind top-right gear (clean chat dash) | done | Chatbot/input settings icons later |
| UI-6 | Movable/resizable panels | done | Desktop resize + persist (KAN-53); Gradio orb panel resize parity |
| OPS-1 | Cursor ops (rules, agents, skills, HOW_WE_WORK) | done | Merged to main via PR #1 |
| OPS-2 | Beginner Cursor setup + PM-owned workflow | done | Human talks only to PM; Grok guide bot retired |
| OPS-C7 | Context7 local API-key + 2B library/security/quality review | done | Epic **KAN-300**; Phase1–3 **KAN-301/303/305**; requirements pinned; Active remains **KAN-291** |
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
| SALES-1 | Installer / second PC | **done** — Test-all **G11** **KAN-237** desk83 (secret-free pack; not company rollout alone) |
| TESTALL-B…D | Failures, project plan, run policy | done | B1–B7, C1–C11, D1–D7 shipped (baselines; deepen later) |
| UI-LAB-MENU | Lab tools back on desktop App menu | done | **KAN-260** desk64 |
| TESTALL-F | Role widget packs on orb home | later | F = HUD packs on **orb home** (not separate homes); F6 assumes E3 redaction |
| TESTALL-G | Plugins widen (desktop cases, API, a11y, …) | later | Stubs stay until deepened |
| TESTALL-H | Manual capture + pipelines + multi-PC share | future | Designs Done (H1–H3); **Track 1** implements H1 Charter Frame after Plans IA |

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

**Council Track 1 (2026-11-18):** Epic **KAN-264** Done. **KAN-275** Manual shell; **KAN-277** Charter Frame MVP (desk92).  
**Council Track 2 (2026-11-18):** Epic **KAN-279** **Done**. Chrome **KAN-281** … propose/confirm **KAN-293**; layout note **KAN-295** accepted; tokens **KAN-297**/**KAN-298** (desk99). **Park** FR-MAN-2. Voice **KAN-81** deferred — do **not** implement.  
**Council Track 3 (2026-11-18):** Epic **KAN-307** Primary Done.  
**TRACK4-LAYOUT:** Done **KAN-324…345**.  
**TRACK5-LAYOUT (2026-11-22 Bridge):** Epic **KAN-347** Done. Phase 1 **KAN-348…352**; Phase 2 **KAN-354**/355 (**desk125**).  
**TRACK3-LAB (2026-11-23 Bridge):** Epic **KAN-359** **Done** (2026-11-26). Stories **360/362/364/366** + bugs **368**/370; human Lab A–E confirm **desk131**.
**TRACE-DEEPEN (2026-11-26):** **KAN-372**/373 Done (**desk132**) — Playwright `trace.zip` on failure.
**OPERATE (2026-11-26 Council):** Unpark daily loop + open-trace on **home-PC demo AUT** (`docs/ops/DAILY_LOOP.md`). OPERATE-4 Documents demo pack **KAN-381**/382 Done. OPERATE-3 **KAN-379**/380 Done (**desk134**). OPERATE-2 **KAN-377**/378 Done (`/demo-aut/`). OPERATE-1 **KAN-375**/376 Done. OPERATE epic baseline complete. Park voice / FR-MAN-2 live circles; next Build **KAN-496** (Option A Accepted).  
**CR 2026-11-27 (Designer; Council+Studio accepted 2026-11-27):** Readable run steps + pass/fail evidence — Spec FR-TEST-4/FR-PLAN-4 deepen; **KAN-496**/497 = Option A Case aside (01–03); **KAN-498**/499 = Plans deep view (05–07; More evidence + thumb expand). Do not absorb into OPERATE-3. Reviews default to whole-team research + requirement discovery (`ADVISORY_COUNCIL.md`).
**Shipped:** A1–A9 as before; **B1–B7** as before; **C1 KAN-157**; **C2 KAN-159**; **UI-NAV-IA-1…4** (**KAN-247…249**, **KAN-253**); **C3 KAN-161**; **C4 KAN-163** coverage gaps (desk45); **C5 KAN-165** acceptance drift (desk46); **C6 KAN-167** traceability matrix (desk48); **C7 KAN-169** tags/priority/smoke/regression (desk49); **C8 KAN-171** import Playwright into suite (desk50); **C9 KAN-173** search plans/cases/failures (desk51); **C10 KAN-175** suite history/compare (desk52); **C11 KAN-177** archive case (desk53); **D1 KAN-179** sequential default + parallel cap (desk54); **D2 KAN-181** flake/quarantine (desk55); **D3 KAN-183** named environments (desk56); **D4 KAN-185** credential status (desk57); **D5 KAN-187** case step timeouts (desk58); **D6 KAN-189** local run-finish notices (desk59); **D7 KAN-191** duration on run/case + compare (desk60); **E1 KAN-193** document privacy for uploads (desk61); **E2 KAN-195** local side-effects audit (desk62); **E3 KAN-197** redact secrets in evidence/exports (desk63); **E4 KAN-199** lab backup/restore (desk65); **E5 KAN-201** offline last plan (desk66).

**Council CR (2026-11-16):** Test-all vision locked; catalogue seeded to Jira; cut nothing; one orb home + HUD widgets for roles.
**Council review (2026-11-17):** On track at E3; cut-nothing holds (reach gap = hub-only lab tools → **KAN-260** after E3); stale Now pointers refreshed here.

Say **“pick up where we left off”** or run `python scripts/next_prompt.py`.
