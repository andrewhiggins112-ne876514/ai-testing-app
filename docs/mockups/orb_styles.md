# Approved Orb Style Mockups (2026-11-06)

Three styles approved for implementation. **Side panels / HUD layers** in mystic and neural mockups are **optional agent-home widgets** (toggle from Screen drawer widget settings) — not the content of App areas such as Settings or Reports. Widgets are add/remove/hide on the home canvas only.

| Id | Look | Renderer |
|----|------|----------|
| `mystic` | Cyan-blue filament sphere with soft halo, swirling arcs, bright core (JARVIS-style) | WebGL / Three.js |
| `aether` | Orange-gold fiery plasma sphere with chaotic swirling arcs and ember particles | WebGL / Three.js |
| `neural` | Translucent blue glass sphere with dark centre, bright cyan rim, sparkling particles | WebGL / Three.js |
| `apex` | Soft white-gold core, sparse geometric data streams in clean arcs, core-only bloom | WebGL / Three.js |

Classic styles (`lightning`, `mist`, `nebula`, `nebula+lightning`) stay on pure canvas.

## Particle caps (home PC)
- mystic points ≤ 280
- aether points ≤ 400; arcs ≤ 24
- neural points ≤ 360; panes ≤ 4
- apex streams ≤ 12; node points ≤ 72

Calm / thinking colours from the settings store still tint the active style.

All three use the same dark-void chat layout. Widgets from the mockups are out of scope for this slice.
