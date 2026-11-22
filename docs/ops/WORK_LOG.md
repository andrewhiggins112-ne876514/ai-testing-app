# Work log — AI Testing Application

**Path:** `D:\Projects\ai_testing_app\docs\ops\WORK_LOG.md`  
**Rule:** Every coding/agent slice **must** append an entry here when the slice finishes (or is paused). Also add a **Jira comment** on the active story with the same summary.

## Active slice (agents: read this first)

| Field | Value |
|-------|--------|
| **Status** | open |
| **Jira story** | **KAN-327** Suites FR-UI-11 inherit |
| **Start task** | — |
| **Epic** | — (TRACK4-LAYOUT inherit) |
| **Roadmap ID** | TRACK4-LAYOUT |
| **Spec** | FR-UI-11 Suites inherit (Plans Cases **KAN-329** next) |
| **Git** | `main` |
| **Test ticket** | **KAN-328** |
| **Shipped** | Settings **KAN-324**; inherit mockups accepted; Lane C tooling restored |
| **Deferred** | **TRACK3-LAB** Lab density; **KAN-81** / **KAN-82** voice; **FR-MAN-2** |
| **Next / Shipped** | Build pick-up implements **KAN-327**. Then **KAN-329** Plans Cases. Do **not** implement Lab / voice / FR-MAN-2. |

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

### 2026-11-22 — Studio — Suites/Plans inherit accepted + Lane C restore
- **Agent/chat:** Cursor IDE Agent (Studio path after deferred pick-up)
- **Done:** Designer **accept** Suites+Plans FR-UI-11 inherit. Mockups under `docs/mockups/suites_plans_layout_inherit/`. Restored missing Lane C tooling from `eec4e25` (`DESIGN_STUDIO.md`, `design-studio` skill, `studio*` agents) + TEAM / AGENTS / ADVISORY_COUNCIL Lane C links. Bridge: Suites Story **KAN-327** / test **KAN-328**; Plans Cases **KAN-329** / test **KAN-330**. Active → **KAN-327**. No product UI code.
- **Files:** mockups pack; Design Intent; `scripts/jira_kan_fr_ui11_inherit_bridge.py`; Studio ops/agents/skill; WORK_LOG / ROADMAP / SPEC / PROJECT_MEMORY
- **Verify:** Open themed Suites/Plans mockups; `/studio` after reload; fresh Build → pick up **KAN-327**
- **Jira:** Bridge comments on **KAN-327** / **KAN-329**
- **Next:** Build implements **KAN-327** Suites inherit

### 2026-11-21 — Bug KAN-326 — Settings rail intermittent (desk108)
- **Agent/chat:** Cursor IDE Agent — Designer reported rail buttons intermittent
- **Done:** Sections only show when selected. Root cause: CSS `display` overrode `[hidden]` on panels + rail lived in scrolling `.area-work` / report `scrollIntoView` moved hit targets. Fix: `[hidden]{display:none!important}`, grammar work `overflow:hidden` (only main scrolls), rail click delegation, no report scrollIntoView. Bug **KAN-326** Relates **KAN-324**/325 → Done.
- **Files:** `ui/desktop/desktop.css`, `desktop.js`, `index.html`, `desktop_app.py`, `tests/test_settings_layout_grammar.py` (+ hub/density)
- **Verify:** pytest Settings grammar/hub/density/occlusion; click each rail button — only that section appears
- **Jira:** **KAN-326** Fix comment + Done
- **Next:** Active still **deferred** (Suites/Plans inherit)

### 2026-11-21 — KAN-324 — Settings FR-UI-11 layout grammar (desk107)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-324
- **Done:** Rehoused desktop Settings to in-area section rail (Layout, Connections, Environments, Model & runner, Report blocks, Credentials) + compact scan tables + detail panes. Env delete / credential clear in detail behind confirm. Report blocks use dedicated 28px checkbox cells with click stopPropagation; row focuses detail. Markers `data-settings-layout-grammar` / rail / scan / checkbox-cell / detail. Cache-bust **desk107**. Gradio App/Report left as-is (out of scope). Theme/orb/home/App nav untouched. CU not required (marker/pytest AC).
- **Files:** `ui/desktop/index.html`, `desktop.css`, `desktop.js`, `desktop_app.py`, `tests/test_settings_layout_grammar.py`, hub/density/reports/occlusion tests, Studio mockups + Spec/ROADMAP/WORK_LOG
- **Verify:** `pytest tests/test_settings_layout_grammar.py tests/test_settings_hub.py tests/test_settings_security_density.py tests/test_occlusion_verify_ae.py tests/test_app_settings.py tests/test_reports_library.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py` — 30 passed. Spot-check: `desktop_app.py` → App → Settings → rail + Environments/Report blocks.
- **Jira:** close-out **KAN-324** + **KAN-325**
- **Next:** Active **deferred** — Suites/Plans FR-UI-11 inherit (create/set Active); not Lab/voice/FR-MAN-2

### 2026-11-21 — Designer unblock — Active → KAN-324 Settings grammar
- **Agent/chat:** Design Studio (handoff to Build)
- **Done:** Set Active slice to **KAN-324** / test **KAN-325** (FR-UI-11 Settings template). TRACK3-LAB / voice / FR-MAN-2 remain deferred. No product code in Studio chat.
- **Files:** `docs/ops/WORK_LOG.md` Active table; `docs/ops/ROADMAP.md` TRACK4-LAYOUT → now
- **Verify:** Fresh Build Agent → “pick up where we left off”
- **Jira:** comment on KAN-324 that Active is open
- **Next:** Build implements KAN-324

### 2026-11-21 — Studio — Settings layout grammar accepted (FR-UI-11 Bridge)
- **Agent/chat:** Design Studio Audit → Redesign (locked chrome)
- **Done:** Audited Settings + Suites + Plans (file evidence; CU skipped — unsafe). Accepted Settings as system template: section rail + compact scan table + detail pane; selection grammar. Spec **FR-UI-11** + FR-SET-4 CR; Design Intent + ROADMAP **TRACK4-LAYOUT**; mockups under `docs/mockups/settings_layout_grammar/`. Jira Story + linked test created for Settings Build. No product UI code. Active Build still **deferred**.
- **Files:** `docs/mockups/DESIGN_INTENT.md`, `docs/mockups/settings_layout_grammar/**`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/ROADMAP.md`, `PROJECT_MEMORY.md`
- **Verify:** Open `01-themed-preferred.html` / `02-annotated-build-note.html`; read FR-UI-11
- **Jira:** Story **KAN-324** + test **KAN-325** Relates (REST bridge script `scripts/jira_kan_fr_ui11_bridge.py`)
- **Next:** Build pick-up implements **KAN-324** when Designer unblocks Active; Suites/Plans inheritance stories after Settings

### 2026-11-21 — Council — Lane C Design Studio ratified
- **Agent/chat:** Council Creative (+ Bridge readiness) → docs/agents draft
- **Done:** Ratified **Lane C Design Studio** (`/studio`) with binding gates (advisory-only; Spec→Jira→Build bridge; theme/orb/home/nav locked; selection grammar; density; tiered CU; synthetic secrets; hard pause if Active-slice slips). Drafted ops guide, Design Intent log, `studio*` agents, `design-studio` skill; updated TEAM / ADVISORY_COUNCIL / AGENTS. No product code. Active Build slice unchanged (**deferred**).
- **Files:** `docs/ops/DESIGN_STUDIO.md`, `docs/mockups/DESIGN_INTENT.md`, `.cursor/agents/studio*.md`, `.cursor/skills/design-studio/SKILL.md`, `docs/ops/TEAM.md`, `docs/ops/ADVISORY_COUNCIL.md`, `AGENTS.md`
- **Verify:** Slash `/studio` after reload if needed; open `docs/ops/DESIGN_STUDIO.md`
- **Jira:** none (tooling lane; no story yet — first Studio Audit can Bridge later)
- **Next:** Designer opens `/studio` Audit on secondary areas (row-soup); Build stays deferred until unblock

### 2026-11-21 — KAN-320 human confirm + Bug KAN-323 checklist dismiss
- **Agent/chat:** Cursor IDE Agent — Designer `confirmed` A–E + reported checklist toggle bug
- **Done:** Closed **KAN-320**/321 on human A–E occlusion confirm. Raised Bug **KAN-323** (First-hour checklist ignored Screen toggle while incomplete); fixed desk106 — toggle authoritative + dismiss localStorage + auto-show only when not dismissed; marker `data-checklist-toggle-dismiss`. Track 3 Primary complete; Active → **TRACK3-LAB deferred**.
- **Files:** `ui/desktop/desktop.js`, `ui/desktop/index.html`, `desktop_app.py`, `tests/test_home_checklist.py` (+ desk106), docs
- **Verify:** Human A–E confirm; `pytest tests/test_home_checklist.py tests/test_occlusion_verify_ae.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py` 16 passed. CU not required for dismiss fix (marker/JS).
- **Jira:** **KAN-320**/321 Done; **KAN-323** Fix comment + Done
- **Next:** Active **deferred** — Lab density / voice / FR-MAN-2. Do not implement until unblocked.

### 2026-11-21 — KAN-320 — Occlusion verify Primary A–E (paused for human)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-320
- **Done:** Encoded TRACK3 A–E occlusion contract as pytest + marker `data-occlusion-verify-ae`; cache-bust **desk105**. Structural Primary×A–E chrome/Confirm/Esc/Back/compact-menu checks green. **CU skipped — unsafe** (WebGL purple orb + First-hour checklist + Cursor CU HUD; Open Plans clicks missed — not soft-passed). Seeded Manual `ms4592cff074a7` (charter KAN-314 density verify) with pending create_bug proposal; `desktop_app.py` left on desk105.
- **Files:** `ui/desktop/index.html`, `desktop_app.py`, `tests/test_occlusion_verify_ae.py` (+ desk105 across UI tests), `docs/design/TRACK3_AREA_WIRES.md`, docs/ops
- **Verify:** `pytest tests/test_occlusion_verify_ae.py` + density/scaffold/nonoverlap suite — 37 passed. Occlusion clickability **awaiting human confirm** (A–E script in chat + KAN-321).
- **Human confirm (occlusion AC):** 1) Focus **AI Testing Agent** (desk105). Prefer classic canvas orb (Screen → orb style) + dismiss First-hour checklist if open. 2) Settings → App area layout = **Overlay**. 3) For each Primary area (Plans, Manual, Reports, Documents, Settings, Security): ▦ App → area; surface title+Back visible; one toolbar clickable; first work row visible; scroll `.area-work` without chrome sliding over inputs; Esc/Back → home. 4) Manual: Session library → Open review on KAN-314 density verify → Confirm dock shows Confirm + Cancel proposal clickable. 5) Repeat steps 3–4 for layout modes **Stage, Orb hub, Split, Floating** (change layout in Settings; hub → spoke → area for Orb hub). 6) Compact ▦ only — no tall rail. Reply **confirm** → agent marks **KAN-320**/321 Done.
- **Jira:** progress comments on **KAN-320** + **KAN-321** (not Done until human confirm)
- **Next:** Human A–E confirm → then Track3 Primary close-out / Lab follow-on

### 2026-11-21 — KAN-318 — Settings + Security density
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-318
- **Done:** Settings + Security Primary density from accepted Track 3 wire: removed intro labels above chrome; Settings category switch (App|Report) + status as single toolbar; Security Level/Switch/Confirm/profile/status always-visible chrome; form bodies (credential status, privacy, audit, backup) scroll in `.area-work`; About collapsed under work; marker `data-settings-security-density`; cache-bust **desk104**. No Lab density; no voice / FR-MAN-2; no occlusion A–E pass (KAN-320).
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_settings_security_density.py` (+ desk104 across UI tests), docs
- **Verify:** `pytest tests/test_settings_security_density.py tests/test_settings_hub.py tests/test_track3_chrome_scaffold.py tests/test_reports_documents_density.py tests/test_manual_density.py tests/test_plans_cases_geometry.py tests/test_area_chrome_nonoverlap.py tests/test_enterprise_layout_tokens.py tests/test_track3_area_wires.py tests/test_security_isolation.py tests/test_export_redaction.py tests/test_credential_status.py tests/test_lab_backup.py tests/test_local_side_effects_audit.py tests/test_nav_overlap.py tests/test_plans_ia.py tests/test_reports_ia.py tests/test_lab_areas_ia.py` 56 passed. Marker/CSS chrome budget primary — CU not required (density structure; occlusion gate is **KAN-320**).
- **Jira:** close-out **KAN-318** + **KAN-319**
- **Next:** Active **KAN-320** Occlusion verify Primary across A–E (test **KAN-321**)

