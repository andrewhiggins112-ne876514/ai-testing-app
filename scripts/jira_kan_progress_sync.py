"""
Sync KAN epic statuses from child stories and add completion/progress comments.
Credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logged.
"""
from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35

DONE_STORY_COMMENTS: Dict[str, str] = {
    "KAN-8": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: Ollama tool-calling agent with sessions, clarification before side effects, "
        "and confirmation gates on Jira/destructive actions.\n\n"
        "*Code:* `agent/agent.py`, `main.py` `POST /chat`.\n"
        "*Verify:* chat against local Ollama; ambiguous requests ask clarifying questions; "
        "Jira writes require yes/confirm."
    ),
    "KAN-9": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: Playwright runner with step execution, evidence/screenshots, and click self-heal "
        "limited to locator strategy (assertions unchanged).\n\n"
        "*Code:* `plugins/playwright_runner.py`.\n"
        "*Verify:* run steps against a URL; broken CSS click attempts alternate locator without changing expected values."
    ),
    "KAN-11": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: baseline JSON + Markdown report export from run metadata.\n\n"
        "*Code:* `reports/exporter.py`.\n"
        "*Verify:* export a run payload; open Markdown for pass/fail summary.\n"
        "*Follow-up:* customisable sections tracked on KAN-51."
    ),
    "KAN-12": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: Jira list/create/transition/comment/epic link with two-step confirm; "
        "credentials only in local settings; live against project KAN.\n\n"
        "*Code:* `plugins/jira_plugin.py`.\n"
        "*Verify:* list KAN stories; create without confirm returns confirmation_required."
    ),
    "KAN-13": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: pytest suite covering Jira plugin, Playwright heal paths, orb/presets, sessions, settings, reports.\n\n"
        "*Code:* `tests/`.\n"
        "*Verify:* `pytest` from repo root in the D: venv."
    ),
    "KAN-16": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: local settings store under `%LOCALAPPDATA%\\ai_testing_app\\settings.json` "
        "(Jira/orb/security); never committed to git.\n\n"
        "*Code:* `settings/store.py`.\n"
        "*Verify:* settings path on `/health`; no real tokens in tracked files."
    ),
    "KAN-39": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: FastAPI `/health`, `/chat`, orb API, static `/ui` including desktop assets.\n\n"
        "*Code:* `main.py`.\n"
        "*Verify:* `GET /health` → ok from `D:\\Projects\\ai_testing_app`."
    ),
    "KAN-41": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: native pywebview desktop shell, dual drawers, WebGL orbs mystic/aether/neural/apex, "
        "per-style localStorage, widget settings (opacity/border/bg), edge-snap drawers.\n\n"
        "*Code:* `desktop_app.py`, `ui/desktop/`, `ui/orb_webgl.js`.\n"
        "*Verify:* `python desktop_app.py`; style switch + sliders persist.\n"
        "*Follow-up:* resizable panels on KAN-53."
    ),
    "KAN-43": (
        "*Completion note (2026-11-15)*\n\n"
        "Shipped: Cursor ops — rules, agents, skills, HOW_WE_WORK, WORK_LOG handoff, "
        "functional spec + KAN ticket template.\n\n"
        "*Code:* `.cursor/`, `docs/ops/*`, `docs/FUNCTIONAL_SPEC.md`.\n"
        "*Verify:* say “pick up where we left off” → Active slice KAN-53."
    ),
}

# Epic key -> expected outcome comment builder uses live children
SKIP_COMMENT_KEYS = frozenset({"KAN-2", "KAN-18"})  # obsolete / probe


