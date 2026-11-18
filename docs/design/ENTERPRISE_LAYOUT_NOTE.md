# Enterprise layout research note (Track 2)

**Story:** KAN-295 (test KAN-296) · **FR:** FR-UI-9, FR-UI-7 · **Roadmap:** TRACK2-UX  
**Status:** **Accepted** by Designer (2026-11-18 Council) — tokens shipped as **KAN-297** (desk99).  
**Scope:** Docs only for KAN-295. Not a component library. CSS/token implement is **KAN-297** (Done).  
**Track 3:** Real geometry / density is **FR-UI-10** — see `docs/design/TRACK3_AREA_WIRES.md` (wires accept gate before HTML/CSS).

Calm Windows-enterprise density for the **existing** desktop shell (`desktop_app.py` / `ui/desktop`). Orb home stays primary (FR-UI-1). Accents continue to follow the active orb style (FR-UI-3). Layout modes A–E stay (FR-UI-7).

---

## 1. Intent

| Goal | Meaning here |
|------|----------------|
| Calm | Fewer competing weights; one chrome band + one work surface; no dashboard chrome farm |
| Enterprise | Readable under sponsor demos; serious without a SaaS rebrand |
| Windows density | Compact toolbars like WinUI / Office ribbons lite — not Material sprawl, not Inter+purple |
| Local-first | System fonts only; no CDN webfonts; no telemetry from layout |

This note feeds **KAN-297** (small CSS variables in `ui/desktop/desktop.css`). Human accept landed 2026-11-18 — Build may apply tokens.

---

## 2. Type scale (area surfaces)

Use the shell’s existing family — already local:

`--font: "Segoe UI", "Bahnschrift", "Trebuchet MS", sans-serif`

Proposed **area** scale (px / CSS rem @ 16px root). Orb title / HUD may stay larger; this scale is for App areas only.

| Token (proposed) | Size | Weight | Use |
|------------------|------|--------|-----|
| `--type-area-title` | 13–14px | 600 | `.area-title` (uppercase ok; letter-spacing ≤ 0.12em) |
| `--type-body` | 13px | 400 | Lists, case names, form values |
| `--type-ui` | 12px | 500–600 | Toolbar labels, status one-liner |
| `--type-meta` | 11px | 600 | Section tabs (`.plan-tab`), chips, timestamps |
| `--type-help` | 11px | 400 | Advanced / collapsed help |

Rules:

- Prefer **one** display size on an area (title), not stacked hero + subhero.
- Do not introduce Inter, Roboto, Arial-as-brand, or any Google/Adobe font CDN.
- Line-height ~1.35 for body; tabs can stay tight (~1.2).

---

## 3. Spacing scale

Base unit **4px**. Prefer multiples of 4; avoid one-off 5/7/9 gaps in new chrome.

| Token (proposed) | Value | Use |
|------------------|-------|-----|
| `--space-1` | 4px | Tab gap, tight stacks |
| `--space-2` | 8px | Default control gap, confirm dock padding |
| `--space-3` | 12px | Area bar / body side padding |
| `--space-4` | 16px | Section separation inside `.area-work` |
| `--space-5` | 24px | Rare — between major blocks only |

Chrome vs work:

- Toolbars / tabs / Confirm dock: `flex-shrink: 0`, **outside** `.area-work` (KAN-281 / KAN-293 pattern).
- `.area-work` scrolls; chrome does not.
- Avoid padding stacks that push primary fields below the fold on a short window (~720px tall).

---

## 4. Header / chrome max height

**Budget (Plans and peers):** the non-scrolling chrome stack above `.area-work` should stay ≤ **~120px** in the common case (single-line toolbar + status + one tab row).

