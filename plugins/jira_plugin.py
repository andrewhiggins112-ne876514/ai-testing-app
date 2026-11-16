"""Jira tools. list_stories is read-only. create_issue POSTs only after the user's own confirmation."""
import asyncio
import json
import os
import platform
import re
import ssl
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from settings.store import load_settings


def _async_client(timeout: float = 20.0) -> httpx.AsyncClient:
    """httpx client using the system CA store (matches scripts/jira_kan_*.py)."""
    return httpx.AsyncClient(timeout=timeout, verify=ssl.create_default_context())

_PROJECT = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,10}")
_LIST_KEY = re.compile(r"[A-Z0-9]{1,10}")
_ISSUE_KEY = re.compile(r"[A-Z][A-Z0-9]{0,9}-\d+")
_TYPE_JQL = {
    "story": "Story",
    "task": "Task",
    "bug": "Bug",
    "test": "test",  # KAN custom type name is lowercase "test"
    "epic": "Epic",
    "subtask": "Sub-task",
    "sub-task": "Sub-task",
}
# KAN issue types (createmeta): Epic, Story, Task, Bug, test, Subtask
TEST_ISSUE_TYPE = "test"
BUG_ISSUE_TYPE = "Bug"
_ISSUE_TYPE = re.compile(r"[A-Za-z][A-Za-z0-9 ]{0,39}")
_WRITE = {"create_test", "update_status", "create_bug"}
_CONFIRM_WORDS = {"yes", "confirm"}
_PENDING: Dict[str, Dict[str, Any]] = {}
_CONFIRM_TTL = 300.0
# Successful confirmed writes that get a local audit line (NFR §4.3 / KAN-99).
_SUCCESS_WRITE_STATUSES = frozenset({"created", "linked", "transitioned", "updated", "commented"})
# FR-JIRA-6 — match scripts/jira_kan_*.py backoff behaviour
_MAX_429_ATTEMPTS = 6
_INTER_CALL_BACKOFF = 0.35
_DEFAULT_RETRY_AFTER = 2.0


