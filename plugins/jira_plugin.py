"""Jira tools. list_stories is read-only. create_issue POSTs only after the user's own confirmation."""
import os
import re
import time
import uuid
from typing import Any, Dict, Optional

import httpx

from settings.store import load_settings

_PROJECT = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,10}")
_LIST_KEY = re.compile(r"[A-Z0-9]{1,10}")
_ISSUE_KEY = re.compile(r"[A-Z][A-Z0-9]{0,9}-\d+")
_TYPE_JQL = {
    "story": "Story",
    "task": "Task",
    "bug": "Bug",
    "epic": "Epic",
    "subtask": "Sub-task",
    "sub-task": "Sub-task",
}
_ISSUE_TYPE = re.compile(r"[A-Za-z][A-Za-z0-9 ]{0,39}")
_WRITE = {"create_test", "update_status", "create_bug"}
_CONFIRM_WORDS = {"yes", "confirm"}
_PENDING: Dict[str, Dict[str, Any]] = {}
_CONFIRM_TTL = 300.0

def _creds() -> Dict[str, str]:
    settings = load_settings()
    return {
        "url": (settings.get("jira_url") or "").rstrip("/"),
        "email": settings.get("jira_email") or "",
        "token": settings.get("jira_api_token") or "",
    }

def _url_ok(url: str) -> bool:
    return url.startswith("https://") or url.startswith("http://127.0.0.1") or url.startswith("http://localhost")

def _stories(payload: Dict[str, Any], project: str) -> Dict[str, Any]:
    stories = []
    for issue in payload.get("issues") or []:
        fields = issue.get("fields") or {}
        status = fields.get("status") or {}
        kind = fields.get("issuetype") or {}
        stories.append({
            "key": issue.get("key", ""),
            "summary": fields.get("summary", ""),
            "status": status.get("name", "") if isinstance(status, dict) else "",
            "type": kind.get("name", "") if isinstance(kind, dict) else "",
        })
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

    async with httpx.AsyncClient(timeout=20.0) as client:
        last_status = 0
        for endpoint, auth, headers in attempts:
            response = await client.get(
                endpoint,
                params=params,
                auth=auth,
                headers={"Accept": "application/json", **headers},
            )
            last_status = response.status_code
            if response.status_code == 404:
                continue
            if response.status_code in (401, 403):
                return {"error": "jira_unauthorized", "status": response.status_code}
            response.raise_for_status()
            return _stories(response.json(), project)
    return {"error": "jira_search_unavailable", "status": last_status}

async def jira_action(
    action: str,
    project: Optional[str] = None,
    summary: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    if action in _WRITE:
        return {
            "status": "confirmation_required",
            "action": action,
            "note": "Jira writes are not enabled. list_stories is read-only.",
        }
    if action != "list_stories":
        return {"error": "Unknown action"}
    if not project or not _PROJECT.fullmatch(project):
        return {"error": "project key required, for example PROJ"}
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
        return await _search(creds["url"], creds["email"], creds["token"], project)
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


async def _list_search(url: str, email: str, token: str, project: str, limit: int, clause: str) -> Dict[str, Any]:
    """GET the search API. The result never includes credentials."""
    params = {
        "jql": f"project = {project}{clause} ORDER BY key DESC",
        "maxResults": limit,
        "fields": "summary,status,issuetype",
    }
    if email:
        attempts = [
            (f"{url}/rest/api/3/search/jql", (email, token), {}),
            (f"{url}/rest/api/2/search", (email, token), {}),
        ]
    else:
        attempts = [(f"{url}/rest/api/2/search", None, {"Authorization": f"Bearer {token}"})]

    async with httpx.AsyncClient(timeout=20.0) as client:
        for endpoint, auth, headers in attempts:
            response = await client.get(
                endpoint,
                params=params,
                auth=auth,
                headers={"Accept": "application/json", **headers},
            )
            if response.status_code == 404:
                continue
            if response.status_code in (401, 403):
                return {"status": "unauthorized", "message": "Jira rejected the credentials"}
            response.raise_for_status()
            payload = response.json()
            stories = _stories(payload, project)["stories"]
            result = {"status": "ok", "stories": stories}
            try:
                total = int(payload.get("total"))
            except (TypeError, ValueError):
                total = None
            if total is not None and total > len(stories):
                result["note"] = f"showing {len(stories)} of {total}"
            return result
    return {"status": "error", "message": "jira_search_unavailable"}


async def list_stories(project: str, max: int = 50, issue_types: Any = None) -> Dict[str, Any]:
    """Read-only issue list. GET only. Missing URL or token returns unconfigured."""
    key = str(project or "").strip().upper()
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
        return await _list_search(creds["url"], creds["email"], creds["token"], key, _clamp_max(max), clause)
    except httpx.HTTPError:
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
        fields["description"] = _adf(preview["description"])
    if preview.get("parent_key"):
        fields["parent"] = {"key": preview["parent_key"]}
    headers, auth = _auth(creds)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{creds['url']}/rest/api/3/issue",
                json={"fields": fields},
                auth=auth,
                headers=headers,
            )
        if response.status_code in (401, 403):
            return {"status": "unauthorized", "message": "Jira rejected the credentials"}
        if response.status_code >= 400:
            return {"status": "error", "message": "jira_request_failed"}
        try:
            data = response.json()
        except ValueError:
            return {"status": "error", "message": "jira_request_failed"}
    except httpx.HTTPError:
        return {"status": "error", "message": "jira_request_failed"}
    return {"status": "created", "key": data.get("key") or ""}


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
    if record.get("action") == "set_parent":
        return await _put_parent(record["preview"])
    return await _post_issue(record["preview"])


async def _read_error(response: Any) -> Optional[Dict[str, str]]:
    if response.status_code in (401, 403):
        return {"status": "unauthorized", "message": "Jira rejected the credentials"}
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
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
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
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
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
