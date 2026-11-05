---
name: slice-workflow
description: Standard low-token development slice replacing the old Grok browser + AFK Pilot copy-paste loop. Use when starting any feature slice.
---

# Slice workflow

1. **Scope** — One ID from `docs/ops/ROADMAP.md` (or a named one-liner). Out of scope listed explicitly.
2. **Discover** — `/explorer-cheap` if paths unknown. No whole-repo read.
3. **Plan** — Plan mode or `/architect` when >1 file or security-sensitive.
4. **Implement** — `/implementer` or Agent on Composer/Auto. Small diff.
5. **Verify** — `/verifier`. Run focused tests.
6. **Memory** — Update `PROJECT_MEMORY.md` Current State if behaviour changed.
7. **Close** — Commit; start a **new chat** for the next slice.

Paste for new coding chats:

```text
Read PROJECT_MEMORY.md and AGENTS.md once. One slice only. Prefer Composer.
Confirm before credentials / Jira writes / deletes / security changes.
```
