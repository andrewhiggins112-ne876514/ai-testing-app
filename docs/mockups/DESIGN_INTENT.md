# Design Intent Log

Living continuity log for **Lane C — Design Studio**. Not product runtime.

Update after every accepted Studio verdict. No secrets, no live Settings captures with credentials.

## Locked (do not reopen without Designer CR)

| Surface | Status | Notes |
|---------|--------|-------|
| Theme tokens / Track 2 chrome | **Locked** | KAN-279 / KAN-295 / KAN-297 — reuse, don’t redo |
| Orb styles (classic + mystic/aether/neural) | **Locked** | Visual identity stays |
| Home / chat / clarify-before-act | **Locked** | Studio may annotate defects only; no restyle |
| App nav model (areas + Screen drawer) | **Locked** | Layout *inside* areas may change |

## Open mandate

**OPERATE (Council 2026-11-26)** — daily loop + open-trace; home-PC demo AUT. Theme/orb/home/App nav stay locked. **Loop-hit polish only** after OPERATE-1 (Plans Run disclosure, Manual idle split, light evidence affordance) — not a new full TRACK6 layout epic. Studio may mock those three touchpoints when Build asks.

**CR 2026-11-27 (Council agreed 2026-11-27; Designer pick 2026-11-27):** Readable **step-by-step run narrative** + **pass/fail evidence** in Case detail (FR-TEST-4/FR-PLAN-4). **Studio Slice-0 Accepted — Option A** (`01` smoke-pass, `02` intentional-fail, `03` honest empty). Build target **KAN-496** / test **KAN-497**. Vertical run story in the existing Case aside: status → plain-language steps → one captured page (or honest None captured) → Open Trace (external). Theme/orb/home/App nav locked. Do **not** absorb into OPERATE-3 (**KAN-379**). Keys: `docs/ops/CR_RUN_EVIDENCE_UX_KEYS.json`. Pack: `docs/mockups/run_evidence_ux/`.

**Research gate (2026-11-26):** Audit/Research modes must cite current enterprise QA UX (charts, Explorer-class Manual, plan readability) — `docs/ops/ENTERPRISE_GAP_RESEARCH.md`.

**GAP-CR (later):** Reports charts; Manual floating snip outside main window; Documents demo pack visuals. **Run-evidence deep view** = separate story (frames 05–07) — in Spec/Jira after Council; not KAN-496.

Active Build: **KAN-496** Option A (Studio pick locked). OPERATE-4 **KAN-381** Done. OPERATE-3 **KAN-379** Done (**desk134**). Lab TRACK3 / TRACE-DEEPEN / OPERATE-1..4 = baselines Done.

### Selection grammar (standing)

- Checkbox = dedicated hit target  
- Row click = open / navigate / focus  
- Ban whole-row toggle  

### Section chrome rule (standing — Studio+Council 2026-11-22)

- **Vertical rail** when an area has ≥3 real sections (Settings, Security)  
- **In-area tabs** when two jobs share one area (Plans FR-UI-9 tabs; Documents Propose | Uploads)  
- **No rail** for a single collection (Suites, Reports, Heal, Manual, Desktop, Sandboxes)  
- Do not stack a second rail beside existing tabs  

### Checkbox verb lexicon (standing)

| Verb | Meaning |
|------|---------|
| Sel | Multi-select for a toolbar action (Run selected, Approve selected) — never Approve/Reject by itself |
| Keep / Include | Include this row in a confirm write |
| Enabled | Plugin / target on |
| A / B (radio) | Compare slot (History) |

## Accepted decisions