### 2026-11-19 — KAN-316 — Reports + Documents density
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-316
- **Done:** Reports + Documents Primary density from accepted Track 3 wire: removed intro labels above toolbars; single toolbar band (actions + status) with `--chrome-toolbar` max-height; About Reports collapsed in `.area-work`; Advanced (export / help) under work; Documents Spec/Proposal/Uploads primary without Ingest chrome; marker `data-reports-documents-density`; cache-bust **desk103**. No Lab density; no voice / FR-MAN-2; no Settings/Security pass.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_reports_documents_density.py` (+ desk103 across UI tests), docs
- **Verify:** `pytest tests/test_reports_documents_density.py tests/test_reports_ia.py tests/test_reports_library.py tests/test_lab_areas_ia.py tests/test_track3_chrome_scaffold.py tests/test_area_chrome_nonoverlap.py tests/test_enterprise_layout_tokens.py tests/test_plans_cases_geometry.py tests/test_manual_density.py tests/test_track3_area_wires.py tests/test_nav_overlap.py tests/test_settings_hub.py` 29 passed. **CU skipped — unsafe** (busy desktop: browser + IDE + prior desk shell contested App-menu clicks). Marker/CSS chrome budget primary.
- **Jira:** close-out **KAN-316** + **KAN-317**
- **Next:** Active **KAN-318** Settings + Security area-work alignment (test **KAN-319**)

### 2026-11-19 — KAN-314 — Human Confirm-dock confirm → Done
- **Agent/chat:** Cursor IDE Agent — human reply `confirm` after Manual Confirm-dock verify
- **Done:** Designer confirmed Confirm + Cancel proposal clickable (occlusion AC). Closed **KAN-314** + **KAN-315**. No further product code in this entry.
- **Files:** docs/ops handoff only (code already on `main` desk102)
- **Verify:** Human confirm 2026-11-19; prior pytest 48 passed; CU skipped — unsafe (honest)
- **Jira:** **KAN-314**/315 → Done
- **Next:** Active **KAN-316** Reports + Documents density (test **KAN-317**)

### 2026-11-19 — KAN-314 — Manual density + Confirm dock (paused for human CU)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-314
- **Done:** Manual Primary density from accepted Track 3 wire: removed intro chrome above toolbar (About Manual collapsed in `.area-work`); single toolbar band with Clear/Open Plans/Refresh + loop + status; library/start/review scroll in `.area-work`; proposal surface without second Review header; Confirm dock sibling below work with `--chrome-confirm` max-height; marker `data-manual-density`; cache-bust **desk102**. No Lab density; no voice / FR-MAN-2.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_manual_density.py` (+ desk102 across UI tests), docs
- **Verify:** `pytest tests/test_manual_density.py tests/test_manual_propose_harden.py tests/test_manual_ia.py tests/test_manual_trustworthy_loop.py tests/test_manual_session_library.py tests/test_area_chrome_nonoverlap.py tests/test_track3_chrome_scaffold.py tests/test_plans_cases_geometry.py tests/test_enterprise_layout_tokens.py tests/test_track3_area_wires.py tests/test_manual_session.py tests/test_charter_snap.py` 48 passed. **CU skipped — unsafe** (WebGL purple orb + Cursor CU HUD + busy desktop contested App-menu clicks). Seeded session `ms4592cff074a7` (charter KAN-314 density verify) on OFFICIAL; app left on `desk102`.
- **Human confirm (occlusion AC):** 1) Focus **AI Testing Agent**. 2) ▦ App → Manual. 3) Session library → Open review on KAN-314 density verify. 4) Propose bug. 5) Confirm dock at bottom: Confirm + Cancel proposal fully visible/clickable without scrolling dock away. 6) Scroll `.area-work` — dock stays. 7) Layout picker A–E — dock still visible/clickable each mode. Reply confirm → agent marks **KAN-314**/315 Done → Active **KAN-316**.
- **Jira:** agent progress comment on **KAN-314** + evidence on **KAN-315** (not Done until human confirm)
- **Next:** Human Confirm-dock verify → then **KAN-316** Reports + Documents density

### 2026-11-18 — KAN-312 — Plans Cases geometry from accepted wire
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-312
- **Done:** Plans · Cases real geometry from accepted Track 3 wire: removed intro chrome above toolbar (About Plans collapsed in `.area-work`); short tab labels (Draft/Cases/Coverage/Trace/History/Run); toolbar+tabs max-heights from `--chrome-*`; Add case ▾ + archived toggle as work header **before** case list; marker `data-plans-cases-geometry`; cache-bust **desk101**. Cases remains default. No Manual Confirm pass; no Lab density; no voice / FR-MAN-2.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_plans_cases_geometry.py` (+ desk101 across UI tests), docs
- **Verify:** `pytest tests/test_plans_cases_geometry.py tests/test_plans_ia.py tests/test_track3_chrome_scaffold.py tests/test_area_chrome_nonoverlap.py tests/test_enterprise_layout_tokens.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_plan_search.py tests/test_plans_tab.py tests/test_keyboard_shortcuts.py tests/test_manual_ia.py tests/test_reports_ia.py tests/test_lab_areas_ia.py tests/test_suites_ia.py tests/test_track3_area_wires.py` 34 passed. CU: proved Plans overlay — surface bar, single toolbar, short tabs with Cases selected, About collapsed, Add case work header clickable; A–E via layout-picker markers (not each mode CU). CU flake after Open click returned home — not soft-passed as full A–E visual.
- **Jira:** close-out **KAN-312** + **KAN-313**
- **Next:** Active **KAN-314** Manual density + Confirm dock (test **KAN-315**)

### 2026-11-18 — KAN-310 — Shared chrome scaffold + retire sticky naming
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-310
- **Done:** Shared `.area-chrome-toolbar` scaffold on all eight area toolbars; retired `*-sticky-toolbar` / `data-*-sticky` names (→ `*-chrome-toolbar` / `data-*-chrome`); Plans single-row toolbar with search+status in-band; search results moved into `.area-work`; Manual status row compacted; marker `data-area-chrome-scaffold`; cache-bust **desk100**. No Plans Cases height pass (KAN-312); no Lab density; no voice / FR-MAN-2.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_track3_chrome_scaffold.py` (+ IA/nonoverlap/token desk100 updates), docs
- **Verify:** `pytest tests/test_track3_chrome_scaffold.py tests/test_area_chrome_nonoverlap.py tests/test_enterprise_layout_tokens.py tests/test_plans_ia.py tests/test_manual_ia.py tests/test_reports_ia.py tests/test_lab_areas_ia.py tests/test_suites_ia.py tests/test_nav_overlap.py` 13 passed. Marker/AC primary — CU not required (scaffold rename; per-area geometry next).
- **Jira:** close-out **KAN-310** + **KAN-311**
- **Next:** Active **KAN-312** Plans · Cases geometry (test **KAN-313**)

### 2026-11-18 — Designer accepted Track 3 wires
- **Agent/chat:** Build chat — Accept gate
- **Done:** Designer **`Accept Track 3 wires`**. Marked `TRACK3_AREA_WIRES.md` Accepted; checklist signed. Unblocked geometry **KAN-310…320**. No product feature code in this entry.
- **Files:** `docs/design/TRACK3_AREA_WIRES.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `docs/ops/TRACK3_ACTIVE_POINTER.txt`
- **Verify:** docs/decision only; wires marker tests still green
- **Jira:** Accept comments on **KAN-308**, **KAN-310**, epic **KAN-307**
- **Next:** Build chat **pick up where we left off** → **KAN-310** (test **KAN-311**)

### 2026-11-18 — KAN-308 — Track3 Slice-0 Primary wires pack
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-308
- **Done:** Filled `docs/design/TRACK3_AREA_WIRES.md` with ASCII wires for Plans · Cases, Manual idle + review/Confirm dock, Reports, Documents, Settings hub, Security chrome; chrome ≤~120px; A–E verify contract; Lab outline-only follow-on; Accept checklist. Docs/tests only — **no** product HTML/CSS geometry. Stopped for Designer **Accept Track 3 wires** before **KAN-310**.
- **Files:** `docs/design/TRACK3_AREA_WIRES.md`, `tests/test_track3_area_wires.py`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`, `docs/ops/TRACK3_ACTIVE_POINTER.txt`
- **Verify:** `pytest tests/test_track3_area_wires.py tests/test_enterprise_layout_note.py` — marker AC; CU not required (docs-only).
- **Jira:** close-out **KAN-308** + **KAN-309**
- **Next:** Active **blocked** — **KAN-310** until Designer Accept; then shared chrome scaffold

### 2026-11-18 — Council Track 3 Slice-0 — CR landed (docs + Jira)
- **Agent/chat:** Council Room (`/council`) — Designer confirm Track 3
- **Done:** Expectation gap recorded (KAN-297 tokens ≠ layout redo). Added **FR-UI-10**; wires pack stub; ROADMAP TRACK3-UX now / TRACK3-LAB later. Seeded epic **KAN-307**, stories **KAN-308…320** + tests **KAN-309…321**. Decisions: wire accept gate yes; Primary-only yes; verify all A–E yes. Active → **KAN-308**. No product feature code.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `docs/design/TRACK3_AREA_WIRES.md`, `docs/design/ENTERPRISE_LAYOUT_NOTE.md`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `scripts/jira_kan_track3_slice0.py`, `docs/ops/TRACK3_ACTIVE_POINTER.txt`
- **Verify:** `python scripts/jira_kan_track3_slice0.py` created keys
- **Jira:** epic **KAN-307**; Active **KAN-308**/test **309**; CR comments on KAN-295/297/279
- **Next:** Build chat **pick up where we left off** → **KAN-308** wires (then stop for Accept before **KAN-310**)

