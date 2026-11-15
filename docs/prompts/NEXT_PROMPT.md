# NEXT_PROMPT.md

**Local zero-token hand-off.** Copy one of the blocks below into a fresh Cursor chat (Agent mode).

---

## Continue (preferred)

```
Pick up where we left off.

1. Read docs/ops/WORK_LOG.md Active slice table.
2. Open that Jira story description (Requirements + AC).
3. Implement that one story now. Keep the diff small.
4. When done: append WORK_LOG, update PROJECT_MEMORY/ROADMAP if needed, add a Jira comment on the story.
```

---

## One-shot custom task

**Task:**  
[write the one-line task here]

**Rules:**  
- Read `docs/ops/WORK_LOG.md` Active slice, then `PROJECT_MEMORY.md` and `AGENTS.md` once.  
- Prefer free / Auto / Composer model.  
- Keep the change small.  
- Do not touch orb visual matching unless this task is explicitly about it.  
- Log the slice in `docs/ops/WORK_LOG.md` and comment on the Jira story.  
- Report: files changed, short summary, commit hash if you commit.

---

*Repo path: `D:\Projects\ai_testing_app`. No Grok Bot required.*
