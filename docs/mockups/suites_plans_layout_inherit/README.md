# Suites + Plans layout inherit (Studio mock)

Advisory mockups only. Not product UI. Reuses tokens/structure from `docs/mockups/settings_layout_grammar/grammar.css` (KAN-297 / FR-UI-11). Synthetic placeholders.

| Step | File |
|------|------|
| Structure wire | `00-structure-wire.html` |
| Themed Suites | `01-themed-suites.html` |
| Themed Plans · Cases | `01b-themed-plans-cases.html` |
| Annotated build note | `02-annotated-build-note.html` |
| Rejected options | `03-rejected-options.html` |

**Inherit from Settings template:** compact **scan table** + **detail pane**; checkbox = dedicated ~28px cell (multi-select only); row click = focus/open. Theme/orb/home/App nav stay locked.

**Area-specific:**
- **Suites** — no new section rail (single collection). Columns: Select · Status · Title · File · Last. Row opens detail; checkboxes drive Run selected.
- **Plans · Cases** — existing plan tabs stay as section chrome (FR-UI-9). Replace `#plan-cases` text dump with scan table; row fills the existing edit form in a detail pane. Trace keeps row-opens-case.

Open the HTML files directly. Do not serve from the desktop app.