### 2026-11-18 — KAN-297 — Apply enterprise layout tokens
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-297
- **Done:** Applied accepted `ENTERPRISE_LAYOUT_NOTE` as `:root` `--type-*` / `--space-*` / `--chrome-*` tokens in `desktop.css`; wired area surface bar, toolbars, Plans tabs, lists, Manual confirm dock, and Lab chrome to those variables; kept FR-UI-3 `--cyan` accents + Segoe local font; marker `data-enterprise-layout-tokens`; cache-bust **desk99**. No nav rewrite, no voice / FR-MAN-2.
- **Files:** `ui/desktop/desktop.css`, `ui/desktop/index.html`, `desktop_app.py`, `tests/test_enterprise_layout_tokens.py` (+ desk99 across UI tests), docs
- **Verify:** `pytest tests/test_enterprise_layout_tokens.py tests/test_area_chrome_nonoverlap.py tests/test_enterprise_layout_note.py tests/test_manual_propose_harden.py tests/test_manual_ia.py tests/test_plans_ia.py tests/test_nav_overlap.py` 22 passed. Token/wiring + non-overlap markers primary — CU not required (geometry unchanged; tiered policy).
- **Jira:** close-out **KAN-297** + **KAN-298**
- **Next:** Active **deferred** — **KAN-81** voice; Track 2 complete; human/council picks next track

### 2026-11-18 — Council — Designer accepted KAN-295 layout note
- **Agent/chat:** Council Room (`/council`) — Accept gate for Track2 UX
- **Done:** Designer **Accept** of `docs/design/ENTERPRISE_LAYOUT_NOTE.md`. Unblocked **KAN-297** tokens. Clarified: this was a human-accept gate, not an unfinished review story (KAN-295/296 already Done).
- **Files:** `docs/design/ENTERPRISE_LAYOUT_NOTE.md`, `docs/ops/WORK_LOG.md`, `docs/ops/ROADMAP.md`, `PROJECT_MEMORY.md`
- **Verify:** docs/decision only
- **Jira:** comments on **KAN-295** + **KAN-297**
- **Next:** Build chat **“pick up where we left off”** → **KAN-297** (test **KAN-298**)

### 2026-11-18 — KAN-295 — Enterprise layout research note (docs)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-295
- **Done:** Shipped local research note for calm Windows-enterprise density: type scale, 4px spacing scale, ~120px chrome budget, occlusion checklist, one Plans Cases wire; hard forbids tall rail / top tab bar / purple SaaS / cloud font CDNs. Tokens coding explicitly deferred to **KAN-297** after human accept.
- **Files:** `docs/design/ENTERPRISE_LAYOUT_NOTE.md`, `tests/test_enterprise_layout_note.py`, `docs/design/H1_MANUAL_SESSION_CAPTURE.md`, `docs/FUNCTIONAL_SPEC.md`, `docs/ops/ROADMAP.md`, `PROJECT_MEMORY.md`, `docs/ops/WORK_LOG.md`
- **Verify:** `pytest tests/test_enterprise_layout_note.py` (marker AC). Docs-only — CU not required.
- **Jira:** close-out **KAN-295** + **KAN-296**
- **Next:** **KAN-297** layout tokens — **blocked** until human accepts the note; do not implement tokens without accept

### 2026-11-18 — KAN-293 — Manual propose/confirm harden
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-293
- **Done:** Failure-class select + explicit File-as-Bug; Create Bug blocked for non-`product_bug` unless explicit (FR-HEAL-4 redirect kinds); Propose Bug builds FR-JIRA-4 defect-packet shape; Confirm dock moved outside `.area-work` (`flex-shrink: 0`); Confirm on bug/comment runs `create_bug`/`add_comment` + `resolve_create` (Manual Confirm = human gate) and marks submitted + audited on success; Cancel writes nothing. Cache-bust **desk99**.
- **Files:** `plans/manual_session.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_manual_propose_harden.py` (+ desk99 across UI tests), docs
- **Verify:** `pytest tests/test_manual_propose_harden.py tests/test_manual_session.py tests/test_manual_trustworthy_loop.py tests/test_manual_assist_drafts.py tests/test_manual_page_context.py tests/test_charter_snap.py tests/test_manual_ia.py tests/test_manual_session_library.py tests/test_area_chrome_nonoverlap.py` 49 passed. Packet/failure-class/API primary; Confirm dock proven by HTML/CSS markers outside scrollport — CU not required (tiered policy).
- **Jira:** close-out **KAN-293** + **KAN-294**
- **Next:** **KAN-295** Enterprise layout research note (docs; test **KAN-296**)

### 2026-11-18 — KAN-291 — Manual session library + GDPR session wipe
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-291
- **Done:** Level-scoped Manual session library UI (list + Open review / reopen); `POST …/reopen` never writes Jira. Privacy `sessions` wipe now removes Manual drafts+stills for the **active** level only (SECRET untouched); inventory includes `manual_sessions`. Level-switch confirm clears Manual UI so previous level’s open session is not visible. Cache-bust **desk97**.
- **Files:** `plans/manual_session.py`, `settings/privacy.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_manual_session_library.py` (+ desk97 across UI tests), docs
- **Verify:** `pytest tests/test_manual_session_library.py tests/test_manual_session.py tests/test_manual_trustworthy_loop.py tests/test_manual_assist_drafts.py tests/test_manual_page_context.py tests/test_charter_snap.py tests/test_manual_ia.py tests/test_privacy_gdpr.py tests/test_local_side_effects_audit.py` 48 passed. Non-visual AC — CU not required (tiered policy).
- **Jira:** close-out **KAN-291** + **KAN-292**
- **Next:** **KAN-293** Manual propose/confirm harden (test **KAN-294**)

### 2026-11-18 — Context7 local: stdio + clear API-key placement
- **Agent/chat:** Follow-up — user still saw streamableHttp terminated; never pasted a key
- **Done:** Switched user MCP `context7` from HTTP to **stdio** (`cmd /c npx @upstash/context7-mcp@latest` + `CONTEXT7_API_KEY` env + Norton CA). Documented exact key places in CONNECTORS (env / local settings / user mcp.json). Script reuses existing key or accepts `$env:CONTEXT7_API_KEY`.
- **Files:** `scripts/setup_context7_mcp_auth.ps1`, `docs/ops/CONNECTORS.md`, `AGENTS.md`
- **Verify:** Human: fully quit/reopen Cursor; Tools & MCP enable `context7` (stdio). Ignore plugin OAuth terminated logs. Optional: paste own `ctx7sk-…` from dashboard into env and re-run script.
- **Jira:** note on **KAN-300** optional
- **Next:** **KAN-291**

### 2026-11-18 — Ops Epic KAN-300 — Context7 local + 2B review (Phases 0–3)
- **Agent/chat:** Agent implementing plan (Context7 local fix + phased 2B)
- **Done:** Phase0 — `setup_context7_mcp_auth.ps1` + Atlassian merge; `npx ctx7 login` + `setup --cursor --mcp` wrote user MCP `context7` (API key) alongside atlassian/supermemory; CLI `ctx7 library fastapi` verified. Phase1 — pinned `requirements.txt` to venv; Context7-audited call sites (no API-drift fixes needed); `tests/test_requirements_pins.py`. Phase2 — security/GDPR isolation audit; no Bugs. Phase3 — stub honesty intentional (Selenium/Cypress/Gradio charter); restore Active **KAN-291**.
- **Files:** `scripts/setup_context7_mcp_auth.ps1`, `scripts/setup_atlassian_mcp_auth.ps1`, `scripts/jira_kan_ops_context7_review.py`, `requirements.txt`, `tests/test_requirements_pins.py`, `AGENTS.md`, `docs/ops/CONNECTORS.md`, `PROJECT_MEMORY.md`, `docs/ops/ROADMAP.md`
- **Verify:** `pytest tests/test_requirements_pins.py tests/test_security_isolation.py tests/test_privacy_gdpr.py` 10 passed; `npx ctx7 library fastapi` OK. Fully quit/reopen Cursor so Tools & MCP shows user `context7` green (plugin OAuth Local Error ignorable).
- **Jira:** Epic **KAN-300**; stories **KAN-301**/test **302**, **KAN-303**/test **304**, **KAN-305**/test **306**
- **Next:** Build chat **KAN-291** Manual session library + GDPR wipe (test **KAN-292**)

### 2026-11-18 — Council CR — Agent stale-advice / Context7 gate
- **Agent/chat:** Council Room (`/council`) — agents using outdated coding advice
- **Done:** Claim validated (default behaviour unless forced to look up). Ops-only CR: ranked source order (repo → venv → Context7/official for installed version → memory last); narrow trigger for FastAPI/Pydantic/Playwright/Gradio/pywebview/Ollama HTTP/httpx; thrift does not skip gate; thin `context7-use` pointer skill; no product code; requirements pin deferred.
- **Files:** `AGENTS.md`, `.cursor/rules/tooling-use.mdc`, `.cursor/rules/00-core-efficiency.mdc`, `.cursor/skills/context7-use/SKILL.md`, `.cursor/skills/slice-workflow/SKILL.md`, `docs/ops/CONNECTORS.md`, `docs/ops/HOW_WE_WORK.md`, `PROJECT_MEMORY.md`
- **Verify:** docs/rules only
- **Jira:** none (optional ops Task later if human wants)
- **Next:** Build chat remains **KAN-291** (inherits gate once on `main`)

### 2026-11-18 — KAN-289 — Page context from headed AUT + annotate still
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-289
- **Done:** Known headed AUT URL/title via `plans/aut_page_context.py` (Playwright pause publishes; cleared when browser closes; no keylog). Manual Start/refresh attaches page context; dock Page + Annotate; stills store local annotation; Propose applies E3 redaction to notes/URL/title/annotations. Cache-bust **desk96**.
- **Files:** `plans/aut_page_context.py`, `plans/manual_session.py`, `plans/pause_session.py`, `plugins/playwright_runner.py`, `main.py`, `ui/desktop/*`, `desktop_app.py`, `tests/test_manual_page_context.py` (+ desk96 across UI tests), docs
- **Verify:** `pytest tests/test_manual_page_context.py tests/test_manual_session.py tests/test_manual_trustworthy_loop.py tests/test_manual_assist_drafts.py tests/test_charter_snap.py tests/test_manual_ia.py` 35 passed. Non-visual AC — CU not required (tiered policy).
- **Jira:** close-out **KAN-289** + **KAN-290**
- **Next:** **KAN-291** Manual session library + GDPR session wipe (test **KAN-292**)

### 2026-11-18 — KAN-287 — Charter Frame window/monitor snap
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-287
- **Done:** Free-region kept. Snap-to-monitor and snap-to-window via Win32 geometry (`plans/charter_snap.py`); session stores `frame_mode` + absolute `screen_bbox` for stills; drag/resize returns to free and clears bbox; dock Monitor/Window picker; assist/mist unchanged. Cache-bust **desk95**.
- **Files:** `plans/charter_snap.py`, `plans/manual_session.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_charter_snap.py` (+ desk95 across UI tests), docs
- **Verify:** `pytest tests/test_charter_snap.py tests/test_manual_session.py tests/test_manual_trustworthy_loop.py tests/test_manual_assist_drafts.py tests/test_manual_ia.py` 29 passed. Non-visual AC — CU not required (tiered policy).
- **Jira:** close-out **KAN-287** + **KAN-288**
- **Next:** **KAN-289** Page context from headed AUT + annotate still (test **KAN-290**)