| Band | Max (approx) | Contents |
|------|--------------|----------|
| Area surface bar | 40px | Title + Back |
| Sticky toolbar | 56px | Picker, Open/Refresh, search, one-line status (wrap → two lines only if window &lt; ~900px wide) |
| Section tabs | 36px | Six Plans tabs; wrap allowed but count toward budget |
| Confirm / primary dock (when shown) | 48px | Confirm + Cancel always fully visible; may sit **below** `.area-work` (Manual) |

If chrome would exceed ~120px before work content, collapse secondary actions under **Advanced** / one **Add case ▾** — never grow a second sticky stack inside the scrollport.

`position: sticky` **inside** a scrolling `.area-body` / `.area-work` remains **forbidden** when it occludes fields (FR-UI-9).

---

## 5. Occlusion checklist (verify on `desktop_app.py`)

Use before accepting any chrome / token change. Prefer pytest/HTML markers for structure; Computer Use only when clickability must be proven (tiered policy).

1. Open Plans (and Manual) in **overlay** and **split** layouts.
2. Resize the native window to ~1280×720.
3. Confirm: plan/case picker, search, Open/Refresh, and status line are fully visible (not under title bar or another panel).
4. Confirm: section tabs are fully visible and clickable.
5. Confirm: primary work controls (case list / Start / Propose) are not covered by chrome.
6. On Manual review with proposals: **Confirm** and **Cancel** stay fully visible and clickable without scrolling the dock away.
7. Scroll `.area-work` — chrome bands must not slide over inputs.
8. Esc/Back still returns to orb home; App menu stays compact `▦` (no tall rail).

Fail any item → fix geometry before shipping tokens.

---

## 6. Plans wire (one screen)

ASCII wire for **Plans · Cases** (default landing). Chrome outside the scrollport; Cases list scrolls.

```
┌─ area-surface ─────────────────────────────────────────┐
│ [←]  PLANS                                              │  ← surface bar (~40px)
├─────────────────────────────────────────────────────────┤
│ Plan ▾ [Open] [Refresh]   🔍 search……    status: ready │  ← toolbar (≤56px)
├─────────────────────────────────────────────────────────┤
│ [Draft] [Cases*] [Coverage] [Trace] [History] [Run]     │  ← tabs (≤36px)
├─────────────────────────────────────────────────────────┤
│  Add case ▾                                             │
│  ┌─ .area-work (scroll) ─────────────────────────────┐  │
│  │  case row …                                        │  │
│  │  case row …                                        │  │
│  │  …                                                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

\*Cases selected. Lab knobs stay under Settings / Lab / collapsed Run setup — not forever-scroll on Cases.

---

## 7. Hard forbids (product constraints)

| Forbidden | Why |
|-----------|-----|
| Tall persistent App side drawer / rail | FR-UI-1 / FR-UI-7 — compact `▦` menu only |
| Persistent top tab bar as app navigation | Same — areas open as dedicated surfaces |
| Purple / indigo SaaS clone (Inter + purple gradient “AI app”) | Brand + sponsor tone; accents stay orb-driven cyan/style |
| Cloud font CDNs / webfont telemetry | Local-first, GDPR, offline Windows laptop |
| Second shell or Gradio-first redesign | Desktop is primary (FR-UI-2) |
| Sticky chrome inside `.area-work` that covers fields | FR-UI-9 / Bug KAN-280 class |
| Rewriting navigation or orb home in the tokens story | Out of scope for KAN-297 |

---

## 8. Handoff to KAN-297 (tokens) — Done

After **human accept** of this note (landed 2026-11-18):

1. Added `--type-*` / `--space-*` / `--chrome-*` under `:root` in `ui/desktop/desktop.css` (**KAN-297** / desk99).
2. Pointed existing area chrome (toolbars, tabs, confirm dock, titles) at those variables — small diff, no new design-system package.
3. Kept FR-UI-3 accent variables (`--cyan`, borders, glow) as the colour system.
4. Cache-bust `desktop_app.py`; area-chrome + Manual confirm marker tests green.
5. Did **not** implement voice (KAN-81) or FR-MAN-2 live circles.
