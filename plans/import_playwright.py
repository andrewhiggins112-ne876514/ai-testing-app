"""Import an existing Playwright project into the in-app suite (KAN-171 / C8).

Lists tests from a discovered Playwright project and adds them as plan cases.
External project files are never deleted or rewritten. Suites-area ``npx`` run
remains available via ``plugins.playwright_suite``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from plans.store import (
    add_case,
    create_plan,
    get_plan,
    record_playwright_source,
)
from plugins.playwright_suite import discover_suite, list_suite_tests


def encode_playwright_ref(
    *,
    suite_path: str,
    file: str | None = None,
    title: str | None = None,
    grep: str | None = None,
) -> str:
    """Stable JSON ref stored on case.source.ref for replay."""
    payload = {
        "suite_path": (suite_path or "").strip()[:500],
        "file": (file or "").strip().replace("\\", "/")[:300],
        "title": (title or "").strip()[:200],
        "grep": (grep or title or "").strip()[:200],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)[:300]


def decode_playwright_ref(ref: str) -> dict[str, str]:
    text = (ref or "").strip()
    if not text:
        return {"suite_path": "", "file": "", "title": "", "grep": ""}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {
                "suite_path": str(data.get("suite_path") or "").strip(),
                "file": str(data.get("file") or "").strip().replace("\\", "/"),
                "title": str(data.get("title") or "").strip(),
                "grep": str(data.get("grep") or data.get("title") or "").strip(),
            }
    except json.JSONDecodeError:
        pass
    # Legacy / plain path fallback
    return {"suite_path": text[:500], "file": "", "title": "", "grep": ""}


def _case_name(test: dict[str, Any]) -> str:
    title = str(test.get("title") or "").strip()
    file_name = str(test.get("file") or "").strip().replace("\\", "/")
    if title and file_name and title != file_name:
        return f"{title} ({file_name})"[:120]
    return (title or file_name or "Playwright test")[:120]


def _existing_refs(plan: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for case in (plan.get("suite") or {}).get("cases") or []:
        if not isinstance(case, dict):
            continue
        src = case.get("source") if isinstance(case.get("source"), dict) else {}
        if str(src.get("kind") or "").lower() != "playwright":
            continue
        ref = str(src.get("ref") or "").strip()
        if ref:
            refs.add(ref)
    return refs


def import_playwright_project(
    suite_path: str = "",
    *,
    plan_id: str | None = None,
    plan_name: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Create or extend a plan with cases from a Playwright project.

    Does not delete or modify files under the external project.
    """
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    discovered = discover_suite(suite_path=suite_path or "")
    if discovered.get("status") != "ok":
        return {
            "status": "error",
            "error": discovered.get("error") or "discover_failed",
            "message": discovered.get("error")
            or discovered.get("message")
            or "Could not discover Playwright project.",
            "security_level": lvl,
            "external_files_deleted": False,
        }

    root = str(discovered.get("suite_path") or "").strip()
    listed = list_suite_tests(suite_path=root)
    if listed.get("status") != "ok":
        return {
            "status": "error",
            "error": listed.get("error") or "list_failed",
            "message": listed.get("error")
            or listed.get("message")
            or "Could not list Playwright tests.",
            "security_level": lvl,
            "suite_path": root,
            "external_files_deleted": False,
        }

    tests = list(listed.get("tests") or [])
    if not tests:
        return {
            "status": "error",
            "error": "no_tests",
            "message": "No Playwright tests found to import.",
            "security_level": lvl,
            "suite_path": root,
            "external_files_deleted": False,
        }

    pid = (plan_id or "").strip()
    created_new = False
    if pid:
        loaded = get_plan(pid, level=lvl)
        if loaded.get("status") != "ok":
            return {
                **loaded,
                "external_files_deleted": False,
            }
        plan = loaded["plan"]
    else:
        folder = Path(root).name or "Playwright project"
        name = (plan_name or "").strip() or f"Playwright: {folder}"
        created = create_plan(
            name,
            intent=f"Imported from Playwright project at {root}. External files unchanged.",
            sources={"playwright_suites": [root]},
            level=lvl,
        )
        if created.get("status") != "ok":
            return {**created, "external_files_deleted": False}
        plan = created["plan"]
        pid = plan["id"]
        created_new = True

    existing = _existing_refs(plan)
    cases_out: list[dict[str, Any]] = []
    skipped_dup = 0
    for test in tests:
        if not isinstance(test, dict):
            continue
        file_name = str(test.get("file") or "").strip().replace("\\", "/")
        title = str(test.get("title") or "").strip() or file_name
        grep = title if title != file_name else ""
        ref = encode_playwright_ref(
            suite_path=root,
            file=file_name,
            title=title,
            grep=grep or title,
        )
        if ref in existing:
            skipped_dup += 1
            continue
        tags = ["playwright", "imported"]
        lower_title = title.lower()
        if "smoke" in lower_title or "smoke" in file_name.lower():
            tags.append("smoke")
        added = add_case(
            pid,
            _case_name(test),
            tags=tags,
            note=f"Imported Playwright test. Project: {root}",
            enabled=True,
            source_kind="playwright",
            source_ref=ref,
            level=lvl,
        )
        if added.get("status") == "ok" and added.get("case"):
            cases_out.append(added["case"])
            existing.add(ref)

    record_playwright_source(pid, root, level=lvl)
    refreshed = get_plan(pid, level=lvl)

    return {
        "status": "ok",
        "message": (
            f"Imported {len(cases_out)} Playwright case(s) from {root}"
            + (f" ({skipped_dup} already present)." if skipped_dup else ".")
            + " External project files were not deleted."
        ),
        "security_level": lvl,
        "suite_path": root,
        "created_plan": created_new,
        "cases_added": len(cases_out),
        "cases_skipped_duplicate": skipped_dup,
        "cases": cases_out,
        "list_source": listed.get("source"),
        "external_files_deleted": False,
        "npx_suite_unchanged": True,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else None,
    }
