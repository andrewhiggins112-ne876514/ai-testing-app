"""Accessibility checks plugin (KAN-227 / G6 / FR-PLUG-1).

Optional sidecar on browser cases: scan page HTML for common WCAG issues
and attach violations to the run. Never replaces the functional result.
Disabled unless the case opts in. Stdlib HTMLParser only (no cloud APM).
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

PLUGIN_NAME = "accessibility_checks"


class _A11yParser(HTMLParser):
    """Collect lightweight accessibility signals from HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: str | None = None
        self.title_text = ""
        self._in_title = False
        self._in_button = False
        self._in_a = False
        self._in_label = False
        self._button_text = ""
        self._a_text = ""
        self._label_text = ""
        self._label_for: str | None = None
        self.imgs: list[dict[str, str]] = []
        self.inputs: list[dict[str, str]] = []
        self.buttons: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self.label_fors: set[str] = set()
        self.ids: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k: (v or "") for k, v in attrs}
        tid = (ad.get("id") or "").strip()
        if tid:
            self.ids.append(tid)
        lower = tag.lower()
        if lower in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if lower == "html":
            self.html_lang = (ad.get("lang") or "").strip() or None
        elif lower == "title":
            self._in_title = True
        elif lower == "img":
            self.imgs.append(
                {
                    "alt": ad.get("alt", ""),
                    "alt_present": "alt" in ad,
                    "src": (ad.get("src") or "")[:120],
                    "aria_label": (ad.get("aria-label") or "").strip(),
                    "role": (ad.get("role") or "").strip(),
                }
            )
        elif lower in {"input", "textarea", "select"}:
            itype = (ad.get("type") or "text").lower()
            if itype in {"hidden", "submit", "button", "image", "reset"}:
                return
            self.inputs.append(
                {
                    "id": tid,
                    "name": (ad.get("name") or "").strip(),
                    "type": itype,
                    "aria_label": (ad.get("aria-label") or "").strip(),
                    "title": (ad.get("title") or "").strip(),
                    "placeholder": (ad.get("placeholder") or "").strip(),
                }
            )
        elif lower == "button":
            self._in_button = True
            self._button_text = ""
            self.buttons.append(
                {
                    "aria_label": (ad.get("aria-label") or "").strip(),
                    "title": (ad.get("title") or "").strip(),
                    "type": (ad.get("type") or "submit").strip(),
                    "text": "",
                }
            )
        elif lower == "a":
            self._in_a = True
            self._a_text = ""
            self.anchors.append(
                {
                    "href": (ad.get("href") or "").strip()[:200],
                    "aria_label": (ad.get("aria-label") or "").strip(),
                    "title": (ad.get("title") or "").strip(),
                    "text": "",
                }
            )
        elif lower == "label":
            self._in_label = True
            self._label_text = ""
            self._label_for = (ad.get("for") or "").strip() or None

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if lower == "title":
            self._in_title = False
        elif lower == "button" and self._in_button:
            self._in_button = False
            if self.buttons:
                self.buttons[-1]["text"] = re.sub(r"\s+", " ", self._button_text).strip()
        elif lower == "a" and self._in_a:
            self._in_a = False
            if self.anchors:
                self.anchors[-1]["text"] = re.sub(r"\s+", " ", self._a_text).strip()
        elif lower == "label" and self._in_label:
            self._in_label = False
            if self._label_for:
                self.label_fors.add(self._label_for)

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_text += data
        if self._in_button:
            self._button_text += data
        if self._in_a:
            self._a_text += data
        if self._in_label:
            self._label_text += data


