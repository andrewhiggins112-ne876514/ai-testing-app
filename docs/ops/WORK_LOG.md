# Work log — AI Testing Application

**Path:** `D:\Projects\ai_testing_app\docs\ops\WORK_LOG.md`  
**Rule:** Every coding/agent slice **must** append an entry here when the slice finishes (or is paused). Also add a **Jira comment** on the active story with the same summary.

## Active slice (agents: read this first)

| Field | Value |
|-------|--------|
| **Status** | ready |
| **Jira story** | **KAN-85** — Generate Playwright steps from Jira AC |
| **Start task** | **KAN-86** (`test`, Relates → KAN-85) |
| **Epic** | (TEST) |
| **Roadmap ID** | FR-TEST-1 gap |
| **Spec** | `docs/FUNCTIONAL_SPEC.md` FR-TEST-1 |
| **Git** | `main` |
| **Test ticket** | **KAN-86** |
| **Shipped** | **KAN-83** / **KAN-84** Done (headed/headless, desk26) |
| **Deferred** | **KAN-81** / **KAN-82** voice — until mic connected |

When the user says **“pick up where we left off”** / **“continue”**: read this Active slice table, open the Jira story description, then start coding that story immediately (no long rediscovery).

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
