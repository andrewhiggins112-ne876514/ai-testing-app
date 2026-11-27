"""Create + close Bug: Reports markdown viewer flex-clipped to unreadable strip.

Never prints tokens. Standing bug-raise authorization during development.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35
PROJECT = "KAN"
SUMMARY = "Bug: Reports markdown viewer clipped to thin unreadable strip"
STORY = "KAN-384"
TEST = "KAN-385"


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    levels = path.parent / "levels"
    level = str(data.get("security_level") or "OFFICIAL").upper()
    cred_path = levels / level / "credentials.json"
    if cred_path.exists():
        creds = json.loads(cred_path.read_text(encoding="utf-8-sig"))
        data = {**data, **creds}
    return (
        (data.get("jira_url") or "https://ai-testing-lab.atlassian.net").rstrip("/"),
        (data["jira_email"], data["jira_api_token"]),
    )


def adf(lines: List[str]) -> Dict[str, Any]:
    content = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": line if line.strip() else " "}],
        }
        for line in lines
    ]
    return {
        "type": "doc",
        "version": 1,
        "content": content
        or [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}],
    }


class Jira:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.base = base
        self.client = httpx.Client(
            timeout=90.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    def close(self) -> None:
        self.client.close()

    def _req(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        r = self.client.request(method, f"{self.base}{path}", **kwargs)
        for _ in range(5):
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
        return r

    def find_bug(self) -> Optional[str]:
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": (
                    f'project = {PROJECT} AND issuetype = Bug AND summary ~ '
                    f'"Reports markdown viewer clipped" ORDER BY created DESC'
                ),
                "maxResults": 5,
                "fields": ["summary"],
            },
        )
        if r.status_code >= 300:
            return None
        for issue in r.json().get("issues") or []:
            if (issue.get("fields") or {}).get("summary") == SUMMARY:
                return issue["key"]
        return None

    def create_bug(self, body_lines: List[str]) -> Optional[str]:
        existing = self.find_bug()
        if existing:
            return existing
        r = self._req(
            "POST",
            "/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": PROJECT},
                    "summary": SUMMARY,
                    "issuetype": {"name": "Bug"},
                    "description": adf(body_lines),
                    "labels": ["gap-cr", "reports", "ui"],
                }
            },
        )
        if r.status_code >= 300:
            print(f"create failed: {r.status_code}", file=sys.stderr)
            return None
        return (r.json() or {}).get("key")

    def link_relates(self, bug: str, other: str) -> None:
        self._req(
            "POST",
            "/rest/api/3/issueLink",
            json={
                "type": {"name": "Relates"},
                "inwardIssue": {"key": bug},
                "outwardIssue": {"key": other},
            },
        )

    def comment(self, key: str, lines: List[str]) -> None:
        self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf(lines)},
        )

    def transition_done(self, key: str) -> bool:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        if r.status_code >= 300:
            return False
        done_id = None
        for tr in r.json().get("transitions") or []:
            name = str((tr.get("to") or {}).get("name") or tr.get("name") or "").lower()
            if name == "done":
                done_id = tr.get("id")
                break
        if not done_id:
            return False
        r2 = self._req(
            "POST",
            f"/rest/api/3/issue/{key}/transitions",
            json={"transition": {"id": done_id}},
        )
        return r2.status_code < 300


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        body = [
            "## Symptom",
            "In Reports detail, the markdown text box collapses to a thin horizontal strip; only the tops of characters are visible.",
            "## Expected",
            "Markdown report body is fully readable with a usable scrollable height.",
            "## Actual",
            "pre#rpt-markdown.report-viewer is flex-shrunk nearly flat when evidence/screenshot fills the detail pane.",
            "## Environment",
            "Windows desktop app (pywebview), Reports area after KAN-384 charts (desk137).",
            "## Replication steps",
            "1. Launch desktop_app.py.",
            "2. Open App menu → Reports.",
            "3. Select a saved report that has a screenshot + markdown body.",
            "4. Observe the markdown box between evidence and Raw JSON — text is vertically clipped.",
        ]
        key = j.create_bug(body)
        if not key:
            return 1
        j.link_relates(key, STORY)
        j.link_relates(key, TEST)
        j.comment(
            key,
            [
                "## Fix",
                "Root cause: flex column detail pane + overflow:auto on .report-viewer → flex min-size 0 → markdown pre shrunk to unreadable strip.",
                "Change: min-height + flex sizing for #rpt-markdown and JSON viewer in .rpt-detail-pane; cache-bust desk138.",
                "Files: ui/desktop/desktop.css, ui/desktop/index.html, desktop_app.py, tests/test_reports_analytics.py",
                "Verify: pytest tests/test_reports_analytics.py -q; reopen Reports detail with screenshot — markdown readable.",
            ],
        )
        done = j.transition_done(key)
        print(json.dumps({"bug": key, "done": done, "linked": [STORY, TEST]}))
        return 0 if done else 0
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
