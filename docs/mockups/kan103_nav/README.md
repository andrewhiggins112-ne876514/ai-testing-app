# KAN-103 navigation UX mockups (A–E are all settings)

**Status:** Design locked as **configurable layout modes**, not a single pick. Desktop App Settings → **App area layout** stores `overlay` | `stage` | `orb_hub` | `split` | `floating` in `localStorage` `desktop-area-layout-v1`. Chrome accents follow the active orb style (mystic cyan, aether orange-gold, neural, apex).

**Plan:** [`docs/ops/KAN102_NAV_WIDGETS_PLAN.md`](../../ops/KAN102_NAV_WIDGETS_PLAN.md)

**Product model (locked):** Agent home = chat + orb; HUD widgets from Screen drawer; App areas = dedicated surfaces; App Settings ≠ Orb settings.

## Comparison

| Id | Mockup | What it does |
|----|--------|----------------|
| `overlay` | A | Full-bleed glass over a dimmed home. Esc/Back closes. |
| `stage` | B | Area owns the stage; orb shrinks to a corner pip. HUD is home-only. |
| `orb_hub` | C | Click the orb for radial spokes, then the area opens as an overlay. App ▦ stays the list. |
| `split` | D | Persistent dock (~half width) beside the orb. Esc closes the dock. |
| `floating` | E | One movable/resizable area window. Orb stays full size. |

Style coupling: D and E settings frames exist in **mystic** and **aether** so the layout chrome is not cyan-only.

## Designer frames

Labeled mystic-cyan frames in [`grok/`](grok/) remain the A–C reference. D/E frames are the root PNGs below.

| Option | Frames |
|--------|--------|
| **A** Full-bleed overlay | `grok/A1-home.png`, `grok/A2-app-settings.png`, `grok/A3-reports.png` |
| **B** Area stage (orb pip) | `grok/B1-home.png`, `grok/B2-app-settings.png`, `grok/B3-reports.png` |
| **C** Orb hub, then overlay A | `grok/C1-orb-hub.png`, `grok/C2-app-settings.png`, `grok/C3-hub-fallback.png` |

**A — pros:** home stays iconic; Settings and Reports are a glass sheet over a dimmed orb, with a clear Back. **Cons:** drawers and the overlay can stack.

**B — pros:** an area feels like its own screen; the orb shrinks to a corner pip and the form owns the stage. **Cons:** the agent presence shrinks while you work.

**C — pros:** seven area labels sit on neural spokes, then the pick opens the same glass as A; the App grid stays the keyboard fallback (`C3`). **Cons:** most UI to build (hub is KAN-109; v1 or phase 2).

Earlier six-frame pass (`option_a_home.png` and siblings) and the HTML wireframes under this folder are layout notes only. Reference chrome: `docs/mockups/screenshots/mystic_desktop_drawers.png`.

## Option A — Full-bleed area overlay

App ▦ = short nav list. Choosing an area opens a **glass full-window panel** over a dimmed/blurred orb+chat. Esc/Back returns home. Screen drawer adds **HUD widget toggles** alongside chat/orb.

| View | HTML | PNG |
|------|------|-----|
| Home + HUD | `option-a-home.html` | `png/option-a-home.png` |
| App Settings | `option-a-app-settings.html` | `png/option-a-app-settings.png` |
| Reports | `option-a-reports.html` | `png/option-a-reports.png` |

**Pros:** Keeps agent home iconic; clear modal focus for configuration; easy Esc/back mental model. **Cons:** Overlay stack / z-index with drawers needs care.

**Tasks most affected:** **KAN-106** (routing + overlay shell), **KAN-107** (HUD on home under scrim), **KAN-108** (Settings surface content).

---

## Option B — Dedicated area stage (orb pip)

Selecting an App area **transitions** the shell: orb scales to a **corner pip**; area content fills a large **stage**. HUD widgets remain **home-only** (off on area stages).

| View | HTML | PNG |
|------|------|-----|
| Home + HUD | `option-b-home.html` | `png/option-b-home.png` |
| App Settings | `option-b-app-settings.html` | `png/option-b-app-settings.png` |
| Reports | `option-b-reports.html` | `png/option-b-reports.png` |

**Pros:** Strong “separate screen” feel; less overlay stacking. **Cons:** Loses full-size orb on area work; pip may feel disconnected from agent.

**Tasks most affected:** **KAN-106** (layout mode switch home vs stage), **KAN-107** (HUD home-only rule), **KAN-108**.

---

## Option C — Orb hub entry + full-bleed screens

Clicking orb (or hub mode) expands **neural spokes** to 7 areas; pick one → **same full-bleed overlay as A**. App ▦ stays linear **a11y fallback**. Hub maps to **KAN-109** — ship with v1 or phase 2 (your call).

| View | HTML | PNG |
|------|------|-----|
| Agent home (hub off) | `option-c-home.html` | `C-home.png` / `png/option-c-home.png` |
| Orb hub expanded | `option-c-hub.html` | `C-hub.png` / `png/option-c-hub.png` |
| App Settings | `option-c-app-settings.html` | `png/option-c-app-settings.png` |
| Reports | `option-c-reports.html` | `png/option-c-reports.png` |

**Pros:** Hero interaction on-brand with mystic/neural orb; fast area jump. **Cons:** Highest implementation cost; hub + App nav must stay consistent; KAN-109 scope decision.

**Tasks most affected:** **KAN-106** + **KAN-109** (hub), **KAN-107**, **KAN-108**.

---

## Option D — Split workspace

Home keeps the full orb. Choosing an area opens a **docked glass panel** on the right (~40–50% width). Esc/Back closes the dock. Useful for glancing at Settings while the agent stays visible.

| View | PNG |
|------|-----|
| Home (mystic) | `option_d_home.png` |
| Settings (mystic) | `option_d_settings.png` / `option_d_settings_mystic.png` |
| Settings (aether) | `option_d_settings_aether.png` |

**Pros:** Agent stays present; no full-screen takeover. **Cons:** Narrow forms; drawer and dock can compete on the right.

---

## Option E — Floating area window

Choosing an area opens **one** movable, resizable `shell-surface` window (same idea as HUD widgets). The orb stays full size. v1 is one window at a time.

| View | PNG |
|------|-----|
| Home (mystic) | `option_e_home.png` |
| Settings (mystic) | `option_e_settings.png` / `option_e_settings_mystic.png` |
| Settings (aether) | `option_e_settings_aether.png` |

**Pros:** Home composition unchanged; window can sit beside chat. **Cons:** Overlap and z-order need care; multiple windows are later.

---

## Regenerate PNGs

```text
.\venv\Scripts\python.exe scripts\render_kan103_mockup_png.py
```

## Decision (2026-11-16)

Do not pick one letter. A–E are all **App area layout** choices. Accents follow Screen → Orb style (FR-UI-3). Hub spokes are a simple radial v1; particle hub polish is still open.