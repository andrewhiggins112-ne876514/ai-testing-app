"""Home-PC Operate Documents demo pack (KAN-381 / OPERATE-4 / FR-LEARN-1).

Synthetic functional-spec + user-guide fixtures under fixtures/operate_docs/.
Seed installs them into OFFICIAL Documents uploads (consent for synthetic data).
Draft-from-document uses existing plans.draft.add_document_draft_cases — no Jira writes.
Never ships employer/customer documents.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "operate_docs"
MARKER = "OPERATE_DOCS_DEMO=1"
SPEC_NAME = "operate-demo-functional-spec.md"
GUIDE_NAME = "operate-demo-user-guide.md"
SPEC_SOURCE = "functional_spec.md"
GUIDE_SOURCE = "user_guide.md"
PLAN_NAME = "OPERATE documents draft"
SOURCE_KIND = "operate-docs"
DEFAULT_LEVEL = "OFFICIAL"


def fixture_paths() -> dict[str, Path]:
    return {
        "spec": FIXTURE_DIR / SPEC_SOURCE,
        "guide": FIXTURE_DIR / GUIDE_SOURCE,
    }


def fixture_present() -> dict[str, Any]:
    paths = fixture_paths()
    details: dict[str, Any] = {}
    all_ok = True
    for key, path in paths.items():
        exists = path.is_file()
        marker = False
        text = ""
        if exists:
            try:
                text = path.read_text(encoding="utf-8")
                marker = MARKER in text
            except OSError:
                marker = False
        ok = bool(exists and marker and len(text.strip()) >= 40)
        details[key] = {
            "path": str(path),
            "exists": exists,
            "marker": marker,
            "ok": ok,
            "bytes": len(text.encode("utf-8")) if text else 0,
        }
        if not ok:
            all_ok = False
    return {
        "ok": all_ok,
        "dir": str(FIXTURE_DIR),
        "marker": MARKER,
        "files": details,
        "upload_names": [SPEC_NAME, GUIDE_NAME],
    }


def _read_fixture(source_name: str) -> str:
    path = FIXTURE_DIR / source_name
    return path.read_text(encoding="utf-8")


def _find_upload_by_filename(level: str, filename: str) -> dict[str, Any] | None:
    from plugins.doc_uploads import list_uploads

    listed = list_uploads(level=level, include_bodies=False)
    for row in listed.get("uploads") or []:
        if str(row.get("filename") or "").strip() == filename:
            return row
    return None


def _find_plan_by_name(level: str, name: str) -> dict[str, Any] | None:
    from plans.store import get_plan, list_plans

    listed = list_plans(level)
    for row in listed.get("plans") or []:
        if str(row.get("name") or "").strip() == name:
            full = get_plan(str(row["id"]), level=level)
            if full.get("status") == "ok":
                return full.get("plan")
    return None


def seed_operate_docs(
    *,
    level: str = DEFAULT_LEVEL,
    force: bool = False,
) -> dict[str, Any]:
    """Install demo docs into Documents uploads for the given level (default OFFICIAL).

    Idempotent: skips filenames already present unless force=True.
    Consent is set true — synthetic lab content installed on purpose.
    Does not switch the active security level; writes into the named level tree.
    """
    from plugins.doc_uploads import list_uploads, record_upload, set_upload_consent

    present = fixture_present()
    if not present.get("ok"):
        return {
            "status": "error",
            "message": (
                "Operate docs fixtures missing or incomplete under "
                f"fixtures/operate_docs/ ({present.get('dir')})."
            ),
            "fixture": present,
        }

    lvl = (level or DEFAULT_LEVEL).strip().upper() or DEFAULT_LEVEL
    if lvl not in {"PERSONAL", "OFFICIAL", "SECRET"}:
        return {
            "status": "error",
            "message": f"Unsupported security level for seed: {level!r}",
            "fixture": present,
        }

    pack = [
        (SPEC_SOURCE, SPEC_NAME),
        (GUIDE_SOURCE, GUIDE_NAME),
    ]
    created: list[dict[str, Any]] = []
    reused: list[dict[str, Any]] = []
    uploads_out: list[dict[str, Any]] = []

    for source_name, upload_name in pack:
        existing = _find_upload_by_filename(lvl, upload_name)
        if existing and not force:
            uid = str(existing.get("id") or "")
            if uid and not bool(existing.get("consent")):
                set_upload_consent(uid, consent=True, level=lvl)
                existing = _find_upload_by_filename(lvl, upload_name) or existing
            reused.append(existing)
            uploads_out.append(existing)
            continue
        body = _read_fixture(source_name)
        recorded = record_upload(
            filename=upload_name,
            text=body,
            consent=True,
            level=lvl,
        )
        created.append(recorded)
        uploads_out.append(recorded)

    listed = list_uploads(level=lvl, include_bodies=False)
    names = {str(u.get("filename") or "") for u in (listed.get("uploads") or [])}
    both_present = SPEC_NAME in names and GUIDE_NAME in names

    return {
        "status": "ok" if both_present else "error",
        "message": (
            f"Documents demo pack ready on {lvl}: "
            f"{len(created)} created, {len(reused)} reused."
            if both_present
            else "Seed finished but both demo filenames are not listed."
        ),
        "created": bool(created),
        "security_level": lvl,
        "uploads": uploads_out,
        "created_uploads": created,
        "reused_uploads": reused,
        "fixture": present,
        "source_kind": SOURCE_KIND,
        "both_present": both_present,
    }


def draft_plan_from_operate_docs(
    *,
    level: str = DEFAULT_LEVEL,
    plan_name: str = PLAN_NAME,
    force_new_plan: bool = False,
    seed_first: bool = True,
) -> dict[str, Any]:
    """Ensure demo docs are seeded, then draft editable cases into a local plan.

    Uses add_document_draft_cases only — never writes to Jira or Settings.
    Idempotent: if the named plan already has document-sourced cases, return it.
    """
    from plans.draft import add_document_draft_cases
    from plans.store import create_plan, get_plan
    from plugins.doc_uploads import read_upload_body

    lvl = (level or DEFAULT_LEVEL).strip().upper() or DEFAULT_LEVEL
    seed_out: dict[str, Any] | None = None
    if seed_first:
        seed_out = seed_operate_docs(level=lvl)
        if seed_out.get("status") != "ok":
            return {
                "status": "error",
                "message": seed_out.get("message") or "seed failed",
                "seed": seed_out,
                "jira_write": False,
            }

    bodies: list[tuple[str, str]] = []
    for upload_name, source_name in (
        (SPEC_NAME, SPEC_SOURCE),
        (GUIDE_NAME, GUIDE_SOURCE),
    ):
        row = _find_upload_by_filename(lvl, upload_name)
        text = ""
        if row and row.get("id"):
            text = read_upload_body(str(row["id"]), level=lvl) or ""
        if not text.strip():
            text = _read_fixture(source_name)
        bodies.append((upload_name, text))

    existing = None if force_new_plan else _find_plan_by_name(lvl, plan_name)
    if existing:
        cases = list((existing.get("suite") or {}).get("cases") or [])
        doc_cases = [
            c
            for c in cases
            if str((c.get("source") or {}).get("kind") or "") == "document"
            or "document" in (c.get("tags") or [])
        ]
        if doc_cases:
            return {
                "status": "ok",
                "message": (
                    f"Plan already present ({existing.get('id')}) with "
                    f"{len(doc_cases)} document-sourced case(s). Nothing written to Jira."
                ),
                "jira_write": False,
                "created_plan": False,
                "plan_id": existing.get("id"),
                "plan_name": plan_name,
                "case_count": len(doc_cases),
                "cases": doc_cases,
                "documents": [n for n, _ in bodies],
                "seed": seed_out,
                "plan": existing,
                "review_required": True,
                "auto_run": False,
                "source_kind": SOURCE_KIND,
            }

    created_plan = False
    plan_id = str((existing or {}).get("id") or "") if existing else ""
    if not plan_id:
        created = create_plan(
            plan_name,
            intent=(
                "Draft cases from OPERATE Documents demo pack "
                "(synthetic spec + user guide). Review before run."
            ),
            sources={
                "jira_keys": [],
                "documents": [SPEC_NAME, GUIDE_NAME],
            },
            level=lvl,
        )
        if created.get("status") != "ok":
            return {
                "status": "error",
                "message": created.get("message") or "create_plan failed",
                "create": created,
                "seed": seed_out,
                "jira_write": False,
            }
        plan = created.get("plan") or {}
        plan_id = str(plan.get("id") or "")
        created_plan = True

    cases_all: list[dict[str, Any]] = []
    draft_results: list[dict[str, Any]] = []
    for doc_name, text in bodies:
        drafted = add_document_draft_cases(
            plan_id,
            document_text=text,
            document_name=doc_name,
            jira_key="",
            level=lvl,
        )
        draft_results.append(
            {
                "document_name": doc_name,
                "status": drafted.get("status"),
                "case_count": len(drafted.get("cases") or []),
                "message": drafted.get("message"),
            }
        )
        if drafted.get("status") == "ok":
            cases_all.extend(list(drafted.get("cases") or []))

    refreshed = get_plan(plan_id, level=lvl)
    ok = refreshed.get("status") == "ok" and len(cases_all) > 0
    return {
        "status": "ok" if ok else "error",
        "message": (
            f"Drafted {len(cases_all)} case(s) into '{plan_name}' from demo docs. "
            "Nothing written to Jira."
            if ok
            else "Draft from operate docs produced no cases."
        ),
        "jira_write": False,
        "created_plan": created_plan,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "case_count": len(cases_all),
        "cases": cases_all,
        "documents": [n for n, _ in bodies],
        "draft_results": draft_results,
        "seed": seed_out,
        "plan": refreshed.get("plan") if refreshed.get("status") == "ok" else None,
        "review_required": True,
        "auto_run": False,
        "source_kind": SOURCE_KIND,
    }
