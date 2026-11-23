# Track 3 — Area wires pack (Primary)

**FR:** FR-UI-10 · **Roadmap:** TRACK3-UX  
**Story:** KAN-308 (test KAN-309)  
**Status:** **Accepted** by Designer (2026-11-18 Build) — reply `Accept Track 3 wires`. Geometry Build (**KAN-310…320**) is unblocked.  
**Density source:** `docs/design/ENTERPRISE_LAYOUT_NOTE.md` (accepted; tokens shipped KAN-297 — geometry still open).

## Designer decisions (Council 2026-11-18)

1. Hard accept gate on this pack before geometry code — **yes**.
2. Track 3 scope = **Primary** areas only; Lab density = follow-on epic — **yes**.
3. Verify density in **all** layout modes A–E — **yes**.

## In scope (Primary)

| Area | Wire depth for Slice-0 |
|------|------------------------|
| Plans · Cases | Full (extends ENTERPRISE_LAYOUT_NOTE §6) |
| Manual (idle / review + Confirm dock) | Full |
| Reports (library) | Full |
| Documents | Full |
| Settings (App category hub) | Full |
| Security (level + credentials chrome) | Full outline (ships with Settings alignment story) |

## Out of scope (follow-on Lab epic — TRACK3-LAB)

Heal review, Desktop plugin area, Suites, Sandboxes — **outline only** below; **no** geometry stories in Track 3 Primary Build.

## Out of scope (forever for Track 3)

Orb home rewrite; tall App rail; top app tab bar; purple SaaS; CDN fonts; Gradio-first; voice; FR-MAN-2; token-only “layout Done”.

## Shared chrome budget (all Primary wires)

| Band | Max | Contents |
|------|-----|----------|
| Surface bar | ~40px | Title + Back (shared `#area-surface` chrome) |
| One toolbar | ~56px | Picker / search / filter / primary actions / one-line status |
| Optional section tabs | ~36px | Plans tabs only in common case |
| Confirm dock (Manual, when shown) | ~48px | **Below** `.area-work` — always fully visible |
| **Stack above work** | ≤ **~120px** | Common case at ~1280×720 |

Rules:

- Chrome lives **outside** `.area-work` (`flex-shrink: 0`). Work scrolls; chrome does not.
- Filter/search live in the **one** toolbar — **no** second filter strip.
- After scaffold story (**KAN-310**): class/marker names must **not** say `sticky` (rename alone without geometry fails).
- Accents stay orb-driven (FR-UI-3). Fonts stay local Segoe stack.
- Compact `▦` App menu only — no tall rail.

---

## 1. Plans · Cases (default landing)

Extends `ENTERPRISE_LAYOUT_NOTE.md` §6. Cases is the default tab (not Draft/Schedule). One **Add case ▾** — no button farm. Lab knobs stay under Settings / Lab / collapsed Run setup.

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  PLANS                                              │  ← surface bar (~40px)
├─────────────────────────────────────────────────────────┤
│ Plan ▾ [Open] [Refresh]   🔍 search……    status: ready │  ← toolbar (≤56px)
├─────────────────────────────────────────────────────────┤
│ [Draft] [Cases*] [Coverage] [Trace] [History] [Run]     │  ← tabs (≤36px)
├─────────────────────────────────────────────────────────┤
│  Add case ▾                                             │  ← in work header
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  case row …                                        │  │
│  │  case row …                                        │  │
│  │  …                                                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

\*Cases selected. Other tabs keep the same chrome stack; only `.area-work` content changes.

**Geometry story:** KAN-312 (after Accept + shared scaffold).

---

## 2. Manual — idle (Start + library)

Toolbar: Clear linked context / Open Plans / Refresh library + loop stage + status (one band). Session library + Start form scroll in `.area-work`. No Confirm dock until a proposal exists. Charter Frame is a free-region overlay (not area chrome).

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  MANUAL                                             │  ← surface bar (~40px)
├─────────────────────────────────────────────────────────┤
│ [Clear ctx] [Open Plans] [Refresh lib]                  │  ← toolbar (≤56px)
│ Loop: idle — enter a charter to Start    status: Ready  │     (status may wrap <900px)
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  Session library (this level only)                 │  │
│  │  · ended draft … [Open review]                     │  │
│  │  ── Start session ──                               │  │
│  │  Charter [textarea]                                │  │
│  │  Link Jira / plan / case fields                    │  │
│  │  [Start session]                                   │  │
│  │  ▸ About Manual capture (Advanced)                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Manual — review + Confirm dock

