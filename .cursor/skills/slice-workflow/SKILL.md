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
5. **Verify** — verifier. Run focused tests. Visible product UI: **`desktop_app.py` + Computer Use** (not browser). IronBee only for AUT/Gradio.  
   - **Desktop-first shell chrome:** App menu / Settings hub / Reports library must be correct on desktop before Done. Gradio mirror alone is not Done.  
   - **Anti false-green:** for App menu, run `tests/test_desktop_app_menu.py`; Computer Use must show a **compact popover** (not tall side rail) with areas from `ui/app_areas.py`. See `docs/ops/SHELL_VERIFY.md`.  
   - **Land on `main`:** branch-only fixes are not shipped — push/merge `main` before Done.  

5b. **Bugs found (mandatory)** — Raise a Jira **Bug**, Relates-link to Story + **test** ticket (create if missing), with symptom / expected vs actual / environment / numbered replication steps. Standing authorization. Do not silently fix-only. When fixed: Fix comment + Bug → Done.  
6. **Memory** — update `PROJECT_MEMORY.md` / `ROADMAP.md`; append `docs/ops/WORK_LOG.md`; set next Active slice.  
7. **Jira close-out (required)** — run `scripts/jira_kan_slice_closeout.py` (or equivalent REST):
   - Story comment: **what the agent did** to complete the story + files + verify.
   - Linked **test** ticket (`issuetype=test` Relates): unit-test evidence comment + Done (create+link if missing).
   - Story → Done only after the story comment exists.
   - **Task** = development work under the Story (e.g. FR check-offs), not tests/bugs.
8. **Land** — after handoff docs + Jira: commit intentional files, then **`git push origin main`**. Do this on every finished (or paused) slice so the next chat can pick up; do not wait for the human to ask.  
9. **Human** — tell them only how to check the app if useful (e.g. `desktop_app.py`). Never ask them to `git pull`, commit, push, or paste a coding prompt into another chat.
