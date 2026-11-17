"""Read-only export pack for a plan case run (KAN-213 / F6 / FR-REP-3).

Writes a self-contained folder someone can open without this app:
report, matrix, and evidence (respecting section toggles). Secrets are
redacted per E3. Pack is labelled with security level and time.
Cloud shared drive is out of scope — local folder only.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from plans.run_report import build_result_for_run
from reports.redact import redact_evidence_index, redact_export_payload
from reports.sections import (
    build_sections,
    load_report_sections,
    normalize_sections,
    render_markdown,
)
from settings.store import app_data_dir, get_security_level

PACK_FORMAT = 1
_REPO = Path(__file__).resolve().parents[1]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _utcnow_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def export_packs_dir() -> Path:
    """Local packs root — never inside the repo; never a cloud mount default."""
    override = os.getenv("AI_TESTING_EXPORT_PACKS")
    if override:
        path = Path(override)
    else:
        path = app_data_dir() / "export_packs"
    resolved = path.resolve()
    repo = _REPO.resolve()
    if resolved == repo or repo in resolved.parents:
        raise RuntimeError("refusing to write export packs inside the repo")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _last_pointer_path() -> Path:
    return export_packs_dir() / "last_export.json"


def _safe_segment(raw: str, fallback: str = "pack") -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (raw or "").strip())
    text = text.strip("_")[:48]
    return text or fallback


def _matrix_markdown(rows: list[dict[str, Any]], count: int) -> str:
    lines = [
        "# Traceability matrix",
        "",
        f"Rows: {count}",
        "",
        "| story | cases | last result | bugs | known |",
        "| --- | --- | --- | --- | --- |",
    ]
    if rows:
        for item in rows:
            if not isinstance(item, dict):
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
    return "\n".join(lines)


def _copy_evidence_files(
    evidence_items: list[Any],
    dest_dir: Path,
) -> list[dict[str, str]]:
    """Copy evidence files into the pack; return relative index entries."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str]] = []
    for idx, item in enumerate(evidence_items or []):
        path_str = ""
        kind = "path"
        if isinstance(item, dict):
            path_str = str(item.get("path") or "").strip()
            kind = str(item.get("kind") or "path")
        else:
            path_str = str(item or "").strip()
            if path_str.lower().endswith(".png"):
                kind = "screenshot"
        if not path_str:
            continue
        src = Path(path_str)
        if not src.is_file():
            copied.append(
                {
                    "kind": kind,
                    "path": path_str,
                    "copied": "missing",
                    "note": "Source file not found on this machine.",
                }
            )
            continue
        name = f"{idx:02d}_{_safe_segment(src.name, 'evidence')}{src.suffix}"
        target = dest_dir / name
        try:
            shutil.copy2(src, target)
            copied.append(
                {
                    "kind": kind,
                    "path": f"evidence/{name}",
                    "source_name": src.name,
                    "copied": "ok",
                }
            )
        except OSError as exc:
            copied.append(
                {
                    "kind": kind,
                    "path": path_str,
                    "copied": "error",
                    "note": str(exc)[:160],
                }
            )
    return copied


def _write_last_pointer(meta: dict[str, Any]) -> None:
    path = _last_pointer_path()
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def last_export_pack() -> dict[str, Any]:
    """HUD-friendly summary of the newest pack (no full machine tree)."""
    empty = {
        "status": "ok",
        "available": False,
        "last_export_time": None,
        "security_level": None,
        "pack_id": None,
        "folder_name": None,
        "cloud": False,
        "requires_app": False,
        "home_only": True,
        "message": "No read-only export pack yet.",
    }
    try:
        pointer = _last_pointer_path()
    except RuntimeError:
        return {**empty, "status": "error", "error": "packs_dir_refused"}
    if not pointer.is_file():
        return empty
    try:
        data = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return empty
    if not isinstance(data, dict):
        return empty
    return {
        "status": "ok",
        "available": True,
        "last_export_time": data.get("exported_at") or data.get("timestamp"),
        "security_level": data.get("security_level"),
        "pack_id": data.get("pack_id"),
        "folder_name": data.get("folder_name"),
        "plan_id": data.get("plan_id"),
        "case_id": data.get("case_id"),
        "run_id": data.get("run_id"),
        "redaction_hits": data.get("redaction_hits", 0),
        "cloud": False,
        "requires_app": False,
        "home_only": True,
        "message": data.get("message")
        or f"Last pack {data.get('folder_name') or ''} at {data.get('exported_at') or ''}".strip(),
    }