Same toolbar budget. Propose actions live **inside** `.area-work`. Confirm / Cancel sit on a **non-scrolling dock below** `.area-work` (~48px) — never inside the scrollport; never covered by chrome.

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  MANUAL                                             │  ← ~40px
├─────────────────────────────────────────────────────────┤
│ [Clear ctx] [Open Plans] [Refresh lib]  Loop: review … │  ← ≤56px
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  Review summary / notes / stills                   │  │
│  │  Failure class ▾   ☐ File as Bug                   │  │
│  │  [Propose bug] [Comment] [Local note] [Steps]      │  │
│  │  proposal preview …                                │  │
│  └────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ Proposal ready — Confirm writes; Cancel writes nothing  │  ← confirm dock (~48px)
│              [Confirm]  [Cancel proposal]               │     outside .area-work
└─────────────────────────────────────────────────────────┘
```

**Geometry story:** KAN-314. FR-MAN-2 live circles remain parked.

---

## 4. Reports (library)

One toolbar: Refresh library / Report settings deep-link + status. Primary = saved-report list + detail. Export run/pack under Advanced (not a second toolbar). Section toggles stay in Settings → Report (FR-REP-4 / FR-SET-4).

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  REPORTS                                            │  ← ~40px
├─────────────────────────────────────────────────────────┤
│ [Refresh library] [Report settings]      status: Ready  │  ← ≤56px (search/filter here if added)
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  Saved reports list                                │  │
│  │  · report …                                        │  │
│  │  ── Detail ──                                      │  │
│  │  markdown / screenshot / JSON                      │  │
│  │  ▸ Advanced (export run / pack)                    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Geometry story:** KAN-316 (with Documents).

---

## 5. Documents

One toolbar: Parse & propose / Refresh uploads + status. Primary = paste/upload + proposal/diff + uploads list. Help/configure under Advanced.

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  DOCUMENTS                                          │  ← ~40px
├─────────────────────────────────────────────────────────┤
│ [Parse & propose] [Refresh uploads]      status: Ready  │  ← ≤56px
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  Spec text [textarea]                              │  │
│  │  Proposal / diff (when present)                    │  │
│  │  [Confirm selected] [Decline]                      │  │
│  │  Uploads list                                      │  │
│  │  ▸ Advanced & help                                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Geometry story:** KAN-316.

---

## 6. Settings (App category hub)

Surface bar + **category switch as the one toolbar band** (App | Report — later categories as needed). Form bodies scroll in `.area-work`. App Settings holds connectors, Jira URL/project, Ollama model, framework, Playwright headed/headless, **App area layout** (A–E), credential *status* (secrets never render). Orb settings stay in Screen drawer (FR-UI-3 / FR-SET-3).

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  SETTINGS                                           │  ← ~40px
├─────────────────────────────────────────────────────────┤
│ [App*] [Report]                           status: Ready │  ← category toolbar ≤56px
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  App: connectors · model · framework · layout A–E  │  │
│  │  credential status (no secrets)                    │  │
│  │  — or —                                            │  │
│  │  Report: section include/exclude + Save            │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

\*App selected. No forever-scroll of every area’s toggles into one panel (FR-SET-3).

**Geometry story:** KAN-318 (with Security).

---

## 7. Security (level + privacy chrome)

Same outside-scrollport pattern. **Level select + Switch/Confirm** stay in the non-scrolling band (or first band of chrome) — never collapsed into Advanced. Privacy wipe checkboxes + audit/backup lists scroll in `.area-work`. OFFICIAL / SECRET stores never merge.

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  SECURITY                                           │  ← ~40px
├─────────────────────────────────────────────────────────┤
│ Level ▾  [Switch level] [Confirm]   profile: …  Ready   │  ← ≤56px — always visible
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  Privacy & local data (checkboxes + Delete…)       │  │
│  │  Local side-effects audit                          │  │
│  │  Export & evidence redaction status                │  │
│  │  Backup & restore                                  │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Geometry story:** KAN-318. Full Lab-tool density for Heal/Desktop/Suites/Sandboxes stays TRACK3-LAB.

---

## 8. Lab tools — density wires (TRACK3-LAB follow-on)

**Epic:** TRACK3-LAB (FR-UI-10 Lab follow-on) · **Bridge:** Council+Designer 2026-11-23  
**Status:** **Awaiting Designer Accept** — reply `Accept Lab wires` before Lab geometry HTML/CSS (Stories 2–4). Story 1 may land chrome-budget **markers** only after Accept.  
**Reuse:** Primary shared chrome budget (§ Shared chrome budget above). **Do not** redo KAN-310 scaffold / sticky renames — Lab toolbars already use `.area-chrome-toolbar`.  
**Locked:** Theme / orb / home / App nav; FR-UI-11 scan+detail grammar; TRACK5 craft (quiet empty, Select a row, keyboard scan, one scroll per pane, Lab Advanced closed by default, Heal no bulk Reject, evidence-first Trace “not hooked”).  
**Out:** Security (Primary **KAN-318**); voice; FR-MAN-2; real Playwright trace deepen; KPI heroes; auto-apply heal; silent sandbox remove.

### Lab shared stack (all four)

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  HEAL | DESKTOP | SUITES | SANDBOXES                │  ← ~40px surface
├─────────────────────────────────────────────────────────┤
│  one toolbar: actions + ONE status line                 │  ← ≤56px
├─────────────────────────────────────────────────────────┤
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  scan + detail (one scroll per pane)              │  │
│  │  Advanced / Policy under work (closed by default) │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
Stack above work ≤ ~120px. No intro <h3> / About above the toolbar.
No second filter strip. No sticky-named classes/markers.
```

