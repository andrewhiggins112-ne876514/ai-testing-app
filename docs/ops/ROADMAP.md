# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| UI-6a | Orb settings behind top-right gear (clean chat dash) | done | Chatbot/input settings icons later |
| UI-6 | Movable/resizable panels | done | Desktop resize + persist (KAN-53); Gradio orb panel resize parity |
| OPS-1 | Cursor ops (rules, agents, skills, HOW_WE_WORK) | done | Merged to main via PR #1 |
| OPS-2 | Beginner Cursor setup + PM-owned workflow | done | Human talks only to PM; Grok guide bot retired |
| UI-5 | Orb presets (save/load/delete named configs) | done | Settings `orb_presets` + Gradio accordion controls |
| UI-ORB-W | WebGL styles mystic / aether / neural | done | Vendored Three.js; classic styles stay canvas |
| UI-DESK-1 | First native desktop window (pywebview mystic shell) | done | `desktop_app.py` + `ui/desktop/`; Gradio kept |
| UI-DESK-2 | Desktop dual drawers + full-void orb canvas | done | App/screen drawers; no top nav; soft cyan glass |
| UI-DESK-3 | Edge-snap drawer buttons + movable widgets | done | Shared shell surfaces; Widget Settings (opacity/border/bg) |

## Near term

| ID | Item | Depends | Notes |
|----|------|---------|-------|
| UI-CHAT | Minimal chat UX polish / Gradio Settings+Reports gaps | UI-6 | **done** — KAN-10 Settings/Reports polish (2026-11-15) |
| JIRA-R | Richer tickets (AC + test steps) | — | **done** (2026-11-15) — multi-audience template + enrich script |
| JIRA-B | Backlog structure (epics/stories/tests/bugs) | JIRA-R | **done** (2026-11-15) — KAN-20…29; Story→Task+`test`+Relates |
| PW-1 | Stronger step gen + screenshot evidence | — | Extend `playwright_runner` |

## Mid term

| ID | Item | Notes |
|----|------|-------|
| SEC-1 | OFFICIAL / SECRET isolation | **done** — KAN-15; level-scoped creds + Playwright profiles + confirm gate |
| DOC-1 | Document ingestion → settings proposals | **done** — KAN-45; propose + consent before store |
| REP-1 | Customisable reporting | **done** — KAN-51; section toggles + exporter |
| HEAL-1 | Broader locator self-heal | **done** — KAN-14; click + fill heal; assertions stay red |
| HEAL-2 | Full FR-HEAL guardrails | **done** — KAN-49; `plugins/heal_policy.py` + runner hooks |

## Later

| ID | Item | Notes |
|----|------|-------|
| DESK-1 | Desktop `.exe` testing plugin | **now** — KAN-47; separate plugin; do not fork Playwright runner |
| MULTI-1 | Multi-sandbox orchestration | Desired earlier; keep as plugin |
| VOICE-1 | Voice input | After text UX is solid |
| SALES-1 | Internal guinea-pig packaging | Company large browser app + Jira + GitHub |

## Blocked / waiting on you

| ID | Blocker |
|----|---------|
| CRED-1 | Real credentials only in local settings store, never chat/repo |

**Resolved (2026-11-15):** **JIRA-LIVE** — site `https://ai-testing-lab.atlassian.net`, project **KAN**. Token in local settings; agent Jira writes remain two-step confirm.

## Definition of done (every slice)

1. One logical behaviour change  
2. Test or manual check recorded  
3. Human review of meaningful diffs  
4. `PROJECT_MEMORY.md` Current State updated when behaviour changes  
5. No secrets in git  
6. Append `docs/ops/WORK_LOG.md` + Jira story comment  

## Next slice (PM-owned — human does not paste prompts)

**[KAN-47](https://ai-testing-lab.atlassian.net/browse/KAN-47)** — Desktop `.exe` testing plugin (DESK-1).  
Say **“pick up where we left off”** or run `python scripts/next_prompt.py`.
