"""Write Playwright run reports outside the repository."""
import json
import os
from datetime import datetime
from pathlib import Path

from reports.sections import build_sections, load_report_sections, render_markdown

_REPO = Path(__file__).resolve().parents[1]


def reports_dir() -> Path:
    override = os.getenv("AI_TESTING_REPORTS")
    if override:
        path = Path(override)
    else:
        base = os.getenv("LOCALAPPDATA")
        if base:
            path = Path(base) / "ai_testing_app" / "reports"
        else:
            path = Path.home() / ".ai_testing_app" / "reports"
    resolved = path.resolve()
    repo = _REPO.resolve()
    if resolved == repo or repo in resolved.parents:
        raise RuntimeError("refusing to write reports inside the repo")
    return resolved


def _pair(folder: Path, stamp: str):
    json_path = folder / f"{stamp}.json"
    if not json_path.exists():
        return json_path, folder / f"{stamp}.md"
    number = 2
    while (folder / f"{stamp}-{number}.json").exists():
        number += 1
    return folder / f"{stamp}-{number}.json", folder / f"{stamp}-{number}.md"


def export_run(
    result,
    request_text: str = "",
    session_id: str = "default",
    sections: dict | None = None,
):
    """Export JSON + Markdown. ``sections`` overrides the saved report profile when provided."""
    try:
        folder = reports_dir()
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        json_path, md_path = _pair(folder, stamp)
        body = result if isinstance(result, dict) else {}
        enabled = sections if sections is not None else load_report_sections()
        section_payload = build_sections(body, request_text, enabled)
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "request": request_text or "",
            "session_id": session_id or "default",
            "result": result,
            "sections": section_payload,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path.write_text(render_markdown(section_payload), encoding="utf-8")
    except Exception:
        return result
    return result


def _safe_stem(report_id: str) -> str | None:
    stem = (report_id or "").strip()
    if not stem or "/" in stem or "\\" in stem or ".." in stem:
        return None
    if Path(stem).name != stem:
        return None
    return stem


def _screenshot_from_markdown(text: str) -> Path | None:
    for line in text.splitlines():
        if line.startswith("Screenshot:"):
            candidate = Path(line.split(":", 1)[1].strip())
            if candidate.is_file():
                return candidate
            break
    return None


def list_saved_reports(limit: int = 50) -> dict:
    """Newest-first library entries for the Reports area (FR-REP-4)."""
    empty_hint = (
        "No saved reports yet. Run a plan case or export a run — "
        "Markdown/JSON land in the local reports folder."
    )
    try:
        folder = reports_dir()
    except RuntimeError:
        return {"reports": [], "count": 0, "empty_hint": empty_hint}
    if not folder.is_dir():
        return {"reports": [], "count": 0, "empty_hint": empty_hint}
    stems: dict[str, float] = {}
    for path in folder.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        stem = path.stem
        mtime = path.stat().st_mtime
        prev = stems.get(stem)
        if prev is None or mtime > prev:
            stems[stem] = mtime
    ordered = sorted(stems.items(), key=lambda item: (item[1], item[0]), reverse=True)
    capped = ordered[: max(1, min(int(limit or 50), 200))]
    reports = []
    for stem, mtime in capped:
        md_path = folder / f"{stem}.md"
        json_path = folder / f"{stem}.json"
        stamp = ""
        if json_path.is_file():
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    stamp = str(payload.get("timestamp") or "")
            except (OSError, json.JSONDecodeError, UnicodeError):
                stamp = ""
        if not stamp:
            stamp = datetime.fromtimestamp(mtime).isoformat(timespec="seconds")
        reports.append(
            {
                "id": stem,
                "label": stem,
                "timestamp": stamp,
                "has_markdown": md_path.is_file(),
                "has_json": json_path.is_file(),
            }
        )
    return {
        "reports": reports,
        "count": len(reports),
        "empty_hint": empty_hint if not reports else "",
    }


