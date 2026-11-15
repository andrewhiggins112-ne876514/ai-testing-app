---
name: orb-slice
description: Implement the next energy-orb / Gradio UI slice. Use for presets, styles, panels, and orb settings persistence.
---

# Orb slice

1. Prefer desktop shell orb paths (`ui/desktop/`, `ui/orb_webgl.js`) unless the story is Gradio-only. Read orb keys in `settings/store.py` (targeted).
2. One slice (e.g. UI-5 presets). No full UI rewrite.
3. Classic styles: pure canvas; mystic/aether/neural may use vendored Three.js. Persist via settings store; keep calm ↔ thinking transitions.
4. Use `/ui-orb` then `/verifier`. **Verify with `desktop_app.py` + Computer Use** — not a browser tab of the shell.
5. Update ROADMAP / PROJECT_MEMORY when the slice lands.

Reference: orb slices 1–4 landed through commit `8553d6a`.
