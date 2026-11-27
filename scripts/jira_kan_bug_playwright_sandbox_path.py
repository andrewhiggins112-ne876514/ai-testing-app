"""Create + close Bug: Cursor PLAYWRIGHT_BROWSERS_PATH breaks OPERATE runs."""
from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35
SUMMARY = "Bug: OPERATE runs fail — Playwright Chromium path points at Cursor sandbox cache"


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
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line if line.strip() else " "}],
            }
            for line in lines
        ],
    }


class Jira:
    def __init__(self, base: str, auth: Tuple[str, str]) -> None:
        self.client = httpx.Client(
            timeout=90.0,
            verify=ssl.create_default_context(),
            auth=auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        self.base = base

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

    def find(self) -> Optional[str]:
        r = self._req(
            "POST",
            "/rest/api/3/search/jql",
            json={
                "jql": 'project = KAN AND issuetype = Bug AND summary ~ "Cursor sandbox cache" ORDER BY created DESC',
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

    def create(self, body: List[str]) -> Optional[str]:
        existing = self.find()
        if existing:
            return existing
        r = self._req(
            "POST",
            "/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": "KAN"},
                    "summary": SUMMARY,
                    "issuetype": {"name": "Bug"},
                    "description": adf(body),
                    "labels": ["operate", "playwright", "environment"],
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

    def done(self, key: str) -> bool:
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
    "After KAN-494 self-probe fix, OPERATE smoke + intentional-fail both fail with BrowserType.launch_persistent_context: Executable doesn't exist under Temp\\cursor-sandbox-cache\\...\\chromium-1255\\chrome-win64\\chrome.exe.",
    "",
    "## Expected",
    "Product desktop runs use %LOCALAPPDATA%\\ms-playwright Chromium (already installed). Smoke can pass; intentional-fail fails on assertion.",
    "",
    "## Actual",
    "PLAYWRIGHT_BROWSERS_PATH inherited from Cursor agent shell points at empty sandbox cache; launch fails. Misclassified as product_bug.",
    "",
    "## Environment",
    "Windows; desktop_app started from agent/Cursor shell; ms-playwright chromium-1255 present in Local AppData.",
    "",
    "## Replication steps",
    "1. In a shell where PLAYWRIGHT_BROWSERS_PATH=...\\cursor-sandbox-cache\\...\\playwright, start desktop_app.py.",
    "2. Run OPERATE golden path smoke.",
    "3. Observe Executable doesn't exist under cursor-sandbox-cache.",
]


FIX = [
    "Fix comment:",
    "Added plugins/playwright_env.sanitize_playwright_browsers_path(); called from desktop_app startup + playwright_runner.",
    "Clears cursor-sandbox-cache / missing-chromium overrides.",
    "Missing-browser errors map to failure_class=environment.",
    "Verify: pytest tests/test_playwright_env_sanitize.py — pass; restart desktop with sanitize; re-run smoke.",
]


def main() -> int:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        key = j.create(BODY)
        if not key:
            return 1
        for rel in ("KAN-377", "KAN-378", "KAN-494"):
            j.link(key, rel)
        j.comment(key, FIX)
        done = j.done(key)
        print(json.dumps({"bug": key, "done": done, "ok": True}))
        return 0 if done else 2
    finally:
        j.close()


if __name__ == "__main__":
    raise SystemExit(main())