### 2026-11-18 — KAN-285 — Real agent-assist local drafts (honest assist)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-285
- **Done:** Removed note-echo “AI” drafts. Assist ON builds real local unpublished step/bug drafts via Ollama at End → review (`plans/manual_assist.py`); Assist OFF produces none; Ollama down → `assist_status=unavailable` + clear message, empty drafts (no fakes). Review UI shows assist status + draft lines; Propose/Confirm still FR-JIRA-5 two-step. Cache-bust **desk94**.
- **Files:** `plans/manual_assist.py`, `plans/manual_session.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_manual_assist_drafts.py` (+ desk94 / assist markers), docs
- **Verify:** `pytest tests/test_manual_assist_drafts.py tests/test_manual_session.py tests/test_manual_trustworthy_loop.py tests/test_manual_ia.py` 22+ passed. Non-visual AC — CU not required (tiered policy).
- **Jira:** close-out **KAN-285** + **KAN-286**
- **Next:** **KAN-287** Charter Frame window/monitor snap (test **KAN-288**)

### 2026-11-18 — Council CR addendum — Human-hands verify handoff
- **Agent/chat:** Council Room — Designer addendum to GPU/CU policy
- **Done:** When CU cannot confirm, agent must leave app ready (running / one start cmd), seed data/stubs, and provide numbered steps in chat + test ticket; human only follows and confirms. Visual/occlusion AC waits on that confirm. No product code.
- **Files:** same ops set as KAN-299 (+ HOW_WE_WORK / PROJECT_MEMORY / WORK_LOG)
- **Verify:** docs/rules only
- **Jira:** comment on **KAN-299**
- **Next:** Build chat **KAN-285** under updated handoff

### 2026-11-18 — Council CR — Build verify: GPU / Computer Use throttle
- **Agent/chat:** Council Room (`/council`) — GPU burnout + CU overlay collision risk
- **Done:** Process/rules CR applied (no product code). Tiered desktop verify: pytest/API first; CU for visual/occlusion only; pause Ollama + classic orb during CU; one overlay; CU skipped/flake honesty — never soft-pass. FR-MAN-2 stays parked. Active Build remains **KAN-285**.
- **Files:** `AGENTS.md`, `.cursor/rules/tooling-use.mdc`, `.cursor/rules/ironbee-devtools-use.mdc`, `.cursor/skills/run-local-stack/SKILL.md`, `.cursor/skills/slice-workflow/SKILL.md`, `PROJECT_MEMORY.md`, `docs/ops/HOW_WE_WORK.md`
- **Verify:** docs/rules only (no pytest/product UI)
- **Jira:** ops Task **KAN-299** created, completion comment, Done — not a product Story
- **Next:** Build chat continues **KAN-285** under new verify policy

### 2026-11-18 — KAN-283 — Trustworthy Manual session loop (headed)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-283
- **Done:** Hardened calm Start→notes/stills→End→review→Propose→Confirm/Cancel loop on desktop. In-app Charter Frame Cancel confirm (no `window.confirm`); loop stages idle/recording/review (`data-manual-loop` / `data-loop-stage`); review hides Start form so Propose/Confirm stay reachable (no sticky-inside-scrollport); Enter-to-note on dock; defaults advertise trustworthy_loop + FR-JIRA-5; Cancel proposal / cancel session write nothing to Jira. Cache-bust **desk93**.
- **Files:** `plans/manual_session.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_manual_trustworthy_loop.py` (+ desk93 across UI tests), docs
- **Verify:** `pytest tests/test_manual_trustworthy_loop.py tests/test_manual_session.py tests/test_manual_ia.py tests/test_area_chrome_nonoverlap.py` 17 passed. Live API on desk93: Start→note→End→Propose bug→Cancel proposal (`writes_jira=False`); cancel session `discarded=True`. Live `desktop_app.py` desk93: Computer Use opened orb home (CALM + First-hour checklist); App-menu Manual clicks contested by HUD (same pattern as KAN-281); HTML markers `data-manual-loop` / `data-charter-cancel-confirm` / `data-manual-confirm` present.
- **Jira:** close-out **KAN-283** + **KAN-284**
- **Next:** **KAN-285** Real agent-assist local drafts (test **KAN-286**)

### 2026-11-18 — KAN-281 — Non-overlapping area chrome (FR-UI-9)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-281
- **Done:** Removed sticky-inside-scrollport occlusion across Plans / Suites / Reports / Manual / Lab. Area chrome is flex-shrink header outside `.area-work` scrollport; `position: sticky` gone from area toolbars. Marker `data-area-chrome-nonoverlap`; eight `data-area-work` wraps. Cache-bust **desk92**. Fixed Bug **KAN-280**.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_area_chrome_nonoverlap.py`, `tests/test_nav_overlap.py` (+ desk92 across UI tests), docs
- **Verify:** `pytest tests/test_area_chrome_nonoverlap.py tests/test_nav_overlap.py tests/test_plans_ia.py tests/test_suites_ia.py tests/test_reports_ia.py tests/test_manual_ia.py tests/test_lab_areas_ia.py tests/test_desktop_app_menu.py tests/test_manual_session.py` 28 passed. Live `desktop_app.py` desk92: Computer Use opened Plans — toolbar + tabs above work; Rename field focused (I-beam); primary fields/tabs visible and clickable (not covered by chrome). HUD checklist contested early clicks; Open Plans succeeded.
- **Jira:** close-out **KAN-281** + **KAN-282**; Bug **KAN-280** Fix + Done
- **Next:** **KAN-283** Trustworthy Manual session loop (test **KAN-284**)

### 2026-11-18 — Council Track 2 Slice-0 — CR landed (docs + Jira)
- **Agent/chat:** Cursor IDE Council Room → CR apply (Designer answers: non-overlap; fix-first; full Manual completion backlog; Build gate off KAN-81)
- **Done:** Amended FR-UI-9 (non-overlapping area chrome) + FR-MAN-1 completion wording in `docs/FUNCTIONAL_SPEC.md`. Seeded epic **KAN-279**, Bug **KAN-280**, Stories **KAN-281…297** + tests **KAN-282…298**. Active → **KAN-281**. Voice / FR-MAN-2 stay parked. No product feature code in this chat.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `docs/design/H1_MANUAL_SESSION_CAPTURE.md`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `.cursor/skills/slice-workflow/SKILL.md`, `scripts/jira_kan_track2_slice0.py`, `docs/ops/TRACK2_ACTIVE_POINTER.txt`
- **Verify:** `python scripts/jira_kan_track2_slice0.py` created keys; Active table points at KAN-281
- **Jira:** CR comments on KAN-241/265/275/277; epic KAN-279
- **Next:** Build chat — **pick up where we left off** → **KAN-281**

### 2026-11-18 — KAN-277 — FR-MAN-1 Charter Frame MVP
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-277
- **Done:** Level-scoped manual sessions under `plans/{LEVEL}/sessions/`; Start/End/Cancel; notes + opt-in stills; assist/mist default OFF; free-region Charter Frame overlay (click-through interior, resize/drag chrome, optional inner mist); End → review → Propose bug/comment/local note/step preview → confirm (Cancel writes nothing to Jira); story required when ticket-bound. Cache-bust **desk92**. Gradio stub points at desktop.
- **Files:** `plans/manual_session.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_manual_session.py`, `tests/test_manual_session_design.py`, `tests/test_manual_ia.py` (+ desk92 across UI tests), docs
- **Verify:** `pytest tests/test_manual_session.py tests/test_manual_session_design.py tests/test_manual_ia.py tests/test_nav_overlap.py` 18 passed. Live `desktop_app.py` opened desk92 (orb home). HTML markers `data-charter-frame` / `data-charter-mvp` / `data-manual-start`.
- **Jira:** close-out **KAN-277** + **KAN-278**
- **Next:** Active **deferred** — **KAN-81** voice; do not implement. Human/council picks next track.

### 2026-11-18 — KAN-275 — Manual Primary App area + Plans deep-link shell
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-275
- **Done:** Primary App menu gains **Manual** (Chat / Settings / Plans / Manual / Reports / Documents). Dedicated Manual area shell with charter + plan/case/story/test fields, assist/mist toggles default off, Start disabled until Charter Frame. Plans **Start manual on this case** deep-link pre-fills Manual. Esc/Back → orb home. Gradio Manual stub/minimal. Cache-bust **desk90**. No recorder/frame (KAN-277).
- **Files:** `ui/app_areas.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `ui/gradio_app.py`, `desktop_app.py`, `tests/test_manual_ia.py` (+ desk90 across UI tests), docs
- **Verify:** `pytest tests/test_manual_ia.py tests/test_desktop_app_menu.py tests/test_gradio_menu_nav.py tests/test_plans_ia.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_lab_areas_ia.py` 24 passed. Live `GET /ui/desktop/index.html?v=desk90` has Manual in Primary (not Lab), `data-manual-ia` / deeplink / start shell. `desktop_app.py` opened desk90 (orb home; App-menu Computer Use contested by HUD checklist; HTML + pytest evidence).
- **Jira:** close-out **KAN-275** + **KAN-276**
- **Next:** **KAN-277** Charter Frame MVP (test **KAN-278**)

### 2026-11-18 — KAN-273 — Lab areas UI tidy
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-273
- **Done:** Documents / Heal / Desktop / Sandboxes progressive disclosure (FR-UI-7 / FR-UI-8): sticky primary actions + status; primary ingest/list / proposals / smoke status / sandbox list; help + configure under Advanced. Control IDs and APIs unchanged; Lab tools App menu group kept. Cache-bust **desk89**.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_lab_areas_ia.py` (+ desk89 across UI tests), docs
- **Verify:** `pytest tests/test_lab_areas_ia.py tests/test_doc_privacy_uploads.py tests/test_doc_ingest.py tests/test_multi_sandbox.py tests/test_desktop_app_menu.py` 30 passed (+ IA suite 7). Live `GET /ui/desktop/index.html?v=desk89` has `data-lab-areas-ia` ×4 + sticky/advanced markers. `desktop_app.py` opened desk89 (orb home; App-menu Computer Use contested; HTML + pytest evidence).
- **Jira:** close-out **KAN-273** + **KAN-274**
- **Next:** **KAN-275** Manual Primary shell (test **KAN-276**)

### 2026-11-18 — KAN-271 — Reports area UI tidy
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-271
- **Done:** Reports progressive disclosure (FR-UI-7 / FR-REP-4): sticky toolbar (Refresh / Report settings + status); primary saved-report list + detail (markdown/screenshot/JSON); Export run/pack collapsed under Advanced. No section toggles in Reports; exporter APIs unchanged. Cache-bust **desk88**.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_reports_ia.py` (+ desk88 across UI tests), docs
- **Verify:** `pytest tests/test_reports_ia.py tests/test_reports_library.py tests/test_suites_ia.py tests/test_plans_ia.py tests/test_nav_overlap.py` 11 passed. Live `GET /ui/desktop/index.html?v=desk88` has `data-reports-ia` / sticky / list / advanced; `/api/reports` empty_hint OK. `desktop_app.py` opened desk88 (orb home; Reports App-menu click contested by HUD/Settings mis-hit; HTML + API + pytest evidence).
- **Jira:** close-out **KAN-271** + **KAN-272**
- **Next:** **KAN-273** Lab areas tidy (test **KAN-274**)

