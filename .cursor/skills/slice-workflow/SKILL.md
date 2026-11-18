---
name: slice-workflow
description: PM-owned development slice with zero human copy-paste between tools. Use when starting any feature slice.
---

# Slice workflow (PM-owned)

0. **Handoff** — If user says continue / pick up where we left off: **`git pull origin main`** first (agent does this), then read `docs/ops/WORK_LOG.md` Active slice + that Jira story, then skip to Implement.  
1. **Scope** — One roadmap ID / one KAN Story. List out-of-scope.  
2. **Discover** — explorer-cheap or targeted reads (PM/agents — not the human).  
3. **Plan** — architect if multi-file or security-sensitive.  
4. **Implement** — PM edits directly, or delegates implementer / ui-orb (Grok 4.7).  
5. **Verify** — verifier. Run focused **pytest / API / HTML** first. Visible product UI: **`desktop_app.py`** (not browser). IronBee only for AUT/Gradio.  
   **Computer Use (tiered — Council 2026-11-18):** use for visual / occlusion / clickable chrome only. Pre-CU: pause Ollama, classic orb, one product overlay (see `run-local-stack`).  
   **Area-chrome / occlusion stories:** when a quiet desktop is achievable, CU must prove primary fields, tabs, and Confirm/Cancel are **clickable** — HTML/CSS markers alone are not enough (Council Track 2). If Cursor CU HUD vs Manual/Charter makes CU unsafe after one quiet retry → **CU skipped — unsafe** + human checklist on the test ticket — **never** soft-pass “opened orb home.”  
   Close-out honesty: state what CU proved vs skipped/flaked.  
5b. **Bugs found (mandatory)** — Raise a Jira **Bug**, Relates-link to Story + **test** ticket (create if missing), with symptom / expected vs actual / environment / numbered replication steps. Standing authorization. Do not silently fix-only. When fixed: Fix comment + Bug → Done.  
6. **Memory** — update `PROJECT_MEMORY.md` / `ROADMAP.md`; append `docs/ops/WORK_LOG.md`; set next Active slice.  
7. **Jira close-out (required)** — run `scripts/jira_kan_slice_closeout.py` (or equivalent REST):
   - Story comment: **what the agent did** to complete the story + files + verify.
   - Linked **test** ticket (`issuetype=test` Relates): unit-test evidence comment + Done (create+link if missing).
   - Story → Done only after the story comment exists.
   - **Task** = development work under the Story (e.g. FR check-offs), not tests/bugs.
8. **Land** — after handoff docs + Jira: commit intentional files, then **`git push origin main`**. Do this on every finished (or paused) slice so the next chat can pick up; do not wait for the human to ask.  
9. **Human** — tell them only how to check the app if useful (e.g. `desktop_app.py`). Never ask them to `git pull`, commit, push, or paste a coding prompt into another chat.