class Jira:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.client = httpx.Client(
            timeout=90.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers={"Accept": "application/json"},
        )
        self.failures: List[str] = []

    def close(self) -> None:
        self.client.close()

    def _req(self, method: str, path: str, **kwargs) -> httpx.Response:
        for _ in range(6):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
        return r

    def search(self, jql: str) -> List[Dict[str, Any]]:
        body = {
            "jql": jql,
            "maxResults": 100,
            "fields": ["summary", "status", "parent", "issuetype", "comment"],
        }
        r = self._req("POST", "/rest/api/3/search/jql", json=body)
        if r.status_code >= 300:
            self.failures.append(f"search: {r.status_code} {r.text[:160]}")
            return []
        return list(r.json().get("issues") or [])

    def transitions(self, key: str) -> Dict[str, str]:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        if r.status_code >= 300:
            return {}
        return {t["to"]["name"]: t["id"] for t in r.json().get("transitions") or []}

    def transition(self, key: str, to_status: str) -> bool:
        mapping = self.transitions(key)
        tid = mapping.get(to_status)
        if not tid:
            self.failures.append(f"no transition {key} -> {to_status} (have {list(mapping)})")
            return False
        r = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/transitions",
            json={"transition": {"id": tid}},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 300:
            self.failures.append(f"transition {key}: {r.status_code} {r.text[:160]}")
            return False
        return True

    def add_comment(self, key: str, markdown: str) -> bool:
        # ADF simple doc from markdown-ish paragraphs
        paragraphs = [p.strip() for p in markdown.split("\n\n") if p.strip()]
        content: List[Dict[str, Any]] = []
        for p in paragraphs:
            lines = p.split("\n")
            for line in lines:
                text = line.replace("*", "") if False else line
                # Keep raw text; bold markers stripped for ADF simplicity — use plain
                plain = text.replace("*", "")
                content.append({"type": "paragraph", "content": [{"type": "text", "text": plain}]})
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": content or [{"type": "paragraph", "content": [{"type": "text", "text": markdown}]}],
            }
        }
        r = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 300:
            self.failures.append(f"comment {key}: {r.status_code} {r.text[:180]}")
            return False
        return True

    def recent_comments_text(self, key: str) -> str:
        r = self._req("GET", f"/rest/api/3/issue/{key}/comment")
        if r.status_code >= 300:
            return ""
        blobs: List[str] = []
        for c in r.json().get("comments") or []:
            # flatten ADF lightly
            blobs.append(json.dumps(c.get("body") or {}))
        return "\n".join(blobs)


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    s = json.loads(path.read_text(encoding="utf-8"))
    return (s["jira_url"].rstrip("/"), (s["jira_email"], s["jira_api_token"]))


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    summary: Dict[str, Any] = {
        "story_comments": [],
        "epic_comments": [],
        "epic_transitions": [],
        "skipped_comments": [],
    }

    stories = j.search("project = KAN AND issuetype = Story ORDER BY key ASC")
    epics = j.search("project = KAN AND issuetype = Epic AND key >= KAN-20 ORDER BY key ASC")

    # Comment Done product stories
    for issue in stories:
        key = issue["key"]
        status = issue["fields"]["status"]["name"]
        if key in SKIP_COMMENT_KEYS:
            continue
        if status != "Done":
            continue
        if key not in DONE_STORY_COMMENTS:
            summary["skipped_comments"].append(key)
            continue
        existing = j.recent_comments_text(key)
        if "Completion note (2026-11-15)" in existing:
            summary["skipped_comments"].append(f"{key}:already")
            continue
        if j.add_comment(key, DONE_STORY_COMMENTS[key]):
            summary["story_comments"].append(key)

    # Group children by epic
    by_epic: Dict[str, List[Dict[str, Any]]] = {e["key"]: [] for e in epics}
    for issue in stories:
        parent = (issue["fields"].get("parent") or {}).get("key")
        if parent in by_epic:
            by_epic[parent].append(issue)

    for epic in epics:
        ek = epic["key"]
        children = by_epic.get(ek) or []
        # ignore obsolete parents outside map
        done = [c for c in children if c["fields"]["status"]["name"] == "Done"]
        open_ = [c for c in children if c["fields"]["status"]["name"] != "Done"]
        cur = epic["fields"]["status"]["name"]

        target: Optional[str] = None
        if children and not open_:
            target = "Done"
        elif done and open_:
            target = "In Progress"
        elif not done and open_:
            target = "To Do"

        if target and cur != target:
            if j.transition(ek, target):
                summary["epic_transitions"].append(f"{ek}:{cur}->{target}")

        # Epic progress comment
        existing = j.recent_comments_text(ek)
        marker = "Progress sync (2026-11-15)"
        if marker in existing:
            continue
        done_list = ", ".join(f"{c['key']} {c['fields']['summary']}" for c in done) or "(none)"
        open_list = ", ".join(f"{c['key']} {c['fields']['summary']}" for c in open_) or "(none)"
        comment = (
            f"{marker}\n\n"
            f"Epic status sync from child Stories.\n\n"
            f"Done ({len(done)}): {done_list}\n\n"
            f"Still open ({len(open_)}): {open_list}\n\n"
            f"Canonical spec: docs/FUNCTIONAL_SPEC.md. Handoff: docs/ops/WORK_LOG.md "
            f"(Active slice KAN-53 when UI work). Repo: D:\\Projects\\ai_testing_app."
        )
        if j.add_comment(ek, comment):
            summary["epic_comments"].append(ek)

    # Ops comment on Active slice
    if "Completion note (2026-11-15) — backlog ready" not in j.recent_comments_text("KAN-53"):
        if j.add_comment(
            "KAN-53",
            (
                "Backlog readiness (2026-11-15) — backlog ready\n\n"
                "This story is the Active slice for “pick up where we left off”.\n\n"
                "Already done elsewhere in UI epic: desktop shell, drawers, WebGL orbs, "
                "widget settings, drag/snap (KAN-41).\n\n"
                "Remaining here: resizable panels on the desktop shell (and Gradio parity as needed).\n\n"
                "Spec: FR-UI-4. Roadmap: UI-6."
            ),
        ):
            summary["story_comments"].append("KAN-53:active")

    print(json.dumps({"failures": j.failures, **summary}, indent=2))
    j.close()
    return 0 if not j.failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
