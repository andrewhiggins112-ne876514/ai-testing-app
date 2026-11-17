"""Draft an in-app plan from Jira story/document/project (KAN-131 / KAN-161 / FR-PLAN-3).

Read-only against Jira — never creates, updates, or comments on issues.
Cases keep the Jira key and (when used) the document name, plus a source_ref
showing why the case was drafted (AC bullet or document line).
"""
from __future__ import annotations

import re
from typing import Any

from plans.store import add_case, create_plan, get_plan, upsert_jira_snapshot

_BULLET = re.compile(r"^[ \t]*(?:[-*]|\d+[.)])\s+(.+)$")
_NUMBERED = re.compile(r"^[ \t]*\d+[.)]\s+(.+)$")

# C3 — visible batch cap for project-wide draft (KAN-161)
DEFAULT_PROJECT_BATCH = 5
MAX_PROJECT_BATCH = 25
MIN_PROJECT_BATCH = 1
_DEFAULT_PROJECT_TYPES = ("Story",)


def clamp_project_batch(value: Any) -> int:
    """Visible batch size: 1..MAX_PROJECT_BATCH (default DEFAULT_PROJECT_BATCH)."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PROJECT_BATCH
    return min(MAX_PROJECT_BATCH, max(MIN_PROJECT_BATCH, number))


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


def _bullets_from_issue_fields(
    *,
    summary: str,
    acceptance: str,
    description: str,
) -> list[str]:
    bullets = _split_ac_bullets(acceptance)
    if not bullets and description:
        # Fall back to short description lines when no AC section exists.
        for line in description.split("\n"):
            text = line.strip()
            if len(text) >= 12 and not text.lower().startswith(
                (
                    "intro",
                    "who this",
                    "user story",
                    "requirements",
                    "behaviour",
                    "out of scope",
                )
            ):
                bullets.append(text[:240])
            if len(bullets) >= 8:
                break
    if not bullets:
        bullets = [f"Verify: {summary}"]
    return bullets


def _add_cases_from_issue(
    plan_id: str,
    *,
    key: str,
    summary: str,
    acceptance: str,
    description: str,
    level: str | None = None,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for bullet in _bullets_from_issue_fields(
        summary=summary, acceptance=acceptance, description=description
    ):
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
    return cases


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
    cases = _add_cases_from_issue(
        plan_id,
        key=key,
        summary=summary,
        acceptance=acceptance,
        description=description,
        level=level,
    )
    upsert_jira_snapshot(
        plan_id,
        key,
        summary=summary,
        acceptance_criteria=acceptance,
        stale=False,
        level=level,
    )

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


async def draft_plan_from_project(
    *,
    batch_size: Any = DEFAULT_PROJECT_BATCH,
    project: str | None = None,
    issue_types: Any = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Draft one local plan from up to batch_size issues in the configured project.

    Uses list_stories + read_issue (FR-JIRA-1 / FR-JIRA-6 backoff). Never writes to Jira.
    Person must review the plan before running a case (A7 path unchanged).
    """
    from plugins.jira_plugin import list_stories, read_issue
    from settings.store import load_settings

    capped = clamp_project_batch(batch_size)
    settings = load_settings()
    project_key = (
        str(project or "").strip().upper()
        or str(settings.get("jira_project") or "").strip().upper()
    )
    if not project_key:
        return {
            "status": "error",
            "error": "project_required",
            "message": (
                "Set jira_project in App Settings (or pass project) before "
                "project-wide draft."
            ),
            "jira_write": False,
            "batch_size": capped,
            "max_batch_size": MAX_PROJECT_BATCH,
        }

    types = issue_types if issue_types is not None else list(_DEFAULT_PROJECT_TYPES)
    listed = await list_stories(
        project_key,
        max=capped,
        issue_types=types,
        include_description=False,
    )
    if listed.get("status") != "ok":
        return {
            "status": "error",
            "error": listed.get("status") or listed.get("error") or "jira_list_failed",
            "message": listed.get("message") or f"Could not list issues in {project_key}.",
            "jira_write": False,
            "batch_size": capped,
            "max_batch_size": MAX_PROJECT_BATCH,
            "project": project_key,
        }

    rows = list(listed.get("stories") or [])[:capped]
    if not rows:
        return {
            "status": "error",
            "error": "no_issues",
            "message": f"No matching issues in project {project_key} for this batch.",
            "jira_write": False,
            "batch_size": capped,
            "max_batch_size": MAX_PROJECT_BATCH,
            "project": project_key,
        }

    keys = [str(r.get("key") or "").strip().upper() for r in rows if r.get("key")]
    keys = [k for k in keys if k]
    intent_lines = [
        f"Project-wide draft from {project_key} (batch {len(keys)} / cap {capped}).",
        "Review cases before any run. Nothing was written to Jira.",
        "Issues in this batch:",
    ]
    for row in rows:
        k = str(row.get("key") or "").strip()
        if k:
            intent_lines.append(f"- {k}: {str(row.get('summary') or '').strip()[:160]}")

    created = create_plan(
        name=f"Project draft {project_key} (batch {len(keys)})",
        intent="\n".join(intent_lines)[:4000],
        sources={"jira_keys": keys, "documents": []},
        level=level,
    )
    if created.get("status") != "ok":
        return {**created, "jira_write": False, "batch_size": capped}

    plan = created["plan"]
    plan_id = plan["id"]
    drafted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    case_total = 0

    for key in keys:
        issue = await read_issue(key)
        if issue.get("status") != "ok":
            skipped.append(
                {
                    "key": key,
                    "error": issue.get("status") or issue.get("error") or "read_failed",
                    "message": issue.get("message") or f"Could not read {key}.",
                }
            )
            continue
        summary = str(issue.get("summary") or key).strip()
        acceptance = str(issue.get("acceptance_criteria") or "").strip()
        description = str(issue.get("description") or "").strip()
        cases = _add_cases_from_issue(
            plan_id,
            key=key,
            summary=summary,
            acceptance=acceptance,
            description=description,
            level=level,
        )
        upsert_jira_snapshot(
            plan_id,
            key,
            summary=summary,
            acceptance_criteria=acceptance,
            stale=False,
            level=level,
        )
        case_total += len(cases)
        drafted.append(
            {
                "key": key,
                "summary": summary,
                "case_count": len(cases),
            }
        )

    refreshed = get_plan(plan_id, level=level)
    note = listed.get("note")
    msg = (
        f"Drafted plan from {len(drafted)} issue(s) in {project_key} "
        f"(batch cap {capped}) with {case_total} case(s). "
        "Review before running. Nothing was written to Jira."
    )
    if skipped:
        msg += f" Skipped {len(skipped)} issue(s) that could not be read."
    if note:
        msg += f" ({note})"

    # C4 — after project draft, list coverage gaps (no auto-create).
    from plans.coverage import plan_coverage_gaps

    coverage = await plan_coverage_gaps(
        plan_id,
        project=project_key,
        issue_types=types,
        level=level,
        include_project_list=True,
    )
    if coverage.get("status") == "ok":
        gaps_n = int(coverage.get("no_case_count") or 0)
        disabled_n = int(coverage.get("all_disabled_count") or 0)
        msg += (
            f" Coverage gaps: {gaps_n} with no case; "
            f"{disabled_n} with all cases disabled."
        )

    return {
        "status": "ok",
        "message": msg,
        "jira_write": False,
        "project": project_key,
        "batch_size": capped,
        "max_batch_size": MAX_PROJECT_BATCH,
        "default_batch_size": DEFAULT_PROJECT_BATCH,
        "issues_drafted": drafted,
        "issues_skipped": skipped,
        "issue_count": len(drafted),
        "case_count": case_total,
        "list_note": note,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else plan,
        "review_required": True,
        "auto_run": False,
        "coverage_gaps": coverage if coverage.get("status") == "ok" else None,
        "cases_created_for_gaps": False,
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
