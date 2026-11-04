"""Write Playwright run reports outside the repository."""
import json
import os
from datetime import datetime
from pathlib import Path

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


def _markdown(result: dict) -> str:
    title = result.get("title") or "Playwright run"
    status = result.get("status") or "fail"
    lines = [
        f"# {title}",
        "",
        f"Overall: {status}",
        "",
        "| action | status |",
        "| --- | --- |",
    ]
    for step in result.get("steps") or []:
        lines.append(f"| {step.get('action', '')} | {step.get('status', '')} |")
    lines.append("")
    lines.append(f"Screenshot: {result.get('screenshot') or ''}")
    return "\n".join(lines) + "\n"


def export_run(result, request_text: str = "", session_id: str = "default"):
    try:
        folder = reports_dir()
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        json_path, md_path = _pair(folder, stamp)
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "request": request_text or "",
            "session_id": session_id or "default",
            "result": result,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        body = result if isinstance(result, dict) else {}
        md_path.write_text(_markdown(body), encoding="utf-8")
    except Exception:
        return result
    return result