### 8a. Suites (highest pain — Done gate for Suites+Sandboxes story)

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  SUITES                                             │
├─────────────────────────────────────────────────────────┤
│ Path […………]  [Discover] [List] [Run sel] [Run all]  Ready│  ← one band; path+actions+ONE status
├─────────────────────────────────────────────────────────┤
│  .area-work: suite scan | detail (FR-UI-11 + TRACK5)   │
│  Advanced (closed): Import / save path                 │
└─────────────────────────────────────────────────────────┘
```

- Path + Discover / List / Run selected / Run all + **one** status line in the **single** toolbar (merge “Saved path” into that status — not a second chrome row).
- Import / save path stays **Advanced** (TRACK5).
- First suite row visible without scrolling chrome away.

### 8b. Sandboxes

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  SANDBOXES                                          │
├─────────────────────────────────────────────────────────┤
│ ☑ Enable   [Save plugin]  Action ▾ [Orchestrate]  Ready │  ← compact; ≤56px
├─────────────────────────────────────────────────────────┤
│  .area-work: scan Id·Label·URL·Ready | detail           │
│  Remove… → Confirm remove in detail (never silent)      │
│  Advanced (closed): Help only                           │
└─────────────────────────────────────────────────────────┘
```

### 8c. Heal review

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  HEAL                                               │
├─────────────────────────────────────────────────────────┤
│ Filter ▾  [Refresh]  [Approve selected (N)]*   Ready    │  ← *bulk only when shown
├─────────────────────────────────────────────────────────┤
│  .area-work: scan | detail (diff + Approve/Reject)      │
│  Approve/Reject on focused detail — fully visible       │
│  Bulk Approve still confirm + “files not written”       │
│  No bulk Reject. Policy & help under work (Advanced)    │
└─────────────────────────────────────────────────────────┘
```

### 8d. Desktop Lab

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  DESKTOP                                            │
├─────────────────────────────────────────────────────────┤
│ [Run smoke] [Run demo steps]                    Ready   │  ← thin band
├─────────────────────────────────────────────────────────┤
│  .area-work: single-target scan | Plugin detail (Save)  │
│  Advanced (closed): secondary fields                    │
└─────────────────────────────────────────────────────────┘
```

