"""Add option-letter + view-caption to KAN-103 mockup HTML."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "mockups" / "kan103_nav"

CAPTIONS = {
    "home": "AGENT HOME",
    "app-settings": "APP SETTINGS",
    "reports": "REPORTS",
    "hub": "ORB HUB (KAN-109)",
}


def letter_and_caption(stem: str) -> tuple[str, str]:
    m = re.match(r"option-([abc])-(.+)", stem)
    if not m:
        return "", ""
    letter = m.group(1).upper()
    cap = CAPTIONS.get(m.group(2), m.group(2).replace("-", " ").upper())
    return letter, cap


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    letter, cap = letter_and_caption(path.stem)
    if not letter:
        return
    inject = f'    <div class="option-letter" aria-hidden="true">{letter}</div>\n    <div class="view-caption">{cap}</div>\n'
    if "option-letter" in text:
        return
    text = text.replace('<div class="shell">', '<div class="shell">\n' + inject, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    for html in sorted(ROOT.glob("option-*.html")):
        if html.name == "option-a.html":
            continue
        patch(html)


if __name__ == "__main__":
    main()