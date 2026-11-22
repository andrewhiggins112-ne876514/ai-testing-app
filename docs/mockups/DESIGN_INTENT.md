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
| 2026-11-22 | **Suites + Plans inherit** FR-UI-11 grammar **accepted**. Suites: Sel·Status·Title·File·Last + detail (no section rail). Plans · Cases: replace `#plan-cases` dump with scan table; row fills detail; plan tabs stay FR-UI-9. Bridge order: Suites first, then Plans Cases. Theme/orb/home/App nav locked. Lab density / voice / FR-MAN-2 still deferred. | `docs/mockups/suites_plans_layout_inherit/` |
| 2026-11-22 | **Rest of App areas** inherit the same grammar. Settings and Suites looks stay the baseline (minor tweaks later). Plans · Cases stays **KAN-329** / **KAN-330**. Other Plans tabs: Coverage + Trace scans (no checkbox; Trace row opens the case); History A/B radio cells; Draft + Run compact forms. Reports: scan + detail, no rail, no section editor. Documents: Propose \| Uploads; Keep cell; Confirm/Decline off the row. Security: in-area rail; Include cell; masked status. Heal: detail Approve/Reject + **bulk approve** via Sel cells + toolbar (checkbox never means approve). Manual: session scan + compact start checks; Charter Frame and home untouched. Desktop + Sandboxes: scan + detail; TRACK3-LAB geometry still deferred. Every story ships with a strict linked test (markers, pytest path, no soft-pass). | `docs/mockups/secondary_areas_rest/` |
| 2026-11-22 | Designer CR on open Studio questions: (1) **History compare = A/B radio cells** — accepted. (2) **Heal bulk approve** — accepted (toolbar Approve selected after dedicated Sel; detail Approve/Reject remain; no checkbox-as-approve; no bulk reject). | `01-themed-plans-tabs.html` History; `01e-themed-heal.html` |

## Rejected / park

| Date | Idea | Why |
|------|------|-----|
| 2026-11-21 | Name lane “Layout Lab” | Collides with product FR-UI-8 / TRACK3-LAB |
| — | Pretty KPI / empty hero dashboards for Suites/Plans/Reports | Fails daily Test Engineer density |
| 2026-11-21 | KPI / card dashboard for Settings (and inherit) | Hides editable fields; fails density |
| 2026-11-21 | Tighter single-scroll Settings column | Still flat hierarchy; label remains whole-row hit; Suites/Plans inherit nothing |
| 2026-11-22 | Whole-card / checkbox-as-approve Heal, report KPI tiles, page-width `.check-row`, new App nav items per tab, Charter Frame / home restyle | Fails selection grammar, density, or a frozen surface. Toolbar bulk approve (Sel + confirm) is **accepted**, not rejected. See `secondary_areas_rest/03-rejected-options.html` |

## Creative backlog (not Active Build)

| Idea | Status | Notes |
|------|--------|-------|
| Secondary-area layout system (Settings → Suites → Plans → Reports → Heal → the rest) | **Designed + bridged 2026-11-22. Active Build stays KAN-329.** | Settings Done (KAN-324). Suites Done (KAN-327). Cases = KAN-329 / KAN-330. Then KAN-331 tabs, KAN-333 Reports, KAN-335 Documents, KAN-337 Security, KAN-339 Heal, KAN-341 Manual, KAN-343 Desktop, KAN-345 Sandboxes. TRACK3-LAB / voice / FR-MAN-2 still deferred. |

## Mockup index

| Topic | Path | Status |
|-------|------|--------|
| Nav / areas options (historical) | `docs/mockups/kan103_nav/` | Reference — nav locked; study density only |
| Orb styles | `docs/mockups/orb_styles.md` | Locked reference |
| Settings layout grammar (system template) | `docs/mockups/settings_layout_grammar/` | **Accepted 2026-11-21** — wire / themed / annotated / rejected |
| Suites + Plans FR-UI-11 inherit | `docs/mockups/suites_plans_layout_inherit/` | **Accepted 2026-11-22** — Suites Done; Cases is Active Build |
| Remaining App areas | `docs/mockups/secondary_areas_rest/` | **Accepted 2026-11-22** — wire / themed / annotated / rejected. Stories KAN-331–KAN-345 |