def jira_write_log_path() -> Path:
    """LOCALAPPDATA jira_write_audit.jsonl (mirrors heal_audit.jsonl)."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "ai_testing_app" if base else Path.home() / ".ai_testing_app"
    return root / "jira_write_audit.jsonl"


def append_jira_write_log(entry: Dict[str, Any]) -> None:
    path = jira_write_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _issue_key_from_outcome(outcome: Dict[str, Any]) -> str:
    for field in ("key", "issue_key"):
        key = _issue_key(outcome.get(field))
        if key:
            return key
    return ""


def _maybe_audit_write(*, session_id: str, action: str, outcome: Optional[Dict[str, Any]]) -> None:
    """Append one local audit line after a successful confirmed write. Never stores tokens."""
    if not isinstance(outcome, dict):
        return
    if outcome.get("status") not in _SUCCESS_WRITE_STATUSES:
        return
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": str(action or ""),
        "issue_key": _issue_key_from_outcome(outcome),
        "session_id": str(session_id or ""),
        "status": outcome.get("status"),
    }
    try:
        append_jira_write_log(entry)
    except Exception:
        pass


async def _sleep(seconds: float) -> None:
    """Awaitable delay. No-op under pytest so the unit suite stays fast."""
    if seconds <= 0:
        return
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    await asyncio.sleep(seconds)


def _retry_after_seconds(response: Any) -> float:
    headers = getattr(response, "headers", None) or {}
    raw = None
    try:
        raw = headers.get("Retry-After")
        if raw is None:
            raw = headers.get("retry-after")
    except (TypeError, AttributeError):
        raw = None
    if raw is None:
        return _DEFAULT_RETRY_AFTER
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return _DEFAULT_RETRY_AFTER


async def _request(client: Any, method: str, url: str, **kwargs: Any) -> Any:
    """HTTP helper with 429 Retry-After retries and light inter-call spacing (FR-JIRA-6)."""
    method_u = str(method or "GET").upper()
    response: Any = None
    for _ in range(_MAX_429_ATTEMPTS):
        if method_u == "GET":
            response = await client.get(url, **kwargs)
        elif method_u == "POST":
            response = await client.post(url, **kwargs)
        elif method_u == "PUT":
            response = await client.put(url, **kwargs)
        else:
            response = await client.request(method_u, url, **kwargs)
        if getattr(response, "status_code", 0) != 429:
            await _sleep(_INTER_CALL_BACKOFF)
            return response
        await _sleep(_retry_after_seconds(response))
    return response


def _auth_error(status: int = 401) -> Dict[str, Any]:
    return {
        "status": "unauthorized",
        "message": (
            "Jira rejected the credentials "
            "(check email and API token in local settings)."
        ),
        "http_status": int(status),
    }


def _rate_limited_error(response: Any = None) -> Dict[str, Any]:
    wait = _retry_after_seconds(response) if response is not None else _DEFAULT_RETRY_AFTER
    seconds = max(1, int(round(wait)))
    return {
        "status": "rate_limited",
        "message": (
            f"Jira rate limit reached. Wait about {seconds}s and try again "
            "(Retry-After was respected)."
        ),
        "http_status": 429,
        "retry_after": wait,
    }

def _creds() -> Dict[str, str]:
    settings = load_settings()
    return {
        "url": (settings.get("jira_url") or "").rstrip("/"),
        "email": settings.get("jira_email") or "",
        "token": settings.get("jira_api_token") or "",
    }

def _url_ok(url: str) -> bool:
    return url.startswith("https://") or url.startswith("http://127.0.0.1") or url.startswith("http://localhost")

def _stories(
    payload: Dict[str, Any],
    project: str,
    *,
    include_description: bool = False,
) -> Dict[str, Any]:
    stories = []
    for issue in payload.get("issues") or []:
        fields = issue.get("fields") or {}
        status = fields.get("status") or {}
        kind = fields.get("issuetype") or {}
        row: Dict[str, Any] = {
            "key": issue.get("key", ""),
            "summary": fields.get("summary", ""),
            "status": status.get("name", "") if isinstance(status, dict) else "",
            "type": kind.get("name", "") if isinstance(kind, dict) else "",
        }
        if include_description:
            description = adf_to_text(fields.get("description"))
            acceptance = extract_acceptance_criteria(description)
            row["description"] = description
            row["acceptance_criteria"] = acceptance
            row["has_acceptance_criteria"] = bool(acceptance)
        stories.append(row)
    return {"stories": stories, "project": project}

async def _search(url: str, email: str, token: str, project: str) -> Dict[str, Any]:
    jql = f"project = {project} AND issuetype = Story ORDER BY updated DESC"
    params = {"jql": jql, "maxResults": 10, "fields": "summary,status"}
    attempts = []
    if email:
        attempts.append((f"{url}/rest/api/3/search/jql", (email, token), {}))
        attempts.append((f"{url}/rest/api/2/search", (email, token), {}))
    else:
        attempts.append((f"{url}/rest/api/2/search", None, {"Authorization": f"Bearer {token}"}))

    async with _async_client() as client:
        last_status = 0
        for endpoint, auth, headers in attempts:
            response = await _request(
                client,
                "GET",
                endpoint,
                params=params,
                auth=auth,
                headers={"Accept": "application/json", **headers},
            )
            last_status = response.status_code
            if response.status_code == 404:
                continue
            if response.status_code in (401, 403):
                err = _auth_error(response.status_code)
                return {
                    "error": "jira_unauthorized",
                    "status": response.status_code,
                    "message": err["message"],
                }
            if response.status_code == 429:
                err = _rate_limited_error(response)
                return {
                    "error": "jira_rate_limited",
                    "status": 429,
                    "message": err["message"],
                }
            if response.status_code >= 400:
                return {"error": "jira_request_failed", "status": response.status_code}
            return _stories(response.json(), project)
    return {"error": "jira_search_unavailable", "status": last_status}

async def jira_action(
    action: str,
    project: Optional[str] = None,
    summary: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    if action == "create_bug":
        return {
            "status": "confirmation_required",
            "action": action,
            "note": "Use the create_bug tool with failed-run fields; Jira writes need an explicit yes/confirm.",
        }
    if action == "create_test":
        return {
            "status": "confirmation_required",
            "action": action,
            "note": "Use the create_test tool with story_key and steps; Jira writes need an explicit yes/confirm.",
        }
    if action == "update_status":
        return {
            "status": "confirmation_required",
            "action": action,
            "note": "Use the update_status tool with issue_key and coverage_evidence; Jira writes need an explicit yes/confirm.",
        }
    if action in _WRITE:
        return {
            "status": "confirmation_required",
            "action": action,
            "note": "Jira writes are not enabled. list_stories is read-only.",
        }
    if action != "list_stories":
        return {"error": "Unknown action"}
    settings = load_settings()
    key = (
        str(project or "").strip().upper()
        or str(settings.get("jira_project") or "").strip().upper()
    )
    if not key or not _LIST_KEY.fullmatch(key):
        return {
            "error": "project key required (argument or jira_project in settings), for example PROJ"
        }
    creds = _creds()
    if not creds["url"] or not creds["token"]:
        return {
            "error": "jira_not_configured",
            "need": ["jira_url", "jira_api_token"],
            "optional": ["jira_email for Jira Cloud"],
        }
    if not _url_ok(creds["url"]):
        return {"error": "jira_url must start with https://"}
    try:
        return await _search(creds["url"], creds["email"], creds["token"], key)
    except httpx.HTTPError as exc:
        detail = str(exc).replace(creds["token"], "***")[:200]
        return {"error": "jira_request_failed", "detail": detail}


def _list_creds() -> Dict[str, str]:
    settings = load_settings()
    base = settings.get("jira_base_url") or settings.get("jira_url") or ""
    token = os.getenv("JIRA_API_TOKEN") or settings.get("jira_api_token") or ""
    email = os.getenv("JIRA_EMAIL") or settings.get("jira_email") or ""
    return {"url": str(base).strip().rstrip("/"), "email": str(email).strip(), "token": str(token).strip()}


def _clamp_max(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 50
    return min(100, max(1, number))


def _type_clause(issue_types: Any) -> Any:
    """JQL fragment from the allow-list, or an error dict. Empty means every type."""
    if issue_types is None:
        return ""
    if isinstance(issue_types, str):
        issue_types = [issue_types]
    if not isinstance(issue_types, (list, tuple)):
        return {"status": "error", "message": "issue type must be Story, Task, Bug, Epic, or Subtask"}
    names = []
    for item in issue_types:
        canonical = _TYPE_JQL.get(str(item or "").strip().casefold())
        if not canonical:
            return {"status": "error", "message": "issue type must be Story, Task, Bug, Epic, or Subtask"}
        if canonical not in names:
            names.append(canonical)
    if not names:
        return ""
    quoted = ", ".join(f'"{name}"' for name in names)
    return f" AND issuetype IN ({quoted})"


async def _list_search(
    url: str,
    email: str,
    token: str,
    project: str,
    limit: int,
    clause: str,
    *,
    include_description: bool = False,
) -> Dict[str, Any]:
    """GET the search API. The result never includes credentials."""
    fields = "summary,status,issuetype"
    if include_description:
        fields += ",description"
    params = {
        "jql": f"project = {project}{clause} ORDER BY key DESC",
        "maxResults": limit,
        "fields": fields,
    }
    if email:
        attempts = [
            (f"{url}/rest/api/3/search/jql", (email, token), {}),
            (f"{url}/rest/api/2/search", (email, token), {}),
        ]
    else:
        attempts = [(f"{url}/rest/api/2/search", None, {"Authorization": f"Bearer {token}"})]

    async with _async_client() as client:
        for endpoint, auth, headers in attempts:
            response = await _request(
                client,
                "GET",
                endpoint,
                params=params,
                auth=auth,
                headers={"Accept": "application/json", **headers},
            )
            if response.status_code == 404:
                continue
            if response.status_code in (401, 403):
                return _auth_error(response.status_code)
            if response.status_code == 429:
                return _rate_limited_error(response)
            if response.status_code >= 400:
                return {"status": "error", "message": "jira_request_failed"}
            payload = response.json()
            stories = _stories(
                payload, project, include_description=include_description
            )["stories"]
            result = {"status": "ok", "stories": stories}
            try:
                total = int(payload.get("total"))
            except (TypeError, ValueError):
                total = None
            if total is not None and total > len(stories):
                result["note"] = f"showing {len(stories)} of {total}"
            return result
    return {"status": "error", "message": "jira_search_unavailable"}


async def list_stories(
    project: Optional[str] = None,
    max: int = 50,
    issue_types: Any = None,
    include_description: bool = False,
) -> Dict[str, Any]:
    """Read-only issue list. GET only. Missing URL or token returns unconfigured.

    Project defaults to settings jira_project when omitted (FR-LEARN-4).
    """
    settings = load_settings()
    key = (
        str(project or "").strip().upper()
        or str(settings.get("jira_project") or "").strip().upper()
    )
    if not key:
        return {
            "status": "error",
            "message": "project key required (argument or jira_project in settings)",
        }
    if not _LIST_KEY.fullmatch(key):
        return {"status": "error", "message": "project key must be 1-10 characters, A-Z and 0-9"}
    clause = _type_clause(issue_types)
    if isinstance(clause, dict):
        return clause
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return {
            "status": "unconfigured",
            "message": "Set jira_url or jira_base_url in local settings and a token in JIRA_API_TOKEN or jira_api_token.",
        }
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    try:
        return await _list_search(
            creds["url"],
            creds["email"],
            creds["token"],
            key,
            _clamp_max(max),
            clause,
            include_description=bool(include_description),
        )
    except httpx.HTTPError:
        return {"status": "error", "message": "jira_request_failed"}


_AC_HEADING = re.compile(
    r"(?im)^[ \t]*(?:\d+\.\s*)?(?:acceptance\s+criteria|ac)\s*:?\s*$"
)
_SECTION_HEADING = re.compile(
    r"(?im)^[ \t]*(?:\d+\.\s*)?(?:"
    r"definition\s+of\s+done|out\s+of\s+scope|technical\s+notes|"
    r"roadmap|dependencies|behaviour|requirements|user\s+story|"
    r"who\s+this\s+is\s+for|intro|evidence|test\s+procedure"
    r")\s*:?\s*$"
)


def adf_to_text(node: Any) -> str:
    """Flatten Atlassian Document Format (or plain string) to readable text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    parts: list[str] = []

    def walk(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, str):
            parts.append(item)
            return
        if isinstance(item, list):
            for child in item:
                walk(child)
            return
        if not isinstance(item, dict):
            return
        kind = str(item.get("type") or "")
        if kind == "text":
            parts.append(str(item.get("text") or ""))
            return
        if kind == "hardBreak":
            parts.append("\n")
            return
        for child in item.get("content") or []:
            walk(child)
        if kind in {
            "paragraph",
            "heading",
            "blockquote",
            "listItem",
            "bulletList",
            "orderedList",
            "codeBlock",
            "rule",
        }:
            if parts and not parts[-1].endswith("\n"):
                parts.append("\n")

    walk(node)
    text = "".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_acceptance_criteria(description: str) -> str:
    """Pull the Acceptance criteria section from a description, if present."""
    raw = (description or "").replace("\r\n", "\n").strip()
    if not raw:
        return ""
    match = _AC_HEADING.search(raw)
    if not match:
        return ""
    rest = raw[match.end() :].lstrip("\n")
    end = _SECTION_HEADING.search(rest)
    body = rest[: end.start()] if end else rest
    return body.strip()


