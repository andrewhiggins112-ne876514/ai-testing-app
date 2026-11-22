# Layout enhancement pack

Advisory mockups only. Not product UI. Do not serve these from the desktop app, and do not treat this folder as a Build slice.

Status: **Proposed — Designer reviewing (2026-11-22)**. Not Accepted until the Designer says so.

Reuses tokens from `docs/mockups/settings_layout_grammar/grammar.css` and extras from `docs/mockups/secondary_areas_rest/rest.css`. Pack-only structure lives in `enhance.css`. Synthetic placeholders only (`OFFICIAL`, `KAN-410`, `https://shop.example.test`, `D:\samples\Shop.exe`). No live secrets.

The chip row above each themed stage is a **Studio note**. It does not ship.

## Locks

Theme tokens, orb styles, home/chat chrome, and the App nav model stay frozen. No Gradio. No new App nav item. Charter Frame is not drawn and is not in scope. TRACK3-LAB density, voice (KAN-81/82), and FR-MAN-2 stay deferred.

## What this pack adds

The FR-UI-11 grammar is already shipped (TRACK4). This pack is the craft on top of it, applied to every secondary area:

| # | Craft | Phase |
|---|--------|--------|
| 1 | Quiet empty scan (one line) and unfocused detail (“Select a row”) | 1 |
| 2 | Keyboard: ↑↓ focus row, Enter detail, Space only on a checkbox/radio cell | 1 |
| 3 | One scroll per pane; sticky header inside the scan scroller only | 1 |
| 4 | Structure tokens: rail (≥3), in-area tabs (2 jobs), no rail (one collection) | 1 (guard) |
| 5 | Checkbox verbs: Sel, Keep, Include, Enabled, A·B | 1 |
| 6 | Plans compact booleans: Show archived, Enabled, Archived, Pause on fail | 1 |
| 7 | Plans case sections Edit / Run / Quarantine / Known issue, pinned Save + Run | 1 |
| 8 | Documents toolbar follows the tab (Propose = Parse, Uploads = Refresh) | 1 |
| 9 | Heal bulk confirm states the count and “files are not written”; Reject stays on the focused detail | 1 |
| 10 | Desktop and Sandboxes Advanced closed. Not TRACK3-LAB density | 1 |
| 11 | Manual: focused session collapses Start; Confirm dock is one line. Charter Frame untouched | 1 |
| 12 | Suites and Reports: optional filter in the existing toolbar | 1 |
| 13 | Evidence hint in Reports, Heal, and Manual detail | **2** |

Click **Empty preview** on a themed file to swap in the quiet empty contract. Focus a scan table and use the arrow keys.

## Files

| Step | File |
|------|------|
| Structure wire | `00-structure-wire.html` |
| Settings | `01a-themed-settings.html` |
| Suites | `01b-themed-suites.html` |
| Plans · Cases | `01c-themed-plans-cases.html` |
| Plans · other tabs | `01d-themed-plans-tabs.html` |
| Reports | `01e-themed-reports.html` |
| Documents | `01f-themed-documents.html` |
| Security | `01g-themed-security.html` |
| Heal | `01h-themed-heal.html` |
| Manual | `01i-themed-manual.html` |
| Desktop | `01j-themed-desktop.html` |
| Sandboxes | `01k-themed-sandboxes.html` |
| Annotated build note | `02-annotated-build-note.html` |
| Rejected | `03-rejected.html` |

Generator: `_gen_mockups.py`. From the repo root:

```text
.\venv\Scripts\python.exe docs\mockups\layout_enhancement_pack\_gen_mockups.py
```

## Phase 1 vs Phase 2 (for a later epic)

Do not open Jira from Design Studio until the Designer accepts this pack. Draft clusters, one story plus a linked test ticket each:

1. **Shared scan craft** — empty, keyboard, one scroll, sticky header, verb labels. Settings, Suites, Plans, Reports, Documents, Security, Heal, Manual, Desktop, Sandboxes. Structure-token regression: do not add a rail to a one-collection area, and do not add a second rail beside tabs.
2. **Plans booleans and case sections** — compact Show archived / Enabled / Archived / Pause on fail; Edit / Run / Quarantine / Known issue; pinned Save and Run.
3. **Documents toolbar scope** — Parse on Propose, Refresh on Uploads.
4. **Heal confirm copy** — count plus “files are not written”. No bulk Reject.
5. **Manual focus chrome** — Start collapses when a session is focused; one-line confirm dock. Charter Frame out.
6. **Suites and Reports filter** — one search field in the existing toolbar.
7. **Lab disclosure** — Desktop and Sandboxes Advanced closed.
8. **Phase 2 — evidence hint** — Reports, Heal, Manual detail only. A single hint region, not a gallery and not a nav item. Does not block 1–7.

Council still needs a pass on whether the keyboard sentence and the Phase 2 slot are spec text (FR-UI-11 craft) or stay UX-only. This Studio pass does not edit `docs/FUNCTIONAL_SPEC.md` and does not edit `ui/desktop/*`.

## Rejected here

KPI or hero dashboards, whole-row toggles, bulk Heal Reject, TRACK3-LAB / voice / FR-MAN-2, a second filter bar, page-width boolean labels, an evidence gallery, a new App nav item. See `03-rejected.html`.
