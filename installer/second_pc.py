"""Build a clean install pack for a second Windows PC (KAN-237 / G11).

AC (catalogue G11 / SALES-1):
- Second PC can install and open the desktop app, enter local connections, draft a plan.
- No shared cloud account.
- Secrets are not inside the installer/pack.
- Not a company-rollout claim alone.
- Out of scope: mandatory telemetry in the installer.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from settings.store import app_data_dir

PACK_FORMAT = 1
_REPO = Path(__file__).resolve().parents[1]

# Curated tree only — never copy LOCALAPPDATA, venv, or credential files.
_INCLUDE_FILES = (
    "desktop_app.py",
    "main.py",
    "run_ui.py",
    "requirements.txt",
    "README.md",
    "AGENTS.md",
    "PROJECT_MEMORY.md",
)
_INCLUDE_DIRS = (
    "agent",
    "installer",
    "plans",
    "plugins",
    "reports",
    "settings",
    "ui",
    "docs",
)

_SECRET_NAME_MARKERS = (
    "credentials.json",
    "settings.json",
    ".env",
    ".env.local",
    "secrets.json",
    "token.json",
)
_SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    "venv",
    ".venv",
    "node_modules",
    "export_packs",
    "install_packs",
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _utcnow_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def install_packs_dir() -> Path:
    """Local packs root — never inside the repo; never a cloud mount default."""
    override = os.getenv("AI_TESTING_INSTALL_PACKS")
    if override:
        path = Path(override)
    else:
        path = app_data_dir() / "install_packs"
    resolved = path.resolve()
    repo = _REPO.resolve()
    if resolved == repo or repo in resolved.parents:
        raise RuntimeError("refusing to write install packs inside the repo")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _last_pointer_path() -> Path:
    return install_packs_dir() / "last_install_pack.json"


def _is_secret_path(path: Path) -> bool:
    name = path.name.lower()
    if name in {m.lower() for m in _SECRET_NAME_MARKERS}:
        return True
    if name.endswith(".pem") or name.endswith(".pfx") or name.endswith(".key"):
        return True
    return False


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    skipped: set[str] = set()
    for name in names:
        lower = name.lower()
        if name in _SKIP_DIR_NAMES or lower in _SKIP_DIR_NAMES:
            skipped.add(name)
            continue
        if lower in {m.lower() for m in _SECRET_NAME_MARKERS}:
            skipped.add(name)
            continue
        if lower.endswith((".pyc", ".pyo", ".pem", ".pfx", ".key")):
            skipped.add(name)
    return skipped


def _write_install_md(dest: Path) -> None:
    text = """# Install on a second Windows PC (G11)

This folder is a **local** install pack for the AI Testing Agent desktop app.
It is **not** a company-wide rollout package and does **not** include a shared cloud account.

## What is NOT in this pack

- No Jira tokens, emails, or passwords
- No `%LOCALAPPDATA%\\ai_testing_app\\settings.json` or level credentials
- No browser profiles from the first PC
- Telemetry stays **off by default** (FR-SEC-2) — the installer does not turn it on

## Prerequisites on the second PC

1. Windows 10/11 with Edge WebView2 (usual for Windows 11).
2. Python 3.11+ on PATH (`py -3 --version`).
3. Optional but recommended: [Ollama](https://ollama.com) with one small local model (7B–8B).
4. Network only as needed for *your* Jira / AUT — nothing phones home by default.

## Setup

From this folder in PowerShell:

```powershell
.\\SetupSecondPC.ps1
```

Or manually:

```powershell
py -3 -m venv venv
.\\venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\venv\\Scripts\\python.exe -m playwright install chromium
```

## Open the desktop app

```powershell
.\\RunDesktop.cmd
```

or:

```powershell
.\\venv\\Scripts\\python.exe desktop_app.py
```

## After first open (acceptance path)

1. Open **Settings → App** and enter local connections (Jira URL/project, target URL, Ollama model).
2. Save credentials only on this PC (never share the pack after filling secrets).
3. Draft a plan from a story key (Plans area) — proof the second PC works standalone.

## Claims

- Maps to roadmap **SALES-1** / Test-all **G11**.
- Does **not** claim enterprise MSI/SCCM rollout by itself.
"""
    (dest / "INSTALL.md").write_text(text, encoding="utf-8")


def _write_setup_ps1(dest: Path) -> None:
    text = r"""# SetupSecondPC.ps1 — clean second-PC bootstrap (no secrets, telemetry off).
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "AI Testing Agent — second PC setup (G11)"
Write-Host "Secrets are NOT copied. Telemetry stays off by default."

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  Write-Error "Python launcher 'py' not found. Install Python 3.11+ and retry."
}

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
  Write-Host "Creating venv..."
  py -3 -m venv venv
}

Write-Host "Installing Python packages..."
& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Installing Playwright Chromium..."
& .\venv\Scripts\python.exe -m playwright install chromium

Write-Host ""
Write-Host "Done. Run .\RunDesktop.cmd then enter local connections in Settings."
Write-Host "No shared cloud account is created by this setup."
"""
    (dest / "SetupSecondPC.ps1").write_text(text, encoding="utf-8")


def _write_run_desktop_cmd(dest: Path) -> None:
    text = """@echo off
