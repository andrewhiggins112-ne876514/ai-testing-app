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

**Secondary App areas layout rework** — **TRACK4-LAYOUT Done** (Settings → Sandboxes). Remaining work is **enhancement polish inside the grammar** (compact residual booleans, scroll ownership, quiet empty/keyboard craft) — not a new skin, and **not** Lab density / voice / FR-MAN-2 (those stay deferred until Active Build is set).

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
| 2026-11-21 | **Settings layout grammar** is the system template for secondary App areas: in-area **section rail** + **compact scan table** + **detail pane**. Checkbox = dedicated ~28px cell (stopPropagation); row click = focus/open; destructive controls live in the detail behind confirm — never on list-row chrome. Theme/orb/home/App nav stay locked. Audit: Settings + Suites + Plans (P0 Plans text-dump; P1 Suites whole-row select + Settings `.check-row`). CU skipped — unsafe for live Settings. Spec: **FR-UI-11**; Build Story **KAN-324** / test **KAN-325** (Settings only). | `docs/mockups/settings_layout_grammar/` |
| 2026-11-22 | **Suites + Plans inherit** FR-UI-11 grammar **accepted**. Suites: Sel·Status·Title·File·Last + detail (no section rail). Plans · Cases: replace `#plan-cases` dump with scan table; row fills detail; plan tabs stay FR-UI-9. Theme/orb/home/App nav locked. Lab density / voice / FR-MAN-2 still deferred. | `docs/mockups/suites_plans_layout_inherit/` |
| 2026-11-22 | **TRACK4-LAYOUT complete** — Reports, Documents, Security, Heal, Manual, Desktop Lab, Sandboxes Lab inherited FR-UI-11 (Stories **KAN-333…KAN-345**, desk112–desk118). History A/B radio cells accepted. Heal: no bulk Reject (detail-only). Theme/orb/home/App nav untouched. | `docs/mockups/secondary_areas_rest/` |
| 2026-11-22 | **Studio + Council + Creative Architect review** — nothing valuable removed; capabilities moved into scan+detail. Docs catch-up applied (this log + FR-UI-11 Inheritance prose). Active Build stays deferred. Enhancement backlog parked (Plans compact booleans, detail sections, one-scroll-per-pane, keyboard scan, quiet empty states, evidence-first detail later). Rejected again: KPI/card dashboards, bulk Heal Reject unless Designer overrides. | Review chat 2026-11-22 |

## Rejected / park

| Date | Idea | Why |
|------|------|-----|
| 2026-11-21 | Name lane “Layout Lab” | Collides with product FR-UI-8 / TRACK3-LAB |
| — | Pretty KPI / empty hero dashboards for Suites/Plans/Reports | Fails daily Test Engineer density |
| 2026-11-21 | KPI / card dashboard for Settings (and inherit) | Hides editable fields; fails density |
| 2026-11-21 | Tighter single-scroll Settings column | Still flat hierarchy; label remains whole-row hit; Suites/Plans inherit nothing |
| 2026-11-22 | Heal bulk Reject | Accepted rest mockup + Security: Reject stays focused-detail only |
| 2026-11-22 | Start TRACK3-LAB / voice / FR-MAN-2 from layout review | Explicitly deferred; not Active |

## Creative backlog (not Active Build)

| Idea | Status | Notes |
|------|--------|-------|
| Secondary-area layout system (Settings → Sandboxes) | **TRACK4 Done** (KAN-324…KAN-345 / desk118) | Grammar shipped. Do not treat Suites/Plans as “still bridging.” |
| Plans residual compact booleans | Proposed | Show archived / Enabled / Archived / Pause on fail → same compact pattern as Manual/Security |
| Plans case detail sections | Proposed | Keep all fields; group Edit / Run / Quarantine / Known issue; pin Save + Run |
| One scroll per pane + sticky thead in scan | Proposed | Scan and detail scroll separately; no third `.area-work` scroll on the split |
| Quiet empty + “Select a row” + keyboard scan | Proposed | Structure pack; Spec clause when Designer accepts Bridge |
| Evidence-first detail slot | Parked (later CR) | After structure pack |
| TRACK3-LAB Lab density; KAN-81/82 voice; FR-MAN-2 | **Deferred** | Not Active until human sets Active slice |

## Mockup index

| Topic | Path | Status |
|-------|------|--------|
| Nav / areas options (historical) | `docs/mockups/kan103_nav/` | Reference — nav locked; study density only |
| Orb styles | `docs/mockups/orb_styles.md` | Locked reference |
| Settings layout grammar (system template) | `docs/mockups/settings_layout_grammar/` | **Accepted 2026-11-21** — wire / themed / annotated / rejected |
| Suites + Plans FR-UI-11 inherit | `docs/mockups/suites_plans_layout_inherit/` | **Accepted 2026-11-22** — shipped KAN-327…KAN-331 |
| Rest secondary areas (Plans tabs → Sandboxes) | `docs/mockups/secondary_areas_rest/` | **Accepted / shipped** — TRACK4 Done through KAN-345 |
