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

**CR 2026-11-27 (Council agreed 2026-11-27):** Readable **step-by-step run narrative** + **pass/fail evidence gallery** in Case detail (FR-TEST-4/FR-PLAN-4). **Studio Slice-0 required** before Build Slice-1 — thin pack under `docs/mockups/run_evidence_ux/` (before, smoke-pass, intentional-fail, honest empty, rejected page-gallery). Preferred: Option A vertical run story in existing Case aside (status → steps → thumbs → Open Trace). Theme/orb/home/App nav locked. Do **not** absorb into OPERATE-3 (**KAN-379**). Keys: `docs/ops/CR_RUN_EVIDENCE_UX_KEYS.json`.

**Research gate (2026-11-26):** Audit/Research modes must cite current enterprise QA UX (charts, Explorer-class Manual, plan readability) — `docs/ops/ENTERPRISE_GAP_RESEARCH.md`.

**GAP-CR (later):** Reports charts; Manual floating snip outside main window; Documents demo pack visuals; **run steps + evidence gallery** (CR 2026-11-27).

Active Build: **KAN-496** after Studio Slice-0 (see `docs/ops/CR_RUN_EVIDENCE_UX_KEYS.json`). OPERATE-4 **KAN-381** Done. OPERATE-3 **KAN-379** Done (**desk134**). Lab TRACK3 / TRACE-DEEPEN / OPERATE-1..4 = baselines Done.

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

## Mockup index

| Topic | Path | Status |
|-------|------|--------|
| Nav / areas options (historical) | `docs/mockups/kan103_nav/` | Reference — nav locked; study density only |
| Orb styles | `docs/mockups/orb_styles.md` | Locked reference |
| Settings layout grammar (system template) | `docs/mockups/settings_layout_grammar/` | **Accepted 2026-11-21** |
| Suites + Plans FR-UI-11 inherit | `docs/mockups/suites_plans_layout_inherit/` | **Accepted / shipped** |
| Rest secondary areas (Plans tabs → Sandboxes) | `docs/mockups/secondary_areas_rest/` | **Accepted / shipped** |
| Layout enhancement pack (all secondary areas) | `docs/mockups/layout_enhancement_pack/` | **Accepted 2026-11-22** — Build via KAN-348…354 |
