"""Create + close Bug: local demo AUT Target timed out (self-HTTP deadlock)."""
from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35
PROJECT = "KAN"
SUMMARY = "Bug: OPERATE demo AUT runs fail Target timed out (self-probe deadlock)"


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
    return {"type": "doc", "version": 1, "content": content}


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
                    f'"self-probe deadlock" ORDER BY created DESC'
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

    def create_bug(self, body: List[str]) -> Optional[str]:
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
                    "description": adf(body),
                    "labels": ["operate", "regression", "demo-aut"],
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

    def mark_done(self, key: str) -> bool:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        for t in r.json().get("transitions") or []:
            if str(t.get("name") or "").lower() in {"done", "closed", "complete", "completed"}:
                tr = self._req(
                    "POST",
                    f"/rest/api/3/issue/{key}/transitions",
                    json={"transition": {"id": t["id"]}},
                )
                return tr.status_code < 300
        return False


BODY = [
    "## Symptom",
    "OPERATE golden path smoke + intentional-fail both record result=error, failure_class=environment, note=\"Target timed out.\" Playwright never runs.",
    "",
    "## Expected",
    "Smoke case against http://127.0.0.1:8765/demo-aut/ reaches the page and can pass. Intentional-fail runs Playwright and fails on missing text (not environment timeout).",
    "",
    "## Actual",
    "Both cases stop at target probe with Target timed out before any browser steps.",
    "",
    "## Environment",
    "Windows home PC; desktop_app.py :8765; OFFICIAL; target_url=http://127.0.0.1:8765/demo-aut/",
    "",
    "## Replication steps",
    "1. Seed OPERATE demo (scripts/seed_operate_demo.py) and start desktop_app.py.",
    "2. Plans → OPERATE golden path → Run smoke case.",
    "3. Observe Target timed out / environment (before fix).",
    "",
    "## Root cause",
    "Run handler (async) called sync httpx HEAD/GET to the same FastAPI process, blocking the event loop so /demo-aut/ could not answer → timeout.",
]


FIX = [
    "Fix comment:",
    "connection_health.is_self_app_url + short-circuit for loopback:8765 (demo AUT fixture check; no nested HTTP).",
    "run_case awaits asyncio.to_thread(_check_target) for external probes.",
    "Files: settings/connection_health.py, plans/run_case.py, tests/test_self_app_target_probe.py, docs/ops/DAILY_LOOP.md",
    "Verify: pytest tests/test_self_app_target_probe.py — 4 passed.",
    "httpx 0.28.1 /encode/httpx ASGITransport is async-only; used in-process short-circuit instead of nested HTTP.",
]


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        key = j.create_bug(BODY)
        if not key:
            return 1
        for rel in ("KAN-377", "KAN-378", "KAN-375", "KAN-493"):
            j.link(key, rel)
        j.comment(key, FIX)
        done = j.mark_done(key)
        print(json.dumps({"bug": key, "done": done, "ok": True}))
        return 0 if done else 2
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
