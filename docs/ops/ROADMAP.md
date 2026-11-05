# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| UI-6a | Orb settings behind top-right gear (clean chat dash) | now | Chatbot/input settings icons later |
| UI-6 | Movable/resizable panels | next | After orb gear lands |
| OPS-1 | Cursor ops (rules, agents, skills, HOW_WE_WORK) | done | Merged to main via PR #1 |
| OPS-2 | Beginner Cursor setup + PM-owned workflow | done | Human talks only to PM; Grok guide bot retired |
| UI-5 | Orb presets (save/load/delete named configs) | done | Settings `orb_presets` + Gradio accordion controls |

## Near term

| ID | Item | Depends | Notes |
|----|------|---------|-------|
| UI-6 | Movable/resizable panels | UI-5 | Keep Gradio; avoid rewrite |
| JIRA-R | Richer tickets (AC + test steps) | — | Structured description; still two-step confirm |
| JIRA-B | Backlog structure (epics/stories/tests/bugs) | JIRA-R | Resume when Jira account exists |
| PW-1 | Stronger step gen + screenshot evidence | — | Extend `playwright_runner` |
| UI-CHAT | Minimal chat UX polish | UI-6 | Still Gradio-first |

## Mid term

| ID | Item | Notes |
|----|------|-------|
| SEC-1 | OFFICIAL / SECRET isolation | Browser profiles + credential scopes — confirm before coding |
| DOC-1 | Document ingestion → settings proposals | Explicit consent; no silent store |
| REP-1 | Customisable reporting | Build on `reports/exporter.py` |
| HEAL-1 | Broader locator self-heal | Beyond current click heal |

## Later

| ID | Item | Notes |
|----|------|-------|
| DESK-1 | Desktop `.exe` testing plugin | Separate plugin; do not fork Playwright runner |
| MULTI-1 | Multi-sandbox orchestration | Desired earlier; keep as plugin |
| VOICE-1 | Voice input | After text UX is solid |
| SALES-1 | Internal guinea-pig packaging | Company large browser app + Jira + GitHub |

## Blocked / waiting on you

| ID | Blocker |
|----|---------|
| JIRA-LIVE | No Jira account yet — do not ask for URL/token until you say one exists |
| CRED-1 | Real credentials only in local settings store, never chat/repo |

## Definition of done (every slice)

1. One logical behaviour change  
2. Test or manual check recorded  
3. Human review of meaningful diffs  
4. `PROJECT_MEMORY.md` Current State updated when behaviour changes  
5. No secrets in git  

## Next slice (PM-owned — human does not paste prompts)

**UI-6** movable/resizable panels. PM implements or delegates; human only pulls and checks the UI.