### Lab Accept checklist

- [ ] Suites wire signed (path+actions+one status; Import in Advanced)
- [ ] Sandboxes wire signed (compact Enable/Save/Action; Remove confirm in detail)
- [ ] Heal wire signed (one toolbar; Approve/Reject visible on focus; no bulk Reject / no auto-apply)
- [ ] Desktop wire signed (smoke/demo + status; Save in detail)
- [ ] Shared ≤~120px stack + no intro above toolbar acknowledged
- [ ] A–E Lab occlusion story remains last (markers + CU/human; never soft-pass “opened Lab”)
- [ ] TRACK4/5 craft locked; theme/orb/home/App nav locked

**Designer Accept phrase:** `Accept Lab wires`

### Lab geometry story map (after Accept)

| After Accept | Focus |
|--------------|--------|
| Story 1 | Chrome-budget markers on four Lab areas (no KAN-310 redo) |
| Story 2 | Suites + Sandboxes Lab density (Suites = Done gate) |
| Story 3 | Heal + Desktop Lab density |
| Story 4 | Lab occlusion verify A–E (Lab areas only) |

Primary Track 3 Build **must not** reopen these Lab geometry stories under Done epic **KAN-307**.

---

## 9. A–E verify contract (FR-UI-7)

Density and occlusion must hold in **every** App area layout mode:

| Mode | Key | Wire implication |
|------|-----|------------------|
| A | `overlay` | Full-bleed area; chrome budget vs dimmed home |
| B | `stage` | Area stage + orb pip — chrome still ≤~120px above work |
| C | `orb_hub` | After spoke → overlay; same chrome stack |
| D | `split` | Docked panel; work list still owns remaining height |
| E | `floating` | Movable window; Confirm dock still fully visible |

**Per-area checklist** (run at ~1280×720 on `desktop_app.py`):

1. Surface title + Back visible; Esc/Back returns to orb home.
2. One toolbar (+ Plans tabs if any) fully visible and clickable — not under title bar / peer panel.
3. First work row / primary field visible without scrolling chrome away.
4. Scroll `.area-work` — chrome bands do not slide over inputs.
5. Manual with proposals: Confirm + Cancel fully visible and clickable in **every** mode A–E.
6. Settings/Security: level / credential-status affordances stay readable; stores unmixed.
7. Compact `▦` only — no tall rail; no top app tab bar.

**Verify policy:** pytest / HTML markers first; Computer Use (or numbered human-hands) for clickability — never soft-pass “opened orb home.” Document CU skipped/flake honestly.

**Occlusion story:** KAN-320.

**KAN-320 status (desk105):** pytest encodes this contract (`tests/test_occlusion_verify_ae.py`, marker `data-occlusion-verify-ae`). Clickability across A–E still requires CU or numbered human confirm — never soft-pass “opened orb home.”

---

## 10. Geometry story map (blocked until Accept)

| After Accept | Story | Focus |
|--------------|-------|--------|
| 1 | KAN-310 | Shared chrome scaffold + retire `*-sticky-*` names |
| 2 | KAN-312 | Plans · Cases geometry from this wire |
| 3 | KAN-314 | Manual density + Confirm dock |
| 4 | KAN-316 | Reports + Documents density |
| 5 | KAN-318 | Settings + Security area-work alignment |
| 6 | KAN-320 | Occlusion verify Primary across A–E |

---

## Accept checklist

- [x] Plans · Cases wire signed  
- [x] Manual idle + review/Confirm wire signed  
- [x] Reports library wire signed  
- [x] Documents wire signed  
- [x] Settings + Security chrome outline signed  
- [x] A–E verify contract acknowledged  
- [x] Lab marked follow-on (not Track 3 Primary Build)  

**Accepted:** Designer `Accept Track 3 wires` (2026-11-18). Next Build: **KAN-310** shared chrome scaffold (then **KAN-312…320**). No HTML/CSS geometry was allowed before this Accept.
