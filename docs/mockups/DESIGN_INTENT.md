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

**Secondary App areas layout rework** — replace undifferentiated row lists and whole-row checkbox hit targets with intentional layout grammar (sections, master–detail, compact tables, dedicated selection controls). Density for power users; no pretty-empty dashboards.

### Selection grammar (standing)

- Checkbox = dedicated hit target  
- Row click = open / navigate / focus  
- Ban whole-row toggle  

## Accepted decisions

| Date | Decision | Mockups / refs |
|------|----------|----------------|
| 2026-11-21 | Council ratifies Lane C Design Studio with binding gates | `docs/ops/DESIGN_STUDIO.md` |
| 2026-11-21 | **Settings layout grammar** is the system template for secondary App areas: in-area **section rail** + **compact scan table** + **detail pane**. Checkbox = dedicated ~28px cell (stopPropagation); row click = focus/open; destructive controls live in the detail behind confirm — never on list-row chrome. Theme/orb/home/App nav stay locked. Audit: Settings + Suites + Plans (P0 Plans text-dump; P1 Suites whole-row select + Settings `.check-row`). CU skipped — unsafe for live Settings. Spec: **FR-UI-11**; Build Story **KAN-324** / test **KAN-325** (Settings only). Suites/Plans inheritance needs follow-on stories. | `docs/mockups/settings_layout_grammar/` |

## Rejected / park

| Date | Idea | Why |
|------|------|-----|
| 2026-11-21 | Name lane “Layout Lab” | Collides with product FR-UI-8 / TRACK3-LAB |
| — | Pretty KPI / empty hero dashboards for Suites/Plans/Reports | Fails daily Test Engineer density |
| 2026-11-21 | KPI / card dashboard for Settings (and inherit) | Hides editable fields; fails density |
| 2026-11-21 | Tighter single-scroll Settings column | Still flat hierarchy; label remains whole-row hit; Suites/Plans inherit nothing |

## Creative backlog (not Active Build)

| Idea | Status | Notes |
|------|--------|-------|
| Secondary-area layout system (Settings → Suites → Plans → Reports → Heal) | **Accepted grammar — Settings mockups Done; Build Settings first** | Inherit: Suites (Status·Title·File·Last + multi-select checkbox column); Plans (replace `#plan-cases` dump with scan table; row fills detail). Security `.check-row` same hit-target fix, own area. Heal/Reports contrasted only. |

## Mockup index

| Topic | Path | Status |
|-------|------|--------|
| Nav / areas options (historical) | `docs/mockups/kan103_nav/` | Reference — nav locked; study density only |
| Orb styles | `docs/mockups/orb_styles.md` | Locked reference |
| Settings layout grammar (system template) | `docs/mockups/settings_layout_grammar/` | **Accepted 2026-11-21** — wire / themed / annotated / rejected |