| Date | Decision | Mockups / refs |
|------|----------|----------------|
| 2026-11-21 | Council ratifies Lane C Design Studio with binding gates | `docs/ops/DESIGN_STUDIO.md` |
| 2026-11-21 | **Settings layout grammar** is the system template for secondary App areas | `docs/mockups/settings_layout_grammar/` |
| 2026-11-22 | **Suites + Plans inherit** FR-UI-11 grammar **accepted** | `docs/mockups/suites_plans_layout_inherit/` |
| 2026-11-22 | **TRACK4-LAYOUT complete** through Sandboxes Lab **KAN-345** | `docs/mockups/secondary_areas_rest/` |
| 2026-11-22 | **Studio + Council + Creative Architect review** — nothing valuable removed; docs catch-up applied | Review chat 2026-11-22 |
| 2026-11-22 | **Layout enhancement pack Accepted** (Designer). All secondary areas. Phase 1 = empty/keyboard/scroll + Plans/Docs/Heal/Lab craft. Phase 2 = evidence-first detail (KAN-354). Epic **KAN-347**. Stories **KAN-348/350/352/354** + tests **349/351/353/355**. Spec FR-UI-11 enhancement clause landed. After TRACK5 → TRACK3-LAB → real Playwright trace deepen. Park: voice, FR-MAN-2, CI, H3 share, bulk Heal Reject, KPI heroes. | `docs/mockups/layout_enhancement_pack/` |
| 2026-11-23 | **TRACK3-LAB Bridge seeded** (Council+Designer). Epic **KAN-359**. Active **KAN-360**. Lab wires §8 in `TRACK3_AREA_WIRES.md`. Stories **362/364/366** after Story 1. | `docs/design/TRACK3_AREA_WIRES.md` §8 |
| 2026-11-23 | **Lab wires Accepted** (Designer `Accept Lab wires`). KAN-360 chrome-budget markers unblocked. | `docs/design/TRACK3_AREA_WIRES.md` §8 |
| 2026-11-27 | **Run evidence Option A Accepted** (Designer). Frames 01–03 = Build **KAN-496**. Aside-only vertical story; no fake green; Open Trace external. | `docs/mockups/run_evidence_ux/` |
| 2026-11-27 | **Council accept + deep view Story** (Designer: thumb also expands). **KAN-498**/499 separate from 496. Frames 05–07. No Trace embed / hosted viewer. | `docs/mockups/run_evidence_ux/` 05–07 |
| 2026-11-28 | **Charter G + side tray Accepted**. Look **4 Compact rail**. Tray hide/show via tray-layout icon (IDE secondary-sidebar glyph). Remember last side; Assist/Mist on tray; Pause = own icon. Do **not** steal Active — code next after current Active finishes. | `docs/mockups/charter_outside_window/` + `looks/look4-*.html` |
| 2026-11-28 | **Under-ring / south bar Rejected** as Look 4 (Council KAN-525). KAN-524 480×88 under-ring was a reliability experiment only — not Accepted design. Side rail remains the look; host = native TOOLWINDOW side chrome (not ~48px WebView2 rail). | Council verdict; Spec FR-MAN-1 CR lock |

## Rejected / park

| Date | Idea | Why |
|------|------|-----|
| 2026-11-21 | Name lane “Layout Lab” | Collides with product FR-UI-8 / TRACK3-LAB |
| — | Pretty KPI / empty hero dashboards for Suites/Plans/Reports | Fails daily Test Engineer density |
| 2026-11-21 | KPI / card dashboard for Settings (and inherit) | Hides editable fields; fails density |
| 2026-11-21 | Tighter single-scroll Settings column | Still flat hierarchy; label remains whole-row hit |
| 2026-11-22 | Heal bulk Reject | Reject stays focused-detail only |
| 2026-11-22 | Start TRACK3-LAB / voice / FR-MAN-2 from layout review | Explicitly deferred until after TRACK5 (Lab) or parked (voice / FR-MAN-2) |
| 2026-11-22 | Second filter bar, evidence gallery, new App nav item, fake Trace control | `layout_enhancement_pack/03-rejected.html` + Council |
| 2026-11-27 | Full-page filmstrip + **embedded** Trace Viewer **as the Cases screen** (and hosted trace.playwright.dev) | `run_evidence_ux/04-rejected-page-gallery.html` — must not replace the Cases list or absorb OPERATE-1 into the shell. Deep view = frames **05–07** as a **separate story**, not this rejected primary. |

## Creative backlog (not Active Build)

| Idea | Status | Notes |
|------|--------|-------|
| TRACK4 grammar (Settings → Sandboxes) | **Done** | KAN-324…KAN-345 |
| TRACK5 Phase 1 shared craft | Done **KAN-348** | Quiet empty, keyboard, one scroll — all areas |
| TRACK5 Plans compact + sections | Done **KAN-350** | desk120 |
| TRACK5 Docs / Heal / Lab disclosure | Done **KAN-352** | desk123 |
| TRACK5 Phase 2 evidence-first | **Done KAN-354** (**desk125**) | TRACK5 complete |
| TRACK3-LAB Lab density | **Done** epic **KAN-359** | human A–E **desk131** |
| Real Playwright trace deepen | **Done KAN-372** (**desk132**) | Real `trace.zip` on failure |
| KAN-81/82 voice; FR-MAN-2 | **Parked** | Mic / DPIA |
| Run-evidence **deep view** (05–07) | **Story KAN-498** / test **KAN-499** | Council accepted 2026-11-27. Doors: **More evidence** + **thumb expand**. Not KAN-496 AC. No new App nav; no Trace embed; Cases list stays. Build after 496 unless elevated. |
| Charter outside-window options A–H | Historical | Superseded by G+tray Accepted |
| Charter **G + side tray** | **Shipped 2026-11-28** (**KAN-512**, desk150) | Look **4 Compact rail** + collapsible tray (tray icon toggle). |

