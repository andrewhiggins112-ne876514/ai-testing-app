# Work log — AI Testing Application

**Path:** `D:\Projects\ai_testing_app\docs\ops\WORK_LOG.md`  
**Rule:** Every coding/agent slice **must** append an entry here when the slice finishes (or is paused). Also add a **Jira comment** on the active story with the same summary.

## Active slice (agents: read this first)

| Field | Value |
|-------|--------|
| **Status** | ready |
| **Jira story** | KAN-75 — Heal proposal review UI (approve or reject pending heals) |
| **Epic** | KAN-23 (Self-healing) |
| **Roadmap ID** | (FR-HEAL-2 / FR-HEAL-5) |
| **Spec** | `docs/FUNCTIONAL_SPEC.md` FR-HEAL-2 / FR-HEAL-5 |
| **Next action** | Implement KAN-75; test Task KAN-76 |

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
