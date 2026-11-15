"""
Post agent completion comments on a KAN Story and its linked test Task(s).

Required on every finished coding slice (see AGENTS.md / work-log-handoff).

Credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logged.

Usage:
  python scripts/jira_kan_slice_closeout.py --story KAN-47 \\
    --done "What the agent implemented..." \\
    --files "a.py, b.py" \\
    --verify "pytest … (N passed)" \\
    [--test-key KAN-48] [--mark-done] [--pytest-cmd "…"]

If --test-key is omitted, uses Relates links with label=test, then TEST_PARENT map.
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

BACKOFF = 0.35

# Keep in sync with scripts/jira_kan_enrich.py TEST_PARENT (inverted)
STORY_TO_TEST: Dict[str, str] = {
    "KAN-8": "KAN-30",
    "KAN-9": "KAN-31",
    "KAN-10": "KAN-32",
    "KAN-11": "KAN-33",
    "KAN-12": "KAN-34",
    "KAN-13": "KAN-35",
    "KAN-14": "KAN-36",
    "KAN-15": "KAN-37",
    "KAN-16": "KAN-38",
    "KAN-39": "KAN-40",
    "KAN-41": "KAN-42",
    "KAN-43": "KAN-44",
    "KAN-45": "KAN-46",
    "KAN-47": "KAN-48",
    "KAN-49": "KAN-50",
    "KAN-51": "KAN-52",
    "KAN-53": "KAN-54",
    "KAN-55": "KAN-56",
    "KAN-57": "KAN-58",
    "KAN-59": "KAN-60",
    "KAN-61": "KAN-62",
    "KAN-63": "KAN-64",
    "KAN-65": "KAN-66",
    "KAN-67": "KAN-68",
    "KAN-69": "KAN-70",
    "KAN-71": "KAN-72",
    "KAN-73": "KAN-74",
    "KAN-75": "KAN-76",
    "KAN-77": "KAN-78",
    "KAN-79": "KAN-80",
    "KAN-81": "KAN-82",
}


def load_creds() -> Tuple[str, Tuple[str, str]]:
    path = Path(os.environ["LOCALAPPDATA"]) / "ai_testing_app" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    # Prefer level-scoped credentials if present
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

    def get_issue(self, key: str, fields: str) -> Optional[Dict[str, Any]]:
        r = self._req("GET", f"/rest/api/3/issue/{key}", params={"fields": fields})
        if r.status_code >= 300:
            self.failures.append(f"get {key}: {r.status_code} {r.text[:160]}")
            return None
        return r.json()

    def add_comment(self, key: str, paragraphs: List[str]) -> bool:
        content: List[Dict[str, Any]] = []
        for para in paragraphs:
            text = (para or "").strip()
            if not text:
                continue
            content.append(
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            )
        if not content:
            self.failures.append(f"comment {key}: empty body")
            return False
        body = {"body": {"type": "doc", "version": 1, "content": content}}
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

    def transitions(self, key: str) -> Dict[str, str]:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        if r.status_code >= 300:
            return {}
        return {t["to"]["name"]: t["id"] for t in r.json().get("transitions") or []}

    def transition(self, key: str, to_status: str = "Done") -> bool:
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

    def related_test_keys(self, story_key: str) -> List[str]:
        issue = self.get_issue(story_key, "issuelinks")
        found: List[str] = []
        if not issue:
            return found
        for link in issue.get("fields", {}).get("issuelinks") or []:
            other = link.get("outwardIssue") or link.get("inwardIssue") or {}
            key = other.get("key")
            if not key:
                continue
            detail = self.get_issue(key, "labels,issuetype,summary")
            if not detail:
                continue
            labels = detail.get("fields", {}).get("labels") or []
            if "test" in labels:
                found.append(key)
        mapped = STORY_TO_TEST.get(story_key)
        if mapped and mapped not in found:
            found.append(mapped)
        return found


def story_comment_paragraphs(done: str, files: str, verify: str, test_keys: List[str]) -> List[str]:
    paras = [
        "Agent completion (Cursor IDE Agent)",
        f"What the agent did to complete this story: {done.strip()}",
    ]
    if files.strip():
        paras.append(f"Files touched: {files.strip()}")
    if verify.strip():
        paras.append(f"How to verify: {verify.strip()}")
    if test_keys:
        paras.append(
            "Linked test Task(s) updated with unit/manual evidence: "
            + ", ".join(test_keys)
        )
    else:
        paras.append(
            "No linked test Task found (label=test Relates). Create one and Relates-link it."
        )
    return paras


def test_comment_paragraphs(story_key: str, verify: str, pytest_cmd: str) -> List[str]:
    paras = [
        f"Agent verification for parent story {story_key}",
        "Automated / recorded checks run by the coding agent:",
    ]
    if pytest_cmd.strip():
        paras.append(f"Unit tests: {pytest_cmd.strip()}")
    if verify.strip():
        paras.append(f"Evidence / verify steps: {verify.strip()}")
    paras.append(
        "Marking this test Task Done because the parent story’s acceptance checks passed."
    )
    return paras


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, help="Story key, e.g. KAN-47")
    parser.add_argument("--done", required=True, help="What the agent implemented")
    parser.add_argument("--files", default="", help="Comma-separated paths")
    parser.add_argument("--verify", default="", help="Verify steps / pytest summary")
    parser.add_argument("--pytest-cmd", default="", help="Exact pytest command + result")
    parser.add_argument("--test-key", action="append", default=[], help="Force test Task key(s)")
    parser.add_argument(
        "--mark-done",
        action="store_true",
        help="Transition story + test Task(s) to Done",
    )
    parser.add_argument(
        "--story-only",
        action="store_true",
        help="Skip test Task updates",
    )
    args = parser.parse_args()

    base, auth = load_creds()
    j = Jira(base, auth)
    summary: Dict[str, Any] = {"story": args.story, "tests": [], "ok": True}

    try:
        test_keys = list(args.test_key) or j.related_test_keys(args.story)
        if not j.add_comment(
            args.story,
            story_comment_paragraphs(args.done, args.files, args.verify, test_keys),
        ):
            summary["ok"] = False
        else:
            summary["story_comment"] = True

        if args.mark_done:
            summary["story_done"] = j.transition(args.story, "Done")

        if not args.story_only:
            for test_key in test_keys:
                ok = j.add_comment(
                    test_key,
                    test_comment_paragraphs(args.story, args.verify, args.pytest_cmd),
                )
                entry: Dict[str, Any] = {"key": test_key, "comment": ok}
                if args.mark_done and ok:
                    entry["done"] = j.transition(test_key, "Done")
                summary["tests"].append(entry)
                if not ok:
                    summary["ok"] = False

        if j.failures:
            summary["failures"] = j.failures
            summary["ok"] = False
    finally:
        j.close()

    print(json.dumps(summary, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
