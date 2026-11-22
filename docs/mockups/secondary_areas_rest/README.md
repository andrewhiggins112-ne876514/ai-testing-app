# Remaining App areas — FR-UI-11 rest pack

Advisory mockups only. Not product UI. Open the HTML files directly.

Reuses tokens from `docs/mockups/settings_layout_grammar/grammar.css`. Synthetic placeholders only (sample shop, `KAN-410`, `OFFICIAL`, `https://shop.example.test`, `D:\samples\Shop.exe`). No live secrets.

Settings and Suites are the accepted baseline and are **not** redrawn here. Plans · Cases stays **KAN-329** / **KAN-330**.

| Step | File |
|------|------|
| Structure wire | `00-structure-wire.html` |
| Plans tabs other than Cases | `01-themed-plans-tabs.html` |
| Reports library | `01b-themed-reports.html` |
| Documents | `01c-themed-documents.html` |
| Security | `01d-themed-security.html` |
| Heal review (contrast) | `01e-themed-heal.html` |
| Manual area | `01f-themed-manual.html` |
| Desktop Lab | `01g-themed-desktop.html` |
| Sandboxes Lab | `01h-themed-sandboxes.html` |
| Annotated build note | `02-annotated-build-note.html` |
| Rejected options | `03-rejected-options.html` |

Generator (same folder): `_gen_mockups.py`. Regenerate, then re-check the Heal diff line if you change that string.

## Evidence (current product, before this pack)

Read from `ui/desktop/index.html` and `desktop.js`. Not a visual pass — Computer Use was not run.

| Area | Current surface | Failure |
|------|-----------------|---------|
| Plans · Cases | `#plan-cases` + edit stack | Owned by KAN-329. Not redrawn. |
| Plans · Draft | `#plan-panel-draft` label stack | Form, not a table. Keep as a compact form. |
| Plans · Coverage | `#plan-coverage-no-case`, `#plan-coverage-disabled` (`drawer-hint`) | Text dump. |
| Plans · Trace | `#plan-trace-matrix` (`drawer-hint`, role=table) | Not a scan table. Row-opens-case must stay. |
| Plans · History | `#plan-history-list` + two `<select>`s | Dump. Compare A/B is not a dedicated cell. |
| Plans · Run | `#plan-panel-run` sections + `#plan-pause-on-fail` on a label | Long form. Pause control is a full-width checkbox label. |
| Reports | `#rpt-library-list` button options **and** `#rpt-library-select` | Duplicate openers. No columns. Detail `#rpt-detail` already exists. |
| Documents | `#doc-diff` builds `label.check-row.doc-diff-row`; `#doc-uploads-list` is a `ul` | Whole-row keep toggle. Uploads are not a scan. |
| Security | Seven `label.check-row` wipe targets + backup includes; `#local-audit-list` is a `ul` | Page-width checkbox hit. Audit is a dump. |
| Heal | `renderHealProposals` puts Approve and Reject on every `.heal-card` | Row chrome is the decision. |
| Manual | `#manual-session-list` rows; three `label.check-row` on start | Library is not a scan. Charter Frame (`#charter-frame-root`) stays out of scope. |
| Desktop | Status paragraph + `label.check-row#desk-enabled` under Advanced | Enable is a page-width row. |
| Sandboxes | `#ms-list` is one hint paragraph; `label.check-row#ms-enabled`; Remove on the form | No scan. Remove is not behind a confirm in the detail. |

## Preferred direction

| Area | Direction |
|------|-----------|
| Plans remaining tabs | Keep FR-UI-9 tabs. Coverage + Trace = scan, no checkbox (Trace row opens the case). History = A/B radio cells (~28px) + row focus. Draft + Run = compact forms; single booleans are compact checks. |
| Reports | Suites shape: no rail. Columns When · Title · Level · Kind. Row opens markdown detail. Drop the duplicate id select. Section editor stays Settings. |
| Documents | In-area Propose \| Uploads (not new App nav). Diff Keep = checkbox cell. Confirm / Decline sit in the detail. Uploads scan Name · Time · Level · Consent. |
| Security | In-area rail: Level, Privacy, Audit, Redaction, Backup. Include = checkbox cell. Switch / delete / restore stay propose-then-confirm. Masked status only. |
| Heal | Scan **Sel** · Class · Locator · Run · When. Detail Approve + Reject for the focused proposal. **Bulk approve** via dedicated Sel cells + toolbar `Approve selected (N)` behind confirm. Checkbox never means approve; row never approves. Reject stays detail-only (no bulk reject). |
| Manual | Session scan When · Charter · Link · Stage. Start checks are compact. Confirm dock stays outside the work scroll. Do not restyle Charter Frame or home. |
| Desktop | One scan row Enabled · Status · Path · Last smoke. Enabled is the cell. TRACK3-LAB geometry deferred. |
| Sandboxes | Scan Id · Label · URL · Ready. No select column. Remove in the detail behind confirm. Enable is a compact toolbar check. TRACK3-LAB deferred. |

Frozen on every file: theme tokens, orb, home/chat, ▦ App menu, Screen drawer.