def get_saved_report(report_id: str) -> dict:
    """Load markdown / JSON / screenshot availability for one saved report."""
    empty = {
        "found": False,
        "id": "",
        "markdown": "No reports yet",
        "json": {"message": "No JSON found"},
        "has_screenshot": False,
        "empty_hint": (
            "No saved reports yet. Run a plan case or export a run — "
            "Markdown/JSON land in the local reports folder. "
            "Section include/exclude is under Settings → Report Settings."
        ),
    }
    stem = _safe_stem(report_id)
    if not stem:
        return empty
    try:
        folder = reports_dir()
    except RuntimeError:
        return empty
    md_path = folder / f"{stem}.md"
    json_path = folder / f"{stem}.json"
    if not md_path.is_file() and not json_path.is_file():
        return empty
    markdown = "No markdown for this report."
    if md_path.is_file():
        try:
            markdown = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            markdown = "Could not read markdown."
    payload: dict | str = {"message": "No JSON found"}
    if json_path.is_file():
        try:
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            payload = loaded if isinstance(loaded, dict) else {"message": "Invalid JSON"}
        except (OSError, json.JSONDecodeError, UnicodeError):
            payload = {"message": "Could not read JSON"}
    shot = _screenshot_from_markdown(markdown) if isinstance(markdown, str) else None
    if shot is None and isinstance(payload, dict):
        result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        candidate = result.get("screenshot") or ""
        if candidate:
            path = Path(str(candidate))
            if path.is_file():
                shot = path
    return {
        "found": True,
        "id": stem,
        "markdown": markdown,
        "json": payload,
        "has_screenshot": shot is not None,
        "empty_hint": "",
    }


def screenshot_path_for_report(report_id: str) -> Path | None:
    """Return an on-disk screenshot path for a saved report, if present."""
    detail = get_saved_report(report_id)
    if not detail.get("found") or not detail.get("has_screenshot"):
        return None
    stem = _safe_stem(report_id)
    if not stem:
        return None
    try:
        folder = reports_dir()
    except RuntimeError:
        return None
    md_path = folder / f"{stem}.md"
    if md_path.is_file():
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            text = ""
        shot = _screenshot_from_markdown(text)
        if shot is not None:
            return shot
    json_path = folder / f"{stem}.json"
    if json_path.is_file():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return None
        if isinstance(payload, dict):
            result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
            candidate = result.get("screenshot") or ""
            if candidate:
                path = Path(str(candidate))
                if path.is_file():
                    return path
    return None


def latest_summary() -> dict:
    """Return HUD-friendly metrics from the newest exported report JSON.

    Never includes paths that could leak machine layout beyond the filename stamp.
    """
    try:
        folder = reports_dir()
    except RuntimeError:
        return {"available": False}
    if not folder.is_dir():
        return {"available": False}
    files = sorted(
        (p for p in folder.glob("*.json") if p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    if not files:
        return {"available": False}
    try:
        payload = json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return {"available": False}
    if not isinstance(payload, dict):
        return {"available": False}
    sections = payload.get("sections") if isinstance(payload.get("sections"), dict) else {}
    summary = sections.get("summary") if isinstance(sections.get("summary"), dict) else {}
    progress = summary.get("progress") if isinstance(summary.get("progress"), dict) else {}
    tests_passed = summary.get("tests_passed", summary.get("passed", progress.get("tests_passed")))
    stories = summary.get("stories_covered", progress.get("stories_covered"))
    pass_rate = summary.get("pass_rate_percent", progress.get("pass_rate_percent"))
    try:
        tests_passed_n = int(tests_passed) if tests_passed is not None else None
    except (TypeError, ValueError):
        tests_passed_n = None
    try:
        stories_n = int(stories) if stories is not None else None
    except (TypeError, ValueError):
        stories_n = None
    try:
        pass_rate_n = float(pass_rate) if pass_rate is not None else None
    except (TypeError, ValueError):
        pass_rate_n = None
    return {
        "available": True,
        "timestamp": payload.get("timestamp") or "",
        "pass_rate_percent": pass_rate_n,
        "stories_covered": stories_n,
        "tests_passed": tests_passed_n,
    }
