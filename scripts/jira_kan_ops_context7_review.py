"""Create ops Epic + Stories for Context7 / 2B review (not product FRs). Never prints tokens."""
from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKOFF = 0.35


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


def adf_text(text: str) -> Dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ],
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

    def _req(self, method: str, path: str, **kwargs) -> httpx.Response:
        for _ in range(6):
            r = self.client.request(method, f"{self.base}{path}", **kwargs)
            if r.status_code != 429:
                time.sleep(BACKOFF)
                return r
            time.sleep(float(r.headers.get("Retry-After", "2")))
        return r

    def create(self, fields: Dict[str, Any]) -> str:
        r = self._req("POST", "/rest/api/3/issue", json={"fields": fields})
        if r.status_code >= 300:
            raise SystemExit(f"create failed {r.status_code}: {r.text[:400]}")
        return r.json()["key"]

    def link_relates(self, a: str, b: str) -> None:
        body = {
            "type": {"name": "Relates"},
            "inwardIssue": {"key": a},
            "outwardIssue": {"key": b},
        }
        r = self._req("POST", "/rest/api/3/issueLink", json=body)
        if r.status_code >= 300:
            print(f"WARN link {a}<->{b}: {r.status_code}")

    def comment(self, key: str, text: str) -> None:
        body = {"body": adf_text(text)}
        r = self._req("POST", f"/rest/api/3/issue/{key}/comment", json=body)
        if r.status_code >= 300:
            print(f"WARN comment {key}: {r.status_code}")

    def transitions(self, key: str) -> List[Dict[str, Any]]:
        r = self._req("GET", f"/rest/api/3/issue/{key}/transitions")
        if r.status_code >= 300:
            return []
        return list(r.json().get("transitions") or [])

    def to_done(self, key: str) -> None:
        for t in self.transitions(key):
            name = str(t.get("name") or "").lower()
            if name in ("done", "closed", "complete"):
                r = self._req(
                    "POST",
                    f"/rest/api/3/issue/{key}/transitions",
                    json={"transition": {"id": t["id"]}},
                )
                print(f"transition {key} -> {t.get('name')}: {r.status_code}")
                return
        print(f"WARN no Done transition for {key}")


def main() -> None:
    base, auth = load_creds()
    j = Jira(base, auth)
    try:
        epic = j.create(
            {
                "project": {"key": "KAN"},
                "summary": "Ops: Context7 local + 2B currency/security/quality review",
                "issuetype": {"name": "Epic"},
                "description": adf_text(
                    "Ops-only (not a product FR). Phase0 Context7 API-key MCP. "
                    "Phase1 pin requirements + Context7 library audit. "
                    "Phase2 OFFICIAL/SECRET + GDPR isolation. "
                    "Phase3 dead code/test gaps. Then restore Track2 Active to KAN-291."
                ),
            }
        )
        print(f"EPIC {epic}")

        stories: List[Tuple[str, str, str]] = [
            (
                "Ops Phase1: pin requirements + Context7 library audit",
                "Pin requirements.txt to venv versions. Context7-audit FastAPI/Pydantic/"
                "Playwright/Gradio/pywebview/httpx/Ollama call sites. Fix API drift only.",
                "test: pytest tests/test_requirements_pins.py (+ related)",
            ),
            (
                "Ops Phase2: OFFICIAL/SECRET + GDPR security pass",
                "Walk credential/browser-profile isolation and GDPR wipe honesty. "
                "Confirm product never calls Context7. File Bugs with replication steps.",
                "test: pytest tests/test_security_isolation.py tests/test_privacy_gdpr.py",
            ),
            (
                "Ops Phase3: dead code / test gaps / restore KAN-291 Active",
                "Targeted dead/stub honesty check; high-value test gaps only; "
                "restore WORK_LOG Active to KAN-291.",
                "test: docs + focused pytest if code changed",
            ),
        ]

        story_keys: List[str] = []
        for summary, desc, test_note in stories:
            sk = j.create(
                {
                    "project": {"key": "KAN"},
                    "summary": summary,
                    "issuetype": {"name": "Story"},
                    "description": adf_text(desc + " Parent epic: " + epic),
                }
            )
            print(f"STORY {sk}")
            story_keys.append(sk)
            j.link_relates(sk, epic)
            tk = j.create(
                {
                    "project": {"key": "KAN"},
                    "summary": f"test: {summary}",
                    "issuetype": {"name": "test"},
                    "description": adf_text(test_note + f" Relates {sk}"),
                }
            )
            print(f"TEST {tk}")
            j.link_relates(tk, sk)

        # Completion comments for Phase0–3 applied in same agent run (keys printed for close-out).
        print("NEXT: agent will comment + Done per phase close-out")
        print("KEYS", epic, ",".join(story_keys))
    finally:
        j.close()


if __name__ == "__main__":
    main()
