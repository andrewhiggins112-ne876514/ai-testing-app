# Roadmap

Ordered for a solo senior tester + Cursor team. One active “Now” item at a time.

Status: `done` | `now` | `next` | `later` | `blocked`

## Now

| ID | Item | Status | Notes |
|----|------|--------|-------|
| OPS-1 | Cursor ops (rules, agents, skills, HOW_WE_WORK) | now | This change set — replaces Grok↔AFK copy-paste |
| OPS-2 | Beginner Cursor setup (merge, panels, guide-bot decision) | now | `docs/ops/SETUP_FOR_BEGINNERS.md` — one step at a time with user |
| UI-5 | Orb presets (save/load named configs) | next | Continues orb slices 1–4 at `8553d6a` |

## Near term (after OPS-1)

| ID | Item | Depends | Notes |
|----|------|---------|-------|
| UI-5 | Orb presets | OPS-1 | Settings store already holds orb config |
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

## Suggested next coding chat (after this ops PR merges)

```text
Slice UI-5 only: orb preset save/load named configs.
Read PROJECT_MEMORY.md + AGENTS.md once. Use /ui-orb and /verifier.
Do not touch Jira writes or security isolation.
```
