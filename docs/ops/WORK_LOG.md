# Work log — AI Testing Application

**Path:** `D:\Projects\ai_testing_app\docs\ops\WORK_LOG.md`  
**Rule:** Every coding/agent slice **must** append an entry here when the slice finishes (or is paused). Also add a **Jira comment** on the active story with the same summary.

## Active slice (agents: read this first)

| Field | Value |
|-------|--------|
| **Status** | ready |
| **Jira story** | **KAN-169** — C7 tags, priority, smoke and regression |
| **Start task** | **KAN-170** (`test`, Relates → KAN-169) |
| **Epic** | Test-all C (see catalogue) |
| **Roadmap ID** | C7 / FR-PLAN-2 |
| **Spec** | `docs/FUNCTIONAL_SPEC.md` |
| **Git** | `main` |
| **Test ticket** | **KAN-170** |
| **Shipped** | … **KAN-167** C6 traceability (desk48); **KAN-257** App menu; **KAN-165** C5; **KAN-163** C4 |
| **Deferred** | **KAN-81** / **KAN-82** voice — until mic; later G10 (**KAN-235**) — **do not implement while deferred** |
| **Next after this** | continue Test-all C after C7 |

When the user says **“pick up where we left off”** / **“continue”**: read this Active slice table. If Status is **deferred**, do **not** code that story. Otherwise open the Jira story description and start coding that story immediately (no long rediscovery).

---

## Entry format

```
### YYYY-MM-DD — KAN-XX — short title
- **Agent/chat:** …
- **Done:** …
- **Files:** …
- **Verify:** …
- **Jira:** story agent-completion comment + linked test Task evidence/Done (yes/no; note test key)
- **Next:** next story key + one line
```

---

## Log

### 2026-11-17 — KAN-167 — C6 traceability matrix
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-167
- **Done:** Plan-level traceability matrix: story key, case count, last result, linked bug keys, known-issue flag. Keys with no runs are `not_loaded` (never fake pass). `GET /api/plans/{id}/traceability`; Desktop Plans grid with row→open case; report section `traceability` on export (run_report attaches rows). desk48.
- **Files:** `plans/traceability.py`, `plans/__init__.py`, `plans/run_report.py`, `reports/sections.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/gradio_app.py`, `desktop_app.py`, `tests/test_plan_traceability.py`, `tests/test_report_sections.py` (+ desk48 cache-bust)
- **Verify:** `pytest tests/test_plan_traceability.py tests/test_report_sections.py tests/test_desktop_app_menu.py tests/test_plan_coverage_gaps.py tests/test_plan_acceptance_drift.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py tests/test_reports_library.py -v` (44 passed). Live `/ui/desktop/?v=desk48` has `plan-trace-matrix` + `/api/plans/{id}/traceability`; `desktop_app.py` opened.
- **Jira:** close-out **KAN-167** + **KAN-168**
- **Next:** **KAN-169** C7 tags/priority/smoke/regression (test **KAN-170**)

### 2026-11-17 — KAN-257 — Desktop App menu still tall (KAN-256 never on main)
- **Agent/chat:** Designer report — desktop ▦ still old 9-item menu vs Gradio Chat…Documents
- **Done:** Root cause: **KAN-256** popover fix lived only on branch `cursor/kan-256-desktop-app-menu-popover` and never merged. Landed popover + moved `#area-section-host` into `#area-body`; App nav aligned to Gradio (Chat/Settings/Plans/Reports/Documents); hub keeps extra tools; C5 drift UI preserved. desk47.
- **Files:** `ui/desktop/index.html`, `desktop.css`, `desktop.js`, `desktop_app.py`, `tests/test_desktop_app_menu.py` (+ desk47 cache-bust)
- **Verify:** pytest menu + related (27 passed). Live desk47 nav has 5 Gradio areas only.
- **Jira:** Bug **KAN-257** Relates KAN-253/254/256; Fix comment + Done
- **Next:** Active remains **KAN-167** C6

### 2026-11-17 — KAN-165 — C5 acceptance text drift
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-165
- **Done:** On demand, re-read linked Jira issues and mark plan snapshots stale when summary/AC differ; show old vs new; Keep re-baselines without changing cases; Refresh disables prior jira cases and adds new AC cases — never deletes cases/runs. Drafts store `jira_snapshots`. desk46.
- **Files:** `plans/drift.py`, `plans/store.py`, `plans/draft.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_acceptance_drift.py` (+ desk46 cache-bust tests)
- **Verify:** `pytest tests/test_plan_acceptance_drift.py tests/test_plan_coverage_gaps.py tests/test_plan_draft.py tests/test_plan_project_draft.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py -v` (32 passed). Live `/ui/desktop/?v=desk46` has `plan-drift-check-btn`; `desktop_app.py` opened.
- **Jira:** close-out **KAN-165** + **KAN-166**
- **Next:** **KAN-167** C6 traceability matrix (test **KAN-168**)

### 2026-11-17 — KAN-163 — C4 Coverage gaps
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-163
- **Done:** After project draft (and on demand), Plans lists stories with no case and stories whose cases are all disabled separately. Filter by key/summary (`q`). Never auto-creates cases. `GET /api/plans/{id}/coverage-gaps`; draft-project response includes `coverage_gaps`. desk45.
- **Files:** `plans/coverage.py`, `plans/draft.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_coverage_gaps.py`, `tests/test_plan_project_draft.py` (+ desk45 cache-bust tests)
- **Verify:** `pytest tests/test_plan_coverage_gaps.py tests/test_plan_project_draft.py tests/test_desktop_app_menu.py tests/test_orb_hub.py tests/test_nav_overlap.py tests/test_settings_hub.py -v` (25 passed). Live `GET /api/plans/{id}/coverage-gaps` → 50 no-case stories, `cases_created=false`; desk45 HTML has `plan-coverage-filter`; `desktop_app.py` opened.
- **Jira:** close-out **KAN-163** + **KAN-164**
- **Next:** **KAN-165** C5 acceptance text drift (test **KAN-166**)

### 2026-11-17 — KAN-253 — UI-NAV-IA-4 Desktop compact App menu
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-253
- **Done:** Replaced tall App side drawer with Gradio-style compact `▦` panel (`app-menu-panel`, nav list only). Panel positions beside the edge-snap toggle; choosing an area closes the panel and opens the dedicated surface (layouts A–E unchanged). Screen drawer stays a resizable tall rail. desk44. Stale orb-hub spoke-count test updated to 9 (Plans); open Bug for SVG lines/nodes still at 7.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_desktop_app_menu.py`, `tests/test_gradio_menu_nav.py`, `tests/test_nav_overlap.py`, `tests/test_orb_hub.py`, `tests/test_settings_hub.py`, `tests/test_reports_library.py`
- **Verify:** `pytest tests/test_desktop_app_menu.py tests/test_gradio_menu_nav.py tests/test_nav_overlap.py tests/test_settings_hub.py tests/test_reports_library.py tests/test_orb_hub.py -v` (27 passed). Computer Use: `desktop_app.py` → ▦ opens compact APP panel (not full-height rail) → Settings opens overlay area.
- **Jira:** close-out **KAN-253** + **KAN-254** Done; Bug **KAN-255** (Relates KAN-253/254/109) — orb-hub SVG 7 lines vs 9 spokes
- **Next:** **KAN-163** C4 coverage gaps (test **KAN-164**)

### 2026-11-17 — Council CR — Desktop compact App menu (match Gradio)
- **Agent/chat:** Advisory Council Room — Designer side-by-side desktop vs Gradio; desktop still tall APP drawer
- **Done (docs/Jira only):** Spec FR-UI-1/2/7 — desktop is primary product; App nav = compact `▦` panel like Gradio (not tall side rail). ROADMAP **UI-NAV-IA-4**. **Active Build → KAN-253** (Designer: do desktop menu before resuming C4). After **KAN-253** Done → **KAN-163**.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`, this log
- **Verify:** n/a (no product code)
- **Jira:** **KAN-253** (test **KAN-254**) under epic **KAN-27**; Relates KAN-248 / KAN-103 / KAN-102; Active reprioritise comments
- **Next:** Build pick-up → **KAN-253**; then **KAN-163** C4

### 2026-11-17 — KAN-161 — C3 project-wide draft in batches
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-161
- **Done:** Project-wide plan draft from configured `jira_project` with a visible batch-size cap (1–25, default 5). Uses `list_stories` + `read_issue` (429 backoff). Creates one local plan with per-issue AC cases; `jira_write=false`; no auto-run (`review_required`). Desktop Plans: batch input + **Draft from project**. `POST /api/plans/draft-project`. desk43.
- **Files:** `plans/draft.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_project_draft.py`
- **Verify:** `pytest tests/test_plan_project_draft.py tests/test_plan_draft.py -v` (7 passed). Live desk43 HTML has `plan-batch-size` + `plan-draft-project-btn`; `POST /api/plans/draft-project` batch=2 → ok, 2 issues, no Jira write; `desktop_app.py` opened.
- **Jira:** close-out **KAN-161** + **KAN-162**
- **Next:** **KAN-163** C4 coverage gaps (test **KAN-164**)

