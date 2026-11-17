"""Desktop App menu area ids — Primary vs Lab tools (KAN-260 / FR-UI-8)."""

from __future__ import annotations

# Compact ▦ App menu — Primary group (always present since KAN-257).
PRIMARY_APP_MENU_AREAS: tuple[str, ...] = (
    "chat",
    "settings",
    "plans",
    "reports",
    "documents",
)

# Compact ▦ App menu — Lab tools group (KAN-260). Reachable in every layout mode.
LAB_APP_MENU_AREAS: tuple[str, ...] = (
    "security",
    "heal",
    "desktop",
    "suites",
    "sandboxes",
)

ALL_APP_MENU_AREAS: tuple[str, ...] = PRIMARY_APP_MENU_AREAS + LAB_APP_MENU_AREAS
