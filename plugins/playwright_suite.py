"""
Import and run existing Playwright project suites (FR-TEST-5 / KAN-59).

Discovers a local Playwright project (config or @playwright/test), stores the
path in settings, lists specs, and runs via `npx playwright test`. Does not
fork the JSON-step runner or the desktop .exe harness.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

_SETTING_KEY = "playwright_suite_path"
_LOG_CAP = 6000
_CONFIG_NAMES = (
    "playwright.config.ts",
    "playwright.config.js",
    "playwright.config.mjs",
    "playwright.config.cjs",
)
_SPEC_GLOBS = ("**/*.spec.ts", "**/*.spec.js", "**/*.test.ts", "**/*.test.js")


def suite_status() -> dict[str, Any]:
    from settings.store import load_settings

    settings = load_settings()
    path = (settings.get(_SETTING_KEY) or "").strip()
    discovered = None
    if path:
        root, err = _resolve_root(path)
        if root and not err:
            discovered = _describe_project(root)
    return {
        _SETTING_KEY: path,
        "discovered": discovered,
        "plugin": "playwright_suite",
    }


def set_suite_path(path: str, confirm: bool = True) -> dict[str, Any]:
    """Persist suite path after a successful discover (confirm writes settings)."""
    from settings.store import update_setting

    root, err = _resolve_root(path)
    if err:
        return {"status": "fail", "error": err, "plugin": "playwright_suite"}
    assert root is not None
    if not confirm:
        return {
            "status": "confirmation_required",
            "proposed": {_SETTING_KEY: str(root)},
            "plugin": "playwright_suite",
        }
    update_setting(_SETTING_KEY, str(root), confirm=True)
    return {
        "status": "ok",
        "message": f"Imported Playwright suite path: {root}",
        **suite_status(),
    }


def discover_suite(suite_path: str = "") -> dict[str, Any]:
    """Validate a Playwright project and summarise configs + local spec files."""
    result: dict[str, Any] = {
        "status": "fail",
        "suite_path": None,
        "config": None,
        "specs": [],
        "spec_count": 0,
        "has_playwright_dep": False,
        "error": None,
        "message": None,
        "plugin": "playwright_suite",
    }
    root, err = _resolve_root(suite_path)
    if err:
        result["error"] = err
        return result
    assert root is not None
    info = _describe_project(root)
    result.update(info)
    result["suite_path"] = str(root)
    result["status"] = "ok"
    result["message"] = (
        f"Found Playwright project ({result['spec_count']} spec file(s)"
        + (f", config {Path(info['config']).name}" if info.get("config") else ", no config file")
        + ")."
    )
    return result


def list_suite_tests(suite_path: str = "") -> dict[str, Any]:
    """List tests via Playwright CLI when available; else fall back to spec files."""
    result: dict[str, Any] = {
        "status": "fail",
        "suite_path": None,
        "tests": [],
        "source": None,
        "error": None,
        "message": None,
        "plugin": "playwright_suite",
    }
    root, err = _resolve_root(suite_path)
    if err:
        result["error"] = err
        return result
    assert root is not None
    result["suite_path"] = str(root)

    cli = _npx_playwright(["test", "--list"], cwd=root, timeout_s=60)
    if cli.get("ok"):
        tests = _parse_list_output(cli.get("stdout") or "")
        if tests:
            result["status"] = "ok"
            result["tests"] = tests
            result["source"] = "playwright_cli"
            result["message"] = f"Listed {len(tests)} test(s) via Playwright CLI."
            return result

    specs = _scan_specs(root)
    result["tests"] = [{"title": s, "file": s, "line": None} for s in specs]
    result["source"] = "filesystem"
    if specs:
        result["status"] = "ok"
        result["message"] = (
            f"Listed {len(specs)} spec file(s) from disk"
            + (
                " (Playwright CLI unavailable or empty --list)."
                if not cli.get("ok")
                else "."
            )
        )
        if not cli.get("ok") and cli.get("error"):
            result["cli_error"] = cli.get("error")
        return result

    result["error"] = cli.get("error") or "No Playwright tests found in project."
    return result


def run_suite(
    suite_path: str = "",
    grep: str = "",
    timeout_s: float = 300.0,
) -> dict[str, Any]:
    """Run an imported Playwright suite via `npx playwright test`."""
    result: dict[str, Any] = {
        "status": "fail",
        "suite_path": None,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "flaky": 0,
        "tests": [],
        "evidence": [],
        "exit_code": None,
        "logs": "",
        "error": None,
        "message": None,
        "plugin": "playwright_suite",
    }
    root, err = _resolve_root(suite_path)
    if err:
        result["error"] = err
        return result
    assert root is not None
    result["suite_path"] = str(root)

    desc = _describe_project(root)
    if not desc.get("config") and not desc.get("has_playwright_dep") and not desc.get("specs"):
        result["error"] = (
            f"Not a Playwright project (no config, @playwright/test, or specs): {root}"
        )
        return result

    from settings.store import get_playwright_headless

    use_headless = bool(get_playwright_headless())
    result["headless"] = use_headless
    result["playwright_mode"] = "headless" if use_headless else "headed"

    args = ["test", "--reporter=json"]
    # CLI defaults to headless; pass --headed when product setting is headed.
    if not use_headless:
        args.append("--headed")
    grep_clean = (grep or "").strip()
    if grep_clean:
        args.extend(["--grep", grep_clean])

    cli = _npx_playwright(args, cwd=root, timeout_s=max(30.0, float(timeout_s)))
    result["exit_code"] = cli.get("returncode")
    result["logs"] = _truncate(
        (cli.get("stdout") or "") + ("\n" + (cli.get("stderr") or "") if cli.get("stderr") else "")
    )

    if not cli.get("ok") and cli.get("error") and cli.get("returncode") is None:
        result["error"] = cli["error"]
        return result

    summary = _parse_json_report(cli.get("stdout") or "")
    if summary:
        result["passed"] = summary["passed"]
        result["failed"] = summary["failed"]
        result["skipped"] = summary["skipped"]
        result["flaky"] = summary.get("flaky", 0)
        result["tests"] = summary["tests"]
        result["evidence"] = summary.get("evidence") or []
        if summary["failed"] == 0 and summary["passed"] > 0:
            result["status"] = "pass"
            result["message"] = (
                f"Suite passed: {summary['passed']} passed, "
                f"{summary['skipped']} skipped."
            )
        elif summary["failed"] == 0 and summary["passed"] == 0:
            result["status"] = "fail"
            result["error"] = "Playwright finished with no executed tests."
            result["message"] = result["error"]
        else:
            result["status"] = "fail"
            result["message"] = (
                f"Suite finished with failures: {summary['failed']} failed, "
                f"{summary['passed']} passed."
            )
            result["error"] = result["message"]
        return result

    # CLI ran but JSON missing — use exit code
    code = cli.get("returncode")
    if code == 0:
        result["status"] = "pass"
        result["message"] = "Playwright exited 0 (no JSON reporter payload parsed)."
        result["passed"] = 1
        return result
    result["error"] = cli.get("error") or (
        f"Playwright exited with code {code}. Could not parse JSON reporter output."
    )
    result["message"] = result["error"]
    return result


def _resolve_root(suite_path: str = "") -> tuple[Optional[Path], Optional[str]]:
    from settings.store import load_settings

    raw = (suite_path or "").strip()
    if not raw:
        raw = (load_settings().get(_SETTING_KEY) or "").strip()
    if not raw:
        return None, (
            "No Playwright suite path. Pass suite_path or set playwright_suite_path "
            "in settings (App → Suites)."
        )
    path = Path(raw).expanduser()
    if not path.exists():
        return None, f"Path not found: {path}"
    if path.is_file():
        # Allow pointing at config file → use parent as project root
        if path.name in _CONFIG_NAMES:
            path = path.parent
        else:
            return None, f"Suite path must be a project directory (or playwright.config.*): {path}"
    if not path.is_dir():
        return None, f"Suite path is not a directory: {path}"
    return path.resolve(), None


def _describe_project(root: Path) -> dict[str, Any]:
    config = None
    for name in _CONFIG_NAMES:
        candidate = root / name
        if candidate.is_file():
            config = str(candidate)
            break
    specs = _scan_specs(root)
    return {
        "config": config,
        "specs": specs,
        "spec_count": len(specs),
        "has_playwright_dep": _has_playwright_dep(root),
    }


def _has_playwright_dep(root: Path) -> bool:
    pkg = root / "package.json"
    if not pkg.is_file():
        return False
    try:
        data = json.loads(pkg.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return False
    for bucket in ("dependencies", "devDependencies", "peerDependencies"):
        deps = data.get(bucket) or {}
        if isinstance(deps, dict) and (
            "@playwright/test" in deps or "playwright" in deps
        ):
            return True
    return False


def _scan_specs(root: Path) -> list[str]:
    found: list[str] = []
    skip_dirs = {"node_modules", ".git", "dist", "build", "test-results", "playwright-report"}
    for pattern in _SPEC_GLOBS:
        for path in root.glob(pattern):
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.is_file():
                found.append(str(path.relative_to(root)).replace("\\", "/"))
    return sorted(set(found))


def _npx_cmd() -> Optional[str]:
    for name in ("npx.cmd", "npx"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _npx_playwright(
    playwright_args: list[str],
    cwd: Path,
    timeout_s: float = 300.0,
) -> dict[str, Any]:
    """Run `npx playwright …`. Overridable in tests via monkeypatch."""
    npx = _npx_cmd()
    if not npx:
        return {
            "ok": False,
            "error": "npx not found on PATH. Install Node.js / Playwright to run suites.",
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }
    cmd = [npx, "--yes", "playwright", *playwright_args]
    env = os.environ.copy()
    # Prefer project-local browsers when present; do not force CI blind.
    env.setdefault("CI", "1")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(5.0, float(timeout_s)),
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"Playwright timed out after {timeout_s}s.",
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "returncode": None,
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Failed to start Playwright: {exc}",
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }
    # Non-zero is still "ok" as a process run — caller interprets failures.
    return {
        "ok": True,
        "error": None if proc.returncode == 0 else f"exit {proc.returncode}",
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "returncode": proc.returncode,
    }


def _parse_list_output(text: str) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    # Typical: "  [chromium] › tests/foo.spec.ts:3:5 › my test"
    pattern = re.compile(
        r"^\s*(?:\[[^\]]+\]\s*›\s*)?(.+?\.(?:spec|test)\.[jt]s)(?::(\d+))?(?::\d+)?\s*›\s*(.+?)\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text or ""):
        tests.append(
            {
                "file": match.group(1).replace("\\", "/"),
                "line": int(match.group(2)) if match.group(2) else None,
                "title": match.group(3).strip(),
            }
        )
    if tests:
        return tests
    # Fallback: any line with ›
    for line in (text or "").splitlines():
        if "›" in line:
            title = line.split("›")[-1].strip()
            if title:
                tests.append({"file": None, "line": None, "title": title})
    return tests


def _parse_json_report(stdout: str) -> Optional[dict[str, Any]]:
    """Extract Playwright JSON reporter object from stdout (may include noise)."""
    text = (stdout or "").strip()
    if not text:
        return None
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Find last JSON object in the stream
        start = text.rfind("{")
        while start >= 0:
            try:
                data = json.loads(text[start:])
                break
            except json.JSONDecodeError:
                start = text.rfind("{", 0, start)
    if not isinstance(data, dict):
        return None
    suites = data.get("suites")
    stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}
    tests_out: list[dict[str, Any]] = []
    evidence: list[str] = []

    def walk(suite: dict, parents: list[str]) -> None:
        title = suite.get("title") or ""
        chain = parents + ([title] if title else [])
        for spec in suite.get("specs") or []:
            if not isinstance(spec, dict):
                continue
            name = " › ".join(chain + [spec.get("title") or "test"])
            ok = bool(spec.get("ok", True))
            status = "passed" if ok else "failed"
            for t in spec.get("tests") or []:
                if not isinstance(t, dict):
                    continue
                results = t.get("results") or []
                if results and isinstance(results[-1], dict):
                    st = (results[-1].get("status") or status).lower()
                    if st in {"passed", "failed", "skipped", "timedout", "interrupted"}:
                        status = "failed" if st in {"timedout", "interrupted"} else st
                    for att in results[-1].get("attachments") or []:
                        if isinstance(att, dict) and att.get("path"):
                            evidence.append(str(att["path"]))
            tests_out.append(
                {
                    "title": name,
                    "file": (spec.get("file") or "").replace("\\", "/"),
                    "status": status,
                }
            )
        for child in suite.get("suites") or []:
            if isinstance(child, dict):
                walk(child, chain)

    if isinstance(suites, list):
        for s in suites:
            if isinstance(s, dict):
                walk(s, [])

    passed = int(stats.get("expected") or 0)
    failed = int(stats.get("unexpected") or 0)
    skipped = int(stats.get("skipped") or 0)
    flaky = int(stats.get("flaky") or 0)
    if not tests_out and (passed or failed or skipped):
        # Stats-only payload
        pass
    elif tests_out and not (passed or failed or skipped):
        passed = sum(1 for t in tests_out if t["status"] == "passed")
        failed = sum(1 for t in tests_out if t["status"] == "failed")
        skipped = sum(1 for t in tests_out if t["status"] == "skipped")

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "flaky": flaky,
        "tests": tests_out,
        "evidence": evidence[:50],
    }


def _truncate(text: str) -> str:
    text = text or ""
    if len(text) <= _LOG_CAP:
        return text
    return text[:_LOG_CAP] + "\n…(truncated)"
