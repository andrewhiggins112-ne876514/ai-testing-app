"""Post Council+Studio+Creative accept comments on KAN-496 / KAN-497 (no tokens printed)."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKOFF = 0.35
STORY = "KAN-496"
TEST = "KAN-497"

COMMENT = """h2. Council+Studio+Creative accept (2026-11-27)

*Decision:* CR / vision align. Designer accepted.

*Scope:* Case detail readable step narrative + pass/fail evidence + Open Trace (external). Not Trace Viewer embed, not Reports charts, not theme/orb/home, not absorb into OPERATE-3 (*KAN-379*).

*Studio Slice-0 (required now, parallel):* thin mockpack under {{docs/mockups/run_evidence_ux/}} — before, smoke-pass, intentional-fail, honest empty, rejected page-gallery. Preferred Option A vertical run story in existing Case aside.

*Build Slice-1:* only after *KAN-379* Done + Designer mock pick. Prefer OPERATE-4 before this Build unless Designer elevates.

*AC adds (from full-room discovery):*
# Evidence list/open filtered by active security level (no cross-level paths).
# No embedded Trace Viewer; Open Trace stays OPERATE-1 path.
# Pytest fails if a placeholder/fake pass image is shown.
# Success evidence default for smoke/golden; configurable off in the same story.
# Honest none-captured copy (not empty decorative gallery).
# Ordered step outcomes persisted on the run (FR-PLAN-4) so UI is not paint-only.

*Process CR:* future reviews = whole team researches per role + surfaces missing requirements early (see ADVISORY_COUNCIL.md).

*Active Build unchanged:* *KAN-379*. No product code in Council chat.
"""


def load_creds() -> tuple[str, tuple[str, str]]:
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


def req(method: str, url: str, auth: tuple[str, str], body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    r = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    import base64

    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    r.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"HTTP {e.code} {url}: {err}") from e


def add_comment(base: str, auth: tuple[str, str], key: str, text: str) -> None:
    # ADF minimal paragraph dump via wiki-style through /rest/api/2
    body = {"body": text}
    req("POST", f"{base}/rest/api/2/issue/{key}/comment", auth, body)
    time.sleep(BACKOFF)


def main() -> int:
    base, auth = load_creds()
    for key in (STORY, TEST):
        add_comment(base, auth, key, COMMENT)
        print(f"commented {key}")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
