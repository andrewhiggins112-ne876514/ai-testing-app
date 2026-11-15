"""Report section profile — which blocks appear in Markdown/JSON exports (FR-REP-2)."""
from __future__ import annotations

import re
from typing import Any, Mapping

SECTION_KEYS = ("summary", "stories", "bugs", "evidence")
SECTION_LABELS = {
    "summary": "Summary",
    "stories": "Stories",
    "bugs": "Bugs",
    "evidence": "Evidence",
}

_JIRA_KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")


def default_sections() -> dict[str, bool]:
    return {key: True for key in SECTION_KEYS}


def normalize_sections(raw: Mapping[str, Any] | None) -> dict[str, bool]:
    """Merge user preferences onto defaults; unknown keys ignored."""
    out = default_sections()
    if not isinstance(raw, Mapping):
        return out
    for key in SECTION_KEYS:
        if key in raw:
            out[key] = bool(raw[key])
    return out


def load_report_sections() -> dict[str, bool]:
    from settings.store import load_settings

    return normalize_sections(load_settings().get("report_sections"))


def save_report_sections(sections: Mapping[str, Any]) -> dict[str, bool]:
    from settings.store import load_settings, write_settings

    normalised = normalize_sections(sections)
    settings = load_settings()
    settings["report_sections"] = normalised
    write_settings(settings)
    return normalised


def _step_counts(steps: list) -> tuple[int, int]:
    passed = failed = 0
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        status = str(step.get("status") or "").lower()
        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
    return passed, failed


def _story_keys(result: Mapping[str, Any], request_text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(key: str) -> None:
        if key and key not in seen:
            seen.add(key)
            found.append(key)

    for source in (result.get("stories"), result.get("jira_keys")):
        if isinstance(source, list):
            for item in source:
                if isinstance(item, str):
                    add(item.strip())
                elif isinstance(item, Mapping):
                    add(str(item.get("key") or item.get("jira_key") or "").strip())
        elif isinstance(source, str):
            for match in _JIRA_KEY.findall(source):
                add(match)
    for match in _JIRA_KEY.findall(request_text or ""):
        add(match)
    return found


def _bug_items(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    bugs: list[dict[str, Any]] = []
    raw = result.get("bugs")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping):
                bugs.append(dict(item))
            elif isinstance(item, str) and item.strip():
                bugs.append({"summary": item.strip()})
    for step in result.get("steps") or []:
        if not isinstance(step, Mapping):
            continue
        classification = str(step.get("classification") or "")
        if classification == "product_bug" or step.get("heal_refused"):
            bugs.append(
                {
                    "action": step.get("action"),
                    "classification": classification or "product_bug",
                    "error": step.get("error"),
                    "heal_refused": step.get("heal_refused"),
                }
            )
    return bugs


def build_sections(
    result: Mapping[str, Any] | None,
    request_text: str = "",
    enabled: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Build only the enabled report sections for JSON export."""
    body = result if isinstance(result, Mapping) else {}
    flags = normalize_sections(enabled)
    steps = list(body.get("steps") or []) if isinstance(body.get("steps"), list) else []
    passed, failed = _step_counts(steps)
    sections: dict[str, Any] = {}

    if flags["summary"]:
        sections["summary"] = {
            "title": body.get("title") or "Playwright run",
            "status": body.get("status") or "fail",
            "passed": passed,
            "failed": failed,
            "error": body.get("error"),
            "steps": steps,
        }
    if flags["stories"]:
        keys = _story_keys(body, request_text)
        sections["stories"] = {
            "keys": keys,
            "count": len(keys),
        }
    if flags["bugs"]:
        items = _bug_items(body)
        sections["bugs"] = {
            "items": items,
            "count": len(items),
        }
    if flags["evidence"]:
        links = []
        shot = body.get("screenshot")
        if shot:
            links.append({"kind": "screenshot", "path": shot})
        extra = body.get("evidence")
        if isinstance(extra, list):
            for item in extra:
                if isinstance(item, Mapping):
                    links.append(dict(item))
                elif isinstance(item, str) and item.strip():
                    links.append({"kind": "link", "path": item.strip()})
        sections["evidence"] = {
            "screenshot": shot,
            "links": links,
        }
    return sections


def render_markdown(sections: Mapping[str, Any]) -> str:
    """Render Markdown for the included sections only."""
    lines: list[str] = []
    summary = sections.get("summary") if isinstance(sections.get("summary"), Mapping) else None
    title = (summary or {}).get("title") or "Playwright run"
    lines.extend([f"# {title}", ""])

    if summary is not None:
        lines.append("## Summary")
        lines.append("")
        lines.append(f"Overall: {summary.get('status') or 'fail'}")
        lines.append(f"Passed: {summary.get('passed', 0)}  Failed: {summary.get('failed', 0)}")
        if summary.get("error"):
            lines.append(f"Error: {summary.get('error')}")
        lines.append("")
        lines.append("| action | status |")
        lines.append("| --- | --- |")
        for step in summary.get("steps") or []:
            if isinstance(step, Mapping):
                lines.append(f"| {step.get('action', '')} | {step.get('status', '')} |")
        lines.append("")

    if "stories" in sections and isinstance(sections["stories"], Mapping):
        lines.append("## Stories")
        lines.append("")
        keys = sections["stories"].get("keys") or []
        if keys:
            for key in keys:
                lines.append(f"- {key}")
        else:
            lines.append("None linked.")
        lines.append("")

    if "bugs" in sections and isinstance(sections["bugs"], Mapping):
        lines.append("## Bugs")
        lines.append("")
        items = sections["bugs"].get("items") or []
        if items:
            for item in items:
                if not isinstance(item, Mapping):
                    continue
                label = item.get("summary") or item.get("action") or item.get("classification") or "bug"
                detail = item.get("error") or item.get("heal_refused") or ""
                if detail:
                    lines.append(f"- {label}: {detail}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("None recorded.")
        lines.append("")

    if "evidence" in sections and isinstance(sections["evidence"], Mapping):
        lines.append("## Evidence")
        lines.append("")
        shot = sections["evidence"].get("screenshot") or ""
        lines.append(f"Screenshot: {shot}")
        for link in sections["evidence"].get("links") or []:
            if isinstance(link, Mapping) and link.get("kind") != "screenshot":
                lines.append(f"- {link.get('kind', 'link')}: {link.get('path', '')}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
