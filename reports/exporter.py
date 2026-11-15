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