async def read_issue(issue_key: str) -> Dict[str, Any]:
    """Read-only fetch of summary + description/AC for one issue. Never returns credentials."""
    key = _issue_key(issue_key)
    if not key:
        return {"status": "error", "message": "issue key must look like KEY-123"}
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{key}",
                params={"fields": "summary,status,issuetype,description"},
                auth=auth,
                headers=headers,
            )
        if response.status_code in (401, 403):
            return _auth_error(response.status_code)
        if response.status_code == 429:
            return _rate_limited_error(response)
        if response.status_code == 404:
            return {"status": "error", "message": f"issue {key} not found"}
        if response.status_code >= 400:
            return {"status": "error", "message": "jira_request_failed"}
        payload = response.json()
        fields = payload.get("fields") or {}
        status = fields.get("status") or {}
        kind = fields.get("issuetype") or {}
        description = adf_to_text(fields.get("description"))
        acceptance = extract_acceptance_criteria(description)
        return {
            "status": "ok",
            "key": payload.get("key") or key,
            "summary": str(fields.get("summary") or ""),
            "issue_status": status.get("name", "") if isinstance(status, dict) else "",
            "type": kind.get("name", "") if isinstance(kind, dict) else "",
            "description": description,
            "acceptance_criteria": acceptance,
            "has_acceptance_criteria": bool(acceptance),
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return {"status": "error", "message": "jira_request_failed"}


def _unconfigured() -> Dict[str, str]:
    return {
        "status": "unconfigured",
        "message": "Set jira_url or jira_base_url in local settings and a token in JIRA_API_TOKEN or jira_api_token.",
    }


def _issue_key(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not _ISSUE_KEY.fullmatch(text):
        return ""
    return text


def _store_pending(session_id: str, preview: Dict[str, Any], action: str = "create") -> str:
    confirm_id = uuid.uuid4().hex
    _PENDING[str(session_id)] = {
        "confirm_id": confirm_id,
        "action": action,
        "preview": preview,
        "expires": time.monotonic() + _CONFIRM_TTL,
    }
    return confirm_id


def _auth(creds: Dict[str, str]) -> tuple:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if creds["email"]:
        return headers, (creds["email"], creds["token"])
    headers["Authorization"] = f"Bearer {creds['token']}"
    return headers, None


def _valid_create(
    project: str,
    summary: str,
    description: Optional[str],
    issue_type: Optional[str],
    parent_key: Optional[str] = None,
) -> Dict[str, Any]:
    key = str(project or "").strip().upper()
    if not _LIST_KEY.fullmatch(key):
        return {"status": "error", "message": "project key must be 1-10 characters, A-Z and 0-9"}
    text = str(summary or "").strip()
    if not text or len(text) > 255:
        return {"status": "error", "message": "summary is required and must be 255 characters or less"}
    kind = str(issue_type or "").strip() or "Task"
    if kind.casefold() == "task":
        kind = "Task"
    if not _ISSUE_TYPE.fullmatch(kind):
        return {"status": "error", "message": "issue type must be 1-40 characters, letters, digits, and spaces"}
    detail = str(description or "").strip()
    parent = ""
    raw_parent = str(parent_key or "").strip()
    if raw_parent:
        parent = _issue_key(raw_parent)
        if not parent:
            return {"status": "error", "message": "parent key must look like KEY-123"}
    preview = {"project": key, "summary": text, "description": detail, "issue_type": kind}
    if parent:
        preview["parent_key"] = parent
    return preview


def _adf(text: str) -> Dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


async def _post_issue(preview: Dict[str, str]) -> Dict[str, Any]:
    """POST one issue. The result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    fields: Dict[str, Any] = {
        "project": {"key": preview["project"]},
        "summary": preview["summary"],
        "issuetype": {"name": preview["issue_type"]},
    }
    if preview.get("description"):
        fields["description"] = _adf_comment(preview["description"])
    if preview.get("parent_key"):
        fields["parent"] = {"key": preview["parent_key"]}
    labels = preview.get("labels")
    if isinstance(labels, (list, tuple)) and labels:
        fields["labels"] = [str(item).strip() for item in labels if str(item or "").strip()]
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "POST",
                f"{creds['url']}/rest/api/3/issue",
                json={"fields": fields},
                auth=auth,
                headers=headers,
            )
            if response.status_code in (401, 403):
                return _auth_error(response.status_code)
            if response.status_code == 429:
                return _rate_limited_error(response)
            if response.status_code >= 400:
                return {"status": "error", "message": "jira_request_failed"}
            try:
                data = response.json()
            except ValueError:
                return {"status": "error", "message": "jira_request_failed"}
            key = data.get("key") or ""
            relates = str(preview.get("relates_to") or "").strip()
            if key and relates:
                await _post_relates_link(client, creds["url"], headers, auth, key, relates)
    except httpx.HTTPError:
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "created", "key": key}

async def create_issue(
    project: str,
    summary: str,
    description: Optional[str] = None,
    issue_type: str = "Task",
    parent_key: Optional[str] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """Store a preview for this session. Never POSTs."""
    preview = _valid_create(project, summary, description, issue_type, parent_key)
    if preview.get("status"):
        return preview
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    confirm_id = _store_pending(session_id, preview, "create")
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": preview}


async def resolve_create(session_id: str, user_message: str) -> Optional[Dict[str, Any]]:
    """Consume this session's pending create. yes/confirm POSTs once. Anything else cancels."""
    record = _PENDING.get(str(session_id))
    if not record:
        return None
    _PENDING.pop(str(session_id), None)
    word = str(user_message or "").strip().casefold()
    if word not in _CONFIRM_WORDS:
        return {"status": "cancelled", "confirm_id": record["confirm_id"]}
    if time.monotonic() >= record["expires"]:
        return {"status": "expired", "confirm_id": record["confirm_id"]}
    action = str(record.get("action") or "create")
    if action == "set_parent":
        outcome = await _put_parent(record["preview"])
    elif action == "transition":
        outcome = await _post_transition(record["preview"])
    elif action == "update_status":
        outcome = await _post_update_status(record["preview"])
    elif action == "comment":
        outcome = await _post_comment(record["preview"])
    else:
        # create / create_bug / create_test share the same POST path
        outcome = await _post_issue(record["preview"])
    _maybe_audit_write(session_id=str(session_id), action=action, outcome=outcome)
    return outcome


async def _post_relates_link(
    client: Any,
    url: str,
    headers: Dict[str, str],
    auth: Any,
    bug_key: str,
    other_key: str,
) -> None:
    """Best-effort Relates link. Never raises into the caller; create already succeeded."""
    try:
        await _request(
            client,
            "POST",
            f"{url}/rest/api/3/issueLink",
            json={
                "type": {"name": "Relates"},
                "inwardIssue": {"key": bug_key},
                "outwardIssue": {"key": other_key},
            },
            auth=auth,
            headers=headers,
        )
    except httpx.HTTPError:
        return


def _as_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [line.strip() for line in text.splitlines() if line.strip()]
    if isinstance(value, (list, tuple)):
        lines = []
        for item in value:
            text = str(item or "").strip()
            if text:
                lines.append(text)
        return lines
    text = str(value).strip()
    return [text] if text else []


def _mask_secrets(text: str) -> str:
    """Strip common credential patterns from bug text. Never echo tokens."""
    cleaned = text or ""
    cleaned = re.sub(
        r"(?i)(api[_-]?token|password|secret|authorization)\s*[:=]\s*\S+",
        r"\1=***",
        cleaned,
    )
    cleaned = re.sub(r"(?i)Bearer\s+[A-Za-z0-9._\-]+", "Bearer ***", cleaned)
    return cleaned


def build_bug_description(
    *,
    symptom: str = "",
    expected: str = "",
    actual: str = "",
    environment: str = "",
    replication_steps: Any = None,
    evidence_paths: Any = None,
) -> str:
    """Human-readable Bug body (FR-JIRA-4 template sections)."""
    steps = _as_lines(replication_steps)
    evidence = _as_lines(evidence_paths)
    blocks = [
        "Symptom",
        _mask_secrets((symptom or "").strip() or "(not provided)"),
        "",
        "Expected",
        _mask_secrets((expected or "").strip() or "(not provided)"),
        "",
        "Actual",
        _mask_secrets((actual or "").strip() or "(not provided)"),
        "",
        "Environment",
        _mask_secrets((environment or "").strip() or "(not provided)"),
        "",
        "Replication steps",
    ]
    if steps:
        for index, step in enumerate(steps, start=1):
            blocks.append(f"{index}. {_mask_secrets(step)}")
    else:
        blocks.append("(not provided)")
    blocks.append("")
    blocks.append("Evidence")
    if evidence:
        for path in evidence:
            blocks.append(f"- {_mask_secrets(path)}")
    else:
        blocks.append("(none)")
    return "\n".join(blocks)


def _fields_from_run(run: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Playwright/desktop/suite run result into bug draft fields."""
    error = str(run.get("error") or "").strip()
    title = str(run.get("title") or "").strip()
    status = str(run.get("status") or "").strip() or "fail"
    level = str(run.get("security_level") or "").strip()
    plugin = str(run.get("plugin") or "").strip()
    url = str(run.get("url") or "").strip()
    symptom = error or title or f"Test run ended with status {status}"
    actual = error or f"Run status: {status}"
    if title:
        actual = f"{actual}\nPage title: {title}" if actual else f"Page title: {title}"
    env_bits = []
    if level:
        env_bits.append(f"Security level: {level}")
    if plugin:
        env_bits.append(f"Plugin: {plugin}")
    if url:
        env_bits.append(f"URL: {url}")
    env_bits.append(f"OS: {platform.platform()}")
    steps_out: list[str] = []
    raw_steps = run.get("steps")
    if isinstance(raw_steps, list) and raw_steps:
        for index, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue
            action = step.get("action") or "step"
            selector = step.get("selector") or ""
            step_status = step.get("status") or ""
            detail = f"{action}"
            if selector:
                detail += f" ({selector})"
            if step_status:
                detail += f" → {step_status}"
            steps_out.append(f"Run recorded step {index}: {detail}")
            if str(step_status).casefold() in {"fail", "failed", "error"}:
                break
    else:
        steps_out = [
            "Reproduce the failing scenario in the application under test.",
            "Observe the failure matching Actual below.",
        ]
    evidence: list[str] = []
    shot = str(run.get("screenshot") or "").strip()
    if shot:
        evidence.append(shot)
    for item in run.get("evidence") or []:
        if isinstance(item, dict):
            path = str(item.get("path") or "").strip()
            if path and path not in evidence:
                evidence.append(path)
        elif isinstance(item, str) and item.strip() and item.strip() not in evidence:
            evidence.append(item.strip())
    classification = str(run.get("classification") or "").strip().casefold()
    return {
        "symptom": symptom,
        "expected": "The scenario passes with the asserted outcome.",
        "actual": actual,
        "environment": "; ".join(env_bits) if env_bits else "",
        "replication_steps": steps_out,
        "evidence_paths": evidence,
        "classification": classification or "product_bug",
        "summary": (symptom[:200] if symptom else "Product bug from failed test run"),
    }


def _load_run_from_report(report_path: str) -> Dict[str, Any]:
    root = _local_reports_dir()
    if root is None:
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    try:
        path = Path(report_path).expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    if path.suffix.lower() != ".json" or root not in path.parents:
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {"status": "error", "message": "report could not be read"}
    if not isinstance(payload, dict):
        return {"status": "error", "message": "report could not be read"}
    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    if not isinstance(result, dict):
        return {"status": "error", "message": "report could not be read"}
    return {"status": "ok", "run": result}


async def create_bug(
    project: Optional[str] = None,
    summary: Optional[str] = None,
    symptom: Optional[str] = None,
    expected: Optional[str] = None,
    actual: Optional[str] = None,
    environment: Optional[str] = None,
    replication_steps: Any = None,
    evidence_paths: Any = None,
    classification: Optional[str] = None,
    relates_to: Optional[str] = None,
    report_path: Optional[str] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """Propose a user-friendly Bug from a failed run. POST only after yes/confirm (FR-JIRA-4/5)."""
    draft: Dict[str, Any] = {
        "symptom": str(symptom or "").strip(),
        "expected": str(expected or "").strip(),
        "actual": str(actual or "").strip(),
        "environment": str(environment or "").strip(),
        "replication_steps": replication_steps,
        "evidence_paths": evidence_paths,
        "classification": str(classification or "").strip().casefold(),
        "summary": str(summary or "").strip(),
    }
    path = str(report_path or "").strip()
    if path:
        loaded = _load_run_from_report(path)
        if loaded.get("status") != "ok":
            return loaded
        from_run = _fields_from_run(loaded["run"])
        for key in (
            "symptom",
            "expected",
            "actual",
            "environment",
            "replication_steps",
            "evidence_paths",
            "classification",
            "summary",
        ):
            if not draft.get(key):
                draft[key] = from_run.get(key)

    class_name = str(draft.get("classification") or "").strip().casefold()
    if class_name and class_name != "product_bug":
        return {
            "status": "error",
            "message": (
                f"Refusing Bug ticket: classification is {class_name!r}. "
                "Only product_bug failures may be filed (FR-HEAL-4 / FR-JIRA-4)."
            ),
        }
    if not class_name:
        draft["classification"] = "product_bug"

    settings = load_settings()
    key = str(project or "").strip().upper() or str(settings.get("jira_project") or "").strip().upper()
    if not _LIST_KEY.fullmatch(key):
        return {
            "status": "error",
            "message": "project key required (argument or jira_project in settings), 1-10 characters A-Z/0-9",
        }

    steps = _as_lines(draft.get("replication_steps"))
    if not draft.get("symptom") and not draft.get("actual"):
        return {
            "status": "error",
            "message": "Provide symptom/actual, or a failed-run report_path under the local reports folder.",
        }
    if not steps:
        return {
            "status": "error",
            "message": "replication_steps are required (numbered steps a human can follow).",
        }

    summary_text = str(draft.get("summary") or "").strip()
    if not summary_text:
        summary_text = str(draft.get("symptom") or "Product bug from failed test run").strip()
    summary_text = _mask_secrets(summary_text)[:255]

    relates = ""
    raw_relates = str(relates_to or "").strip()
    if raw_relates:
        relates = _issue_key(raw_relates)
        if not relates:
            return {"status": "error", "message": "relates_to must look like KEY-123"}

    description = build_bug_description(
        symptom=str(draft.get("symptom") or ""),
        expected=str(draft.get("expected") or ""),
        actual=str(draft.get("actual") or ""),
        environment=str(draft.get("environment") or ""),
        replication_steps=steps,
        evidence_paths=draft.get("evidence_paths"),
    )
    if len(description) > 20000:
        return {"status": "error", "message": "bug description is too long"}

    preview = _valid_create(key, summary_text, description, "Bug")
    if preview.get("status"):
        return preview
    if relates:
        preview["relates_to"] = relates
    preview["classification"] = "product_bug"

    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}

    confirm_id = _store_pending(session_id, preview, "create_bug")
    shown = {
        "project": preview["project"],
        "summary": preview["summary"],
        "issue_type": "Bug",
        "classification": "product_bug",
        "description_preview": description[:500],
    }
    if relates:
        shown["relates_to"] = relates
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": shown}


def build_test_description(
    *,
    story_key: str,
    steps: Any = None,
    acceptance: Any = None,
    notes: str = "",
) -> str:
    """Structured test Task body (FR-JIRA-2 / JIRA_TICKET_TEMPLATE test Task)."""
    step_lines = _as_lines(steps)
    ac_lines = _as_lines(acceptance)
    blocks = [
        f"Intro — verifies story {story_key}",
        "",
        "Who this is for",
        "Testers and Cursor agents verifying the linked story.",
        "",
        "Test procedure",
    ]
    if step_lines:
        for index, step in enumerate(step_lines, start=1):
            blocks.append(f"{index}. {_mask_secrets(step)}")
    else:
        blocks.append("(not provided — add steps before marking Done)")
    blocks.append("")
    blocks.append("Acceptance criteria")
    if ac_lines:
        for line in ac_lines:
            blocks.append(f"- {_mask_secrets(line)}")
    else:
        blocks.append("- Cover the linked story acceptance criteria.")
    blocks.append("")
    blocks.append("Evidence")
    blocks.append("(pending until coverage is proven and update_status is confirmed)")
    note = _mask_secrets((notes or "").strip())
    if note:
        blocks.extend(["", "Notes", note])
    return "\n".join(blocks)


def _project_from_issue_key(issue_key: str) -> str:
    text = str(issue_key or "").strip().upper()
    if "-" not in text:
        return ""
    return text.split("-", 1)[0]


def _is_test_ticket(issue_type: str = "", labels: Any = None) -> bool:
    """True when issue is the KAN test type and/or labelled test (legacy)."""
    type_name = str(issue_type or "").strip().lower()
    label_list = labels if isinstance(labels, list) else []
    return type_name == TEST_ISSUE_TYPE.lower() or "test" in {
        str(item).lower() for item in label_list
    }


async def create_test(
    story_key: str,
    summary: Optional[str] = None,
    steps: Any = None,
    acceptance: Any = None,
    notes: Optional[str] = None,
    project: Optional[str] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """Propose a linked test issue (type=test, Relates). POST only after yes/confirm (FR-JIRA-2/5)."""
    story = _issue_key(story_key)
    if not story:
        return {"status": "error", "message": "story_key must look like KEY-123"}

    settings = load_settings()
    key = (
        str(project or "").strip().upper()
        or _project_from_issue_key(story)
        or str(settings.get("jira_project") or "").strip().upper()
    )
    if not _LIST_KEY.fullmatch(key):
        return {
            "status": "error",
            "message": "project key required (argument, story prefix, or jira_project in settings)",
        }

    step_lines = _as_lines(steps)
    ac_lines = _as_lines(acceptance)
    if not step_lines and not ac_lines:
        return {
            "status": "error",
            "message": "Provide steps and/or acceptance criteria for the test ticket.",
        }

    summary_text = _mask_secrets(str(summary or "").strip())
    if not summary_text:
        summary_text = f"Test: cover {story}"
    summary_text = summary_text[:255]

    description = build_test_description(
        story_key=story,
        steps=step_lines,
        acceptance=ac_lines,
        notes=str(notes or ""),
    )
    if len(description) > 20000:
        return {"status": "error", "message": "test description is too long"}

    preview = _valid_create(key, summary_text, description, TEST_ISSUE_TYPE)
    if preview.get("status"):
        return preview
    preview["labels"] = ["test"]
    preview["relates_to"] = story

    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}

    confirm_id = _store_pending(session_id, preview, "create_test")
    shown = {
        "project": preview["project"],
        "summary": preview["summary"],
        "issue_type": TEST_ISSUE_TYPE,
        "labels": ["test"],
        "relates_to": story,
        "description_preview": description[:500],
    }
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": shown}


async def _read_error(response: Any) -> Optional[Dict[str, Any]]:
    if response.status_code in (401, 403):
        return _auth_error(response.status_code)
    if response.status_code == 429:
        return _rate_limited_error(response)
    if response.status_code == 404:
        return {"status": "error", "message": "epic not found"}
    if response.status_code >= 400:
        return {"status": "error", "message": "jira_request_failed"}
    return None


async def _get_issue_type(key: str) -> Dict[str, Any]:
    """GET one issue type. The result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{key}",
                params={"fields": "issuetype"},
                auth=auth,
                headers=headers,
            )
        failed = await _read_error(response)
        if failed:
            return failed
        fields = (response.json().get("fields") or {})
        kind = fields.get("issuetype") or {}
        name = kind.get("name", "") if isinstance(kind, dict) else ""
    except (httpx.HTTPError, ValueError):
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "ok", "type": name}


async def _put_parent(preview: Dict[str, str]) -> Dict[str, Any]:
    """PUT fields.parent only. The result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "PUT",
                f"{creds['url']}/rest/api/3/issue/{preview['issue_key']}",
                json={"fields": {"parent": {"key": preview["epic_key"]}}},
                auth=auth,
                headers=headers,
            )
        failed = await _read_error(response)
        if failed:
            return failed
    except httpx.HTTPError:
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "linked", "issue_key": preview["issue_key"], "epic_key": preview["epic_key"]}


async def set_parent(issue_key: str, epic_key: str, session_id: str = "default") -> Dict[str, Any]:
    """Preview a parent link. PUT happens only after the user's own confirmation."""
    issue = _issue_key(issue_key)
    epic = _issue_key(epic_key)
    if not issue or not epic:
        return {"status": "error", "message": "issue and epic keys must look like KEY-123"}
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    looked = await _get_issue_type(epic)
    if looked.get("status") != "ok":
        return looked
    if str(looked.get("type") or "").casefold() != "epic":
        return {"status": "error", "message": "parent is not an Epic"}
    preview = {"issue_key": issue, "epic_key": epic}
    confirm_id = _store_pending(session_id, preview, "set_parent")
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": preview}


def _status_failure(response: Any, missing: str) -> Optional[Dict[str, Any]]:
    if response.status_code in (401, 403):
        return _auth_error(response.status_code)
    if response.status_code == 429:
        return _rate_limited_error(response)
    if response.status_code == 404:
        return {"status": "error", "message": missing}
    if response.status_code >= 400:
        return {"status": "error", "message": "jira_request_failed"}
    return None


def _option_names(transitions: Any) -> list:
    names = []
    for item in transitions or []:
        if not isinstance(item, dict):
            continue
        to = item.get("to") or {}
        label = to.get("name") if isinstance(to, dict) else ""
        if not label:
            label = item.get("name") or ""
        if label and label not in names:
            names.append(label)
    return names


def _pick_transition(transitions: Any, target: str) -> Optional[Dict[str, Any]]:
    wanted = target.casefold()
    status_hits = []
    name_hits = []
    for item in transitions or []:
        if not isinstance(item, dict) or item.get("id") in (None, ""):
            continue
        to = item.get("to") or {}
        to_name = to.get("name", "") if isinstance(to, dict) else ""
        if str(to_name).casefold() == wanted:
            status_hits.append(item)
        elif str(item.get("name") or "").casefold() == wanted:
            name_hits.append(item)
    hits = status_hits or name_hits
    if len(hits) != 1:
        return None
    return hits[0]


async def _load_transition(key: str) -> Dict[str, Any]:
    """GET the current status and transitions. The result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            issue = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{key}",
                params={"fields": "status"},
                auth=auth,
                headers=headers,
            )
            failed = _status_failure(issue, "issue not found")
            if failed:
                return failed
            fields = issue.json().get("fields") or {}
            status = fields.get("status") or {}
            current = status.get("name", "") if isinstance(status, dict) else ""
            listed = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{key}/transitions",
                auth=auth,
                headers=headers,
            )
            failed = _status_failure(listed, "issue not found")
            if failed:
                return failed
            transitions = listed.json().get("transitions") or []
    except (httpx.HTTPError, ValueError):
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "ok", "current_status": current, "transitions": transitions}


async def _post_transition(preview: Dict[str, str]) -> Dict[str, Any]:
    """POST one transition after checking it is still available."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            listed = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{preview['issue_key']}/transitions",
                auth=auth,
                headers=headers,
            )
            failed = _status_failure(listed, "issue not found")
            if failed:
                return failed
            transitions = listed.json().get("transitions") or []
            still = [
                item for item in transitions
                if isinstance(item, dict) and str(item.get("id")) == str(preview.get("transition_id"))
            ]
            if len(still) != 1:
                return {
                    "status": "error",
                    "message": "transition is no longer available",
                    "options": _option_names(transitions),
                }
            response = await _request(
                client,
                "POST",
                f"{creds['url']}/rest/api/3/issue/{preview['issue_key']}/transitions",
                json={"transition": {"id": str(preview["transition_id"])}},
                auth=auth,
                headers=headers,
            )
            failed = _status_failure(response, "issue not found")
            if failed:
                return failed
    except (httpx.HTTPError, ValueError):
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "transitioned", "issue_key": preview["issue_key"], "target": preview["target"]}


