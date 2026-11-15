# KAN-103 navigation UX mockups (design choice — not locked)

**Status:** Awaiting Designer pick of **A**, **B**, **C**, or hybrid before `ui/desktop/` implementation.

**Plan:** [`docs/ops/KAN102_NAV_WIDGETS_PLAN.md`](../../ops/KAN102_NAV_WIDGETS_PLAN.md)

**Product model (locked):** Agent home = chat + orb; HUD widgets from Screen drawer; App areas = dedicated surfaces; App Settings ≠ Orb settings.

Open [`index.html`](index.html) in a browser for links. Reference chrome: mystic cyan (`#50cdff`) on void black — see `docs/mockups/screenshots/mystic_desktop_drawers.png`.

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
| Home hub idle | `option-c-home.html` | `png/option-c-home.png` |
| App Settings | `option-c-app-settings.html` | `png/option-c-app-settings.png` |
| Reports | `option-c-reports.html` | `png/option-c-reports.png` |

**Pros:** Hero interaction on-brand with mystic/neural orb; fast area jump. **Cons:** Highest implementation cost; hub + App nav must stay consistent; KAN-109 scope decision.

**Tasks most affected:** **KAN-106** + **KAN-109** (hub), **KAN-107**, **KAN-108**.

---

## Regenerate PNGs

```text
.\venv\Scripts\python.exe scripts\render_kan103_mockup_png.py
```

## Your decision

Reply with **A**, **B**, **C**, or **hybrid** (e.g. “A overlay + C hub in phase 2”). PM will lock design in Jira and start **KAN-106** implementation.