# Jira ticket description template (KAN)

Multi-audience template used by `scripts/jira_kan_enrich.py`. Based on Atlassian user-story guidance (As a / I want / so that), epic outcome framing, and a shared Definition of Done separate from story acceptance criteria.

Audiences that must be able to read every ticket without opening other docs:

| Audience | Needs |
|----------|--------|
| Management | Outcome, value, scope boundary, success measure |
| Developers | Requirements, behaviour, technical notes, paths |
| Testers | Acceptance criteria + test procedure (test Tasks) |
| Cursor agents | Self-contained FR text, DoD, next-slice pointers |
| AI Testing App | Machine-usable FR-IDs and explicit AC for later ingestion |

## Epic structure

1. **Intro** — outcome in 2–4 sentences  
2. **Who this is for** — one line per audience  
3. **Problem / outcome** — why this area exists  
4. **Requirements** — bold `FR-*` + full text (never “see spec”)  
5. **Scope** — in / out  
6. **Success criteria** — epic-level measurable done  
7. **Dependencies / risks**  
8. **Technical notes**  
9. **Mockups** — filenames + what to look for (attachments when UI)

## Story structure

1. **Intro**  
2. **Who this is for**  
3. **User story** — `As a … I want … so that …`  
4. **Requirements** — FR text inlined  
5. **Behaviour** — short paragraphs  
6. **Acceptance criteria** — numbered, Given/When/Then preferred  
7. **Definition of done** — team quality bar (always present)  
8. **Out of scope**  
9. **Dependencies**  
10. **Technical notes** — repo paths  
11. **Mockups**

## Test Task structure (`label = test`, Relates → Story)

1. **Intro** — which story this verifies  
2. **Who this is for** (testers + agents primary)  
3. **Test procedure** — Step N + **Expected**  
4. **Acceptance criteria** — slim copy of parent AC  
5. **Evidence** — screenshots/logs required  

## Definition of done (team — every Story)

Copied into tickets from `docs/FUNCTIONAL_SPEC.md` §7:

1. One logical behaviour change delivered  
2. Test or recorded manual check exists  
3. Human reviewed meaningful diffs  
4. `PROJECT_MEMORY.md` Current State updated if behaviour changed  
5. No secrets in git  
6. Side-effecting actions still require confirmation  
7. Self-healing (if touched) obeys “how not what” + approval  
8. Errors logged and surfaced (not swallowed)  
9. Entry appended to `docs/ops/WORK_LOG.md`  
10. **Jira story comment** stating what **the agent did** to complete the story (implementation + files + verify) — not a one-liner “done”  
11. **Linked test Task** (`label=test`, Relates) has a verification comment (pytest command + result or manual evidence) and is marked **Done**

Helper: `python scripts/jira_kan_slice_closeout.py --story KAN-XX --done "…" --files "…" --verify "…" --pytest-cmd "…" --mark-done`  

## Hierarchy reminder

- **Epic** = multi-slice outcome (FR area)  
- **Story** = one sprintable slice of user/product value  
- **Task** + `test` = verification linked with Relates (KAN has no Test issue type)  

## Spec vs Jira

| Location | Role |
|----------|------|
| `docs/FUNCTIONAL_SPEC.md` | **Canonical** — edit first on any user CR |
| KAN ticket descriptions | **Derived** — must stay in sync (enrich script or manual edit) |

Human CRs → update spec + tickets + memory/roadmap/work log together.