### 2026-11-18 — KAN-269 — Suites area UI tidy
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-269
- **Done:** Suites progressive disclosure (FR-UI-7 / FR-TEST-5): sticky path toolbar (Discover / List / Run selected / Run all + status); primary suite list with selection; Import + help collapsed under Advanced. Existing playwright_suite APIs unchanged; external files never deleted. Cache-bust **desk87**.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_suites_ia.py` (+ desk87 across UI tests), docs
- **Verify:** `pytest tests/test_suites_ia.py tests/test_playwright_suite.py tests/test_plans_ia.py tests/test_nav_overlap.py` 12 passed. Live `GET /ui/desktop/index.html?v=desk87` has `data-suites-ia` / sticky / list / advanced. `desktop_app.py` opened desk87 (orb home; Suites App-menu click contested by HUD; HTML + API + pytest evidence).
- **Jira:** close-out **KAN-269** + **KAN-270**
- **Next:** **KAN-271** Reports area UI tidy (test **KAN-272**)

### 2026-11-18 — KAN-267 — Framework stub honesty
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-267
- **Done:** FR-PLUG-3 honesty UX: Playwright labelled **ready**; Selenium/Cypress labelled **not implemented — never pass**; Plans framework select no longer defaults to Selenium; empty/API default is Playwright; desktop Run disabled for stub case or stub Settings framework with clear status hint; stubs remain selectable. Cache-bust **desk86**.
- **Files:** `plugins/framework_switch.py`, `plans/framework_case.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `ui/gradio_app.py`, `tests/test_framework_stub_honesty.py` (+ desk86 across UI tests), docs
- **Verify:** `pytest tests/test_framework_stub_honesty.py tests/test_framework_switch.py tests/test_plan_framework_case.py` 18 passed. Live `GET /ui/desktop/index.html?v=desk86` has `data-stub-honesty`, Playwright selected, no Selenium selected; `/api/test-framework` stub_honesty + ui_labels. `desktop_app.py` opened desk86 (orb home; Plans click contested by HUD drag; HTML + API + pytest evidence).
- **Jira:** close-out **KAN-267** + **KAN-268**
- **Next:** **KAN-269** Suites area UI tidy (test **KAN-270**)