### 2026-11-17 — KAN-249 — UI-NAV-IA-3 Settings hub (App / Report)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-249
- **Done:** Settings is a hub with App / Report category switch (stays on Settings). Desktop: `#settings-cat-*` panels + deep link from Reports opens Report category. Gradio: Radio category switch + show/hide App vs Report columns. Security confirm gates remain on Security (desktop). desk42.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_settings_hub.py`, `tests/test_reports_library.py`
- **Verify:** `pytest tests/test_settings_hub.py tests/test_reports_library.py tests/test_gradio_menu_nav.py tests/test_report_sections.py -v` (23 passed). Live `/ui/desktop/?v=desk42` has `settings-cat-switch` + panels; `desktop_app.py` opened.
- **Jira:** close-out **KAN-249** + **KAN-252**
- **Next:** **KAN-161** C3 project-wide draft in batches (test **KAN-162**)

### 2026-11-17 — KAN-248 — UI-NAV-IA-2 Gradio menu button (no top tabs)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-248
- **Done:** Replaced Gradio `gr.Tabs` strip with App menu button (`▦`) + panel (Chat / Settings / Plans / Reports / Documents). Area columns toggle via `select_app_area`; home stays Chat + orb. Orb gear remains orb-only. Desktop drawer unchanged (no top tab bar).
- **Files:** `ui/gradio_app.py`, `tests/test_gradio_menu_nav.py`, `tests/test_plans_tab.py`, `tests/test_reports_library.py`
- **Verify:** `pytest tests/test_gradio_menu_nav.py tests/test_plans_tab.py tests/test_reports_library.py tests/test_reports_tab.py -v` (20 passed). Live Gradio: menu visible, `tab_nav_count=0`, Plans switch works, orb gear → Presets. Desktop HTML still has `app-drawer-toggle` / no `tab-nav`.
- **Jira:** close-out **KAN-248** + **KAN-251**
- **Next:** **KAN-249** Settings hub (test **KAN-252**)

### 2026-11-17 — KAN-247 — UI-NAV-IA-1 Reports library / Report Settings
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-247
- **Done:** Reports area is a saved-report library (list/open markdown + screenshot + raw JSON; empty hint; Export chosen run kept). Section include/exclude + Save moved under Settings → Report Settings with deep link from Reports. Gradio same split. APIs `GET /api/reports`, `GET /api/reports/{id}`, `GET /api/reports/{id}/screenshot`. desk41.
- **Files:** `reports/exporter.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_reports_library.py`, cache-bust refs
- **Verify:** `pytest tests/test_reports_library.py tests/test_report_sections.py tests/test_reports_tab.py tests/test_plan_run_report.py tests/test_heal_review.py tests/test_plan_run_case.py -v` (43 passed). Live desk41 HTML has `rpt-library-select` + `report-settings-heading`; toggles not in Reports block; `/api/reports` + `/api/report-sections` OK; `desktop_app.py` opened.
- **Jira:** close-out **KAN-247** + **KAN-250**
- **Next:** **KAN-248** Gradio menu button (test **KAN-251**)

### 2026-11-17 — KAN-159 — C2 report sections and heal review for a run
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-159
- **Done:** Plan case runs pre-allocate `run_id` and stamp locator heals via `heal_run_context`. Reports area keeps section toggles and can **Export chosen run** (`GET /api/plans/exportable-runs`, `POST …/runs/{run_id}/export`). Heal review shows run on cards + optional run filter (`GET /api/heal/proposals?run_id=`). Approve/reject unchanged; no suite auto-commit. Screens kept (desk40).
- **Files:** `plugins/heal_policy.py`, `plans/run_case.py`, `plans/store.py`, `plans/run_report.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_run_report.py`, `tests/test_heal_review.py`, `tests/test_plan_run_case.py`
- **Verify:** `pytest tests/test_plan_run_report.py tests/test_heal_review.py tests/test_plan_run_case.py -v` (27 passed). Live `/ui/desktop/?v=desk40` has `rpt-export-run` + `heal-run-filter`; `/api/plans/exportable-runs` + `/api/heal/proposals` OK; desktop window opened.
- **Jira:** close-out **KAN-159** + **KAN-160**
- **Next:** **KAN-247** UI-NAV-IA-1 Reports library / move section toggles (test **KAN-250**)

### 2026-11-17 — Council CR — Nav IA (Reports data → menu → Settings hub)
- **Agent/chat:** Advisory Council Room — Designer CR after Gradio top tabs + settings-like area pages
- **Done (docs/Jira only):** Spec updated FR-UI-1/2/7, FR-SET-3/4, FR-REP-2/4. ROADMAP UI-NAV-IA-1…3. Sequence locked: (1) Reports library + move section toggles, (2) Gradio menu button, (3) Settings category hub. Active Build **unchanged: KAN-159**.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`, this log
- **Verify:** n/a (no product code)
- **Jira:** **KAN-247** (test **KAN-250**) Reports data; **KAN-248** (test **KAN-251**) Gradio menu; **KAN-249** (test **KAN-252**) Settings hub — epic **KAN-27**; Relates + comments on KAN-102/103/159
- **Next:** pick-up still **KAN-159**; then **KAN-247** UI-NAV-IA-1

### 2026-11-17 — KAN-157 — C1 same plan in Gradio
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-157
- **Done:** Gradio **Plans** tab lists level-scoped plans from the same store as desktop; case picker + last-run detail; Refresh reloads desktop results; **Run case** calls `run_single_case` (headed A7 path). Chat/Settings/Reports/Documents tabs kept.
- **Files:** `ui/gradio_app.py`, `tests/test_plans_tab.py`
- **Verify:** `pytest tests/test_plans_tab.py -v` (5 passed). Live Gradio `/config` has tabitem Plans + `plans-panel` + Run case; Computer Use showed Plans among tabs on `127.0.0.1:7860`.
- **Jira:** close-out **KAN-157** + **KAN-158**
- **Next:** **KAN-159** C2 report sections and heal review for a run