def export_pack_status() -> dict[str, Any]:
    """Status for GET /api/export-pack — policy + last pack."""
    last = last_export_pack()
    try:
        root = str(export_packs_dir())
    except RuntimeError:
        root = ""
    return {
        "status": "ok",
        "format": PACK_FORMAT,
        "cloud": False,
        "cloud_shared_drive_default": False,
        "requires_app": False,
        "opens_without_app": True,
        "redaction": "E3",
        "packs_root_configured": bool(root),
        "last": last,
        "home_widget": {
            "id": "hud-export-last",
            "shows": "last_export_time",
            "home_only": True,
        },
    }


def create_export_pack(
    plan_id: str,
    case_id: str,
    run_id: str,
    *,
    sections: Mapping[str, Any] | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Build a read-only pack folder for one run."""
    from plugins.heal_policy import list_pending_heals

    lvl = (level or get_security_level()).strip().upper()
    built = build_result_for_run(plan_id, case_id, run_id, level=lvl)
    if built.get("status") != "ok":
        return built

    enabled = (
        normalize_sections(sections)
        if sections is not None
        else load_report_sections()
    )
    result_body = built["result"] if isinstance(built.get("result"), dict) else {}
    request_text = str(built.get("request_text") or "")
    section_payload = build_sections(result_body, request_text, enabled)

    payload: dict[str, Any] = {
        "timestamp": _utcnow_iso(),
        "request": request_text,
        "session_id": "export-pack",
        "result": result_body,
        "sections": section_payload,
        "pack": {
            "kind": "read_only_export_pack",
            "format": PACK_FORMAT,
            "requires_app": False,
            "cloud": False,
        },
    }
    payload = redact_export_payload(payload)
    section_payload = (
        payload.get("sections")
        if isinstance(payload.get("sections"), dict)
        else section_payload
    )
    redaction = (
        payload.get("redaction") if isinstance(payload.get("redaction"), dict) else {}
    )
    hits = int(redaction.get("redaction_hits") or 0)
    shot_warn = redaction.get("screenshot_redaction_warning")

    stamp = _utcnow_stamp()
    base_id = f"{lvl}_{stamp}_{_safe_segment(run_id, 'run')}"
    try:
        root = export_packs_dir()
    except RuntimeError as exc:
        return {
            "status": "error",
            "error": "packs_dir_refused",
            "message": str(exc),
            "security_level": lvl,
        }
    pack_id = base_id
    folder = root / pack_id
    number = 2
    while folder.exists():
        pack_id = f"{base_id}-{number}"
        folder = root / pack_id
        number += 1
    folder.mkdir(parents=True, exist_ok=False)

    # Label + human README (open without the app).
    label_lines = [
        f"Security level: {lvl}",
        f"Exported at (UTC): {payload.get('timestamp')}",
        f"Plan: {plan_id}",
        f"Case: {case_id}",
        f"Run: {run_id}",
        "Requires this app: no",
        "Cloud shared drive: not used (local folder only)",
        f"Redaction hits: {hits}",
    ]
    (folder / "LABEL.txt").write_text("\n".join(label_lines) + "\n", encoding="utf-8")

    readme = [
        "# Read-only export pack",
        "",
        "Open this folder in any text editor or Markdown viewer — you do **not**",
        "need the AI Testing Agent app.",
        "",
        f"- **Security level:** {lvl}",
        f"- **Exported at (UTC):** {payload.get('timestamp')}",
        f"- **Plan / case / run:** `{plan_id}` / `{case_id}` / `{run_id}`",
        f"- **Redaction hits:** {hits}",
        "",
        "## Contents",
        "",
        "- `report.md` / `report.json` — report (sections as configured)",
    ]
    if enabled.get("traceability"):
        readme.append("- `matrix.md` / `matrix.json` — traceability matrix")
    if enabled.get("evidence"):
        readme.append("- `evidence/` — copied evidence files + `index.json`")
    readme.extend(
        [
            "- `LABEL.txt` — level and time stamp",
            "- `manifest.json` — machine-readable pack metadata",
            "",
            "Secrets in text fields are redacted (E3). Screenshots are not OCR-wiped;",
            "review images before sharing.",
            "",
        ]
    )
    if shot_warn:
        readme.append(f"> {shot_warn}")
        readme.append("")
    (folder / "README.md").write_text("\n".join(readme), encoding="utf-8")

    (folder / "report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (folder / "report.md").write_text(
        render_markdown(section_payload), encoding="utf-8"
    )

    files_written = ["README.md", "LABEL.txt", "report.md", "report.json"]

    # Matrix as separate files when the section is on.
    if enabled.get("traceability"):
        matrix_block = (
            section_payload.get("traceability")
            if isinstance(section_payload.get("traceability"), dict)
            else {}
        )
        rows = list(matrix_block.get("rows") or [])
        matrix_doc = {
            "label": "traceability matrix",
            "count": matrix_block.get("count", len(rows)),
            "rows": rows,
            "security_level": lvl,
            "exported_at": payload.get("timestamp"),
            "requires_app": False,
        }
        (folder / "matrix.json").write_text(
            json.dumps(matrix_doc, indent=2), encoding="utf-8"
        )
        (folder / "matrix.md").write_text(
            _matrix_markdown(rows, int(matrix_doc["count"] or 0)),
            encoding="utf-8",
        )
        files_written.extend(["matrix.md", "matrix.json"])

    evidence_copied: list[dict[str, str]] = []
    if enabled.get("evidence"):
        evidence_src = result_body.get("evidence") or []
        if not evidence_src and result_body.get("screenshot"):
            evidence_src = [
                {"kind": "screenshot", "path": str(result_body.get("screenshot"))}
            ]
        evidence_copied = _copy_evidence_files(list(evidence_src), folder / "evidence")
        index = {
            "run_id": run_id,
            "plan_id": plan_id,
            "case_id": case_id,
            "created_at": payload.get("timestamp"),
            "security_level": lvl,
            "items": evidence_copied,
            "screenshot_redaction_warning": shot_warn,
        }
        index = redact_evidence_index(index)
        (folder / "evidence" / "index.json").write_text(
            json.dumps(index, indent=2), encoding="utf-8"
        )
        files_written.append("evidence/index.json")
        for entry in evidence_copied:
            if entry.get("copied") == "ok" and entry.get("path"):
                files_written.append(str(entry["path"]))

    heals = list_pending_heals(run_id=str(run_id or "").strip())
    manifest = {
        "format": PACK_FORMAT,
        "pack_id": pack_id,
        "folder_name": pack_id,
        "kind": "read_only_export_pack",
        "security_level": lvl,
        "exported_at": payload.get("timestamp"),
        "plan_id": plan_id,
        "case_id": case_id,
        "run_id": run_id,
        "sections": enabled,
        "files": files_written,
        "redaction_hits": hits,
        "screenshot_redaction_warning": shot_warn,
        "requires_app": False,
        "cloud": False,
        "cloud_shared_drive_default": False,
        "heal_pending_count": heals.get("count") or 0,
        "evidence_count": len(evidence_copied),
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    files_written.append("manifest.json")
    manifest["files"] = files_written

    pointer = {
        "pack_id": pack_id,
        "folder_name": pack_id,
        "exported_at": payload.get("timestamp"),
        "security_level": lvl,
        "plan_id": plan_id,
        "case_id": case_id,
        "run_id": run_id,
        "redaction_hits": hits,
        "path": str(folder),
        "message": (
            f"Pack {pack_id} · level {lvl} · "
            f"{payload.get('timestamp')} (open folder without this app)"
        ),
    }
    _write_last_pointer(pointer)

    msg = (
        f"Wrote read-only pack {pack_id} under local export_packs "
        f"(level {lvl}). Open README.md without this app. "
        f"Redaction hits: {hits}."
    )
    if shot_warn:
        msg += f" {shot_warn}"

    return {
        "status": "ok",
        "security_level": lvl,
        "pack_id": pack_id,
        "folder_name": pack_id,
        "path": str(folder),
        "exported_at": payload.get("timestamp"),
        "sections": enabled,
        "files": files_written,
        "redaction_hits": hits,
        "screenshot_redaction_warning": shot_warn,
        "requires_app": False,
        "cloud": False,
        "cloud_shared_drive_default": False,
        "heal_pending_count": heals.get("count") or 0,
        "manifest": manifest,
        "message": msg,
    }
