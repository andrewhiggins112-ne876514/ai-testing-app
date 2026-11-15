"""Screenshot KAN-103 HTML mockups to PNG (optional local run)."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOCK = REPO / "docs" / "mockups" / "kan103_nav"
OUT = MOCK / "png"


def main() -> int:
    pages = sorted(MOCK.glob("option-*.html"))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())