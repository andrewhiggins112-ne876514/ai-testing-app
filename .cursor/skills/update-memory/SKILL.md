---
name: update-memory
description: After a finished slice, update PROJECT_MEMORY Current State and ROADMAP statuses. Use when behaviour or process changed.
---

# Update memory

1. Read Current State in `PROJECT_MEMORY.md` once.  
2. Patch only what changed (features landed, blockers, next step).  
3. Set roadmap IDs to `done` / `now` / `next` in `docs/ops/ROADMAP.md`.  
4. Append `docs/ops/WORK_LOG.md` and advance the **Active slice** table to the next open story.  
5. **Jira close-out:** story comment stating what the agent implemented + linked test Task evidence + Done (use `scripts/jira_kan_slice_closeout.py`).  
6. `add_memory` with `namespace` = `repo_ai_testing_app__bbdc87968dd0838c`: short durable note of the change + next slice (Supermemory v5; not `supermemory_add`).  
7. **Git land:** commit + `git push origin main` (no secrets; clear message). Required before the human starts a new pick-up chat. The **next** Agent chat pulls — never tell the human to `git pull`.  
8. If the human issued a **CR**: update `docs/FUNCTIONAL_SPEC.md` first, then related KAN tickets, then memory/roadmap/work log + `add_memory`.  
9. Do not paste long chat logs or secrets into memory.  

