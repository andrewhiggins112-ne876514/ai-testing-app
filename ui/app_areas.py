"""Canonical primary App menu areas (desktop product chrome).

Desktop is the product UI. Gradio must mirror these labels for the App menu
popover only — extra tools (Security, Heal, Desktop, Suites, Sandboxes) stay on
the desktop orb hub / dedicated surfaces, not in the compact App menu.
"""

from __future__ import annotations

# Order matters — matches Gradio App menu button order (KAN-248 / KAN-257).
PRIMARY_APP_MENU_AREAS: tuple[str, ...] = (
    "Chat",
    "Settings",
    "Plans",
    "Reports",
    "Documents",
)

# data-section values on desktop .app-nav-item buttons
PRIMARY_APP_MENU_SECTIONS: tuple[str, ...] = tuple(
    name.lower() for name in PRIMARY_APP_MENU_AREAS
)

# Must not appear in the compact App menu nav (hub / other surfaces only).
APP_MENU_EXCLUDED_SECTIONS: tuple[str, ...] = (
    "security",
    "heal",
    "desktop",
    "suites",
    "sandboxes",
)
