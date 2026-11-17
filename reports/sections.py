"""Report section profile — which blocks appear in Markdown/JSON exports (FR-REP-2)."""
from __future__ import annotations

import re
from typing import Any, Mapping

SECTION_KEYS = (
    "summary",
    "stories",
    "bugs",
    "evidence",
    "known_issues",
    "traceability",
)
SECTION_LABELS = {
    "summary": "Summary",
    "stories": "Stories",
    "bugs": "Bugs",
    "evidence": "Evidence",
    "known_issues": "Known issues",
    "traceability": "Traceability",
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


def _pass_rate(passed: int, failed: int) -> float | None:
    total = passed + failed
    if total <= 0:
        return None
    return round(100.0 * passed / total, 1)


def _story_keys(result: Mapping[str, Any], request_text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(key: str) -> None:
        key = (key or "").strip().upper()
        if key and _JIRA_KEY.fullmatch(key) and key not in seen:
            seen.add(key)
            found.append(key)

    for source in (
        result.get("stories"),
        result.get("stories_covered"),
        result.get("jira_keys"),
    ):
        if isinstance(source, list):
            for item in source:
                if isinstance(item, str):
                    add(item)
                elif isinstance(item, Mapping):
                    add(str(item.get("key") or item.get("jira_key") or ""))
        elif isinstance(source, str):
            for match in _JIRA_KEY.findall(source):
                add(match)
    for match in _JIRA_KEY.findall(request_text or ""):
        add(match)
    return found


def _area_label(raw: Any) -> str:
    text = str(raw or "").strip()
    return text if text else "unspecified"


def _bug_story_key(item: Mapping[str, Any], fallback_stories: list[str]) -> str:
    for field in ("story_key", "story", "relates_to", "linked_story"):
        value = str(item.get(field) or "").strip().upper()
        if value and _JIRA_KEY.fullmatch(value):
            return value
    blob = " ".join(
        str(item.get(field) or "")
        for field in ("summary", "error", "action", "key", "jira_key")
    )
    mentioned = [m.upper() for m in _JIRA_KEY.findall(blob)]
    own = str(item.get("key") or item.get("jira_key") or "").strip().upper()
    for key in mentioned:
        if key != own:
            return key
    if len(fallback_stories) == 1:
        return fallback_stories[0]
    return ""


def _normalise_bug_item(
    item: Mapping[str, Any],
    fallback_stories: list[str],
    default_area: str,
) -> dict[str, Any]:
    out = dict(item)
    key = str(out.get("key") or out.get("jira_key") or "").strip().upper()
    if key and _JIRA_KEY.fullmatch(key):
        out["key"] = key
    story = _bug_story_key(out, fallback_stories)
    if story:
        out["story_key"] = story
    area = _area_label(out.get("functional_area") or out.get("area") or default_area)
    out["area"] = area
    return out


def _bug_items(result: Mapping[str, Any], story_keys: list[str]) -> list[dict[str, Any]]:
    bugs: list[dict[str, Any]] = []
    default_area = _area_label(result.get("functional_area") or result.get("area"))
    raw = result.get("bugs")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping):
                bugs.append(_normalise_bug_item(item, story_keys, default_area))
            elif isinstance(item, str) and item.strip():
                bugs.append(
                    _normalise_bug_item(
                        {"summary": item.strip()},
                        story_keys,
                        default_area,
                    )
                )
    for step in result.get("steps") or []:
        if not isinstance(step, Mapping):
            continue
        classification = str(step.get("classification") or "")
        if classification == "product_bug" or step.get("heal_refused"):
            bugs.append(
                _normalise_bug_item(
                    {
                        "action": step.get("action"),
                        "classification": classification or "product_bug",
                        "error": step.get("error"),
                        "heal_refused": step.get("heal_refused"),
                        "story_key": step.get("story_key") or step.get("story"),
                        "area": step.get("functional_area") or step.get("area"),
                        "key": step.get("bug_key") or step.get("jira_key"),
                    },
                    story_keys,
                    default_area,
                )
            )
    return bugs


def _group_bugs(
    items: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_story: dict[str, list[dict[str, Any]]] = {}
    by_area: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        story = str(item.get("story_key") or "").strip().upper() or "unlinked"
        area = _area_label(item.get("area"))
        by_story.setdefault(story, []).append(item)
        by_area.setdefault(area, []).append(item)
    return by_story, by_area


def _bug_keys(items: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = str(item.get("key") or "").strip().upper()
        if key and _JIRA_KEY.fullmatch(key) and key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def _counts_map(grouped: Mapping[str, list]) -> dict[str, int]:
    return {key: len(value) for key, value in grouped.items()}


def build_sections(
    result: Mapping[str, Any] | None,
    request_text: str = "",
    enabled: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Build only the enabled report sections for JSON export (FR-REP-1 metrics)."""
    body = result if isinstance(result, Mapping) else {}
    flags = normalize_sections(enabled)
    steps = list(body.get("steps") or []) if isinstance(body.get("steps"), list) else []
    passed, failed = _step_counts(steps)
    story_keys = _story_keys(body, request_text)
    bug_items = _bug_items(body, story_keys)
    by_story, by_area = _group_bugs(bug_items)
    bug_key_list = _bug_keys(bug_items)
    pass_rate = _pass_rate(passed, failed)
    sections: dict[str, Any] = {}

    if flags["summary"]:
        sections["summary"] = {
            "title": body.get("title") or "Playwright run",
            "status": body.get("status") or "fail",
            "passed": passed,
            "failed": failed,
            "tests_passed": passed,
            "tests_failed": failed,
            "pass_rate_percent": pass_rate,
            "stories_covered": len(story_keys),
            "bugs_raised": len(bug_items),
            "progress": {
                "tests_passed": passed,
                "tests_failed": failed,
                "pass_rate_percent": pass_rate,
                "stories_covered": len(story_keys),
                "bugs_raised": len(bug_items),
            },
            "error": body.get("error"),
            "steps": steps,
        }
    if flags["stories"]:
        sections["stories"] = {
            "keys": story_keys,
            "count": len(story_keys),
            "covered": story_keys,
            "covered_count": len(story_keys),
            "by_key": {
                key: {
                    "covered": True,
                    "bugs_raised": len(by_story.get(key) or []),
                }
                for key in story_keys
            },
        }
    if flags["bugs"]:
        sections["bugs"] = {
            "items": bug_items,
            "count": len(bug_items),
            "raised_count": len(bug_items),
            "keys": bug_key_list,
            "by_story": by_story,
            "by_area": by_area,
            "counts_by_story": _counts_map(by_story),
            "counts_by_area": _counts_map(by_area),
        }
    if flags["evidence"]:
        from plans.notes import notes_from_result

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
        note_items = notes_from_result(body)
        sections["evidence"] = {
            "screenshot": shot,
            "links": links,
            "notes": note_items,
        }
    if flags.get("known_issues"):
        from plans.known_issue import known_issues_from_result

        ki_items = known_issues_from_result(body)
        sections["known_issues"] = {
            "items": ki_items,
            "count": len(ki_items),
            "excluded_from_regression": True,
            "label": "known",
        }
    if flags.get("traceability"):
        raw_rows = body.get("traceability")
        rows: list[dict[str, Any]] = []
        if isinstance(raw_rows, list):
            for item in raw_rows:
                if isinstance(item, Mapping):
                    rows.append(dict(item))
        sections["traceability"] = {
            "rows": rows,
            "count": len(rows),
            "label": "traceability matrix",
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
        lines.append(
            f"Passed: {summary.get('passed', 0)}  Failed: {summary.get('failed', 0)}"
        )
        rate = summary.get("pass_rate_percent")
        if rate is not None:
            lines.append(f"Pass rate: {rate}%")
        lines.append(f"Stories covered: {summary.get('stories_covered', 0)}")
        lines.append(f"Bugs raised: {summary.get('bugs_raised', 0)}")
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
        stories = sections["stories"]
        lines.append("## Stories")
        lines.append("")
        lines.append(f"Covered: {stories.get('covered_count', stories.get('count', 0))}")
        keys = stories.get("keys") or stories.get("covered") or []
        by_key = stories.get("by_key") if isinstance(stories.get("by_key"), Mapping) else {}
        if keys:
            for key in keys:
                meta = by_key.get(key) if isinstance(by_key.get(key), Mapping) else {}
                bugs_n = meta.get("bugs_raised", 0) if meta else 0
                lines.append(f"- {key} (covered; bugs raised: {bugs_n})")
        else:
            lines.append("None linked.")
        lines.append("")

    if "bugs" in sections and isinstance(sections["bugs"], Mapping):
        bugs = sections["bugs"]
        lines.append("## Bugs")
        lines.append("")
        lines.append(f"Raised: {bugs.get('raised_count', bugs.get('count', 0))}")
        keys = bugs.get("keys") or []
        if keys:
            lines.append("Bug keys: " + ", ".join(str(k) for k in keys))
        counts_story = (
            bugs.get("counts_by_story")
            if isinstance(bugs.get("counts_by_story"), Mapping)
            else {}
        )
        counts_area = (
            bugs.get("counts_by_area")
            if isinstance(bugs.get("counts_by_area"), Mapping)
            else {}
        )
        if counts_story:
            lines.append("")
            lines.append("By story:")
            for story, count in counts_story.items():
                lines.append(f"- {story}: {count}")
        if counts_area:
            lines.append("")
            lines.append("By area:")
            for area, count in counts_area.items():
                lines.append(f"- {area}: {count}")
        items = bugs.get("items") or []
        if items:
            lines.append("")
            for item in items:
                if not isinstance(item, Mapping):
                    continue
                label = (
                    item.get("key")
                    or item.get("summary")
                    or item.get("action")
                    or item.get("classification")
                    or "bug"
                )
                detail = item.get("error") or item.get("heal_refused") or item.get("summary") or ""
                story = item.get("story_key") or ""
                area = item.get("area") or ""
                suffix_parts = []
                if story:
                    suffix_parts.append(f"story {story}")
                if area and area != "unspecified":
                    suffix_parts.append(f"area {area}")
                suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
                if detail and detail != label:
                    lines.append(f"- {label}: {detail}{suffix}")
                else:
                    lines.append(f"- {label}{suffix}")
        elif not counts_story and not counts_area:
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
        notes = sections["evidence"].get("notes") or []
        if notes:
            lines.append("")
            lines.append("Notes:")
            for item in notes:
                if not isinstance(item, Mapping):
                    continue
                text = item.get("text") or ""
                if not text:
                    continue
                scope = item.get("scope") or "note"
                name = item.get("case_name") or item.get("case_id") or ""
                rid = item.get("run_id") or ""
                label = f"{scope}"
                if name:
                    label += f" · {name}"
                if rid:
                    label += f" · run {rid}"
                lines.append(f"- {label}: {text}")
        lines.append("")

    if "known_issues" in sections and isinstance(sections["known_issues"], Mapping):
        known = sections["known_issues"]
        lines.append("## Known issues")
        lines.append("")
        lines.append(
            f"Count: {known.get('count', 0)} (labelled known; not new regressions)"
        )
        items = known.get("items") or []
        if items:
            for item in items:
                if not isinstance(item, Mapping):
                    continue
                name = item.get("case_name") or item.get("case_id") or "case"
                key = item.get("jira_key") or ""
                note = item.get("note") or ""
                result = item.get("result") or ""
                bits = [f"known · {name}"]
                if result:
                    bits.append(str(result))
                if key:
                    bits.append(str(key))
                if note:
                    bits.append(str(note))
                lines.append("- " + " — ".join(bits))
        else:
            lines.append("None linked.")
        lines.append("")

    if "traceability" in sections and isinstance(sections["traceability"], Mapping):
        matrix = sections["traceability"]
        lines.append("## Traceability")
        lines.append("")
        lines.append(f"Rows: {matrix.get('count', 0)}")
        lines.append("")
        lines.append("| story | cases | last result | bugs | known |")
        lines.append("| --- | --- | --- | --- | --- |")
        rows = matrix.get("rows") or []
        if rows:
            for item in rows:
                if not isinstance(item, Mapping):
                    continue
                story = item.get("story_key") or ""
                cases_n = item.get("case_count", 0)
                last = item.get("last_result") or "not_loaded"
                bugs = ", ".join(str(b) for b in (item.get("linked_bug_keys") or [])) or "—"
                known = "yes" if item.get("known_issue") else "no"
                lines.append(f"| {story} | {cases_n} | {last} | {bugs} | {known} |")
        else:
            lines.append("| — | 0 | not_loaded | — | no |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
