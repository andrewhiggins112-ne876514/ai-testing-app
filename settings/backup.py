"""Lab backup and restore (KAN-199 / E4 / FR-SET-1 / FR-SEC-1).

Copies plans (with embedded runs), evidence index bundles, and optionally
settings. Secrets (level credentials) are off by default. Restore requires
confirm and refuses to mix OFFICIAL and SECRET folders. No cloud backup.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from settings.store import (
    SECURITY_LEVELS,
    _SECRET_MARKERS,
    app_data_dir,
    get_security_level,
    settings_path,
)

BACKUP_FORMAT = 1


def _utcnow_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def backups_dir() -> Path:
    path = app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def evidence_root() -> Path:
    return app_data_dir() / "evidence"


def _is_secret_key(key: str) -> bool:
    return any(marker in key.lower() for marker in _SECRET_MARKERS)


def _sanitize_settings(data: dict) -> dict:
    """Shared settings without secret-looking values (credentials live separately)."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if _is_secret_key(str(key)):
            continue
        out[key] = value
    return out


def _plan_run_ids(plans_folder: Path) -> List[str]:
    ids: List[str] = []
    if not plans_folder.is_dir():
        return ids
    for path in sorted(plans_folder.glob("*.json")):
        try:
            plan = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        for case in plan.get("cases") or []:
            if not isinstance(case, dict):
                continue
            for run in case.get("runs") or []:
                if not isinstance(run, dict):
                    continue
                rid = str(run.get("run_id") or "").strip()
                if rid and rid not in ids:
                    ids.append(rid)
    return ids


def _copy_tree_files(src: Path, dest: Path) -> int:
    """Copy files under src into dest; return file count."""
    if not src.exists():
        return 0
    count = 0
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return 1
    for child in src.rglob("*"):
        if not child.is_file():
            continue
        rel = child.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(child, target)
        count += 1
    return count


def backup_status() -> Dict[str, Any]:
    level = get_security_level()
    plans = app_data_dir() / "plans" / level
    plan_files = sorted(plans.glob("*.json")) if plans.is_dir() else []
    run_ids = _plan_run_ids(plans)
    evidence_indexes = 0
    for rid in run_ids:
        if (evidence_root() / rid / "bundle.json").is_file():
            evidence_indexes += 1
    recent = list_backups(limit=20)
    return {
        "status": "ok",
        "security_level": level,
        "format_version": BACKUP_FORMAT,
        "secrets_default": False,
        "cloud_backup": False,
        "plans_count": len(plan_files),
        "run_ids_count": len(run_ids),
        "evidence_indexes_count": evidence_indexes,
        "backups_dir": str(backups_dir()),
        "recent_backups": recent,
        "note": (
            "Backup copies plans, runs, and evidence index for the active level. "
            "Settings are optional; secrets (credentials) stay off unless opted in. "
            "No automatic cloud backup."
        ),
    }


