# Approved Orb Style Mockups (2026-11-06)

Three styles approved for implementation. Widgets shown in the mockups are future configurable panels (add/remove/hide).

## Mystic
Cyan-blue filament sphere with soft halo, swirling arcs, bright core. Closest to the JARVIS video reference. Good but not pixel-perfect.

## Aether
Orange-gold fiery plasma sphere with chaotic swirling arcs and ember particles.

## Neural
Translucent blue glass sphere with dark centre, bright cyan rim, sparkling particles.

All three use the same dark-void + floating HUD panel layout.

Implementation target: add these as selectable styles in the existing Gradio orb (ui/gradio_app.py or orb_webgl if present). Start with cheapest model (Composer). Visual matching may need stronger model if first attempt is off.
