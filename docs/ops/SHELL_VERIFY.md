# Shell chrome verification (desktop-first)

**Why this exists:** KAN-253 was marked Done while the desktop App menu still looked like the old tall APP rail. Pytest only checked for class-name strings. Computer Use notes claimed success without geometric checks. A later fix (KAN-256) sat on a feature branch and never reached `main` until KAN-257 — so the Designer kept seeing no change.

## Product priority

1. **Desktop (`desktop_app.py`) is the product.** Gradio is a lab/dev shell only and will not be the post-release UI.
2. Any App-menu / Settings-hub / Reports-library chrome change is **not Done** until it is correct on **desktop**.
3. Gradio may mirror desktop for convenience, but Gradio-only delivery is a process failure for primary chrome.

## False-green rules (agents)

Do **not** mark a shell story Done if any of these are true:

| Trap | Required instead |
|------|------------------|
| Pytest only asserts a class name / comment string exists | Assert **structure + geometry**: nav item list equals `ui/app_areas.py`; `#area-section-host` not under `#app-drawer`; CSS rule `#app-drawer.app-menu-panel` has `position: fixed` + `height: fit-content` and does **not** use tall-rail `top: 24px` / `bottom: 88px` / `width: var(--drawer-size)` |
| Computer Use “opened App menu” without describing size | Screenshot open menu; confirm **compact popover under ▦**, not a full-height side rail; count visible App nav labels (must match `PRIMARY_APP_MENU_AREAS`) |
| Fix only on a feature branch | Slice close-out requires **`git push origin main`** (or merge to `main` before Done). Branch-only fixes are not shipped |
| Gradio looks right, desktop unchecked | Verify **native** `desktop_app.py` window. Browser tab of `/ui/desktop/` is not the product |

## Checklist before Story → Done (App menu / shell)

1. `pytest tests/test_desktop_app_menu.py tests/test_gradio_menu_nav.py -v` passes.
2. Restart `desktop_app.py` (new `?v=deskNN` cache bust).
3. Computer Use on the **native** window: ▦ → compact App panel with Chat / Settings / Plans / Reports / Documents only.
4. Choosing Settings / Reports opens the **area surface**, not inline drawer content; menu closes.
5. Commit + **push `main`** (or merge) before Done.

## Canonical areas

See `ui/app_areas.py` — single source of truth for the compact App menu. Extra tools stay on the orb hub / dedicated surfaces.
