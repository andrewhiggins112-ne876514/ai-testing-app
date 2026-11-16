"""Draft an in-app plan from one Jira story and optional document (KAN-131 / FR-PLAN-3).

Read-only against Jira — never creates, updates, or comments on issues.
Cases keep the Jira key and (when used) the document name, plus a source_ref
showing why the case was drafted (AC bullet or document line).
"""
from __future__ import annotations

import re
from typing import Any

from plans.store import add_case, create_plan, get_plan

_BULLET = re.compile(r"^[ \t]*(?:[-*]|\d+[.)])\s+(.+)$")
_NUMBERED = re.compile(r"^[ \t]*\d+[.)]\s+(.+)$")


def _split_ac_bullets(acceptance: str) -> list[str]:
    lines: list[str] = []
    for raw in (acceptance or "").replace("\r\n", "\n").split("\n"):
        text = raw.strip()
        if not text:
            continue
        match = _BULLET.match(text) or _NUMBERED.match(text)
        bullet = (match.group(1) if match else text).strip()
        if len(bullet) < 3:
            continue
        if bullet not in lines:
            lines.append(bullet[:240])
    return lines


def _case_name_from_bullet(bullet: str, *, prefix: str = "") -> str:
    body = " ".join((bullet or "").split())
    if prefix:
        body = f"{prefix}{body}"
    return (body[:100] or "Drafted case").strip()


async def draft_plan_from_issue(
    issue_key: str,
    *,
    document_text: str = "",
    document_name: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Create a local plan from one issue key (+ optional document). No Jira writes."""
    from plugins.jira_plugin import read_issue

    key = (issue_key or "").strip().upper()
    if not key:
        return {
            "status": "error",
            "error": "issue_key_required",
            "message": "Provide a Jira issue key (e.g. KAN-131).",
        }

    issue = await read_issue(key)
    if issue.get("status") != "ok":
        return {
            "status": "error",
            "error": issue.get("status") or issue.get("error") or "jira_read_failed",
            "message": issue.get("message") or f"Could not read {key}.",
            "jira_write": False,
        }

    summary = str(issue.get("summary") or key).strip()
    acceptance = str(issue.get("acceptance_criteria") or "").strip()
    description = str(issue.get("description") or "").strip()
    bullets = _split_ac_bullets(acceptance)
    if not bullets and description:
        # Fall back to short description lines when no AC section exists.
        for line in description.split("\n"):
            text = line.strip()
            if len(text) >= 12 and not text.lower().startswith(
                ("intro", "who this", "user story", "requirements", "behaviour", "out of scope")
            ):
                bullets.append(text[:240])
            if len(bullets) >= 8:
                break
    if not bullets:
        bullets = [f"Verify: {summary}"]

    doc_name = (document_name or "").strip()[:200]
    sources: dict[str, list[str]] = {"jira_keys": [key], "documents": []}
    if doc_name:
        sources["documents"] = [doc_name]

    intent_parts = [f"Draft from {key}: {summary}"]
    if acceptance:
        intent_parts.append("Acceptance criteria:\n" + acceptance[:3000])
    created = create_plan(
        name=f"Plan for {key}",
        intent="\n\n".join(intent_parts)[:4000],
        sources=sources,
        level=level,
    )
    if created.get("status") != "ok":
        return created
    plan = created["plan"]
    plan_id = plan["id"]
    cases: list[dict[str, Any]] = []

    for bullet in bullets:
        added = add_case(
            plan_id,
            _case_name_from_bullet(bullet),
            jira_key=key,
            tags=["draft", "jira"],
            note="",
            enabled=True,
            source_kind="jira",
            source_ref=bullet[:300],
            level=level,
        )
        if added.get("status") == "ok" and added.get("case"):
            cases.append(added["case"])

    doc_cases: list[dict[str, Any]] = []
    if (document_text or "").strip():
        doc_result = add_document_draft_cases(
            plan_id,
            document_text=document_text,
            document_name=doc_name or "uploaded-document",
            jira_key=key,
            level=level,
        )
        if doc_result.get("status") == "ok":
            doc_cases = list(doc_result.get("cases") or [])

    refreshed = get_plan(plan_id, level=level)
    return {
        "status": "ok",
        "message": (
            f"Drafted plan from {key} with {len(cases)} AC case(s)"
            + (f" and {len(doc_cases)} document case(s)" if doc_cases else "")
            + ". Nothing was written to Jira."
        ),
        "jira_write": False,
        "issue_key": key,
        "summary": summary,
        "acceptance_criteria": acceptance,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else plan,
        "case_count": len(cases) + len(doc_cases),
        "document_name": doc_name or None,
    }


def add_document_draft_cases(
    plan_id: str,
    *,
    document_text: str,
    document_name: str = "uploaded-document",
    jira_key: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Append draft cases from document text only — does not rewrite Jira or settings."""
    from plugins.doc_ingest import extract_test_ideas
    from plans.store import get_plan, record_document_source

    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    ideas = extract_test_ideas(document_text or "", limit=20)
    if not ideas:
        # Soft fallback: first non-empty lines as draft ideas.
        for line in (document_text or "").replace("\r\n", "\n").split("\n"):
            text = " ".join(line.split()).strip()
            if len(text) >= 12:
                ideas.append(text[:240])
            if len(ideas) >= 10:
                break
    if not ideas:
        return {
            "status": "error",
            "error": "no_ideas",
            "message": "No draft cases found in the document.",
            "jira_write": False,
        }

    doc_name = (document_name or "uploaded-document").strip()[:200] or "uploaded-document"
    key = (jira_key or "").strip().upper()
    cases_out: list[dict[str, Any]] = []
    for idea in ideas:
        added = add_case(
            plan_id,
            _case_name_from_bullet(idea, prefix="Doc: "),
            jira_key=key,
            tags=["draft", "document"],
            note="",
            enabled=True,
            source_kind="document",
            source_ref=idea[:300],
            level=level,
        )
        if added.get("status") == "ok" and added.get("case"):
            cases_out.append(added["case"])

    record_document_source(plan_id, doc_name, jira_key=key, level=level)
    refreshed = get_plan(plan_id, level=level)

    return {
        "status": "ok",
        "message": f"Added {len(cases_out)} draft case(s) from {doc_name}. Nothing written to Jira.",
        "jira_write": False,
        "document_name": doc_name,
        "cases": cases_out,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else None,
    }
