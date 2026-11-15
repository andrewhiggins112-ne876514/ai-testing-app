---
name: slice-workflow
description: PM-owned development slice with zero human copy-paste between tools. Use when starting any feature slice.
---

# Slice workflow (PM-owned)

0. **Handoff** — If user says continue / pick up where we left off: read `docs/ops/WORK_LOG.md` Active slice + that Jira story, then skip to Implement.  
1. **Scope** — One roadmap ID / one KAN Story. List out-of-scope.  
2. **Discover** — explorer-cheap or targeted reads (PM/agents — not the human).  
3. **Plan** — architect if multi-file or security-sensitive.  
4. **Implement** — PM edits directly, or delegates implementer / ui-orb (Grok 4.7).  
5. **Verify** — verifier. Run focused tests. Visible product UI: **`desktop_app.py` + Computer Use** (not browser). IronBee only for AUT/Gradio.  
6. **Memory** — update `PROJECT_MEMORY.md` / `ROADMAP.md`; append `docs/ops/WORK_LOG.md`; set next Active slice.  
7. **Jira** — comment on the story with what shipped + verify steps; transition when Done.  
8. **Land** — after handoff docs + Jira: commit intentional files, then **`git push origin main`**. Do this on every finished (or paused) slice so the next chat can pick up; do not wait for the human to ask.  
9. **Human** — tell them only: `git pull` + how to check the app. Never ask them to paste a coding prompt into another chat.
