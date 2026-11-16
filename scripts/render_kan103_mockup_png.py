"""Screenshot KAN-103 HTML mockups to PNG (optional local run)."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOCK = REPO / "docs" / "mockups" / "kan103_nav"
OUT = MOCK / "png"


ALIASES = {
    "option-a-home.png": "A-home.png",
    "option-a-app-settings.png": "A-settings.png",
    "option-a-reports.png": "A-reports.png",
    "option-b-home.png": "B-home.png",
    "option-b-app-settings.png": "B-settings.png",
    "option-b-reports.png": "B-reports.png",
    "option-c-home.png": "C-home.png",
    "option-c-app-settings.png": "C-settings.png",
    "option-c-hub.png": "C-hub.png",
    "option-c-reports.png": "C-reports.png",
}


def main() -> int:
    pages = sorted(p for p in MOCK.glob("option-*.html") if p.name != "option-a.html")
    if not pages:
        print("no html mockups")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed; HTML previews still valid")
        return 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1328, "height": 848})
        for html in pages:
            uri = html.resolve().as_uri()
            page.goto(uri, wait_until="networkidle")
            out = OUT / (html.stem + ".png")
            page.screenshot(path=str(out), full_page=False)
            print("wrote", out.relative_to(REPO))
        browser.close()

    for src, dst in ALIASES.items():
        src_path = OUT / src
        if src_path.is_file():
            (MOCK / dst).write_bytes(src_path.read_bytes())
            print("alias", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())