REM Launch native desktop window (pywebview). No secrets bundled.
cd /d "%~dp0"
if not exist "venv\\Scripts\\python.exe" (
  echo Run SetupSecondPC.ps1 first.
  exit /b 1
)
"venv\\Scripts\\python.exe" desktop_app.py
"""
    (dest / "RunDesktop.cmd").write_text(text, encoding="utf-8")


def _scan_for_secrets(root: Path) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and _is_secret_path(path):
            hits.append(str(path.relative_to(root)).replace("\\", "/"))
    return hits


def create_second_pc_pack(*, session_id: str | None = None) -> dict[str, Any]:
    """Copy a curated, secret-free tree into a dated install pack folder."""
    packs_root = install_packs_dir()
    stamp = _utcnow_stamp()
    folder_name = f"second_pc_{stamp}"
    dest = packs_root / folder_name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    for name in _INCLUDE_FILES:
        src = _REPO / name
        if not src.is_file():
            continue
        if _is_secret_path(src):
            continue
        shutil.copy2(src, dest / name)
        copied_files.append(name)

    for dirname in _INCLUDE_DIRS:
        src = _REPO / dirname
        if not src.is_dir():
            continue
        shutil.copytree(
            src,
            dest / dirname,
            ignore=_copy_ignore,
            dirs_exist_ok=True,
        )
        copied_files.append(dirname + "/")

    _write_install_md(dest)
    _write_setup_ps1(dest)
    _write_run_desktop_cmd(dest)

    secret_hits = _scan_for_secrets(dest)
    if secret_hits:
        shutil.rmtree(dest, ignore_errors=True)
        return {
            "status": "error",
            "error": "refused_secrets_in_pack",
            "message": "Install pack aborted: secret-named files would have been included.",
            "secret_paths": secret_hits,
        }

    exported_at = _utcnow_iso()
    manifest = {
        "format": PACK_FORMAT,
        "kind": "second_pc_windows_install",
        "roadmap": "G11",
        "sales": "SALES-1",
        "exported_at": exported_at,
        "folder_name": folder_name,
        "shared_cloud_account": False,
        "secrets_included": False,
        "telemetry_enabled_default": False,
        "mandatory_telemetry": False,
        "company_rollout_claim": False,
        "desktop_entry": "desktop_app.py",
        "install_doc": "INSTALL.md",
        "setup_script": "SetupSecondPC.ps1",
        "run_script": "RunDesktop.cmd",
        "copied": copied_files,
        "session_id": (session_id or "").strip() or None,
        "acceptance": [
            "Install on second Windows PC via SetupSecondPC.ps1",
            "Open desktop app via RunDesktop.cmd",
            "Enter local connections in Settings",
            "Draft a plan from a story key",
        ],
    }
    (dest / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (dest / "LABEL.txt").write_text(
        "\n".join(
            [
                "AI Testing Agent — second Windows PC install pack",
                f"Exported: {exported_at}",
                "Secrets: none",
                "Shared cloud account: no",
                "Telemetry default: off",
                "Company rollout claim: no (SALES-1 / G11 baseline)",
                "",
            ]
        ),
        encoding="utf-8",
    )

    pointer = {
        "status": "ok",
        "path": str(dest),
        "folder_name": folder_name,
        "exported_at": exported_at,
        "shared_cloud_account": False,
        "secrets_included": False,
        "telemetry_enabled_default": False,
        "company_rollout_claim": False,
    }
    _last_pointer_path().write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "path": str(dest),
        "folder_name": folder_name,
        "exported_at": exported_at,
        "pack_format": PACK_FORMAT,
        "shared_cloud_account": False,
        "secrets_included": False,
        "telemetry_enabled_default": False,
        "mandatory_telemetry": False,
        "company_rollout_claim": False,
        "install_doc": "INSTALL.md",
        "setup_script": "SetupSecondPC.ps1",
        "run_script": "RunDesktop.cmd",
        "acceptance": manifest["acceptance"],
        "opens_desktop_app": True,
        "local_connections_after_install": True,
    }


def last_second_pc_pack() -> dict[str, Any]:
    path = _last_pointer_path()
    if not path.is_file():
        return {
            "status": "empty",
            "path": None,
            "folder_name": None,
            "exported_at": None,
            "shared_cloud_account": False,
            "secrets_included": False,
            "telemetry_enabled_default": False,
            "company_rollout_claim": False,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "error",
            "error": "corrupt_last_pointer",
            "message": "Could not read last install pack pointer.",
        }
    if not isinstance(data, dict):
        return {"status": "error", "error": "invalid_last_pointer"}
    data.setdefault("status", "ok")
    data.setdefault("shared_cloud_account", False)
    data.setdefault("secrets_included", False)
    data.setdefault("telemetry_enabled_default", False)
    data.setdefault("company_rollout_claim", False)
    return data


def second_pc_status() -> dict[str, Any]:
    last = last_second_pc_pack()
    return {
        "status": "ok",
        "feature": "second_pc_installer",
        "roadmap": "G11",
        "sales": "SALES-1",
        "shared_cloud_account": False,
        "secrets_in_installer": False,
        "telemetry_enabled_default": False,
        "mandatory_telemetry": False,
        "company_rollout_claim": False,
        "packs_dir": str(install_packs_dir()),
        "last": last,
        "steps": [
            "Build install pack (this PC)",
            "Copy folder to second Windows PC",
            "Run SetupSecondPC.ps1",
            "Run RunDesktop.cmd",
            "Enter local connections",
            "Draft a plan",
        ],
    }