def list_backups(*, limit: int = 20) -> List[Dict[str, Any]]:
    root = backups_dir()
    rows: List[Dict[str, Any]] = []
    for path in sorted(root.glob("lab-backup-*.zip"), reverse=True):
        if not path.is_file():
            continue
        info: Dict[str, Any] = {
            "filename": path.name,
            "path": str(path),
            "bytes": path.stat().st_size,
            "modified": datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            )
            .replace(microsecond=0)
            .isoformat(),
        }
        try:
            with zipfile.ZipFile(path, "r") as zf:
                if "manifest.json" in zf.namelist():
                    manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                    info["security_level"] = manifest.get("security_level")
                    info["created_at"] = manifest.get("created_at")
                    info["include_settings"] = bool(manifest.get("include_settings"))
                    info["include_secrets"] = bool(manifest.get("include_secrets"))
                    info["contents"] = manifest.get("contents") or {}
        except (OSError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
            info["error"] = "unreadable"
        rows.append(info)
        if len(rows) >= max(1, int(limit)):
            break
    return rows


def create_backup(
    *,
    include_settings: bool = False,
    include_secrets: bool = False,
    dest_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Write a level-scoped lab backup zip under the local backups folder."""
    level = get_security_level()
    if level not in SECURITY_LEVELS:
        return {"status": "error", "message": f"Invalid security level: {level}"}

    stamp = _utcnow_stamp()
    filename = f"lab-backup-{level}-{stamp}.zip"
    if dest_path:
        out = Path(dest_path)
        if out.is_dir():
            out = out / filename
    else:
        out = backups_dir() / filename

    staging = backups_dir() / f".staging-{level}-{stamp}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    contents: Dict[str, Any] = {
        "plans": 0,
        "evidence_indexes": 0,
        "evidence_files": 0,
        "settings": False,
        "secrets": False,
    }

    try:
        plans_src = app_data_dir() / "plans" / level
        plans_dest = staging / "plans" / level
        contents["plans"] = _copy_tree_files(plans_src, plans_dest)

        run_ids = _plan_run_ids(plans_src)
        for rid in run_ids:
            bundle = evidence_root() / rid / "bundle.json"
            if not bundle.is_file():
                continue
            dest_bundle = staging / "evidence" / rid / "bundle.json"
            dest_bundle.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle, dest_bundle)
            contents["evidence_indexes"] += 1
            # Prefer index only; also copy sibling non-binary notices if tiny text.
            for sibling in (evidence_root() / rid).iterdir():
                if not sibling.is_file() or sibling.name == "bundle.json":
                    continue
                if sibling.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".zip"}:
                    continue
                if sibling.stat().st_size > 256_000:
                    continue
                shutil.copy2(sibling, dest_bundle.parent / sibling.name)
                contents["evidence_files"] += 1

        if include_settings:
            shared_path = settings_path()
            if shared_path.is_file():
                raw = json.loads(shared_path.read_text(encoding="utf-8-sig"))
                if isinstance(raw, dict):
                    clean = _sanitize_settings(raw)
                    # Keep level stamp aligned with this backup; never silently flip level.
                    clean["security_level"] = level
                    (staging / "settings.json").write_text(
                        json.dumps(clean, indent=2),
                        encoding="utf-8",
                    )
                    contents["settings"] = True

        if include_secrets:
            creds = app_data_dir() / "levels" / level / "credentials.json"
            if creds.is_file():
                dest_creds = staging / "levels" / level / "credentials.json"
                dest_creds.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(creds, dest_creds)
                contents["secrets"] = True

        # Refuse to stage a mixed-level archive (defence in depth).
        staged_levels = {
            p.name.upper()
            for p in (staging / "plans").iterdir()
            if p.is_dir()
        } if (staging / "plans").is_dir() else set()
        if len(staged_levels) > 1:
            return {
                "status": "error",
                "message": "Refusing to create backup that mixes OFFICIAL and SECRET folders.",
                "levels_found": sorted(staged_levels),
            }
        if staged_levels and level not in staged_levels:
            return {
                "status": "error",
                "message": "Staged plans level does not match active security level.",
                "levels_found": sorted(staged_levels),
                "security_level": level,
            }

        manifest = {
            "format_version": BACKUP_FORMAT,
            "created_at": _utcnow_iso(),
            "security_level": level,
            "include_settings": bool(include_settings),
            "include_secrets": bool(include_secrets and contents["secrets"]),
            "secrets_default": False,
            "cloud_backup": False,
            "contents": contents,
            "app_data_hint": str(app_data_dir()),
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in staging.rglob("*"):
                if not file_path.is_file():
                    continue
                arc = file_path.relative_to(staging).as_posix()
                zf.write(file_path, arcname=arc)

        return {
            "status": "created",
            "path": str(out),
            "filename": out.name,
            "security_level": level,
            "include_settings": bool(include_settings),
            "include_secrets": bool(include_secrets and contents["secrets"]),
            "contents": contents,
            "manifest": manifest,
            "message": (
                f"Backup written for {level}: {contents['plans']} plan file(s), "
                f"{contents['evidence_indexes']} evidence index(es). "
                "Secrets "
                + ("included." if contents["secrets"] else "omitted (default).")
            ),
        }
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _read_manifest_from_zip(zf: zipfile.ZipFile) -> Dict[str, Any]:
    if "manifest.json" not in zf.namelist():
        raise ValueError("Backup missing manifest.json")
    data = json.loads(zf.read("manifest.json").decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid manifest")
    return data


def _levels_in_namelist(names: List[str]) -> List[str]:
    found: set[str] = set()
    for name in names:
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2 and parts[0] == "plans" and parts[1].upper() in SECURITY_LEVELS:
            found.add(parts[1].upper())
        if len(parts) >= 2 and parts[0] == "levels" and parts[1].upper() in SECURITY_LEVELS:
            found.add(parts[1].upper())
    return sorted(found)


def _restore_preview(zf: zipfile.ZipFile, level: str) -> Dict[str, Any]:
    names = zf.namelist()
    plans_would = [
        n for n in names
        if n.replace("\\", "/").startswith(f"plans/{level}/") and n.endswith(".json")
    ]
    evidence_would = [
        n for n in names
        if n.replace("\\", "/").startswith("evidence/") and n.endswith("bundle.json")
    ]
    has_settings = "settings.json" in names
    has_secrets = any(
        n.replace("\\", "/").startswith(f"levels/{level}/") and n.endswith("credentials.json")
        for n in names
    )
    existing_plans = 0
    plans_dir = app_data_dir() / "plans" / level
    if plans_dir.is_dir():
        existing_plans = len(list(plans_dir.glob("*.json")))
    return {
        "plans_in_backup": len(plans_would),
        "evidence_indexes_in_backup": len(evidence_would),
        "settings_in_backup": has_settings,
        "secrets_in_backup": has_secrets,
        "existing_plans_at_level": existing_plans,
        "will_replace": {
            "plans": True if plans_would else False,
            "evidence_indexes": True if evidence_would else False,
            "settings": has_settings,
            "secrets": has_secrets,
        },
    }


def restore_backup(
    path: str | Path,
    *,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Restore a local lab backup. Requires confirm; never mixes security levels."""
    zip_path = Path(path)
    if not zip_path.is_file():
        return {"status": "error", "message": f"Backup not found: {zip_path}"}

    current = get_security_level()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            try:
                manifest = _read_manifest_from_zip(zf)
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                return {"status": "error", "message": f"Invalid backup: {exc}"}

            backup_level = str(manifest.get("security_level") or "").strip().upper()
            if backup_level not in SECURITY_LEVELS:
                return {
                    "status": "error",
                    "message": f"Backup has invalid security_level: {backup_level!r}",
                }

            levels_found = _levels_in_namelist(zf.namelist())
            if len(levels_found) > 1:
                return {
                    "status": "error",
                    "message": (
                        "Restore refused: backup mixes OFFICIAL and SECRET folders."
                    ),
                    "levels_found": levels_found,
                }
            if levels_found and backup_level not in levels_found:
                return {
                    "status": "error",
                    "message": (
                        "Restore refused: manifest level does not match archive folders."
                    ),
                    "security_level": backup_level,
                    "levels_found": levels_found,
                }
            if backup_level != current:
                return {
                    "status": "error",
                    "message": (
                        f"Restore refused: backup is {backup_level} but active level "
                        f"is {current}. Switch level (with confirm) before restoring, "
                        "or restore on a matching profile. OFFICIAL and SECRET must not mix."
                    ),
                    "backup_security_level": backup_level,
                    "active_security_level": current,
                }

            preview = _restore_preview(zf, backup_level)
            if not confirm:
                return {
                    "status": "confirmation_required",
                    "path": str(zip_path),
                    "filename": zip_path.name,
                    "security_level": backup_level,
                    "manifest": {
                        "created_at": manifest.get("created_at"),
                        "include_settings": manifest.get("include_settings"),
                        "include_secrets": manifest.get("include_secrets"),
                        "contents": manifest.get("contents"),
                    },
                    "preview": preview,
                    "message": (
                        "Confirm restore? This replaces plans / evidence index "
                        f"(and optional settings/secrets if present) for {backup_level}."
                    ),
                }

            replaced: Dict[str, Any] = {
                "plans": [],
                "evidence_indexes": [],
                "settings": False,
                "secrets": False,
            }

            # Plans: extract into plans/{level}/, replacing files present in backup.
            for name in zf.namelist():
                norm = name.replace("\\", "/")
                if norm.endswith("/"):
                    continue
                if norm.startswith(f"plans/{backup_level}/"):
                    rel = Path(norm)
                    dest = app_data_dir() / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    replaced["plans"].append(str(dest))
                elif norm.startswith("evidence/") and norm.endswith("bundle.json"):
                    # Only evidence index (bundle.json) — keep screenshots outside unless present.
                    dest = app_data_dir() / Path(norm)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    replaced["evidence_indexes"].append(str(dest))
                elif norm.startswith("evidence/") and not norm.endswith("/"):
                    # Optional small sibling files from backup
                    dest = app_data_dir() / Path(norm)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                elif norm == "settings.json":
                    raw = json.loads(zf.read(name).decode("utf-8"))
                    if isinstance(raw, dict):
                        clean = _sanitize_settings(raw)
                        clean["security_level"] = current
                        # Merge into existing shared settings rather than wiping unknown keys.
                        existing: dict[str, Any] = {}
                        sp = settings_path()
                        if sp.is_file():
                            try:
                                loaded = json.loads(sp.read_text(encoding="utf-8-sig"))
                                if isinstance(loaded, dict):
                                    existing = loaded
                            except (OSError, json.JSONDecodeError):
                                existing = {}
                        merged = {**existing, **clean}
                        # Never introduce secret keys from backup settings.json
                        for key in list(merged.keys()):
                            if _is_secret_key(str(key)):
                                merged.pop(key, None)
                        sp.parent.mkdir(parents=True, exist_ok=True)
                        sp.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                        replaced["settings"] = True
                elif norm == f"levels/{backup_level}/credentials.json":
                    dest = app_data_dir() / "levels" / backup_level / "credentials.json"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    replaced["secrets"] = True

            return {
                "status": "restored",
                "path": str(zip_path),
                "filename": zip_path.name,
                "security_level": backup_level,
                "replaced": {
                    "plans_count": len(replaced["plans"]),
                    "plans": replaced["plans"][:50],
                    "evidence_indexes_count": len(replaced["evidence_indexes"]),
                    "evidence_indexes": replaced["evidence_indexes"][:50],
                    "settings": replaced["settings"],
                    "secrets": replaced["secrets"],
                },
                "message": (
                    f"Restored {backup_level} lab backup: "
                    f"{len(replaced['plans'])} plan file(s), "
                    f"{len(replaced['evidence_indexes'])} evidence index(es)"
                    + (", settings" if replaced["settings"] else "")
                    + (", secrets" if replaced["secrets"] else "")
                    + " replaced."
                ),
            }
    except zipfile.BadZipFile:
        return {"status": "error", "message": "File is not a valid zip backup."}
