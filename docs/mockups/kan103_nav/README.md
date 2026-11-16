# KAN-103 navigation UX mockups (design choice — not locked)

**Status:** Awaiting user pick of **A**, **B**, or **C** before `ui/desktop/` implementation. Active slice stays **KAN-103** (start **KAN-106** after the pick). **KAN-75** stays deferred.

**Plan:** [`docs/ops/KAN102_NAV_WIDGETS_PLAN.md`](../../ops/KAN102_NAV_WIDGETS_PLAN.md)

**Product model (locked):** Agent home = chat + orb; HUD widgets from Screen drawer; App areas = dedicated surfaces; App Settings ≠ Orb settings.

## Generated frames (pick from these)

Dark void, mystic cyan (no purple). Open the HTML file beside each pair if the PNG viewer is inconvenient.

| Option | Frames | HTML fallback |
|--------|--------|----------------|
| **A** Full-bleed overlay | `option_a_home.png`, `option_a_settings.png` | `option_a.html` |
| **B** Area stage (orb pip) | `option_b_home.png`, `option_b_settings.png` | `option_b.html` |
| **C** Orb hub, then overlay A | `option_c_hub.png`, `option_c_settings.png` | `option_c.html` |

**A** keeps the full orb on home and dims it under a glass Settings/Reports window. The App button is a nav list only; the Screen drawer is HUD widget toggles. **B** puts work on a large stage and shrinks the orb to a pip, so the area feels like its own screen. **C** adds neural spokes from the orb to the seven areas, then opens the same full-window glass as A.

Earlier HTML pack and rendered PNGs under `png/` remain for layout detail. Reference chrome: `docs/mockups/screenshots/mystic_desktop_drawers.png`.

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

## Regenerate PNGs

```text
.\venv\Scripts\python.exe scripts\render_kan103_mockup_png.py
```

## Your decision

Reply with **A**, **B**, **C**, or **hybrid** (e.g. “A overlay + C hub in phase 2”). PM will lock design in Jira and start **KAN-106** implementation.