### 2026-11-17 — KAN-155 — B7 notes on a case and on a run
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-155
- **Done:** Local exploratory notes on a case (`case.note`) and on a run (`run.tester_note`, preserves system/error `run.note`). `POST /api/plans/…/notes` + Plans desk39 Case/Run note fields + Save notes. Notes appear under Evidence in report export when that section is on. Level-scoped with the plan.
- **Files:** `plans/notes.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `reports/sections.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_run_case.py`, `tests/test_report_sections.py`
- **Verify:** `pytest tests/test_plan_run_case.py tests/test_report_sections.py -v` (26 passed). Live desk39 HTML has `plan-notes-save` + `plan-run-note`.
- **Jira:** close-out **KAN-155** + **KAN-156**
- **Next:** **KAN-157** C1 same plan in Gradio

### 2026-11-16 — KAN-153 — B6 known issues and exclusions
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-153
- **Done:** Case/run can link known-issue note + optional Jira key via `POST /api/plans/…/known-issue`. Failed runs stay red and are labelled **known**. Reports gain `known_issues` section toggle (include/exclude). Nothing auto-transitioned in Jira. Plans desk38 UI + Gradio Reports checkbox.
- **Files:** `plans/known_issue.py`, `plans/store.py`, `plans/run_case.py`, `reports/sections.py`, `main.py`, `ui/desktop/*`, `ui/gradio_app.py`, `desktop_app.py`, `tests/test_plan_run_case.py`, `tests/test_report_sections.py`
- **Verify:** `pytest tests/test_plan_run_case.py tests/test_report_sections.py -v` (23 passed). Live `/api/report-sections` includes `known_issues`; desk38 HTML has `plan-known-save` + `rpt-known-issues`.
- **Jira:** close-out **KAN-153** + **KAN-154**
- **Next:** **KAN-155** B7 notes on a case and on a run

### 2026-11-16 — KAN-151 — B5 rerun failed only
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-151
- **Done:** From finished failures, `POST /api/plans/{id}/rerun-failed` runs only failed/error cases sequentially; new `suite_run` id linked on the same plan; case runs stamped with `suite_run_id`. Disabled/quarantined candidates skipped with reasons shown. Plans desk37 **Rerun failed only** + skip/result panel.
- **Files:** `plans/rerun_failed.py`, `plans/store.py`, `plans/run_case.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_run_case.py`
- **Verify:** `pytest tests/test_plan_run_case.py -v` (15 passed). Live desk37 HTML has `plan-rerun-failed`; desktop window opened on desk37.
- **Jira:** close-out **KAN-151** + **KAN-152**
- **Next:** **KAN-153** B6 known issues and exclusions

### 2026-11-16 — KAN-149 — B4 pause on fail
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-149
- **Done:** Run option `pause_on_fail` (off by default). On step fail, headed browser stays open until Continue (remaining steps) or Stop (records failed run). Session APIs + Plans checkbox / Continue / Stop (desk36).
- **Files:** `plans/pause_session.py`, `plans/run_case.py`, `plugins/playwright_runner.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_run_case.py`
- **Verify:** `pytest tests/test_plan_run_case.py -v` (11 passed). Live desk36 HTML has `plan-pause-on-fail` + Continue/Stop.
- **Jira:** close-out **KAN-149** + **KAN-150**
- **Next:** **KAN-151** B5 rerun failed only

### 2026-11-16 — KAN-147 — B3 defect packet preview
- **Agent/chat:** implementer subagent — six-ticket pick-up (6/6)
- **Done:** `GET /api/plans/…/defect-preview` builds symptom/expected/actual/environment/replication/evidence from last run — confirm still required for Jira create.
- **Files:** `plans/defect_packet.py`, `main.py`, `ui/desktop/*`, `tests/test_plan_run_case.py`
- **Verify:** `pytest tests/test_plan_run_case.py -v` (8 passed, includes preview test)
- **Jira:** close-out **KAN-147** + **KAN-148**
- **Next:** **KAN-149** B4 pause on fail

### 2026-11-16 — KAN-145 — B2 failure class before filing
- **Agent/chat:** implementer — six-ticket pick-up (5/6)
- **Done:** `set_run_failure_class` + Plans dropdown; create-bug allowed only for `product_bug`.
- **Files:** `plans/failure_class.py`, `plans/store.py`, `main.py`, `ui/desktop/*`
- **Verify:** pytest failure_class test in `test_plan_run_case.py`
- **Jira:** **KAN-145** + **KAN-146**
- **Next:** **KAN-147**

### 2026-11-16 — KAN-143 — B1 evidence bundle on failed case
- **Agent/chat:** implementer — (4/6)
- **Done:** Failure bundle under `%LOCALAPPDATA%/ai_testing_app/evidence/{run_id}/` (bundle.json, screenshot path, console-like step errors).
- **Files:** `plans/evidence_bundle.py`, `plans/run_case.py`, `plans/store.py`
- **Verify:** pytest `test_evidence_bundle_paths`
- **Jira:** **KAN-143** + **KAN-144**
- **Next:** **KAN-145**

### 2026-11-16 — KAN-141 — A9 case keeps source links
- **Agent/chat:** implementer — (3/6)
- **Done:** `GET /api/plans/{plan}/cases/{case}` + Plans case detail panel; case list shows Jira key, source ref, manual-draft, last run line.
- **Files:** `plans/run_case.py` (`case_detail`), `main.py`, `ui/desktop/*`
- **Verify:** pytest `test_case_detail_source_and_last_run`
- **Jira:** **KAN-141** + **KAN-142**
- **Next:** **KAN-143**

### 2026-11-16 — KAN-139 — A8 degraded mode
- **Agent/chat:** implementer — (2/6)
- **Done:** `GET /api/degraded-mode`; chat blocked with clear message when Ollama down; draft responses attach degraded hints when Jira/read fails; target-down runs stay environment error.
- **Files:** `settings/degraded.py`, `main.py`, `ui/desktop/desktop.js`
- **Verify:** pytest degraded tests + `tests/test_connection_health.py`
- **Jira:** **KAN-139** + **KAN-140**
- **Next:** **KAN-141**

### 2026-11-16 — KAN-137 — A7 run a single case and show evidence
- **Agent/chat:** implementer — six-ticket pick-up (1/6)
- **Done:** `POST /api/plans/…/cases/…/run` runs Playwright headed for one enabled case; records pass/fail/duration/screenshot; disabled cases refused; desk35 Run case UI.
- **Files:** `plans/run_case.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_run_case.py`
- **Verify:** `pytest tests/test_plan_run_case.py tests/test_plan_edit.py tests/test_connection_health.py -v` (14 passed)
- **Jira:** **KAN-137** + **KAN-138**
- **Next:** **KAN-139**

### 2026-11-16 — KAN-135 — A6 empty state / starter template on orb home
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-135
- **Done:** Orb-home Lab checklist HUD auto-shows when the active level has no plans (check connection, draft from story key, start template). `plans/starter.py` + `GET /api/plans/home` + `POST /api/plans/starter` create a normal editable starter plan (3 cases). No second welcome canvas; App areas still open (starter opens Plans). Screen drawer can also toggle Lab checklist. Cache bust desk34.
- **Files:** `plans/starter.py`, `plans/__init__.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_plan_starter.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP
- **Verify:** `pytest tests/test_plan_starter.py tests/test_plan_edit.py tests/test_plan_store.py -v` (7 passed). Live desk34 HTML has `hud-lab`; Computer Use: empty checklist visible → Start a template → Plans with Starter plan 3 cases.
- **Jira:** story agent-completion + **KAN-136** evidence/Done; **KAN-135** Done
- **Next:** **KAN-137** A7 run a single case and show evidence (test **KAN-138**)

### 2026-11-16 — KAN-129 / KAN-131 / KAN-133 — A3–A5 (model + draft + edit plan)
- **Agent/chat:** Cursor IDE Agent (Composer) — multi-ticket pick-up (next three)
- **Done:** **A3** list/save Ollama model (`settings/ollama_models.py`, App Settings + Gradio); chat uses saved model; missing model refused. **A4** draft plan from one Jira issue + optional document (`plans/draft.py`); cases keep jira_key + source_ref; no Jira writes. **A5** rename/reorder/disable/note cases; `cases_for_run` skips disabled; desktop **Plans** area (desk33).
- **Files:** `settings/ollama_models.py`, `settings/store.py`, `settings/connection_health.py`, `plans/draft.py`, `plans/store.py`, `plans/__init__.py`, `agent/agent.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_ollama_model.py`, `tests/test_plan_draft.py`, `tests/test_plan_edit.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP
- **Verify:** `pytest tests/test_ollama_model.py tests/test_plan_draft.py tests/test_plan_edit.py -v` (10 passed). Live `/api/ollama-models` (5 models); draft/edit/runnable smoke OK; desk33 HTML has `set-ollama-model` + `app-section-plans`.
- **Jira:** story agent-completion + tests **KAN-130**/**KAN-132**/**KAN-134** evidence/Done; stories **KAN-129**/**KAN-131**/**KAN-133** Done
- **Next:** **KAN-135** A6 empty state / starter template (test **KAN-136**)

### 2026-11-16 — KAN-127 — Connect-once checklist and health (A2)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-127
- **Done:** Connect-once checklist on existing App Settings keys (Jira URL/project, target URL, optional exe, messaging, level). `GET /api/connection-health` reports up/down for Jira, Ollama, and target without secrets (system CA via `ssl.create_default_context`). Desktop desk32 Save connection + Check health; Gradio Check health. Level switch still confirm-gated. No new credential store.
- **Files:** `settings/connection_health.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_connection_health.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP
- **Verify:** `pytest tests/test_connection_health.py tests/test_app_settings.py -v` (10 passed). Live `GET /api/connection-health` → Jira up, Ollama up, target not_configured; desk32 HTML has Connect-once / `conn-health-btn`.
- **Jira:** story agent-completion + **KAN-128** evidence/Done; **KAN-127** Done
- **Next:** **KAN-129** A3 choose Ollama model (test **KAN-130**)

### 2026-11-16 — KAN-125 — Local plan, suite, case, and run model (A1)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-125
- **Done:** Level-scoped in-app plan store: plan → suite of cases → runs under `%LOCALAPPDATA%/ai_testing_app/plans/{LEVEL}/`. OFFICIAL/SECRET lists isolated. Create/add_case/add_run do not rewrite settings, reports, or Playwright project files. Thin API `/api/plans*`. Privacy wipe category `plans` added. No new UI (OOS).
- **Files:** `plans/store.py`, `plans/__init__.py`, `main.py`, `settings/privacy.py`, `tests/test_plan_store.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, TEST_ALL_BACKLOG
- **Verify:** `pytest tests/test_plan_store.py tests/test_privacy_gdpr.py tests/test_multi_sandbox.py tests/test_playwright_suite.py tests/test_security_isolation.py -v` (26 passed)
- **Jira:** story agent-completion + **KAN-126** evidence/Done; **KAN-125** Done
- **Next:** **KAN-127** A2 connect-once checklist and health (test **KAN-128**)

### 2026-11-16 — OPS — Test-all CR (docs + Jira catalogue)
- **Agent/chat:** Council Room → option 2 after expanded catalogue + orb-home widgets amend
- **Done:** Locked test-all vision (cut nothing; in-app plan/suite; one orb home + HUD widgets). Updated FUNCTIONAL_SPEC (FR-CONN/FR-PLAN/FR-CI/FR-MAN), PROJECT_MEMORY, ROADMAP, work-log-handoff deferred guard. Seeded Jira epics **KAN-117…124**, stories+tests **KAN-125…246**. Commented **KAN-81**. Active slice → **KAN-125** (A1).
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `docs/ops/test_all_catalogue.json`, `scripts/jira_kan_seed_test_all.py`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `.cursor/rules/work-log-handoff.mdc`
- **Verify:** Jira keys created; dry-run then seed exit 0; FIRST_ALPHA_STORY=KAN-125
- **Jira:** backlog seed (not a product-feature close-out); KAN-81 comment posted
- **Next:** Build chat pick-up **KAN-125** (A1 plan/suite model)

### 2026-11-16 — OPS — Advisory Council Room (separate from Build pick-up)
- **Agent/chat:** Cursor IDE Agent — design + land council roster
- **Done:** Added Council Room as a **separate** Agent chat (`council`) for review/creative multi-persona debate. Build lane (“pick up where we left off”) unchanged. Council may update docs/Jira/rules after confirm; no product feature coding. Seats include future company-wide users (QA, test manager, developer, PO, release, security) plus auditors/architect/UX/scope/pragmatist.
- **Files:** `docs/ops/ADVISORY_COUNCIL.md`, `docs/ops/TEAM.md`, `docs/ops/HOW_WE_WORK.md`, `AGENTS.md`, `PROJECT_MEMORY.md`, `.cursor/skills/advisory-council/SKILL.md`, `.cursor/agents/council.md`, `.cursor/agents/council-*.md`
- **Verify:** Open Agent → select **`council`**; Build chat still uses pick-up only
- **Jira:** n/a (ops tooling, not a KAN story)
- **Next:** Active coding slice remains **KAN-81** deferred; use Build pick-up when coding resumes

### 2026-11-16 — KAN-99 — Audit log for Jira write operations (FR-JIRA-5 / NFR §4.3)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-99
- **Done:** Confirmed Jira writes (create/bug/test/transition/comment/update_status/set_parent) append a local `jira_write_audit.jsonl` line (timestamp, action, issue_key, session_id, status) under LOCALAPPDATA. Declined confirm leaves no success audit line. Tokens never stored. Privacy wipe includes `jira_write_audit`.
- **Files:** `plugins/jira_plugin.py`, `settings/privacy.py`, `tests/test_jira_write_audit.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_jira_write_audit.py tests/test_create_bug.py tests/test_privacy_gdpr.py -v` (14 passed)
- **Jira:** story agent-completion + **KAN-100** evidence/Done; **KAN-99** Done
- **Next:** **KAN-81** voice — deferred until mic connected

### 2026-11-16 — KAN-97 — Busy and long-run UX while agent or tests execute (FR-AGENT-5 / NFR §4.6)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-97
- **Done:** Desktop chat shows busy bar (label + elapsed + Cancel) during `/chat`, orb thinking mode, send disabled without locking drawers. AbortController cancel. Agent/HTTP failures render as error messages (`ok:false` from `/chat`). Gradio `respond` surfaces failures clearly. Cache bust desk31.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `main.py`, `ui/gradio_app.py`, `tests/test_busy_ux.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_busy_ux.py tests/test_jira_project_default.py tests/test_jira_read_ux.py tests/test_sessions.py -v` (20 passed). Live `http://127.0.0.1:8765` desk31 HTML/JS has `chat-busy` / Cancel / `setChatBusy`. Desktop window opened (`desktop_app.py` desk31).
- **Jira:** story agent-completion + **KAN-98** evidence/Done; **KAN-97** Done
- **Next:** **KAN-99** Jira write audit (test KAN-100)

### 2026-11-16 — KAN-95 — Multi-sandbox real orchestration beyond stub (FR-PLUG-1)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-95
- **Done:** Replaced hardcoded mock sandboxes with level-scoped `multi_sandboxes` records, local status, prepare (profile dirs), upsert/remove, and max-4 limit. Plan mode is `local` (not `mock`). Plugin toggle kept. Desktop Sandboxes (desk30) + Gradio + agent `orchestrate_sandboxes` actions extended. No cloud farms.
- **Files:** `plugins/multi_sandbox.py`, `plugins/registry.py`, `settings/store.py`, `main.py`, `agent/agent.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_multi_sandbox.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_multi_sandbox.py -v` (7 passed). Live API enable→upsert→plan(local)→prepare→remove→disable→list disabled. Plugin prepare created profile under LOCALAPPDATA browser_profiles.
- **Jira:** story agent-completion + **KAN-96** evidence/Done; **KAN-95** Done
- **Next:** **KAN-97** busy/long-run UX (test KAN-98)

### 2026-11-16 — KAN-93 — First-class jira_project default for agent Jira reads (FR-LEARN-4)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-93
- **Done:** `list_stories` / `jira_action` default to settings `jira_project` when project omitted; empty settings returns a clear “project key required” message. App Settings API + desktop (desk29 `set-jira-project`) + Gradio expose and save `jira_project`. Agent tool schemas make project optional and prompt asks for a key when the tool says required. Writes still confirm-gated.
- **Files:** `plugins/jira_plugin.py`, `settings/store.py`, `main.py`, `agent/agent.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_jira_project_default.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_jira_project_default.py tests/test_app_settings.py tests/test_jira_readonly.py tests/test_jira_read_ux.py -v` (22 passed). Live `list_stories()` with `jira_project=KAN` → ok + 50 stories. `POST /api/app-settings` jira_project=KAN → updated.
- **Jira:** story agent-completion + **KAN-94** evidence/Done; **KAN-93** Done
- **Next:** **KAN-95** multi-sandbox real orchestration beyond stub (test KAN-96)

### 2026-11-16 — KAN-91 — Jira rate-limit backoff and human-readable 429/auth errors (FR-JIRA-6)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-91
- **Done:** Shared `_request` in `jira_plugin` retries on HTTP 429 using `Retry-After` (default 2s, up to 6 attempts) with light inter-call spacing. 401/403/429 return human-readable `unauthorized` / `rate_limited` messages; never echoes tokens. Wired through search, read_issue, create, transition, comment, and related helpers.
- **Files:** `plugins/jira_plugin.py`, `tests/test_jira_rate_limit.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_jira_rate_limit.py tests/test_jira_read_ux.py tests/test_jira_steps.py tests/test_jira_readonly.py -v` (26 passed)
- **Jira:** story agent-completion + **KAN-92** evidence/Done; **KAN-91** Done
- **Next:** **KAN-93** jira_project default for agent reads (test KAN-94)

### 2026-11-16 — KAN-89 — Read Jira story descriptions and acceptance criteria (FR-JIRA-1)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-89
- **Done:** Exposed fuller read UX on top of KAN-85 `read_issue`: agent tool `read_issue`; `list_stories(include_description=…)`; `GET/POST /api/jira-issue`; App Settings **Read Jira story** (desk28). Responses never include credentials; missing/unauthorized return clear messages.
- **Files:** `plugins/jira_plugin.py`, `agent/agent.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_jira_read_ux.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_jira_read_ux.py tests/test_jira_steps.py tests/test_jira_readonly.py -v` (17 passed). Live `read_issue('KAN-89')` + `GET /api/jira-issue/KAN-89` → ok + AC; HTML desk28 has `jira-read-key` / Read story.
- **Jira:** story agent-completion + **KAN-90** evidence/Done; **KAN-89** Done
- **Next:** **KAN-91** Jira 429 backoff / auth errors (test KAN-92)

### 2026-11-16 — KAN-87 — Expand desktop .exe plugin beyond smoke (FR-TEST-3)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-87
- **Done:** Extended `desktop_runner` with structured steps (`launch`, `wait_window`, `focus_window`, `type_text`, `wait`, `close`) via stdlib + Win32 ctypes (no Playwright fork). Smoke path unchanged. Agent `run_desktop` accepts `steps`; API `/api/desktop-smoke` accepts `steps` / `demo`; App Desktop area **Run demo steps** (desk27). Bug **KAN-116**: Win11 Notepad survived `Popen.terminate` — fixed with `taskkill /T /F` fallback.
- **Files:** `plugins/desktop_runner.py`, `plugins/registry.py`, `main.py`, `agent/agent.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_desktop_runner.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_desktop_runner.py -v` (10 passed). Live `POST /api/desktop-smoke` demo → pass (launch/wait_window/type_text/close). HTML desk27 has Run demo steps; plugin status lists `supported_actions`.
- **Jira:** story agent-completion + **KAN-88** evidence/Done; Bug **KAN-116** Fix+Done; **KAN-87** Done
- **Next:** **KAN-89** read Jira story descriptions / AC (test KAN-90)

### 2026-11-16 — KAN-85 — Generate Playwright steps from Jira AC (FR-TEST-1)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-85
- **Done:** `read_issue` fetches summary/description/AC (ADF→text). `generate_steps_from_jira` builds happy+negative drafts with `expect_*`; fetch failure / empty AC returns clear error and never invents AC. Agent `generate_playwright_steps` accepts `issue_key`. Fixed jira_plugin httpx SSL via `_async_client(verify=ssl.create_default_context())` (Bug **KAN-115** Fix+Done).
- **Files:** `plugins/jira_plugin.py`, `plugins/playwright_steps.py`, `agent/agent.py`, `tests/test_jira_steps.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_jira_steps.py -v` (8 passed). Live: `generate_steps_from_jira('KAN-85')` → ok + expect_*; `KAN-99999` → not found, `invented_ac=false`.
- **Jira:** story agent-completion + **KAN-86** evidence/Done; Bug **KAN-115** Fix+Done; **KAN-85** Done
- **Next:** **KAN-87** expand desktop .exe plugin beyond smoke (test KAN-88)

### 2026-11-16 — KAN-83 — Playwright headed/headless mode setting (FR-TEST-2)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-83
- **Done:** Settings key `playwright_headless` (default headed). App Settings + Gradio expose headed/headless; runner `launch_persistent_context(headless=…)`; suite adds `--headed` when headed; optional `run_playwright(headless=)` override. Partial `POST /api/app-settings` no longer clears omitted fields (bug found+fixed during verify).
- **Files:** `settings/store.py`, `plugins/playwright_runner.py`, `plugins/playwright_suite.py`, `main.py`, `agent/agent.py`, `ui/desktop/*`, `desktop_app.py` (desk26), `ui/gradio_app.py`, `tests/test_playwright_mode.py`, `tests/test_app_settings.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_playwright_mode.py tests/test_app_settings.py tests/test_framework_switch.py -v` (18 passed). Live desk26 API mode toggle + HTML `set-playwright-mode`; jira_url restored after accidental partial wipe then fixed.
- **Jira:** story agent-completion + **KAN-84** evidence/Done; Bug **KAN-114** partial-settings wipe Fix+Done; **KAN-83** Done
- **Next:** **KAN-85** generate Playwright steps from Jira AC (test KAN-86)

### 2026-11-16 — OPS — Defer KAN-81 voice until mic available
- **Agent/chat:** Cursor IDE Agent — user CR / priority
- **Done:** Voice input (**KAN-81** / test **KAN-82**) deferred until a microphone is connected. Active slice → **KAN-83** headed/headless (test **KAN-84**).
- **Files:** WORK_LOG, ROADMAP, PROJECT_MEMORY, FUNCTIONAL_SPEC note
- **Verify:** Active slice table points at KAN-83; KAN-81 remains open/deferred
- **Jira:** deferral comments on KAN-81 / KAN-82
- **Next:** **KAN-83** Playwright headed/headless mode setting

### 2026-11-16 — KAN-79 — Dynamic framework switching stub via settings (FR-PLUG-3)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-79
- **Done:** Settings key `test_framework` defaults to Playwright. Stub module + registry entry; Selenium/Cypress selectable; run returns clear `not_implemented` (no crash). APIs `GET/POST /api/test-framework` + `/run`; App Settings select (desktop desk25 + Gradio); agent tool `test_framework`; Playwright run/suite gated when non-Playwright active.
- **Files:** `plugins/framework_switch.py`, `plugins/registry.py`, `settings/store.py`, `main.py`, `agent/agent.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_framework_switch.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_framework_switch.py tests/test_app_settings.py tests/test_multi_sandbox.py -v` (13 passed). Live desk25: HTML has Test framework select; API set selenium → run `not_implemented` → reset playwright.
- **Jira:** story agent-completion + **KAN-80** evidence/Done; **KAN-79** Done (yes)
- **Next:** **KAN-81** voice input (test KAN-82)

### 2026-11-16 — KAN-77 — First-class target URL, exe path, messaging endpoints (FR-LEARN-2/3)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-77
- **Done:** Promoted `target_url`, `target_app_path`, and `api_endpoint` to first-class App Settings (level-scoped). `save_app_settings` + GET/POST `/api/app-settings`; desktop Settings fields (desk24); Gradio Settings target section; agent prompt/tool description; doc-ingest messaging/exe decline covered.
- **Files:** `settings/store.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `agent/agent.py`, `tests/test_app_settings.py`, `tests/test_doc_ingest.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_app_settings.py tests/test_doc_ingest.py -v` (13 passed). Live `POST /api/app-settings` persisted URL/exe/messaging under OFFICIAL. Desktop `desktop_app.py` desk24 launched; HTML fields present.
- **Jira:** story agent-completion + **KAN-78** evidence/Done; **KAN-77** Done (yes)
- **Next:** **KAN-79** dynamic framework switching stub (test KAN-80)

### 2026-11-16 — KAN-75 — Heal proposal review UI (FR-HEAL-2/5)
- **Agent/chat:** Cursor IDE Agent (Composer) — heal review
- **Done:** Pending locator heals from `heal_audit.jsonl` surfaced in App → **Heal review** (desk23). APIs `GET /api/heal/proposals`, `POST /api/heal/approve|reject`. Approve records approver; reject leaves unaccepted; no suite auto-commit. Hub spokes → 8.
- **Files:** `plugins/heal_policy.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_heal_review.py`, `tests/test_orb_hub.py`, `tests/test_nav_overlap.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_heal_review.py tests/test_heal_policy.py tests/test_orb_hub.py tests/test_nav_overlap.py -v` (18 passed). Computer Use on `desktop_app.py` desk23: App → Heal review shows locator diffs + Approve/Reject; live API approve/reject cleared pending.
- **Jira:** story agent-completion + **KAN-76** evidence/Done; **KAN-75** Done (yes)
- **Next:** **KAN-77** first-class target URL / exe path / messaging endpoints (test KAN-78)

### 2026-11-16 — KAN-104 — Full verify closes KAN-103 (UI-DESK-4)
- **Agent/chat:** Cursor IDE Agent (Composer) — desktop shell verify
- **Done:** KAN-104 Computer Use + pytest evidence. Native `desktop_app.py` desk22g: agent home chat+orb; App drawer → Settings dedicated surface (layout A–E, Jira URL, no orb sliders); Esc closes; App toggle seam-tab (KAN-101/110); Screen → Widget Settings → Security HUD Level OFFICIAL. Story **KAN-103** + test **KAN-104** → Done.
- **Files:** WORK_LOG, PROJECT_MEMORY, ROADMAP, KAN102 plan (no product code this slice)
- **Verify:** `pytest tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_area_layout.py tests/test_hud_widgets.py -v` (15 passed). Computer Use on `desktop_app.py`.
- **Jira:** story agent-completion + **KAN-104** evidence/Done; **KAN-103** Done (yes)
- **Next:** **KAN-75** heal proposal review UI

### 2026-11-16 — KAN-110 — App drawer / chat nav hit overlap (desk22g)
- **Agent/chat:** Cursor IDE Agent (Composer) — desktop shell
- **Done:** Park open-drawer toggle as an outside seam tab (`parkToggleOnOpenDrawer`); raise open drawer z-index; disable chat pointer-events while App drawer open; nudge chat left gutter clear of App toggle; Esc closes drawers; cache desk22g. Fixes KAN-101 / KAN-113 class.
- **Files:** `ui/desktop/desktop.js`, `desktop.css`, `index.html`, `desktop_app.py`, `tests/test_nav_overlap.py`, `tests/test_orb_hub.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, KAN102 plan, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_area_layout.py tests/test_hud_widgets.py -v` (15 passed). Computer Use on `desktop_app.py` desk22*: App drawer opens; Security/Reports area surfaces open from App nav; toggle no longer covers nav list.
- **Jira:** Task **KAN-110** Done; Bugs **KAN-101** + **KAN-113** Fix+Done; progress on **KAN-103**; evidence on **KAN-104** (story stays In Progress for full verify)
- **Next:** **KAN-104** full Computer Use checklist → close **KAN-103**; then **KAN-75**

### 2026-11-16 — KAN-109 — Orb hub particle polish (desk21b)
- **Agent/chat:** Cursor IDE Agent (Composer) — desktop shell
- **Done:** Particle hub for layout `orb_hub`: SVG spoke lines, node dots, drifting particles, accent CSS vars, open/close scale motion + `aria-expanded` on orb hit. App drawer remains a11y fallback. Cache-bust desk21b. Fixed hub `[hidden]` display override that could steal hits while closed.
- **Files:** `ui/desktop/index.html`, `desktop.js`, `desktop.css`, `desktop_app.py`, `tests/test_orb_hub.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, KAN102 plan, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_orb_hub.py tests/test_area_layout.py tests/test_hud_widgets.py -v` (12 passed). Computer Use on `desktop_app.py` desk21b: App → Documents opens dedicated surface (Back returns home). Hub radial polish unit-covered; full orb-hub click path deferred to KAN-110 when App-toggle/chat overlap is cleared.
- **Jira:** Task **KAN-109** Done + agent comment; progress on **KAN-103**; evidence on **KAN-104**; Bug **KAN-113** (App/chat nav hit conflict) Relates → KAN-103/104/110 (story stays In Progress)
- **Next:** **KAN-110** KAN-101 drawer toggle vs Settings nav overlap under **KAN-103**

### 2026-11-16 — KAN-107 — Agent-home HUD widgets (desk20)
- **Agent/chat:** Cursor IDE Agent (Composer) — desktop shell
- **Done:** Replaced stub chips with movable Security + Reports mini panels on agent home. Screen drawer toggles persist in `desktop-hud-widgets-v1`; positions use `desktop-shell-layout-v1`. Live Security level from `/api/security-level`; Reports from new `GET /api/reports/latest-summary` (`reports.exporter.latest_summary`). HUD is home-only (hidden when any App area is open). Cache-bust desk20.
- **Files:** `ui/desktop/index.html`, `desktop.js`, `desktop.css`, `desktop_app.py`, `main.py`, `reports/exporter.py`, `tests/test_hud_widgets.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, KAN102 plan, FUNCTIONAL_SPEC
- **Verify:** `pytest tests/test_hud_widgets.py tests/test_area_layout.py -v` (9 passed). Computer Use on `desktop_app.py`: enable both HUD toggles → Security Level OFFICIAL + Reports “Last run: 1 test”; App → Settings hides HUD.
- **Jira:** Task **KAN-107** Done + agent comment; progress on **KAN-103**; evidence on **KAN-104** (story stays In Progress)
- **Next:** **KAN-109** orb hub particle polish under **KAN-103**

### 2026-11-16 — OPS — desk19 PM handoff (pick-up alignment)
- **Agent/chat:** PM + doc-keeper — WORK_LOG Active slice, Jira REST, docs; standard “pick up where we left off” flow
- **Done:** Active slice → **KAN-103** / start **KAN-107**; KAN-102 description + Fix comment (dedicated surfaces + layout A–E + style coupling); reconciled Tasks **KAN-106–112**, test **KAN-104** (no duplicate KAN-105 story); FUNCTIONAL_SPEC/ROADMAP/plan sync
- **Files:** `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/ROADMAP.md`, `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`, `scripts/jira_kan103_desk19_handoff.py`, `scripts/jira_kan_slice_closeout.py`
- **Verify:** Jira **KAN-103** In Progress; open Jira **KAN-107** for AC; `pytest tests/test_area_layout.py` (4 passed); `desktop_app.py` desk19
- **Jira:** KAN-102/106/108/112 Done; KAN-103 In Progress; KAN-107/109/110/104 open; KAN-105 duplicate noted
- **Next:** Say **pick up where we left off** → implement **KAN-107** under **KAN-103**

### 2026-11-16 — KAN-103 — Configurable area layouts A–E + style accents
- **Agent/chat:** Designer + Implementer (Grok) — desktop shell
- **Done:** CR locked all mockups as settings, not one pick. Added split (D) and floating (E) frames, including aether settings variants. App Settings **App area layout** persists `desktop-area-layout-v1` (`overlay`, `stage`, `orb_hub`, `split`, `floating`). App drawer opens `#area-surface` instead of inline sections. Esc/Back closes. Orb-hub mode uses radial spokes then overlay. Screen drawer HUD toggles stub (Security / Reports chips). Area chrome uses the active orb accent variables. Story left open for hub polish and fuller HUD.
- **Files:** `ui/desktop/index.html`, `desktop.js`, `desktop.css`, `desktop_app.py`, `settings/area_layout.py`, `tests/test_area_layout.py`, `docs/mockups/kan103_nav/option_d_*.png`, `option_e_*.png`, README, FUNCTIONAL_SPEC, PROJECT_MEMORY, ROADMAP, KAN102 plan, WORK_LOG
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_area_layout.py -v`. Desktop: App → Settings → App area layout; Screen → Orb style mystic vs aether recolors the open surface.
- **Jira:** comments + description note on KAN-103, KAN-102, KAN-106–109; new Task **KAN-112** (story not marked Done)
- **Next:** Hub particle polish and richer HUD widgets on KAN-103; **KAN-75** stays deferred

### 2026-11-16 — OPS — KAN-103 nine labeled mockups in grok/ (design gate)
- **Agent/chat:** ui-orb (Grok) — images and README only; no `ui/desktop/` code
- **Done:** Nine labeled mystic-cyan frames under `docs/mockups/kan103_nav/grok/` (A1–A3, B1–B3, C1–C3) for the Designer pick. README now points at that set. Active slice was already **KAN-103** / **KAN-106** after the pick; **KAN-75** stays deferred. Design not locked.
- **Files:** docs/mockups/kan103_nav/grok/*.png, docs/mockups/kan103_nav/README.md, docs/ops/WORK_LOG.md
- **Verify:** Open the nine PNGs in `grok/` and choose A, B, C, or hybrid.
- **Jira:** skipped — Active slice and prior KAN-103 comment already in place
- **Next:** User selects **A**, **B**, **C**, or hybrid → lock design → implement KAN-106

### 2026-11-16 — OPS — KAN-103 Grok image mockups A/B/C (design gate)
- **Agent/chat:** Cursor IDE Agent (Designer + PM — images and docs only; no `ui/desktop/` code)
- **Done:** Generated six mystic-cyan frames for nav options A/B/C and saved them under `docs/mockups/kan103_nav/` (`option_a_home.png`, `option_a_settings.png`, `option_b_home.png`, `option_b_settings.png`, `option_c_hub.png`, `option_c_settings.png`) plus HTML fallbacks `option_a.html`, `option_b.html`, `option_c.html`. Active slice remains **KAN-103** / start **KAN-106** after the user picks; **KAN-75** stays deferred.
- **Files:** docs/mockups/kan103_nav/option_*.png, option_{a,b,c}.html, README.md, docs/ops/WORK_LOG.md
- **Verify:** Open the six PNGs (or the three HTML files) and choose A, B, or C.
- **Jira:** comment on KAN-102 and KAN-103 pointing at the generated frames (design not locked).
- **Next:** User selects **A**, **B**, or **C** → lock design → implement KAN-106.

### 2026-11-15 — OPS — Active slice → KAN-103; nav mockups A/B/C (design gate)
- **Agent/chat:** Cursor IDE Agent (PM + Designer slice — docs, mockups, Jira; no `ui/desktop/` code)
- **Done:** Reprioritized Active slice to **KAN-103** (start **KAN-106** after mockup pick). **KAN-75** deferred. Added mockup pack `docs/mockups/kan103_nav/` (HTML + PNG for options A/B/C), README, `scripts/render_kan103_mockup_png.py`, `scripts/jira_kan103_mockup_gate.py`. Updated WORK_LOG, KAN102 plan, ROADMAP Now, PROJECT_MEMORY.
- **Files:** docs/mockups/kan103_nav/**, docs/ops/WORK_LOG.md, docs/ops/KAN102_NAV_WIDGETS_PLAN.md, docs/ops/ROADMAP.md, PROJECT_MEMORY.md, scripts/render_kan103_mockup_png.py, scripts/jira_kan103_mockup_gate.py
- **Verify:** Open `docs/mockups/kan103_nav/index.html`; browse PNGs under `png/`; Jira comments on KAN-103/102/75
- **Jira:** descriptions prepended on KAN-103/106/107/108; comments KAN-103/102/75 (yes)
- **Next:** User selects **A**, **B**, **C**, or hybrid → lock design → KAN-106 implementation

### 2026-11-15 — OPS — KAN-102 CR: nav model, widgets, App vs Orb settings (PM sync)
- **Agent/chat:** Cursor IDE Agent (PM slice — docs + Jira only, no UI code)
- **Done:** Product decision locked per Designer CR: agent home = chat + orb; mockup side panels = HUD widgets (Screen drawer toggles); App areas = dedicated surfaces; App Settings ≠ Orb settings. Updated FUNCTIONAL_SPEC (FR-UI-6/7, FR-SET-3), PROJECT_MEMORY, ROADMAP (UI-DESK-4), orb_styles.md, `docs/ops/KAN102_NAV_WIDGETS_PLAN.md`. Jira: KAN-102 description + comment; parent Story under KAN-27 + Tasks + test ticket; comments on KAN-73/74/101. Helper: `scripts/jira_kan102_pm_cr.py` (re-runnable).
- **Files:** docs/FUNCTIONAL_SPEC.md, PROJECT_MEMORY.md, docs/ops/ROADMAP.md, docs/ops/WORK_LOG.md, docs/ops/KAN102_NAV_WIDGETS_PLAN.md, docs/mockups/orb_styles.md, scripts/jira_kan102_pm_cr.py
- **Verify:** Jira browse KAN-102 Relates; read plan doc; spec §3.8/3.10
- **Jira:** KAN-102 updated; **KAN-103** Story, **KAN-104** test, Tasks **KAN-106–110**; comments KAN-73/74/101; duplicate **KAN-105** marked do-not-use
- **Next:** Active remains **KAN-75**; then **KAN-103** (start KAN-106)

### 2026-11-15 — OPS — Raised KAN-102 App area nav UX (screens/popups + orb idea)
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** Bug **KAN-102** — App nav areas should open separate screens or full-window popups (not inline drawer sections). Includes designer discussion note: orb as clickable settings hub with particle/neural links. Relates KAN-73/74/101. Needs product decision before implement.
- **Files:** WORK_LOG only (Jira ticket).
- **Verify:** https://ai-testing-lab.atlassian.net/browse/KAN-102
- **Jira:** KAN-102 Bug created + Relates + comment on KAN-73.
- **Next:** Active remains KAN-75; decide KAN-102 UX before coding.

### 2026-11-15 — OPS — KAN Bug + test issue types enabled; migrate + docs
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** User enabled Jira **Bug** and **`test`** issue types on KAN. Migrated 40 Task+label=test → `test` (41 total), KAN-101 Task+label=bug → Bug. Updated agent instructions + `create_test` / closeout / seed / rebuild to use `test` and Bug. **Task** reserved for development work under a Story (e.g. one Task per FR). Added `scripts/jira_kan_migrate_issue_types.py`.
- **Files:** plugins/jira_plugin.py, agent/agent.py, tests/test_create_test.py, scripts/jira_kan_*.py, AGENTS.md, JIRA_TICKET_TEMPLATE, skills/rules, PROJECT_MEMORY, WORK_LOG.
- **Verify:** `issuetype=test` count 41; `issuetype=Bug` includes KAN-101; pytest tests/test_create_test.py (+ related).
- **Jira:** types migrated in place (no recreate/close needed).
- **Next:** Active remains KAN-75 heal proposal review UI.

### 2026-11-15 — OPS — Mandatory Bug tickets during development (agent instructions)
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** Strengthened standing rule: any bug found during development must be raised on Jira and Relates-linked to the Story (+ test Task). Documented KAN createmeta has no Bug type → use Task + `label=bug` + `[Bug] …` until Bug type enabled. Raised KAN-101 for App drawer toggle overlapping Settings (found during KAN-73 verify; Relates KAN-73/KAN-74).
- **Files:** AGENTS.md, `.cursor/rules/work-log-handoff.mdc`, `.cursor/rules/00-core-efficiency.mdc`, `.cursor/skills/slice-workflow/SKILL.md`, `.cursor/skills/jira-safe/SKILL.md`, `.cursor/agents/implementer.md`, `.cursor/agents/verifier.md`, `docs/ops/HOW_WE_WORK.md`, `docs/ops/JIRA_TICKET_TEMPLATE.md`, WORK_LOG.
- **Verify:** KAN-101 created + Relates; instruction text present in AGENTS / skills / rules.
- **Jira:** KAN-101 (Task+bug); comment on KAN-73.
- **Next:** Active remains KAN-75 heal proposal review UI.

### 2026-11-15 — KAN-73 — Desktop App Settings panel (Jira URL and local-store summary)
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** FR-UI-1/FR-SET-1 desktop App drawer Settings: Jira base URL edit + Save, local store path, credential configured/incomplete/not-set label (never echoes email/token). Shared `app_settings_status` / `save_jira_url` in settings store; GET/POST `/api/app-settings`; Gradio summary uses same helper; desk18 cache-bust.
- **Files:** `settings/store.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_app_settings.py`, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_app_settings.py tests/test_settings_tab.py -v` (5 passed). Live `/api/app-settings` returns no secrets; desktop App drawer shows Settings nav (desk18).
- **Jira:** story Agent completion + KAN-74 test evidence/Done + KAN-73 Done (via closeout script).
- **Next:** KAN-75 heal proposal review UI (FR-HEAL-2/5; test KAN-76).

### 2026-11-15 — KAN-71 — Prompt-injection mitigations for untrusted inputs
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** FR-SEC-4: `agent/prompt_guard.py` — wrap untrusted data fences, injection heuristics, SECRET tool narrowing (hide `run_desktop` / `orchestrate_sandboxes`; always refuse shell/network/fs-outside tools). Agent system prompt + tool-result fencing; `confirm` from model args ignored for settings/delete (only exact user yes/confirm). Doc ingest marks untrusted + redacts secrets in model excerpts. Ollama `temperature: 0.2` for smaller local models.
- **Files:** `agent/prompt_guard.py`, `agent/agent.py`, `plugins/doc_ingest.py`, `tests/test_prompt_injection.py`, FUNCTIONAL_SPEC, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_prompt_injection.py tests/test_doc_ingest.py tests/test_privacy_gdpr.py tests/test_tool_calling.py -v` (34 passed).
- **Jira:** story Agent completion + KAN-72 test evidence/Done + KAN-71 Done (via closeout script).
- **Next:** KAN-73 desktop App Settings panel (FR-UI-1/FR-SET-1; test KAN-74).

### 2026-11-15 — KAN-69 — GDPR easy local data deletion and consent surfaces
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** FR-SEC-2: `settings/privacy.py` inventory + confirm-gated `delete_local_data` (reports/screenshots/heal_audit/sessions/browser_profiles; never credentials/settings.json). `telemetry_enabled` default false; `/health` + `/api/privacy` expose status; agent tool `delete_local_data`; App → Security Privacy UI (desk17) + Gradio Privacy section; doc ingest consent language reinforced.
- **Files:** `settings/privacy.py`, `settings/store.py`, `main.py`, `agent/agent.py`, `plugins/doc_ingest.py`, `ui/desktop/*`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_privacy_gdpr.py`, FUNCTIONAL_SPEC, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_privacy_gdpr.py tests/test_security_isolation.py -v` (9 passed). Live `/health` telemetry false; `/api/privacy/delete` confirm gate; desk17 Privacy markup served.
- **Jira:** story Agent completion + KAN-70 test evidence/Done + KAN-69 Done (via closeout script).
- **Next:** KAN-71 prompt-injection mitigations (FR-SEC-4; test KAN-72).

### 2026-11-15 — KAN-67 — Richer report metrics — stories covered and bugs raised
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** FR-REP-1 richer export metrics in `reports/sections.py`: summary progress (tests passed/failed, pass rate, stories covered, bugs raised); stories section with covered keys + per-story bugs_raised; bugs section with keys, counts/items by story and functional area. Markdown mirrors metrics. Section toggles still omit disabled blocks (FR-REP-2).
- **Files:** `reports/sections.py`, `tests/test_report_sections.py`, FUNCTIONAL_SPEC §5, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_report_sections.py tests/test_report_export.py tests/test_reports_tab.py -v` (11 passed).
- **Jira:** story Agent completion + KAN-68 test evidence/Done + KAN-67 Done (via closeout script).
- **Next:** KAN-69 GDPR easy local data deletion and consent surfaces (FR-SEC-2).

### 2026-11-15 — KAN-65 — Create linked test tickets and mark Done when covered
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** `create_test` proposes Task + `label=test` + Relates to story with structured Test procedure / Acceptance / Evidence (confirm gate). `update_status` requires coverage evidence (text / pytest_cmd / report_path), refuses non-test labels, comments coverage then transitions to Done on yes/confirm. Agent tools + system prompt; `jira_action` points at real tools. `_post_issue` supports labels.
- **Files:** `plugins/jira_plugin.py`, `agent/agent.py`, `tests/test_create_test.py`, FUNCTIONAL_SPEC §5, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_create_test.py tests/test_create_bug.py tests/test_create_issue.py tests/test_transition_issue.py tests/test_add_comment.py -v` (37 passed).
- **Jira:** story Agent completion + KAN-66 test evidence/Done + KAN-65 Done (via closeout script).
- **Next:** KAN-67 richer report metrics — stories covered and bugs raised (FR-REP-1).

### 2026-11-15 — KAN-63 — Raise user-friendly Bug tickets from failed runs
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** `create_bug` proposes Jira Bugs with Symptom / Expected / Actual / Environment / Replication steps / Evidence (from fields or local `reports/*.json`); only `product_bug`; masks token-like strings; optional Relates link after create; POST only on yes/confirm. Agent tool + system prompt. `jira_action create_bug` points at the real tool.
- **Files:** `plugins/jira_plugin.py`, `agent/agent.py`, `tests/test_create_bug.py`, FUNCTIONAL_SPEC §5, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_create_bug.py tests/test_create_issue.py tests/test_jira_readonly.py tests/test_add_comment.py -v` (23 passed).
- **Jira:** story Agent completion + KAN-64 test evidence/Done + KAN-63 Done (via closeout script).
- **Next:** KAN-65 create linked test tickets + mark Done when covered (FR-JIRA-2/3).

### 2026-11-15 — KAN-61 — Tool-calling reliability + JSON-in-text fallback
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** Hardened Ollama chat loop for FR-AGENT-6: `parse_tool_calls_from_text` recovers JSON-in-text / fenced / prose-embedded tool calls (`name`+`arguments|parameters`, `function`, `tool_calls`); chat sends `think: false` + `options.num_ctx` (env `OLLAMA_NUM_CTX`, default 8192); `grounded_tool_reply` blocks success claims when any tool result fails validation.
- **Files:** `agent/agent.py`, `tests/test_tool_calling.py`, FUNCTIONAL_SPEC §5, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_tool_calling.py -v` (8 passed); sessions + mocked LLM step regression also OK.
- **Jira:** story Agent completion + KAN-62 test evidence/Done + KAN-61 Done (via closeout script).
- **Next:** KAN-63 raise user-friendly Bug tickets from failed runs (FR-JIRA-4/5).

### 2026-11-15 — KAN-59 — Import and run existing Playwright suites
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** `plugins/playwright_suite.py` discovers/imports/lists/runs existing Playwright projects via `npx playwright test` (JSON reporter). Settings key `playwright_suite_path` (level-scoped). Agent tool `run_playwright_suite`; API `/api/playwright-suite*`; desktop App → Suites; Gradio Settings suite controls; registry entry.
- **Files:** `plugins/playwright_suite.py`, `plugins/registry.py`, `settings/store.py`, `agent/agent.py`, `main.py`, `ui/desktop/*`, `desktop_app.py` (desk16), `ui/gradio_app.py`, `tests/test_playwright_suite.py`, FUNCTIONAL_SPEC, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_playwright_suite.py -v` (7 passed); API discover OK + invalid path fails; desktop Suites nav present (desk16 cache-bust).
- **Jira:** story Agent completion + KAN-60 test evidence/Done + KAN-59 Done (via closeout script).
- **Next:** KAN-61 tool-calling reliability + JSON-in-text fallback (FR-AGENT-6).

### 2026-11-15 — KAN-57 — Stronger Playwright step gen + screenshot evidence
- **Agent/chat:** Cursor IDE Agent (Composer / Auto)
- **Done:** `plugins/playwright_steps.py` generates happy-path + negative/edge drafts with `expect_text`/`expect_url`; assesses/rejects visibility-only flows (FR-TEST-6). Runner adds `expect_visible`, `step_quality`, failure screenshots always under local app data, success screenshots gated by `playwright_success_evidence`. Agent tool `generate_playwright_steps` + stronger `run_playwright` prompt/schema.
- **Files:** `plugins/playwright_steps.py`, `plugins/playwright_runner.py`, `agent/agent.py`, `settings/store.py`, `tests/test_playwright_steps.py`, FUNCTIONAL_SPEC, PROJECT_MEMORY, ROADMAP, WORK_LOG.
- **Verify:** `$env:PLAYWRIGHT_BROWSERS_PATH='0'; .\venv\Scripts\python.exe -m pytest tests/test_playwright_steps.py -v` (8 passed); heal regression 14 passed.
- **Jira:** story Agent completion + KAN-58 test evidence/Done + KAN-57 Done (via closeout script).
- **Next:** KAN-59 import/run existing Playwright suites (FR-TEST-5).

### 2026-11-15 — OPS — FR coverage audit gap pass (Done ≠ complete FR)
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Audited every FR-* against code. Created 9 more Stories + tests for work still incomplete under Done parents (headless, Jira AC read, 429 backoff, desktop beyond smoke, LEARN-4, sandbox beyond stub, busy UX, Jira write audit, generate-from-Jira-AC). Commented gap pointers on Done KAN-8/9/11/12/15/45/47/49/55. Added FR→ticket matrix to FUNCTIONAL_SPEC §5.
- **Files:** `scripts/jira_kan_seed_backlog.py`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `scripts/jira_kan_slice_closeout.py`.
- **Verify:** Open Stories include KAN-83…KAN-99; Active still KAN-57.
- **Jira:** created KAN-83–100; Done parents commented (not reopened — remainder is ticketed).
- **Next:** KAN-57 PW-1.

### 2026-11-15 — OPS — Seed unfinished FR backlog + Bug process
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Seeded 13 open Stories + linked test Tasks from unfinished FUNCTIONAL_SPEC FRs (`scripts/jira_kan_seed_backlog.py`). Closed orphan open test Tasks for Done parents (KAN-30/31/33/34/35/38/40/42/44). Encoded mandatory Bug ticket workflow (replication steps + Fix comment) in AGENTS / HOW_WE_WORK / JIRA_TICKET_TEMPLATE / work-log-handoff / jira-safe.
- **Files:** `scripts/jira_kan_seed_backlog.py`, `AGENTS.md`, `docs/ops/HOW_WE_WORK.md`, `docs/ops/JIRA_TICKET_TEMPLATE.md`, `.cursor/rules/work-log-handoff.mdc`, `.cursor/skills/jira-safe/SKILL.md`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`.
- **Verify:** Jira open Stories KAN-57…KAN-81 with tests KAN-58…KAN-82; Active = KAN-57.
- **Jira:** created KAN-57–82; orphans closed; no product story Done this slice.
- **Next:** KAN-57 PW-1 step gen + screenshot evidence.

### 2026-11-15 — KAN-55 — Multi-sandbox orchestration stub
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** `plugins/multi_sandbox.py` stub (list/plan mock) + `plugins/registry.py` manifests; toggle `plugin_multi_sandbox_enabled` default off (FR-PLUG-2). Disabled → not-enabled message. Agent tools `list_plugins` / `orchestrate_sandboxes`. API `GET /api/plugins`, `GET/POST /api/multi-sandbox-plugin`, `POST /api/multi-sandbox/orchestrate`. Gradio Settings + App drawer → Sandboxes.
- **Files:** `plugins/multi_sandbox.py`, `plugins/registry.py`, `settings/store.py`, `agent/agent.py`, `main.py`, `ui/gradio_app.py`, `ui/desktop/*`, `desktop_app.py` (desk15), `tests/test_multi_sandbox.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_multi_sandbox.py -v` (4 passed). Desktop: App ▦ → Sandboxes → Orchestrate while off → enable message; enable + Save → list/plan OK; Plugins line shows multi_sandbox.
- **Jira:** story Agent completion comment + KAN-56 test evidence/Done + KAN-55 Done (yes).
- **Next:** optional desktop Settings polish / PW-1.

### 2026-11-15 — OPS — Jira agent-completion comments + test Task evidence
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Backfilled “Agent completion” comments on recent Done stories (KAN-10/14/15/45/47/49/51/53) and closed linked test Tasks (KAN-32/36/37/46/48/50/52/54) with unit/manual evidence. Added `scripts/jira_kan_slice_closeout.py`. Hardened AGENTS, work-log-handoff, jira-safe, slice-workflow, update-memory, HOW_WE_WORK, JIRA_TICKET_TEMPLATE, tooling-use.
- **Files:** `scripts/jira_kan_slice_closeout.py`, `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`, `.cursor/rules/tooling-use.mdc`, `.cursor/skills/*`, `docs/ops/*`, WORK_LOG.
- **Verify:** Open e.g. KAN-47 Activity for “Agent completion …” comment; KAN-48 Done with pytest evidence comment.
- **Jira:** backfill via closeout script (yes).
- **Next:** KAN-55 (Active slice unchanged).

### 2026-11-15 — KAN-47 — Desktop `.exe` testing plugin
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Separate `plugins/desktop_runner.py` stdlib smoke harness (no Playwright fork). Toggle `plugin_desktop_enabled` (FR-PLUG-2); disabled → graceful enable message. Agent tool `run_desktop`; API `GET/POST /api/desktop-plugin` + `POST /api/desktop-smoke`. Gradio Settings desktop controls; App drawer → Desktop panel. Uses `target_app_path` or path override.
- **Files:** `plugins/desktop_runner.py`, `settings/store.py`, `agent/agent.py`, `main.py`, `ui/gradio_app.py`, `ui/desktop/*`, `desktop_app.py` (desk14), `tests/test_desktop_runner.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_desktop_runner.py -v` (5 passed). Desktop: App ▦ → Desktop → toggle off → Run smoke → enable message; enable + path (e.g. notepad.exe) → pass.
- **Jira:** comment + Done on KAN-47 (REST).
- **Next:** KAN-55 multi-sandbox orchestration plugin (MULTI-1).

### 2026-11-15 — KAN-15 — OFFICIAL / SECRET isolation
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Level-scoped credentials under `%LOCALAPPDATA%\ai_testing_app\levels\{LEVEL}\credentials.json`; shared UI prefs stay in `settings.json`. Flat legacy keys migrate into OFFICIAL on load. `set_security_level` requires confirm (FR-SEC-3). Playwright uses `launch_persistent_context` per `browser_profiles\{LEVEL}`. API `GET/POST /api/security-level`; Gradio two-step Confirm level switch; desktop App → Security. Secrets never echoed in status/API.
- **Files:** `settings/store.py`, `plugins/playwright_runner.py`, `main.py`, `ui/gradio_app.py`, `ui/desktop/*`, `desktop_app.py` (desk13), `tests/test_security_isolation.py`, `tests/test_settings_tab.py`, `tests/test_doc_ingest.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_security_isolation.py tests/test_settings_tab.py tests/test_settings_bom.py tests/test_doc_ingest.py -v` (16 passed). API on `:8765`: propose SECRET → `confirmation_required`; confirm → `SECRET` profile path; restore OFFICIAL. Desktop: App ▦ → Security → Switch → Confirm.
- **Jira:** comment + Done on KAN-15 (REST).
- **Next:** KAN-47 desktop `.exe` testing plugin (DESK-1).

### 2026-11-15 — KAN-45 — Document ingestion → settings proposals
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** `plugins/doc_ingest.py` parses Markdown/text/baseline PDF; extracts URLs, Jira project/email/token placeholders, exe paths, messaging endpoints + test ideas; presents settings diff; writes only after confirm (decline = no change). Agent tool `ingest_document` + chat yes/decline; `settings.store.apply_settings_diff`; API `POST /api/doc-ingest` `/apply` `/decline`; desktop App → Documents; Gradio Documents tab. Secrets masked in proposals.
- **Files:** `plugins/doc_ingest.py`, `settings/store.py`, `agent/agent.py`, `main.py`, `ui/desktop/*`, `desktop_app.py` (desk12), `ui/gradio_app.py`, `tests/test_doc_ingest.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5/§6.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_doc_ingest.py -v` (8 passed). API smoke on `:8765`. Desktop: `desktop_app.py` → App ▦ → Documents → Parse → Confirm/Decline.
- **Jira:** comment + Done on KAN-45 (REST).
- **Next:** KAN-15 OFFICIAL/SECRET isolation (SEC-1).

### 2026-11-15 — KAN-51 — Customisable reporting sections
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** FR-REP-2 section profile (`summary` / `stories` / `bugs` / `evidence`) in local settings; `reports/sections.py` builds only enabled blocks; exporter Markdown/JSON omit disabled sections; defaults all on. Gradio Reports toggles + Save; desktop App drawer → Reports + `GET/POST /api/report-sections`.
- **Files:** `reports/sections.py`, `reports/exporter.py`, `settings/store.py`, `main.py`, `ui/gradio_app.py`, `ui/desktop/*`, `desktop_app.py` (desk11), `tests/test_report_sections.py`, `tests/test_report_export.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_report_sections.py tests/test_report_export.py tests/test_reports_tab.py -v` (9 passed). API round-trip on `:8765/api/report-sections`. Desktop: `desktop_app.py` → App ▦ → Reports → Save sections.
- **Jira:** comment + Done on KAN-51 (REST).
- **Next:** KAN-45 document ingestion → settings proposals (DOC-1).

### 2026-11-15 — KAN-49 — Enforce self-healing guardrails
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Central `plugins/heal_policy.py` (FR-HEAL-1…5): mandatory classification; refuse assertion weaken (toHaveText→toBeVisible), value change, skip/fixme, timeout inflation, AUT patch; product bugs stay red; locator-only allowed pending review + audit log. Playwright runner hooks into policy. Agent guides CR: product UI = `desktop_app.py` + Computer Use (not browser shell).
- **Files:** `plugins/heal_policy.py`, `plugins/playwright_runner.py`, `tests/test_heal_policy.py`, `tests/test_locator_heal.py`, AGENTS + `.cursor/rules|skills|agents` + CONNECTORS/HOW_WE_WORK, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5/§6.
- **Verify:** `.\venv\Scripts\python.exe -m pytest tests/test_heal_policy.py tests/test_locator_heal.py tests/test_click_heal.py -v` (14 passed). UI slices: `desktop_app.py` + Computer Use (not browser).
- **Jira:** comment + Done on KAN-49 (REST).
- **Next:** KAN-51 customisable reporting sections.

### 2026-11-15 — KAN-14 — Self-healing selector improvements
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Extended locator self-heal beyond click to `fill` (value never changed). Assertion steps (`expect_text` / `expect_url`) stay red with `heal_refused` + `product_bug` classification. Heal proposals + `%LOCALAPPDATA%\ai_testing_app\heal_audit.jsonl` audit lines (`pending_review`). Word-subset scoring so `#email` can match “Email address”.
- **Files:** `plugins/playwright_runner.py`, `tests/test_locator_heal.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5.
- **Verify:** `$env:PLAYWRIGHT_BROWSERS_PATH='0'; .\venv\Scripts\python.exe -m pytest tests/test_click_heal.py tests/test_locator_heal.py -v`
- **Jira:** comment + Done on KAN-14 (REST).
- **Next:** KAN-49 enforce full FR-HEAL guardrails.

### 2026-11-15 — OPS — commit + push required on slice close-out
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Agent guide CR — finished/paused slices must `git commit` + `git push origin main` before the human opens a new pick-up chat. Updated AGENTS, work-log-handoff, 00-core-efficiency, slice-workflow, update-memory, HOW_WE_WORK.
- **Files:** `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`, `.cursor/rules/00-core-efficiency.mdc`, `.cursor/skills/slice-workflow/SKILL.md`, `.cursor/skills/update-memory/SKILL.md`, `docs/ops/HOW_WE_WORK.md`, WORK_LOG.
- **Verify:** rules say push on slice close-out; this session lands KAN-53+KAN-10 on `origin/main`.
- **Jira:** n/a (process).
- **Next:** KAN-14 after push.

### 2026-11-15 — KAN-10 — Gradio Settings/Reports polish
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Settings tab: human labels, FR-UI-1 hint, local-store path + credential configured/not-set (never echoes secrets), Save → status. Reports tab: newest-first picker, details path, markdown/screenshot/JSON, Refresh. Theme CSS aligned with orb panels. Tests updated/added.
- **Files:** `ui/gradio_app.py`, `tests/test_settings_tab.py`, `tests/test_reports_tab.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5.
- **Verify:** `python run_ui.py` → http://127.0.0.1:7860 → Settings Save; Reports picker + Refresh. `python -m unittest tests.test_settings_tab tests.test_reports_tab`.
- **Jira:** yes — comment + Done on KAN-10 (REST).
- **Next:** KAN-14 self-healing selector improvements (desktop Settings/Reports drawer still “Coming soon” if you want that first).

### 2026-11-15 — KAN-53 — UI-6 resizable panels
- **Agent/chat:** Cursor IDE Agent (Composer)
- **Done:** Desktop shell resize handles (E/S/SE) on movable widgets; drawer edge resize; persist width/height in `desktop-shell-layout-v1`. Gradio orb settings panel `resize: both` + `gradio-orb-panel-size-v1`. IronBee: live resize grew chat 440→500×340 and restored after reload.
- **Files:** `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `ui/desktop/index.html`, `ui/gradio_app.py`, WORK_LOG, PROJECT_MEMORY, ROADMAP, FUNCTIONAL_SPEC §5.
- **Verify:** `http://127.0.0.1:8000/ui/desktop/index.html` — drag SE handle on chat, reload; open Gradio gear panel and drag native resize corner.
- **Jira:** yes — comment + Done on KAN-53 (REST).
- **Next:** KAN-10 Gradio Settings/Reports polish (remaining UX).

### 2026-11-15 — OPS — proactive Supermemory + tooling-use rule
- **Agent/chat:** Cursor PM chat
- **Done:** Added `.cursor/rules/tooling-use.mdc` (always apply): supermemory_search at pick-up, supermemory_add after slices/CRs; Jira REST fallback; GitHub plugin; IronBee UI. Wired into AGENTS, work-log-handoff, update-memory. MCP add from this chat may still connection-error — IDE Agent should add memories on next pick-up.
- **Files:** `.cursor/rules/tooling-use.mdc`, `AGENTS.md`, work-log-handoff, update-memory skill, WORK_LOG.
- **Verify:** rule alwaysApply; Active slice KAN-53.
- **Jira:** n/a.
- **Next:** Fresh IDE Agent: “pick up where we left off” (will search Supermemory + implement KAN-53).

### 2026-11-15 — OPS — clean tree + agent instructions for verified IDE tooling
- **Agent/chat:** Cursor PM chat
- **Done:** Removed IDE_CAPABILITIES walkthrough from repo; updated AGENTS/HOW_WE_WORK/CONNECTORS/work-log-handoff for verified tooling (GitHub plugin, Jira REST fallback, IronBee, Supermemory, Context7 optional); handoff remains KAN-53.
- **Files:** `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`, `docs/ops/*`, deleted `docs/ops/IDE_CAPABILITIES.md`.
- **Verify:** `git status` clean after commit; Active slice still KAN-53.
- **Jira:** n/a.
- **Next:** KAN-53 UI-6 resizable panels — user starts fresh IDE Agent chat with “pick up where we left off”.

### 2026-11-15 — OPS — remove IDE_CAPABILITIES walkthrough from repo
- **Agent/chat:** Cursor PM chat
- **Done:** Deleted `docs/ops/IDE_CAPABILITIES.md` and references; login/config walkthrough stays in chat only. Short tooling preference list kept in `AGENTS.md`.
- **Files:** deleted IDE_CAPABILITIES; CONNECTORS/INSTALL/ROADMAP/PROJECT_MEMORY/WORK_LOG cleaned.
- **Verify:** no IDE_CAPABILITIES path in repo.
- **Jira:** n/a.
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — document Jira MCP → REST fallback
- **Agent/chat:** Cursor PM chat
- **Done:** Instructed agents: when Atlassian MCP is blocked, use local-settings REST / `scripts/jira_kan_*.py` instead of giving up (`jira-safe`, CONNECTORS, AGENTS, work-log-handoff).
- **Files:** `.cursor/skills/jira-safe/SKILL.md`, `docs/ops/CONNECTORS.md`, `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`.
- **Verify:** skill section “MCP failure → REST fallback”.
- **Jira:** n/a (process).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — Jira progress comments + epic status sync
- **Agent/chat:** Cursor PM chat
- **Done:** Commented Done stories with completion notes; commented epics KAN-20…29 with Done/open child lists; transitioned epics (Done or In Progress from children); noted KAN-53 as Active slice. Helper: `scripts/jira_kan_progress_sync.py`.
- **Files:** `scripts/jira_kan_progress_sync.py`, WORK_LOG.
- **Verify:** Browse KAN-8 / KAN-20 / KAN-53 comments; epic statuses updated.
- **Jira:** yes — story + epic comments.
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — sync FUNCTIONAL_SPEC §5 done vs open
- **Agent/chat:** Cursor PM chat
- **Done:** Updated §5 Current State vs Target to 2026-11-15 (D: paths, KAN backlog done, open stories mapped to KAN keys; Active slice KAN-53).
- **Files:** `docs/FUNCTIONAL_SPEC.md`
- **Verify:** §5 no longer lists “richer Jira backlog” as open.
- **Jira:** statuses unchanged (MCP API token still blocked for live re-query this turn; statuses from last known enrich).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — CR sync rule for functional spec
- **Agent/chat:** Cursor PM chat
- **Done:** Documented that `docs/FUNCTIONAL_SPEC.md` is canonical in-repo; Jira inlines FRs. Agent instructions now require user CRs to update spec + related KAN tickets + memory/roadmap/work log.
- **Files:** `AGENTS.md`, `.cursor/rules/work-log-handoff.mdc`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/JIRA_TICKET_TEMPLATE.md`, `PROJECT_MEMORY.md`, `update-memory` skill.
- **Verify:** Instructions searchable for “User change requests (CRs)”.
- **Jira:** n/a (process only).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — handoff + multi-audience Jira template
- **Agent/chat:** Cursor PM chat
- **Done:** Added `docs/ops/JIRA_TICKET_TEMPLATE.md`, `docs/ops/WORK_LOG.md`, `.cursor/rules/work-log-handoff.mdc`; updated AGENTS/PROJECT_MEMORY/ROADMAP/HOW_WE_WORK/NEXT_PROMPT/next_prompt.py/slice-workflow; re-ran `jira_kan_enrich.py` with Who-this-is-for, User story, DoD, Dependencies, Traceability.
- **Files:** ops docs, agent rules/skills, `scripts/jira_kan_enrich.py`, `scripts/next_prompt.py`.
- **Verify:** `python scripts/next_prompt.py` prints KAN-53 Active slice; enrich exit 0.
- **Jira:** all active KAN descriptions refreshed (sample KAN-53).
- **Next:** KAN-53 UI-6 resizable panels.

### 2026-11-15 — OPS — project move, Ollama move, KAN backlog + ticket enrichment
- **Agent/chat:** Cursor PM chat (this session)
- **Done:** Moved repo to `D:\Projects\ai_testing_app` (Python 3.13 venv); moved Ollama to `D:\Program Files\Ollama` with `OLLAMA_MODELS`; removed old C: copies; added `docs/FUNCTIONAL_SPEC.md`; rebuilt KAN epics KAN-20…29; enriched/reformatted ticket descriptions; models restored + `qwen3:8b`; Model location set to D: in Ollama Settings.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `scripts/jira_kan_rebuild.py`, `scripts/jira_kan_enrich.py`, path docs.
- **Verify:** `/health` OK; `ollama list` shows 5 models; KAN backlog browsable.
- **Jira:** backlog rebuilt/enriched (no per-story ship comments for this ops day).
- **Next:** KAN-53 UI-6 resizable panels.