async def transition_issue(issue_key: str, target: str, session_id: str = "default") -> Dict[str, Any]:
    """Preview a status change. POST happens only after the user's own confirmation."""
    issue = _issue_key(issue_key)
    if not issue:
        return {"status": "error", "message": "issue key must look like KEY-123"}
    wanted = str(target or "").strip()
    if not wanted:
        return {"status": "error", "message": "target status is required"}
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    loaded = await _load_transition(issue)
    if loaded.get("status") != "ok":
        return loaded
    match = _pick_transition(loaded["transitions"], wanted)
    if not match:
        return {
            "status": "error",
            "message": "no matching transition",
            "options": _option_names(loaded["transitions"]),
        }
    to = match.get("to") or {}
    label = to.get("name") if isinstance(to, dict) and to.get("name") else (match.get("name") or wanted)
    stored = {
        "issue_key": issue,
        "current_status": loaded["current_status"],
        "target": label,
        "transition_id": str(match.get("id")),
    }
    confirm_id = _store_pending(session_id, stored, "transition")
    shown = {key: stored[key] for key in ("issue_key", "current_status", "target")}
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": shown}


async def _load_issue_labels(key: str) -> Dict[str, Any]:
    """GET labels + status for one issue. Result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "GET",
                f"{creds['url']}/rest/api/3/issue/{key}",
                params={"fields": "labels,status,issuetype,summary"},
                auth=auth,
                headers=headers,
            )
        failed = _status_failure(response, "issue not found")
        if failed:
            return failed
        fields = response.json().get("fields") or {}
        labels = fields.get("labels") or []
        if not isinstance(labels, list):
            labels = []
        status = fields.get("status") or {}
        current = status.get("name", "") if isinstance(status, dict) else ""
        kind = fields.get("issuetype") or {}
        type_name = kind.get("name", "") if isinstance(kind, dict) else ""
        summary = str(fields.get("summary") or "")
    except (httpx.HTTPError, ValueError):
        return {"status": "error", "message": "jira_request_failed"}
    return {
        "status": "ok",
        "labels": [str(item) for item in labels],
        "current_status": current,
        "issue_type": type_name,
        "summary": summary,
    }


async def _post_update_status(preview: Dict[str, Any]) -> Dict[str, Any]:
    """Optional coverage comment, then transition to Done. Never echoes credentials."""
    body = str(preview.get("coverage_comment") or "").strip()
    if body:
        commented = await _post_comment({"issue_key": preview["issue_key"], "body": body})
        if commented.get("status") != "commented":
            return commented
    transitioned = await _post_transition(
        {
            "issue_key": preview["issue_key"],
            "target": preview["target"],
            "transition_id": preview["transition_id"],
        }
    )
    if transitioned.get("status") != "transitioned":
        return transitioned
    return {
        "status": "updated",
        "issue_key": preview["issue_key"],
        "target": preview["target"],
        "commented": bool(body),
    }


async def update_status(
    issue_key: str,
    coverage_evidence: Optional[str] = None,
    report_path: Optional[str] = None,
    pytest_cmd: Optional[str] = None,
    target: str = "Done",
    session_id: str = "default",
) -> Dict[str, Any]:
    """Propose marking a test ticket Done when coverage exists. POST only after yes/confirm (FR-JIRA-3/5)."""
    issue = _issue_key(issue_key)
    if not issue:
        return {"status": "error", "message": "issue_key must look like KEY-123"}

    wanted = str(target or "").strip() or "Done"
    evidence_bits: list[str] = []
    raw_evidence = str(coverage_evidence or "").strip()
    if raw_evidence:
        evidence_bits.append(_mask_secrets(raw_evidence))
    cmd = str(pytest_cmd or "").strip()
    if cmd:
        evidence_bits.append(f"Pytest: {_mask_secrets(cmd)}")
    path = str(report_path or "").strip()
    if path:
        summary = _report_summary(path)
        if isinstance(summary, dict):
            return summary
        evidence_bits.append(_mask_secrets(str(summary)))
    if not evidence_bits:
        return {
            "status": "error",
            "message": "coverage_evidence, pytest_cmd, or a local report_path is required before marking Done.",
        }

    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}

    looked = await _load_issue_labels(issue)
    if looked.get("status") != "ok":
        return looked
    labels = looked.get("labels") or []
    issue_type = str(looked.get("issue_type") or "")
    if not _is_test_ticket(issue_type, labels):
        return {
            "status": "error",
            "message": (
                f"{issue} is not a test ticket (issuetype '{TEST_ISSUE_TYPE}' or label=test). "
                "update_status only marks linked test tickets Done (FR-JIRA-3)."
            ),
        }

    loaded = await _load_transition(issue)
    if loaded.get("status") != "ok":
        return loaded
    match = _pick_transition(loaded["transitions"], wanted)
    if not match:
        return {
            "status": "error",
            "message": "no matching transition",
            "options": _option_names(loaded["transitions"]),
        }
    to = match.get("to") or {}
    label = to.get("name") if isinstance(to, dict) and to.get("name") else (match.get("name") or wanted)

    coverage_comment = "Coverage evidence\n\n" + "\n".join(f"- {bit}" for bit in evidence_bits)
    if len(coverage_comment) > 5000:
        return {"status": "error", "message": "coverage evidence is too long for a Jira comment"}

    stored = {
        "issue_key": issue,
        "current_status": loaded["current_status"],
        "target": label,
        "transition_id": str(match.get("id")),
        "coverage_comment": coverage_comment,
        "labels": labels,
    }
    confirm_id = _store_pending(session_id, stored, "update_status")
    shown = {
        "issue_key": issue,
        "current_status": loaded["current_status"],
        "target": label,
        "labels": labels,
        "coverage_preview": coverage_comment[:400],
    }
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": shown}


def _adf_comment(text: str) -> Dict[str, Any]:
    """Turn plain text into ADF paragraphs. Blank lines stay blank paragraphs."""
    paragraphs = []
    for line in text.splitlines() or [text]:
        if line:
            paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": line}]})
        else:
            paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": " "}]})
    return {"type": "doc", "version": 1, "content": paragraphs}


def _local_reports_dir() -> Optional[Path]:
    base = os.getenv("LOCALAPPDATA")
    if not base or not str(base).strip():
        return None
    return (Path(base) / "ai_testing_app" / "reports").resolve()


def _report_summary(report_path: str) -> Any:
    """Overall status and step lines from a report JSON inside the local reports folder."""
    root = _local_reports_dir()
    if root is None:
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    try:
        path = Path(report_path).expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    if path.suffix.lower() != ".json" or root not in path.parents:
        return {"status": "error", "message": "report path must be inside the local reports folder"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {"status": "error", "message": "report could not be read"}
    if not isinstance(payload, dict):
        return {"status": "error", "message": "report could not be read"}
    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    if not isinstance(result, dict):
        return {"status": "error", "message": "report could not be read"}
    lines = [f"Report overall: {result.get('status') or 'unknown'}"]
    steps = result.get("steps") or []
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            lines.append(f"- {step.get('action') or ''}: {step.get('status') or ''}")
    return "\n".join(lines)


async def _post_comment(preview: Dict[str, str]) -> Dict[str, Any]:
    """POST one comment. The result never includes credentials."""
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    headers, auth = _auth(creds)
    try:
        async with _async_client() as client:
            response = await _request(
                client,
                "POST",
                f"{creds['url']}/rest/api/3/issue/{preview['issue_key']}/comment",
                json={"body": _adf_comment(preview["body"])},
                auth=auth,
                headers=headers,
            )
        failed = _status_failure(response, "issue not found")
        if failed:
            return failed
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return {"status": "error", "message": "jira_request_failed"}
    return {
        "status": "commented",
        "issue_key": preview["issue_key"],
        "comment_id": str(data.get("id") or ""),
    }


async def add_comment(
    issue_key: str,
    body: str,
    report_path: Optional[str] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """Preview a comment. POST happens only after the user's own confirmation."""
    issue = _issue_key(issue_key)
    if not issue:
        return {"status": "error", "message": "issue key must look like KEY-123"}
    text = str(body or "").strip()
    if not text:
        return {"status": "error", "message": "comment body is required"}
    if len(text) > 5000:
        return {"status": "error", "message": "comment body must be 5000 characters or less"}
    path = str(report_path or "").strip()
    if path:
        summary = _report_summary(path)
        if isinstance(summary, dict):
            return summary
        text = text + "\n\n" + summary
        if len(text) > 5000:
            return {"status": "error", "message": "comment body must be 5000 characters or less"}
    creds = _list_creds()
    if not creds["url"] or not creds["token"]:
        return _unconfigured()
    if not _url_ok(creds["url"]):
        return {"status": "error", "message": "jira_url must start with https://"}
    stored = {"issue_key": issue, "body": text}
    confirm_id = _store_pending(session_id, stored, "comment")
    shown = {"issue_key": issue, "body": text[:300]}
    return {"status": "confirmation_required", "confirm_id": confirm_id, "preview": shown}
