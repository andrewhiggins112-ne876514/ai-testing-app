"""
Migrate legacy KAN tickets after Bug / test issue types were enabled.

- Tasks with label=test  → issuetype test
- Tasks with label=bug   → issuetype Bug

Credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logged.

Usage:
  python scripts/jira_kan_migrate_issue_types.py
  python scripts/jira_kan_migrate_issue_types.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.3
TEST_TYPE = "test"
BUG_TYPE = "Bug"


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    level = str(data.get("security_level") or "OFFICIAL").upper()
    cred_path = path.parent / "levels" / level / "credentials.json"
    if cred_path.exists():
        data = {**data, **json.loads(cred_path.read_text(encoding="utf-8-sig"))}
    return (
        (data.get("jira_url") or "https://ai-testing-lab.atlassian.net").rstrip("/"),
        (data["jira_email"], data["jira_api_token"]),
    )


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

    def _req(self, method: str, path: str, **kwargs) -> httpx.Response:
        for _ in range(6):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
        return r

    def search(self, jql: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        fields = fields or ["summary", "status", "issuetype", "labels"]
        out: List[Dict[str, Any]] = []
        next_token: Optional[str] = None
        while True:
            body: Dict[str, Any] = {"jql": jql, "maxResults": 100, "fields": fields}
            if next_token:
                body["nextPageToken"] = next_token
            r = self._req("POST", "/rest/api/3/search/jql", json=body)
            r.raise_for_status()
            payload = r.json()
            issues = payload.get("issues") or []
            out.extend(issues)
            next_token = payload.get("nextPageToken")
            if not next_token or not issues:
                break
        return out

    def set_type(self, key: str, type_name: str) -> int:
        r = self._req(
            "PUT",
            f"/rest/api/3/issue/{key}",
            json={"fields": {"issuetype": {"name": type_name}}},
        )
        return r.status_code


def migrate(dry_run: bool) -> Dict[str, Any]:
    base, auth = load_creds()
    j = Jira(base, auth)
    report: Dict[str, Any] = {
        "converted_test": [],
        "converted_bug": [],
        "skipped": [],
        "failures": [],
    }
    try:
        tests = j.search("project = KAN AND labels = test ORDER BY key ASC")
        for issue in tests:
            key = issue["key"]
            cur = ((issue.get("fields") or {}).get("issuetype") or {}).get("name") or ""
            if str(cur).lower() == TEST_TYPE.lower():
                report["skipped"].append({"key": key, "reason": "already_test"})
                continue
            if dry_run:
                report["converted_test"].append({"key": key, "from": cur, "dry_run": True})
                continue
            code = j.set_type(key, TEST_TYPE)
            if code in (200, 204):
                report["converted_test"].append({"key": key, "from": cur, "code": code})
            else:
                report["failures"].append({"key": key, "target": TEST_TYPE, "code": code})

        bugs = j.search("project = KAN AND labels = bug ORDER BY key ASC")
        for issue in bugs:
            key = issue["key"]
            cur = ((issue.get("fields") or {}).get("issuetype") or {}).get("name") or ""
            if cur == BUG_TYPE:
                report["skipped"].append({"key": key, "reason": "already_bug"})
                continue
            if dry_run:
                report["converted_bug"].append({"key": key, "from": cur, "dry_run": True})
                continue
            code = j.set_type(key, BUG_TYPE)
            if code in (200, 204):
                report["converted_bug"].append({"key": key, "from": cur, "code": code})
            else:
                report["failures"].append({"key": key, "target": BUG_TYPE, "code": code})
    finally:
        j.close()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = migrate(dry_run=args.dry_run)
    print(json.dumps(report, indent=2))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