### 2026-11-18 — KAN-265 — Plans IA tidy (Cases-first + sticky toolbar)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-265 after Slice-0 on main
- **Done:** Desktop Plans reorganised for FR-UI-9: sticky toolbar (plan picker, Open/Refresh, search, status); section tabs with **Cases** default; Draft/Coverage/Trace/History/Run setup secondary; one **Add case ▾** menu (all prior add types kept); schedule detail collapsed under Run setup. Cache-bust **desk85**.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_plans_ia.py` (+ desk85 across UI tests), docs (WORK_LOG, ROADMAP, FUNCTIONAL_SPEC, PROJECT_MEMORY)
- **Verify:** `pytest tests/test_plans_ia.py tests/test_plan_desktop_case.py tests/test_plan_framework_case.py tests/test_plan_schedule.py` 22 passed. Live `GET /ui/desktop/index.html?v=desk85` has `data-plans-ia` / sticky / tabs / Add case. `desktop_app.py` opened desk85 (Computer Use contested by other apps; HTML + pytest evidence).
- **Jira:** close-out **KAN-265** + **KAN-266**
- **Next:** **KAN-267** Framework stub honesty (test **KAN-268**)

### 2026-11-18 — Council Track 1 Slice-0 — Charter Frame CR + Plans IA
- **Agent/chat:** Cursor IDE `/council` → human picked Track **1**; choices A3/B1/C3/D1/E2 + agent-assist + mist toggles; G1 defaults off; H1 create Jira (full tidy set, not Manual-only)
- **Done:** Slice-0 docs + Jira epic/stories/tests. Extended FR-MAN-1; FR-MAN-2 parked; FR-UI-9; Manual Primary; stub honesty; H1 §9–§10. Jira: epic **KAN-264**; **KAN-265/266** Plans IA; **267/268** stub honesty; **269/270** Suites tidy; **271/272** Reports tidy; **273/274** Lab areas tidy; **275/276** Manual shell; **277/278** Charter Frame MVP. Commented **KAN-241**.
- **Files:** `docs/FUNCTIONAL_SPEC.md`, `docs/design/H1_MANUAL_SESSION_CAPTURE.md`, `plans/manual_session_design.py`, `tests/test_manual_session_design.py`, `docs/ops/ROADMAP.md`, `docs/ops/WORK_LOG.md`, `PROJECT_MEMORY.md`, `scripts/jira_kan_track1_slice0.py`
- **Verify:** `pytest tests/test_manual_session_design.py` 4 passed; Jira create script exit 0
- **Jira:** epic + 7 stories + 7 tests created (yes)
- **Next:** Build chat “pick up where we left off” → **KAN-265**

### 2026-11-18 — KAN-245 — H3 Plan shared use without a cloud (design only)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-245
- **Done:** Short FR-SEC-1 design: local/on-prem options (F6 export pack, E4 backup copy, future shared folder), security limits (OFFICIAL/SECRET, no shared creds, confirm import, no cloud multi-tenant). **No network/share service shipped.** Machine outline in `plans/shared_use_design.py`.
- **Files:** `docs/design/H3_SHARED_USE_WITHOUT_CLOUD.md`, `plans/shared_use_design.py`, `tests/test_shared_use_design.py`, `docs/FUNCTIONAL_SPEC.md`
- **Verify:** `pytest tests/test_shared_use_design.py` 4 passed (outline AC, doc headings, assert_design_complete, no share/sync surface in product).
- **Jira:** close-out **KAN-245** + **KAN-246**
- **Next:** Catalogue H designs complete; Active **deferred** — **KAN-81** / G10 voice (do not implement); human/council picks next track

### 2026-11-17 — KAN-243 — H2 Plan the pipelines section (design only)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-243
- **Done:** Short FR-CI-1 design: what a pipeline record shows, what it will not do (no suite replacement; CI green ≠ local pass), secrets stay local in level credentials. **No CI integration shipped.** Machine outline in `plans/pipelines_design.py`.
- **Files:** `docs/design/H2_PIPELINES_SECTION.md`, `plans/pipelines_design.py`, `tests/test_pipelines_design.py`, `docs/FUNCTIONAL_SPEC.md`
- **Verify:** `pytest tests/test_pipelines_design.py` 4 passed (outline AC, doc headings, assert_design_complete, no CI surface in product).
- **Jira:** close-out **KAN-243** + **KAN-244**
- **Next:** **KAN-245** H3 Plan shared use without a cloud — design only (test **KAN-246**); G10 voice still deferred

### 2026-11-17 — KAN-241 — H1 Plan manual session capture (design only)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-241
- **Done:** Short FR-MAN-1 design: charter start, what is recorded (notes + opt-in screenshots; no keylogger/silent video), bug/comment propose via defect-packet + two-step confirm, OFFICIAL/SECRET isolation. **No recorder shipped.** Machine outline in `plans/manual_session_design.py`.
- **Files:** `docs/design/H1_MANUAL_SESSION_CAPTURE.md`, `plans/manual_session_design.py`, `tests/test_manual_session_design.py`, `docs/FUNCTIONAL_SPEC.md`
- **Verify:** `pytest tests/test_manual_session_design.py` 4 passed (outline AC, doc headings, assert_design_complete, no recorder surface in product).
- **Jira:** close-out **KAN-241** + **KAN-242**
- **Next:** **KAN-243** H2 Plan the pipelines section — design only (test **KAN-244**); G10 voice still deferred

### 2026-11-17 — KAN-239 — G12 Scheduled local run
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-239
- **Done:** One local tagged schedule on this PC (plan + tag + HH:MM). Sequential only (D1 default). Uses saved connection. Missed slots (PC off past fire window) recorded as `not_run`, never pass. Off until created; not cloud-hosted. Plans UI Scheduled local run + `GET/POST /api/plans/schedule*` + desk84.
- **Files:** `plans/schedule.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_schedule.py` (+ desk84 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_schedule.py` 7 passed. Live `GET /api/plans/schedule` → enabled false / off_until_created true / cloud false; desk84 HTML has `plan-schedule-save`. `desktop_app.py` opened desk84 (orb home; Computer Use contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-239** + **KAN-240**
- **Next:** **KAN-241** H1 Plan manual session capture — design only (test **KAN-242**); G10 voice still deferred

### 2026-11-17 — KAN-237 — G11 Installer for a second Windows PC
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-237
- **Done:** Secret-free second-PC install pack (SALES-1 / G11): curated source copy + INSTALL.md + SetupSecondPC.ps1 + RunDesktop.cmd + pack_manifest (no shared cloud account, telemetry off by default, not a company-rollout claim). Settings → App “Build install pack”; `GET/POST /api/installer/second-pc*` + desk83.
- **Files:** `installer/second_pc.py`, `installer/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_second_pc_installer.py` (+ desk83 cache-bust across UI tests)
- **Verify:** `pytest tests/test_second_pc_installer.py` 2 passed. Live `GET /api/installer/second-pc` → secrets false / cloud false / telemetry default false; `POST …/second-pc-pack` → ok pack folder; desk83 HTML has `set-second-pc-pack`. `desktop_app.py` opened desk83 (orb home; Computer Use Settings click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-237** + **KAN-238**
- **Next:** **KAN-239** G12 Scheduled local run (test **KAN-240**); G10 voice still deferred

### 2026-11-17 — KAN-233 — G9 Another framework runner
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-233
- **Done:** Plan cases can select Playwright / Selenium / Cypress (`source.kind=framework`). Run uses same case/run model and stores `framework`. Selenium/Cypress → not-implemented, result error (never pass). Playwright remains default ready runner; settings framework stub kept. Settings-level Selenium/Cypress also blocks browser case pass. Plans UI framework select + “Add framework case”; `POST /api/plans/{id}/cases/framework` + desk82.
- **Files:** `plans/framework_case.py`, `plugins/framework_switch.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_framework_case.py` (+ desk82 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_framework_case.py tests/test_framework_switch.py` 13 passed. Live `POST /api/plans/.../cases/framework` → kind framework; run → runner framework_switch, result error, status not_implemented. desk82 HTML has `plan-add-framework-btn` / `plan-framework-select`. `desktop_app.py` opened desk82 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-233** + **KAN-234**
- **Next:** **KAN-237** G11 Installer for a second Windows PC (test **KAN-238**); G10 voice still deferred

### 2026-11-17 — KAN-231 — G8 Sandbox chosen as the run environment
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-231
- **Done:** When multi-sandbox plugin enabled, plan/suite runs can name one existing sandbox; run + suite_run store `sandbox` name; blank selection keeps normal browser profile (`profile_dir` override in Playwright). Sandboxes screen still manages records. Parallel still D1-capped. Plans UI “Run sandbox” select + `GET /api/plans/run-sandboxes` + desk82.
- **Files:** `plans/sandbox_run.py`, `plugins/multi_sandbox.py`, `plugins/playwright_runner.py`, `plugins/registry.py`, `plans/store.py`, `plans/run_case.py`, `plans/run_by_tag.py`, `plans/rerun_failed.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_sandbox_run.py` (+ desk82 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_sandbox_run.py tests/test_multi_sandbox.py` 17 passed. Live `GET /api/plans/run-sandboxes` → plugin off empty / on lists sandboxes; desk82 HTML has `plan-sandbox-select`. `desktop_app.py` opened desk82 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-231** + **KAN-232**
- **Next:** **KAN-233** G9 Another framework runner (test **KAN-234**)

### 2026-11-17 — KAN-229 — G7 Performance budget plugin
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-229
- **Done:** Optional numeric `performance_budget_ms` on cases. Local duration only; over budget fails that case; cases without budget unchanged. `performance_budget` plugin + evidence JSON. Plans UI “Add performance budget case”; `POST /api/plans/{id}/cases/perf` + set/clear `…/cases/{id}/perf` + desk80.
- **Files:** `plugins/performance_budget.py`, `plugins/registry.py`, `plans/perf_case.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_performance_budget.py` (+ desk80 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_performance_budget.py` 9 passed (+ a11y 8 = 17). Live `POST /api/plans/.../cases/perf` → budget_ms set, local_only true, cloud_apm false; plain case budget None. desk80 HTML has `plan-add-perf-btn`. `desktop_app.py` opened desk80 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-229** + **KAN-230**
- **Next:** **KAN-231** G8 Sandbox chosen as the run environment (test **KAN-232**)

### 2026-11-17 — KAN-227 — G6 Accessibility checks plugin
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-227
- **Done:** Optional a11y sidecar on browser cases (`a11y_check` / tags `a11y`|`accessibility`). `accessibility_checks` plugin scans HTML (stdlib) and attaches violations to the run; functional result unchanged. Off unless case opts in. Plans UI “Add accessibility check case”; `POST /api/plans/{id}/cases/a11y` + enable toggle `…/cases/{id}/a11y` + desk79.
- **Files:** `plugins/accessibility_checks.py`, `plugins/registry.py`, `plans/a11y_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_a11y.py` (+ desk79 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_a11y.py` 8 passed. Live `POST /api/plans/.../cases/a11y` → a11y_check true; plain case false until enable. desk79 HTML has `plan-add-a11y-btn`. `desktop_app.py` opened desk79 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-227** + **KAN-228**
- **Next:** **KAN-229** G7 Performance budget plugin (test **KAN-230**)

### 2026-11-17 — KAN-225 — G5 Visual baseline screenshots
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-225
- **Done:** Opt-in visual baseline cases (`source.kind=visual`). Level-scoped PNG baselines under `%LOCALAPPDATA%/ai_testing_app/baselines/{level}/`. Compare on run; mismatch fails with baseline + current linked in evidence. Update-baseline is explicit only (`POST …/visual-baseline` or `update_baseline=true`). Off unless case opts in; one browser at a time (capture lock). Plans UI “Add visual baseline case” + “Update visual baseline”; `POST /api/plans/{id}/cases/visual` + desk78.
- **Files:** `plugins/visual_baseline.py`, `plugins/registry.py`, `plans/visual_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_visual_baseline.py` (+ desk78 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_visual_baseline.py` 11 passed. Live `POST /api/plans/.../cases/visual` → kind visual; run with current_path → runner visual_baseline pass + `run.visual_baseline`. desk78 HTML has `plan-add-visual-btn` / `plan-update-baseline-btn`. `desktop_app.py` opened desk78 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-225** + **KAN-226**
- **Next:** **KAN-227** G6 Accessibility checks plugin (test **KAN-228**)

### 2026-11-17 — KAN-223 — G4 Seed data and fixtures
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-223
- **Done:** Plan cases may name a level-scoped seed fixture (`source.kind=seed`). `seed_fixture` plugin loads named JSON under `%LOCALAPPDATA%/ai_testing_app/fixtures/{level}/`; default `seed_user.json` ensured on add. Run stores `seed_fixture` name; missing fixture → `failure_class=environment`. No global silent injection. Plans UI “Add seed/fixture case”; `POST /api/plans/{id}/cases/seed` + desk77.
- **Files:** `plugins/seed_fixture.py`, `plugins/registry.py`, `plans/seed_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_seed_fixture.py` (+ desk77 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_seed_fixture.py` 7 passed. Live `POST /api/plans/.../cases/seed` → kind seed; run → runner seed_fixture, `run.seed_fixture=seed_user.json`, pass. Missing fixture → environment. desk77 HTML has `plan-add-seed-btn`. `desktop_app.py` opened desk77 (orb home; Computer Use focus contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-223** + **KAN-224**
- **Next:** **KAN-225** G5 Visual baseline screenshots (test **KAN-226**)

### 2026-11-17 — KAN-221 — G3 Contract and mock responses
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-221
- **Done:** API cases may select a local mock fixture (`mock_fixture` in source.ref). `contract_mock` plugin loads level-scoped fixtures under `%LOCALAPPDATA%/ai_testing_app/mocks/{level}/`; default `contract_ok.json` ensured on add. Run record stores `mock: true` + note/evidence say mock. Live API/messaging cases unchanged when no fixture selected. Plans UI “Add mock/contract case”; `POST /api/plans/{id}/cases/contract` + desk76.
- **Files:** `plugins/contract_mock.py`, `plugins/registry.py`, `plans/api_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_contract_mock.py` (+ desk76 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_contract_mock.py tests/test_plan_api_case.py` 16 passed. Live `POST /api/plans/.../cases/contract` → kind api + mock_fixture; run → runner contract_mock, `run.mock` true, pass. desk76 HTML has `plan-add-contract-btn`. `desktop_app.py` opened desk76 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-221** + **KAN-222**
- **Next:** **KAN-223** G4 Seed data and fixtures (test **KAN-224**)

### 2026-11-17 — KAN-219 — G2 API and messaging checks
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-219
- **Done:** API/messaging-typed plan cases (`source.kind=api`) call saved Settings messaging/API endpoint via `api_messaging_runner`; store HTTP/TCP status + redacted body summary on same case/run model; failures class like other cases (product_bug / environment); secrets in body redacted in log/evidence. Plans UI “Add API/messaging case”; messaging Settings field kept. `POST /api/plans/{id}/cases/api` + desk75.
- **Files:** `plugins/api_messaging_runner.py`, `plans/api_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_api_case.py` (+ desk75 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_api_case.py` 8 passed. Live `POST /api/plans/.../cases/api` → kind api; desk75 HTML has `plan-add-api-btn` + `set-api-endpoint`. `desktop_app.py` opened desk75; Computer Use Plans shows Add API/messaging case.
- **Jira:** close-out **KAN-219** + **KAN-220**
- **Next:** **KAN-221** G3 Contract and mock responses (test **KAN-222**)

### 2026-11-17 — KAN-217 — G1 Desktop cases on the same suite
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-217
- **Done:** Desktop-typed plan cases (`source.kind=desktop`) run via `desktop_runner` against connected exe; results on the same case/run model as browser cases. Plans UI “Add desktop case”; Desktop area smoke unchanged; browser Playwright path unchanged. `POST /api/plans/{id}/cases/desktop` + desk74.
- **Files:** `plans/desktop_case.py`, `plans/run_case.py`, `plans/store.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_desktop_case.py` (+ desk74 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_desktop_case.py` (+ run_case + desktop_runner) 35 passed. Live `POST /api/plans/.../cases/desktop` → kind desktop. desk74 HTML has `plan-add-desktop-btn`. `desktop_app.py` opened desk74 (orb home; Computer Use Plans click contested; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-217** + **KAN-218**
- **Next:** **KAN-219** G2 API and messaging checks (test **KAN-220**)

### 2026-11-17 — KAN-215 — F7 Home checklist widget
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-215
- **Done:** First-hour checklist HUD on orb home: connection → first plan → first run. Auto-shows until all done, then hides; reopen from Screen drawer. Deep-links to Settings/Plans; does not block chat or App areas (not a forced wizard). `GET /api/plans/home-checklist` + desk73.
- **Files:** `plans/home_checklist.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_home_checklist.py` (+ desk73 cache-bust across UI tests)
- **Verify:** `pytest tests/test_home_checklist.py` 3 passed. Live `GET /api/plans/home-checklist` → home_only true, forced_wizard false, steps connection/first_plan/first_run; desk73 HTML has `hud-checklist` / `hud-checklist-toggle`. `desktop_app.py` opened desk73 with checklist 2/3 visible.
- **Jira:** close-out **KAN-215** + **KAN-216**
- **Next:** **KAN-217** G1 Desktop cases on the same suite (test **KAN-218**)

### 2026-11-17 — KAN-213 — F6 Read-only export pack
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-213
- **Done:** Local read-only export pack folder under export_packs: README + LABEL (level + time), report.md/json, matrix.md/json, evidence/ with redacted index. Opens without the app; secrets redacted per E3; not a cloud shared drive. Reports button + optional home HUD for last export time; desk72.
- **Files:** `reports/export_pack.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_export_pack.py` (+ desk72 cache-bust across UI tests)
- **Verify:** `pytest tests/test_export_pack.py` 2 passed. Live `GET /api/export-pack` → opens_without_app true, cloud false; desk72 HTML has `rpt-export-pack` / `hud-export-last`. `desktop_app.py` opened desk72.
- **Jira:** close-out **KAN-213** + **KAN-214**
- **Next:** **KAN-215** F7 Home checklist widget (test **KAN-216**)

### 2026-11-17 — KAN-211 — F5 Keyboard on orb home and inside areas
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-211
- **Done:** Documented power-user shortcuts on orb home + Plans: Alt+R run selected case, Alt+N next failure (open plan fails, else Tester HUD last-run fails), Esc Back to orb. Explicitly no shortcuts for Jira write confirm or heal approve. Screen drawer Keyboard doc + Plans hint; desk71.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_keyboard_shortcuts.py` (+ desk71 cache-bust across UI tests)
- **Verify:** `pytest tests/test_keyboard_shortcuts.py` 1 passed. Live desk71 HTML has `keyboard-shortcuts-doc` / `plan-keyboard-hint`; JS has run/next/back handlers and never-list for jira_write_confirm + heal_approve. `desktop_app.py` opened desk71 (orb home visible).
- **Jira:** close-out **KAN-211** + **KAN-212**
- **Next:** **KAN-213** F6 Read-only export pack (test **KAN-214**)

### 2026-11-17 — KAN-209 — F4 Coverage HUD widget pack on orb home
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-209
- **Done:** Optional Coverage HUD pack on orb home: open-story AC lines covered/partial/missing. Screen drawer toggles; home-only (hidden while App area open); choosing a line opens Plan/Suite on linked case; never edits Jira. No separate PO home. `GET /api/plans/coverage-hud` (+ optional `story_key`) + desk70.
- **Files:** `plans/coverage_hud.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_coverage_hud.py` (+ desk70 cache-bust across UI tests)
- **Verify:** `pytest tests/test_coverage_hud.py` (+ release/manager/tester) 8 passed. Live `GET /api/plans/coverage-hud` → home_only true, separate_po_home false, jira_write false; desk70 HTML has coverage HUD ids/toggles. `desktop_app.py` opened desk70.
- **Jira:** close-out **KAN-209** + **KAN-210**
- **Next:** **KAN-211** F5 Keyboard on orb home and inside areas (test **KAN-212**)

### 2026-11-17 — KAN-207 — F3 Release HUD widget pack on orb home
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-207
- **Done:** Optional Release HUD pack on orb home: environment name, last run, uncovered stories, open product bugs. Screen drawer toggles; home-only (hidden while App area open); rows/buttons deep-link into Reports readiness (ticks stay on Reports). No separate Release home. `GET /api/plans/release-hud` + desk69.
- **Files:** `plans/release_hud.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_release_hud.py` (+ desk69 cache-bust across UI tests)
- **Verify:** `pytest tests/test_release_hud.py` (+ manager/tester) 6 passed. Live `GET /api/plans/release-hud` → home_only true, separate_release_home false, readiness_ticks_on_reports true; desk69 HTML has release HUD ids/toggles. `desktop_app.py` opened desk69.
- **Jira:** close-out **KAN-207** + **KAN-208**
- **Next:** **KAN-209** F4 Coverage HUD widget pack on orb home (test **KAN-210**)

### 2026-11-17 — KAN-205 — F2 Manager HUD widget pack on orb home
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-205
- **Done:** Optional Manager HUD pack on orb home: pass rate, known-issue count, stories with no cases, bugs from plan. Screen drawer toggles; home-only (hidden while App area open); pass rate opens Reports; rows deep-link into Plans. Known issues never shown as passes. No separate Manager home. `GET /api/plans/manager-hud` + desk68.
- **Files:** `plans/manager_hud.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_manager_hud.py` (+ desk68 cache-bust across UI tests)
- **Verify:** `pytest tests/test_manager_hud.py` (+ tester/orb) 7 passed. Live `GET /api/plans/manager-hud` → home_only true, separate_manager_home false, known_not_shown_as_pass true; desk68 HTML has manager HUD ids/toggles. `desktop_app.py` opened desk68 (Computer Use focus contested by other apps; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-205** + **KAN-206**
- **Next:** **KAN-207** F3 Release HUD widget pack on orb home (test **KAN-208**)

### 2026-11-17 — KAN-203 — F1 Tester HUD widget pack on orb home
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-203
- **Done:** Optional Tester HUD pack on orb home: connection health, last run, failed cases, quarantined cases. Screen drawer toggles; home-only (hidden while App area open); rows deep-link into Plans on that case. No separate Tester home. `GET /api/plans/tester-hud` + desk67.
- **Files:** `plans/tester_hud.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_tester_hud.py` (+ desk67 cache-bust across UI tests)
- **Verify:** `pytest tests/test_tester_hud.py` (+ hud widgets) 7 passed. Live `GET /api/plans/tester-hud` → home_only true, separate_tester_home false, connection checks present; desk67 HTML has tester HUD ids/toggles. `desktop_app.py` opened desk67 (orb home visible; Computer Use drawer click contested by other apps; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-203** + **KAN-204**
- **Next:** **KAN-205** F2 Manager HUD widget pack on orb home (test **KAN-206**)

### 2026-11-17 — KAN-201 — E5 Read last plan while Jira is down
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-201
- **Done:** Offline last-plan read: with Jira down, search and traceability matrix stay on stored keys/results; network actions (draft from story/project, drift check/refresh, read Jira story, Jira write) disabled with reasons; stored rows labelled with fetch time (`jira_snapshots.captured_at` + run finish). `GET /api/plans/offline-read` + `GET /api/plans/{id}/offline-read`. Plans UI banner + desk66. Writing to Jira while offline remains out of scope.
- **Files:** `plans/offline_read.py`, `plans/search.py`, `plans/traceability.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_offline_read.py` (+ desk66 cache-bust across UI tests)
- **Verify:** `pytest tests/test_plan_offline_read.py` (+ search/traceability) 13 passed. Live `GET /api/plans/offline-read` → offline true, search/matrix offline true, jira_write_while_offline false, 6 network actions disabled; desk66 HTML has `plan-offline-banner`. `desktop_app.py` opened desk66 (Computer Use focus contested by other apps; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-201** + **KAN-202**
- **Next:** **KAN-203** F1 Tester HUD widget pack on orb home (test **KAN-204**)

### 2026-11-17 — KAN-199 — E4 Backup and restore of this lab
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-199
- **Done:** Local lab backup zip under `%LOCALAPPDATA%\ai_testing_app\backups\`: plans + runs + evidence index for the active security level; optional settings (secrets stripped); credentials/secrets off by default. Restore requires confirm, refuses OFFICIAL/SECRET mix and level mismatch, reports what it replaced. Security panel Backup & restore UI (desk65). No cloud backup.
- **Files:** `settings/backup.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_lab_backup.py` (+ desk65 cache-bust across UI tests)
- **Verify:** `pytest tests/test_lab_backup.py` + related Security suite (37 passed). Live `GET/POST /api/backup` → created OFFICIAL zip, secrets_default false, cloud false; desk65 HTML has `backup-create` / `backup-restore-confirm`. `desktop_app.py` opened desk65 (Computer Use window focus contested by other apps; API + HTML + pytest evidence).
- **Jira:** close-out **KAN-199** + **KAN-200**
- **Next:** **KAN-201** E5 Read last plan while Jira is down (test **KAN-202**)

### 2026-11-17 — KAN-260 — Lab tools in App menu (UI-NAV-IA-5)
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-260
- **Done:** Compact ▦ App menu now has Primary + Lab tools groups. Lab tools (Security, Heal review, Desktop, Suites, Sandboxes) reachable in every layout mode; orb hub spokes kept as accelerators. Spec FR-UI-8. `ui/app_areas.py` constants. desk64 cache-bust.
- **Files:** `ui/desktop/index.html`, `ui/desktop/desktop.css`, `ui/desktop/desktop.js`, `ui/app_areas.py`, `desktop_app.py`, `tests/test_desktop_app_menu.py` (+ desk64 across UI tests), `docs/FUNCTIONAL_SPEC.md`
- **Verify:** `pytest tests/test_desktop_app_menu.py` + nav suite (8 + 20 passed). Live HTML at `:8765` has Primary/Lab tools + sandboxes. `desktop_app.py` opened desk64 (Computer Use click targeting flaky on DPI; HTML + pytest evidence).
- **Jira:** close-out **KAN-260** + **KAN-262**
- **Next:** **KAN-199** E4 Backup and restore of this lab (test **KAN-200**)

### 2026-11-17 — KAN-197 — E3 Redact secrets in evidence and exports
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-197
- **Done:** Exports and evidence index (`bundle.json`) redact known secret patterns and stored token values (`jira_api_token`, `target_secret`). Export summary counts `redaction_hits`; screenshots get an explicit non-OCR warning (not a wipe). `GET /api/redaction` + Security panel blurb (desk63).
- **Files:** `reports/redact.py`, `reports/exporter.py`, `reports/sections.py`, `plans/evidence_bundle.py`, `plans/run_report.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_export_redaction.py` (+ desk63 cache-bust across UI tests)
- **Verify:** `pytest tests/test_export_redaction.py` + related (45 passed). Live `GET /api/redaction` → patterns on, ocr false, wipes false; desk63 HTML has `redaction-status` / `redaction-screenshot-warn`; `desktop_app.py` opened (desk63).
- **Jira:** close-out **KAN-197** + **KAN-198**
- **Next:** **KAN-260** Lab tools in App menu (then E4…)

### 2026-11-17 — Council review — track / gaps / cut-nothing
- **Agent/chat:** Cursor IDE Agent `/council` — Review mode (no product code)
- **Done:** Confirmed on track at **KAN-197** E3. Cut-nothing holds in tree; reach gap = five lab tools hub-only on default overlay (already **KAN-260**). Designer chose **KAN-260** as next after E3 (before E4). Doc drift patched: ROADMAP Now → TESTALL-E/E3; PROJECT_MEMORY / FUNCTIONAL_SPEC §5–§6 / TEST_ALL_BACKLOG Active → KAN-197; Active slice Next → KAN-260. Jira comments on **KAN-260**, **KAN-81**, **KAN-235**.
- **Files:** `docs/ops/WORK_LOG.md`, `docs/ops/ROADMAP.md`, `docs/ops/TEST_ALL_BACKLOG.md`, `PROJECT_MEMORY.md`, `docs/FUNCTIONAL_SPEC.md`
- **Verify:** Active slice still KAN-197; Next after this = KAN-260; ROADMAP Now = TESTALL-E
- **Jira:** comments on KAN-260 / KAN-81 / KAN-235 (no status change)
- **Next:** Build chat — pick up **KAN-197**; after Done → **KAN-260**

### 2026-11-17 — KAN-195 — E2 Audit log for local side effects
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-195
- **Done:** Local side-effects audit (`local_side_effects_audit.jsonl`) records plan case edits, quarantine set/clear, and confirmed privacy wipes with time, action, plan/case id, level, session. Scrubs tokens and document bodies. `GET /api/local-audit` + Security panel list (desk62). Jira write audit remains separate; no cloud SIEM.
- **Files:** `settings/local_audit.py`, `settings/privacy.py`, `plans/store.py`, `plans/quarantine.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_local_side_effects_audit.py` (+ desk62 cache-bust)
- **Verify:** `pytest tests/test_local_side_effects_audit.py` + related (32 passed in batch). Live `GET /api/local-audit` → jira_write_audit_remains true, cloud_siem false; confirmed wipe appends `local_data_wipe`; desk62 HTML has `local-audit-list` / `priv-local-audit`; `desktop_app.py` opened (desk62).
- **Jira:** close-out **KAN-195** + **KAN-196**
- **Next:** **KAN-197** E3 redact secrets in evidence and exports (test **KAN-198**)

### 2026-11-17 — KAN-193 — E1 Document privacy for uploads
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-193
- **Done:** Local upload registry records filename, time, security level, and consent (consent flips true when extracted settings are confirmed). Privacy inventory includes `uploads`; confirm-gated delete-local-data can wipe them. Report section `documents` defaults off so exports omit document bodies unless opted in. Documents UI lists local uploads (desk61). No cloud sync.
- **Files:** `plugins/doc_uploads.py`, `plugins/doc_ingest.py`, `settings/privacy.py`, `reports/sections.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_doc_privacy_uploads.py`, `tests/test_report_sections.py` (+ desk61 cache-bust)
- **Verify:** `pytest tests/test_doc_privacy_uploads.py` + related (25 passed). Live `GET /api/privacy` includes uploads; `GET /api/doc-uploads` bodies=false cloud=false; `GET /api/report-sections` documents=false; desk61 HTML has `rpt-documents` / `priv-uploads` / `doc-uploads-list`; `desktop_app.py` opened (desk61).
- **Jira:** close-out **KAN-193** + **KAN-194**
- **Next:** **KAN-195** E2 audit log for local side effects (test **KAN-196**)

### 2026-11-17 — KAN-191 — D7 Duration on the run and the case
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-191
- **Done:** Case runs and suite runs store `duration_ms` locally. Suite finish persists duration (case-sum when wall clock is 0 due to second-precision timestamps). History compare returns suite duration delta plus `duration_changes` for same-result slower/faster cases. `GET /api/plans/duration` documents local-only (no upload). Desktop Plans compare UI shows suite + case duration deltas (desk60).
- **Files:** `plans/duration.py`, `plans/store.py`, `plans/history.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_duration.py` (+ desk60 cache-bust)
- **Verify:** `pytest tests/test_plan_duration.py` + related (24 passed). Live `GET /api/plans/duration` → upload/cloud_perf false; desk60 HTML/JS has duration compare; `desktop_app.py` opened (desk60).
- **Jira:** close-out **KAN-191** + **KAN-192**
- **Next:** **KAN-193** E1 Document privacy for uploads (test **KAN-194**)

### 2026-11-17 — KAN-189 — D6 Local notification when a run finishes
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-189
- **Done:** Local run-finish notice with pass/fail counts only (no secrets/page text). No email or cloud push. Preference `run_finish_notify_enabled` (default on) via Settings + `GET/POST /api/plans/run-notify`. Wired into standalone case run, tag run, and rerun-failed. Windows toast best-effort + in-app toast (desk59).
- **Files:** `plans/run_notify.py`, `plans/run_case.py`, `plans/run_by_tag.py`, `plans/rerun_failed.py`, `settings/store.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `ui/desktop/desktop.css`, `desktop_app.py`, `tests/test_plan_run_notify.py` (+ desk59 cache-bust)
- **Verify:** `pytest tests/test_plan_run_notify.py` + related (8 + 53 passed). Live `GET /api/plans/run-notify` → enabled, email/cloud false; desk59 HTML has `set-run-finish-notify` / `run-finish-toast`; `desktop_app.py` opened (desk59).
- **Jira:** close-out **KAN-189** + **KAN-190**
- **Next:** **KAN-191** D7 duration on the run and the case (test **KAN-192**)

### 2026-11-17 — KAN-187 — D5 Timeouts visible on the case
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-187
- **Done:** Case stores editable `step_timeout_ms` (default 10000 = current Playwright click timeout). Runner uses case budget; timeout failure notes always say timeout and include the budget. API `GET /api/plans/step-timeout` + case update/detail. Desktop Plans Edit selected case field (desk58). No silent timeout inflation heal.
- **Files:** `plans/timeouts.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_timeouts.py` (+ desk58 cache-bust)
- **Verify:** `pytest tests/test_plan_timeouts.py` + related (42 passed). Live `GET /api/plans/step-timeout` → default 10000; desk58 HTML has `plan-case-step-timeout`; `desktop_app.py` → App ▦ → Plans → Step timeout 10000 visible.
- **Jira:** close-out **KAN-187** + **KAN-188**
- **Next:** **KAN-189** D6 local notification when a run finishes (test **KAN-190**)

### 2026-11-17 — KAN-185 — D4 Credential status without revealing secrets
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-185
- **Done:** Per-field set/missing for Jira email, Jira API token, and target secret (never values). Test-connection uses stored Jira secret and returns success or human-readable auth error. Clear-secret is confirm-gated; `credentials_audit.jsonl` records clear events with no old value. Level-scoped `target_secret` key. API `GET /api/credentials/status`, `POST …/test-connection`, `…/clear`, `…/target-secret`. Desktop Settings Credential status UI (desk57).
- **Files:** `settings/credential_status.py`, `settings/store.py`, `settings/connection_health.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_credential_status.py` (+ desk57 cache-bust)
- **Verify:** `pytest tests/test_credential_status.py` + related (43 passed). Live `GET /api/credentials/status` → set/missing only; `POST /api/credentials/test-connection` → success without secrets; desk57 HTML has `cred-status-list` / `cred-test-btn` / `cred-clear-confirm-btn`; `desktop_app.py` opened (desk57).
- **Jira:** close-out **KAN-185** + **KAN-186**
- **Next:** **KAN-187** D5 timeouts visible on the case (test **KAN-188**)

### 2026-11-17 — KAN-183 — D3 Named environments
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-183
- **Done:** Level-scoped named targets (local/test/staging). Connection stores more than one under the active security level. Activate switches target URL/exe/messaging without changing security level. Credentials stay in the level store — never copied into a plan. Case runs and suite runs record `environment_name`. API `GET/POST /api/environments`, activate, delete. Desktop Settings + Plans controls (desk56).
- **Files:** `settings/environments.py`, `settings/store.py`, `plans/store.py`, `plans/history.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_named_environments.py` (+ desk56 cache-bust)
- **Verify:** `pytest tests/test_named_environments.py` + related (32 passed). Live create local+staging + activate staging keeps OFFICIAL; desk56 HTML has `set-env-active` / `plan-env-active`; `desktop_app.py` opened (desk56).
- **Jira:** close-out **KAN-183** + **KAN-184**
- **Next:** **KAN-185** D4 credential status without revealing secrets (test **KAN-186**)

### 2026-11-17 — KAN-181 — D2 Flake score and quarantine
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-181
- **Done:** Suite flake scores (fail count in last N runs, default 10). Quarantine requires reason + future expiry; quarantined cases skipped and listed on runnable/tag/rerun (never counted as pass). After expiry (or clear) return to selectable set. Raw last failure remains on case detail. desk55 Plans UI.
- **Files:** `plans/quarantine.py`, `plans/store.py`, `plans/run_case.py`, `plans/run_by_tag.py`, `plans/rerun_failed.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_quarantine.py` (+ desk55 cache-bust)
- **Verify:** `pytest tests/test_plan_quarantine.py` + related Plans/UI suite (54 + 45 passed). Live desk55 HTML has quarantine/flake controls; `GET /api/plans/{id}/flake` + quarantine POST; `desktop_app.py` opened (desk55).
- **Jira:** close-out **KAN-181** + **KAN-182**
- **Next:** **KAN-183** D3 named environments (test **KAN-184**)

### 2026-11-17 — KAN-179 — D1 Sequential default and a parallel cap
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-179
- **Done:** Suite runs default parallel=1 (sequential). Cap max=2 visible in Plans. Suite run stores `parallel_count`. API refuses above cap (`parallel_above_cap`). Wired into tag run + rerun-failed. `GET /api/plans/parallel-cap`. desk54.
- **Files:** `plans/parallel.py`, `plans/store.py`, `plans/run_by_tag.py`, `plans/rerun_failed.py`, `plans/history.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_parallel.py` (+ desk54 cache-bust)
- **Verify:** `pytest tests/test_plan_parallel.py` + related Plans/UI suite (80 passed). Live `GET /api/plans/parallel-cap` → default 1 max 2; desk54 HTML has `plan-parallel-count`; `desktop_app.py` opened → App ▦ → Plans → Suite parallel.
- **Jira:** close-out **KAN-179** + **KAN-180**
- **Next:** **KAN-181** D2 flake score and quarantine (test **KAN-182**)

### 2026-11-17 — KAN-177 — C11 Archive a case without deleting history
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-177
- **Done:** Soft-archive via `update_case(archived=…)`. Archived cases skip runnable/tag runs and refuse single-case run; runs/evidence kept. Unarchive restores. Desktop Plans: Show archived filter (default hide) + Archived checkbox on case edit. desk53.
- **Files:** `plans/store.py`, `plans/run_case.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_archive.py` (+ desk53 cache-bust)
- **Verify:** `pytest tests/test_plan_archive.py` + related Plans/UI suite (83 passed). API archive keeps evidence; unarchive restores runnable. Live desk53 HTML has `plan-case-archived` / `plan-show-archived`; `desktop_app.py` opened → App ▦ → Plans.
- **Jira:** close-out **KAN-177** + **KAN-178**
- **Next:** **KAN-179** D1 sequential default and a parallel cap (test **KAN-180**)

### 2026-11-17 — KAN-175 — C10 Suite history and compare two runs
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-175
- **Done:** Suite history lists past runs with time, duration, pass/fail, tag (level-local). Compare two runs shows cases whose result changed; known issues labelled. API `GET /api/plans/{id}/suite-history` + `…/suite-compare`. Desktop Plans: history list + A/B compare. desk52.
- **Files:** `plans/history.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_suite_history.py` (+ desk52 cache-bust)
- **Verify:** `pytest tests/test_plan_suite_history.py tests/test_plan_search.py tests/test_plan_run_by_tag.py tests/test_plan_import_playwright.py tests/test_plan_traceability.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py tests/test_reports_library.py -q` (52 passed). Live `/ui/desktop/?v=desk52` has `plan-history-list` / `plan-compare-btn`; `GET /api/plans/{id}/suite-history` → ok, `cross_level=false`; `desktop_app.py` opened (desk52, App menu → Plans path).
- **Jira:** close-out **KAN-175** + **KAN-176**
- **Next:** **KAN-177** C11 archive a case without deleting history (test **KAN-178**)

### 2026-11-17 — KAN-173 — C9 Search plans, cases, and failures
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-173
- **Done:** Level-scoped search across plans/cases/failures matching plan name, case name, Jira key, tag, and failure class. Results never cross OFFICIAL/SECRET. Opening a hit opens the plan and selects the case. API `GET /api/plans/search`. Desktop Plans: search box + clickable hits. desk51.
- **Files:** `plans/search.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_search.py` (+ desk51 cache-bust)
- **Verify:** `pytest tests/test_plan_search.py tests/test_plan_import_playwright.py tests/test_plan_run_by_tag.py tests/test_plan_run_case.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py tests/test_plan_store.py -q` (59 passed). Live `/ui/desktop/?v=desk51` has `plan-search-q` / `plan-search-btn`; `GET /api/plans/search?q=smoke` → ok, `cross_level=false`; `desktop_app.py` opened (desk51).
- **Jira:** close-out **KAN-173** + **KAN-174**
- **Next:** **KAN-175** C10 suite history and compare two runs (test **KAN-176**)

### 2026-11-17 — KAN-171 — C8 import Playwright project into suite
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-171
- **Done:** Import Playwright project tests as in-app plan cases (`source.kind=playwright`). Create plan or add to open plan. External project files never deleted. Suites npx path unchanged. Single imported case runs via `playwright_suite.run_suite` (optional `test_file` + grep). API `POST /api/plans/import-playwright`. Desktop Plans: path + Import Playwright / Add to open plan. desk50.
- **Files:** `plans/import_playwright.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `plugins/playwright_suite.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_import_playwright.py` (+ desk50 cache-bust)
- **Verify:** `pytest tests/test_plan_import_playwright.py tests/test_playwright_suite.py tests/test_plan_run_case.py tests/test_plan_run_by_tag.py tests/test_desktop_app_menu.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py -q` (59 passed). Live `POST /api/plans/import-playwright` → 1 case, `external_files_deleted=false`; desk50 HTML has `plan-pw-path` / `plan-import-pw-btn`; `desktop_app.py` opened.
- **Jira:** close-out **KAN-171** + **KAN-172**
- **Next:** **KAN-173** C9 search plans/cases/failures (test **KAN-174**)

### 2026-11-17 — KAN-169 — C7 tags, priority, smoke and regression
- **Agent/chat:** Cursor IDE Agent (Composer) — pick-up KAN-169
- **Done:** Cases keep priority + tags (smoke/regression first-class). Sequential tag run: `plans/run_by_tag.py`; suite_run stores id + tag used; untagged listed as `not_selected`. API `GET/POST /api/plans/{id}/run-by-tag`. Desktop Plans: tag/priority edit, Run by tag / Run smoke / Run regression. desk49.
- **Files:** `plans/run_by_tag.py`, `plans/store.py`, `plans/run_case.py`, `plans/__init__.py`, `main.py`, `ui/desktop/index.html`, `ui/desktop/desktop.js`, `desktop_app.py`, `tests/test_plan_run_by_tag.py` (+ desk49 cache-bust tests)
- **Verify:** `pytest tests/test_plan_run_by_tag.py tests/test_plan_run_case.py tests/test_desktop_app_menu.py tests/test_plan_edit.py tests/test_plan_traceability.py tests/test_plan_coverage_gaps.py tests/test_plan_acceptance_drift.py tests/test_nav_overlap.py tests/test_orb_hub.py tests/test_settings_hub.py tests/test_reports_library.py -q` (65 passed). Live `/ui/desktop/?v=desk49` has `plan-case-tags` + `plan-run-by-tag`; `desktop_app.py` opened.
- **Jira:** close-out **KAN-169** + **KAN-170**
- **Next:** **KAN-171** C8 import Playwright into suite (test **KAN-172**)

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