def scan_html(html: str, *, url: str = "") -> dict[str, Any]:
    """Scan HTML for common a11y violations. Returns structured plugin result."""
    text = html or ""
    parser = _A11yParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # noqa: BLE001 — surface parse issues
        return {
            "plugin": PLUGIN_NAME,
            "status": "error",
            "error": f"HTML parse failed: {exc}"[:300],
            "message": f"HTML parse failed: {exc}"[:300],
            "url": (url or "")[:500] or None,
            "violation_count": 0,
            "violations": [],
            "replaces_functional": False,
        }

    violations: list[dict[str, Any]] = []

    if not parser.html_lang:
        violations.append(
            {
                "id": "html-lang",
                "impact": "serious",
                "help": "Document language is missing (html lang).",
                "nodes": 1,
            }
        )
    if not (parser.title_text or "").strip():
        violations.append(
            {
                "id": "document-title",
                "impact": "serious",
                "help": "Page title is missing or empty.",
                "nodes": 1,
            }
        )

    missing_alt = [
        img
        for img in parser.imgs
        if not img.get("alt_present")
        and not img.get("aria_label")
        and img.get("role") != "presentation"
    ]
    if missing_alt:
        violations.append(
            {
                "id": "image-alt",
                "impact": "critical",
                "help": "Image(s) missing alt text.",
                "nodes": len(missing_alt),
            }
        )

    unlabeled = []
    for inp in parser.inputs:
        iid = inp.get("id") or ""
        if iid and iid in parser.label_fors:
            continue
        if inp.get("aria_label") or inp.get("title"):
            continue
        unlabeled.append(inp)
    if unlabeled:
        violations.append(
            {
                "id": "label",
                "impact": "critical",
                "help": "Form control(s) without an accessible name.",
                "nodes": len(unlabeled),
            }
        )

    empty_buttons = [
        b
        for b in parser.buttons
        if not (b.get("text") or "").strip()
        and not b.get("aria_label")
        and not b.get("title")
    ]
    if empty_buttons:
        violations.append(
            {
                "id": "button-name",
                "impact": "critical",
                "help": "Button(s) without accessible name.",
                "nodes": len(empty_buttons),
            }
        )

    empty_links = [
        a
        for a in parser.anchors
        if (a.get("href") or "").strip()
        and not (a.get("text") or "").strip()
        and not a.get("aria_label")
        and not a.get("title")
    ]
    if empty_links:
        violations.append(
            {
                "id": "link-name",
                "impact": "serious",
                "help": "Link(s) without accessible name.",
                "nodes": len(empty_links),
            }
        )

    seen: set[str] = set()
    dupes = 0
    for eid in parser.ids:
        if eid in seen:
            dupes += 1
        else:
            seen.add(eid)
    if dupes:
        violations.append(
            {
                "id": "duplicate-id",
                "impact": "moderate",
                "help": "Duplicate id attribute(s) found.",
                "nodes": dupes,
            }
        )

    count = len(violations)
    return {
        "plugin": PLUGIN_NAME,
        "status": "pass" if count == 0 else "violations",
        "error": None,
        "message": (
            "No accessibility violations found."
            if count == 0
            else f"{count} accessibility violation rule(s) found."
        ),
        "url": (url or "")[:500] or None,
        "violation_count": count,
        "violations": violations,
        "replaces_functional": False,
    }


def fetch_html(url: str, *, timeout: float = 8.0) -> dict[str, Any]:
    """Fetch page HTML for a11y scan (local check; no cloud service)."""
    target = (url or "").strip()
    if not target:
        return {
            "status": "fail",
            "error": "No URL for accessibility check.",
            "html": "",
            "url": None,
        }
    try:
        req = Request(
            target,
            headers={"User-Agent": "ai-testing-app-a11y/1.0"},
            method="GET",
        )
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — user target URL
            raw = resp.read(2_000_000)
            charset = "utf-8"
            ctype = str(resp.headers.get("Content-Type") or "")
            if "charset=" in ctype.lower():
                charset = ctype.lower().split("charset=")[-1].split(";")[0].strip() or "utf-8"
            html = raw.decode(charset, errors="replace")
            return {"status": "ok", "html": html, "url": target, "error": None}
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        return {
            "status": "fail",
            "error": f"Could not fetch page for a11y: {exc}"[:300],
            "html": "",
            "url": target,
        }


def run_accessibility_check(
    *,
    html: str = "",
    url: str = "",
    opted_in: bool = False,
) -> dict[str, Any]:
    """Run opt-in a11y check. Off unless opted_in. Never flips functional result."""
    base: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "opted_in": bool(opted_in),
        "checked": False,
        "status": "skipped",
        "error": None,
        "message": "Accessibility check disabled (case did not opt in).",
        "url": (url or "")[:500] or None,
        "violation_count": 0,
        "violations": [],
        "replaces_functional": False,
    }
    if not opted_in:
        return base

    page = (html or "").strip()
    target = (url or "").strip()
    if not page and target:
        fetched = fetch_html(target)
        if fetched.get("status") != "ok":
            return {
                **base,
                "checked": True,
                "status": "error",
                "error": fetched.get("error"),
                "message": fetched.get("error") or "A11y fetch failed.",
                "url": fetched.get("url") or target,
            }
        page = str(fetched.get("html") or "")
        target = str(fetched.get("url") or target)

    if not page:
        return {
            **base,
            "checked": True,
            "status": "error",
            "error": "No HTML available for accessibility check.",
            "message": "No HTML available for accessibility check.",
        }

    scanned = scan_html(page, url=target)
    return {
        **scanned,
        "opted_in": True,
        "checked": True,
        "replaces_functional": False,
    }
