---
name: orb-slice
description: Implement the next energy-orb / Gradio UI slice. Use for presets, styles, panels, and orb settings persistence.
---

# Orb slice

1. Read current orb behaviour only in `ui/gradio_app.py` and orb keys in `settings/store.py` (targeted).
2. One slice (e.g. UI-5 presets). No full UI rewrite.
3. Pure canvas JS; persist via settings store; keep calm ↔ thinking transitions.
4. Use `/ui-orb` then `/verifier`.
5. Update ROADMAP / PROJECT_MEMORY when the slice lands.

Reference: orb slices 1–4 landed through commit `8553d6a`.
