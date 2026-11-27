"""Create + close Bug: GET /api/plans removed in KAN-375 (Plans dropdown empty).

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
SUMMARY = "Bug: Plans dropdown shows (none yet) — GET /api/plans missing (KAN-375 regression)"


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
        {"type": "paragraph", "content": [{"type": "text", "text": line if line.strip() else " "}]}
        for line in lines
    ]
    return {"type": "doc", "version": 1, "content": content or [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]}


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
                "jql": f'project = {PROJECT} AND issuetype = Bug AND summary ~ "GET /api/plans missing" ORDER BY created DESC',
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
                    "labels": ["operate", "regression", "plans"],
                }
            },
        )
        if r.status_code != 201:
            print(json.dumps({"create_error": r.status_code, "body": r.text[:400]}))
            return None
        return r.json().get("key")

    def link(self, a: str, b: str) -> None:
        self._req(
            "POST",
            "/rest/api/3/issueLink",
            json={
                "type": {"name": "Relates"},
                "inwardIssue": {"key": a},
                "outwardIssue": {"key": b},
            },
        )

    def comment(self, key: str, lines: List[str]) -> None:
        self._req(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json={"body": adf(lines)},
        )

    def transitions(self, key: str) -> List[Dict[str, Any]]:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        if r.status_code >= 300:
            return []
        return list(r.json().get("transitions") or [])

    def mark_done(self, key: str) -> bool:
        for t in self.transitions(key):
            name = str(t.get("name") or "").lower()
            if name in {"done", "closed", "complete", "completed"}:
                r = self._req(
                    "POST",
                    f"/rest/api/3/issue/{key}/transitions",
                    json={"transition": {"id": t["id"]}},
                )
                return r.status_code < 300
        return False


BODY = [
    "## Symptom",
    "Plans area Plan dropdown shows only \"(none yet)\" even when plan JSON files exist under %LOCALAPPDATA%/ai_testing_app/plans/OFFICIAL/ (including OPERATE golden path from KAN-377).",
    "",
    "## Expected",
    "GET /api/plans returns the active-level plan list; desktop Plans dropdown shows OPERATE golden path and other plans.",
    "",
    "## Actual",
    "GET /api/plans returns HTTP 405 Method Not Allowed. UI loadPlanList treats missing plans[] as empty → \"(none yet)\".",
    "",
    "## Environment",
    "Windows home PC; desktop_app.py on 127.0.0.1:8765; security level OFFICIAL; native desktop window.",
    "",
    "## Replication steps",
    "1. Confirm plan files exist (e.g. OPERATE golden path p97123b7e8640.json under plans/OFFICIAL).",
    "2. Start desktop_app.py.",
    "3. Open App → Plans.",
    "4. Observe Plan dropdown \"(none yet)\".",
    "5. GET http://127.0.0.1:8765/api/plans → 405.",
    "",
    "## Root cause (found)",
    "KAN-375 commit replaced @app.get(\"/api/plans\") with @app.post(\"/api/playwright-trace/open\") instead of inserting beside it.",
]


FIX = [
    "Fix comment:",
    "Restored GET /api/plans → list_plans() in main.py.",
    "Kept POST /api/playwright-trace/open (KAN-375) intact.",
    "Added tests/test_plans_list_api.py regression.",
    "Verify: pytest tests/test_plans_list_api.py tests/test_operate_open_trace.py tests/test_operate_demo_aut.py — 17 passed.",
    "Restart desktop_app.py then Plans → Refresh — OPERATE golden path appears.",
]


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        key = j.create_bug(BODY)
        if not key:
            return 1
        for rel in ("KAN-375", "KAN-376", "KAN-377", "KAN-378"):
            j.link(key, rel)
        j.comment(key, FIX)
        done = j.mark_done(key)
        print(json.dumps({"bug": key, "done": done, "ok": True}))
        return 0 if done else 2
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