## Mockup index

| Topic | Path | Status |
|-------|------|--------|
| Nav / areas options (historical) | `docs/mockups/kan103_nav/` | Reference — nav locked; study density only |
| Orb styles | `docs/mockups/orb_styles.md` | Locked reference |
| Settings layout grammar (system template) | `docs/mockups/settings_layout_grammar/` | **Accepted 2026-11-21** |
| Suites + Plans FR-UI-11 inherit | `docs/mockups/suites_plans_layout_inherit/` | **Accepted / shipped** |
| Rest secondary areas (Plans tabs → Sandboxes) | `docs/mockups/secondary_areas_rest/` | **Accepted / shipped** |
| Layout enhancement pack (all secondary areas) | `docs/mockups/layout_enhancement_pack/` | **Accepted 2026-11-22** — Build via KAN-348…354 |
| Run evidence UX (Case aside Option A) | `docs/mockups/run_evidence_ux/` 01–03 | **Accepted 2026-11-27** — Build **KAN-496** |
| Run evidence deep view | `docs/mockups/run_evidence_ux/` 05–07 | **KAN-498**/499 — Council Accepted; thumb also expands; `04` = rejected primary only |
| Charter outside-window (options A–H) | `docs/mockups/charter_outside_window/index.html` | Historical options gallery |
| Charter **G + side tray** (Accepted) | `docs/mockups/charter_outside_window/looks/look4-picker.html` | **Accepted 2026-11-28.** Look 4 Compact rail + tray icon collapse. |

## Accepted — Charter G + side tray (2026-11-28)

**Status: Accepted (structure + look).** Spec CR lock 2026-11-28 (Council KAN-525). Build Active = **KAN-525** host restore; then **KAN-510**/511.

| Decision | Choice |
|----------|--------|
| Route | Option G: Manual steps back to session chip; only overlay open |
| Look | **4 — Compact rail** (dense ~36–40px VS Code–tight chrome; thin cyan hairline; minimal glow) |
| Chrome | One hollow OS capture shell (click-through hole) + icon tray glued to a side |
| Tray host | **Native TOOLWINDOW side chrome on the ring thread** (Council 2026-11-28). ~48px second WebView2 rail rejected for paint/ghost class. |
| Tray collapse | **Hide/show tray** via tray-layout icon (rounded rect + right vertical strip — IDE secondary-sidebar glyph). Collapsed = hollow frame only + that toggle on the frame edge. Expanded = full icon stack. Remember collapsed/expanded with last side. |
| Tray side | **Remember last side** (default east; flip west at screen edge / user preference). **Side only** — see Rejected under-ring. |
| Assist / Mist | **On the tray** (icon toggles, default off) |
| Pause | **Own icon** on the tray (not status-slot reuse) |
| Active Build | **KAN-525** (native side tray + Resume/End→Start); then residuals **KAN-510**/511 |
| Bugs KAN-510 / 511 | **Paused** until KAN-525/526 human paths pass |

### Rejected — under-ring / south reliability bar (2026-11-28)

| Decision | Choice |
|----------|--------|
| Under-ring 480×88 horizontal verb bar (KAN-524 desk155) | **Rejected** as Look 4 and as an Acceptable degraded mode. Reliability must change the **host**, not relocate chrome under the capture hole. |
| Taskbar-only Charter Frame + dead click | **Fail** — not a restore path. Prefer no taskbar entry; Manual chip Restore is the backup. |
| Manual session chip as primary chrome | **Rejected** — backup only. |

**Frozen:** theme tokens, orb, home/chat, App nav. **OOS for KAN-525 slice:** outward note-sheet HWND, FR-MAN-2, voice, keylog/clipboard/mic, continuous video, Gradio OS float, dual WebView fallback, SetWindowRgn.

Research: `docs/mockups/charter_outside_window/RESEARCH_G_TRAY.md`. Look frames: `looks/look4-expanded.html`, `looks/look4-collapsed.html`.
