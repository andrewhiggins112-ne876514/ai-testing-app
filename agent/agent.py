"""
Core agent loop.
Uses Ollama for local tool-calling.
Forces clarification on ambiguous or side-effecting requests.
"""
import json
import os
from typing import Any, Dict, List, Optional
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")  # installed locally; qwen3:8b also fine

SYSTEM_PROMPT = """You are a local AI testing agent (Jarvis-style).
You help testers by reasoning about requests and calling tools.

Rules:
- Always clarify ambiguous requests before acting (e.g. "use the new strategy or the existing one?"). A Jira request that names a project key and a summary is not ambiguous.
- Never update credentials, create Jira tickets, or run destructive actions without explicit confirmation.
- Prefer structured tool calls over guessing.
- Report results clearly, including failures and suggested next steps.
- Security context is important: respect the current level (OFFICIAL / SECRET).
- For a browse request, call run_playwright with steps, a list of {action, selector?, value?}; action is goto, click, fill, expect_text, or expect_url, and click a visible label with selector text=Label.
- When the user asks to list Jira issues or stories, call list_stories with the project key and do not invent issues. Set issue_types only when the user names types. "list issues in KAN" omits issue_types.
- When the user asks to create a Jira issue and names a project key and summary, call create_issue immediately with those values. Do not clarify and do not answer yes for the user. Wait for the user to reply yes or confirm.
- To link a Jira issue to an epic, call set_parent with the issue key and epic key, then wait for the user to reply yes. Do not answer yes for the user.
- To change a Jira issue's status, call transition_issue with the issue key and target status, then wait for the user to reply yes. Do not answer yes for the user.
- To comment on a Jira issue, call add_comment with the issue key and body, then wait for the user to reply yes. Do not answer yes for the user. Pass report_path only when the user names a report file.
"""

class Agent:
    def __init__(self):
        self.tools = self._register_tools()
        self.histories: Dict[str, List[Dict]] = {}

    def _cap(self, hist: List[Dict]) -> None:
        if len(hist) > 50:
            del hist[:-50]

    def _register_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_playwright",
                    "description": "Run Playwright steps against a page. Returns status, title, screenshot, error, and per-step pass/fail.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target URL"},
                            "mode": {"type": "string", "enum": ["generate", "existing"], "description": "Generate new or run existing"},
                            "steps": {
                                "type": "array",
                                "description": "Ordered steps. Example: [{\"action\":\"goto\",\"value\":\"https://example.com\"},{\"action\":\"click\",\"selector\":\"text=More information\"},{\"action\":\"expect_url\",\"value\":\"iana\"}]. goto and expect_* need value. click needs selector. fill needs selector and value.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "action": {"type": "string", "enum": ["goto", "click", "fill", "expect_text", "expect_url"]},
                                        "selector": {"type": "string"},
                                        "value": {"type": "string"}
                                    },
                                    "required": ["action"]
                                }
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "jira_action",
                    "description": "Read-only Jira. Lists stories for one project key. Requires jira_url and jira_api_token in local settings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["list_stories"]},
                            "project": {"type": "string", "description": "Jira project key, for example PROJ"}
                        },
                        "required": ["action", "project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_stories",
                    "description": "Read-only GET. List Jira issues for one project key. Returns key, summary, status, and type. Omit issue_types to list every type.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "Jira project key: 1-10 characters, A-Z and 0-9"},
                            "max": {"type": "integer", "description": "Maximum issues to return. Default 50, capped at 100."},
                            "issue_types": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["Story", "Task", "Bug", "Epic", "Subtask"]},
                                "description": "Optional. Omit to list every issue type."
                            }
                        },
                        "required": ["project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_issue",
                    "description": "Call this immediately when the user names a Jira project key and an issue summary. Returns a preview only. Does not create the issue. The user must reply yes or confirm.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "Jira project key: 1-10 characters, A-Z and 0-9"},
                            "summary": {"type": "string", "description": "Issue summary, 255 characters or less"},
                            "description": {"type": "string", "description": "Optional issue description"},
                            "issue_type": {"type": "string", "description": "Issue type name. Default Task."},
                            "parent_key": {"type": "string", "description": "Optional parent issue key, like KAN-5."}
                        },
                        "required": ["project", "summary"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_parent",
                    "description": "Preview linking a Jira issue to an epic. Does not change Jira until the user replies yes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_key": {"type": "string", "description": "Issue to link, like KAN-2"},
                            "epic_key": {"type": "string", "description": "Epic key, like KAN-5"}
                        },
                        "required": ["issue_key", "epic_key"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transition_issue",
                    "description": "Preview a Jira status change. Does not change Jira until the user replies yes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_key": {"type": "string", "description": "Issue key, like KAN-4"},
                            "target": {"type": "string", "description": "Target status name, like In Progress"}
                        },
                        "required": ["issue_key", "target"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_comment",
                    "description": "Preview a Jira comment. Does not post until the user replies yes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_key": {"type": "string", "description": "Issue key, like KAN-4"},
                            "body": {"type": "string", "description": "Plain-text comment, 5000 characters or less"},
                            "report_path": {"type": "string", "description": "Optional report JSON inside the local reports folder"}
                        },
                        "required": ["issue_key", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_settings",
                    "description": "Propose or apply settings changes (credentials, URLs, security level). Always confirm first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                            "confirm": {"type": "boolean"}
                        },
                        "required": ["key", "value"]
                    }
                }
            }
        ]

    async def chat(self, user_message: str, session_id: str = "default") -> str:
        from plugins.jira_plugin import resolve_create
        history = self.histories.setdefault(
            session_id, [{"role": "system", "content": SYSTEM_PROMPT}]
        )
        outcome = await resolve_create(session_id, user_message)
        if outcome is not None and outcome.get("status") != "cancelled":
            reply = _create_reply(outcome)
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": reply})
            self._cap(history)
            return reply
        history.append({"role": "user", "content": user_message})
        self._cap(history)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": history,
                    "tools": self.tools,
                    "stream": False
                }
            )
            data = resp.json()
            message = data.get("message", {})
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                parsed = self._tool_from_text(message.get("content") or "")
                if parsed:
                    tool_calls = [{"function": parsed}]
                    message = {**message, "tool_calls": tool_calls}
            history.append(message)

            # Handle tool calls
            if tool_calls:
                tool_results = []
                for call in tool_calls:
                    result = await self._execute_tool(call, user_message, session_id)
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": call.get("id", "call_1")
                    })
                history.extend(tool_results)
                self._cap(history)

                # Second call to get final response
                resp2 = await client.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": MODEL,
                        "messages": history,
                        "stream": False
                    }
                )
                final = resp2.json().get("message", {}).get("content", "Done.")
                history.append({"role": "assistant", "content": final})
                self._cap(history)
                return final

            self._cap(history)
            return message.get("content", "No response.")

    def _tool_from_text(self, content: str):
        text = content.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        name = data.get("name") if isinstance(data, dict) else None
        if name not in {"jira_action", "run_playwright", "update_settings", "list_stories", "create_issue", "set_parent", "transition_issue", "add_comment"}:
            return None
        return {"name": name, "arguments": data.get("arguments") or {}}

    def _parse_call(self, call: Dict):
        function = call.get("function") or {}
        raw = function.get("arguments") or {}
        if isinstance(raw, str):
            raw = json.loads(raw) if raw.strip() else {}
        if not isinstance(raw, dict):
            raw = {}
        return function.get("name"), raw

    async def _execute_tool(self, call: Dict, request_text: str = "", session_id: str = "default") -> Dict:
        name, args = self._parse_call(call)

        if name == "run_playwright":
            from plugins.playwright_runner import run_playwright
            allowed = {"url", "mode", "steps", "security_level"}
            kwargs = {k: v for k, v in args.items() if k in allowed}
            kwargs["request_text"] = request_text
            kwargs["session_id"] = session_id
            return await run_playwright(**kwargs)
        elif name == "jira_action":
            from plugins.jira_plugin import jira_action
            allowed = {"action", "project", "summary", "status"}
            return await jira_action(**{k: v for k, v in args.items() if k in allowed})
        elif name == "list_stories":
            from plugins.jira_plugin import list_stories
            allowed = {"project", "max", "issue_types"}
            return await list_stories(**{k: v for k, v in args.items() if k in allowed})
        elif name == "create_issue":
            from plugins.jira_plugin import create_issue
            allowed = {"project", "summary", "description", "issue_type", "parent_key"}
            kwargs = {k: v for k, v in args.items() if k in allowed}
            kwargs["session_id"] = session_id
            return await create_issue(**kwargs)
        elif name == "set_parent":
            from plugins.jira_plugin import set_parent
            allowed = {"issue_key", "epic_key"}
            kwargs = {k: v for k, v in args.items() if k in allowed}
            kwargs["session_id"] = session_id
            return await set_parent(**kwargs)
        elif name == "transition_issue":
            from plugins.jira_plugin import transition_issue
            allowed = {"issue_key", "target"}
            kwargs = {k: v for k, v in args.items() if k in allowed}
            kwargs["session_id"] = session_id
            return await transition_issue(**kwargs)
        elif name == "add_comment":
            from plugins.jira_plugin import add_comment
            allowed = {"issue_key", "body", "report_path"}
            kwargs = {k: v for k, v in args.items() if k in allowed}
            kwargs["session_id"] = session_id
            return await add_comment(**kwargs)
        elif name == "update_settings":
            from settings.store import update_setting
            allowed = {"key", "value", "confirm"}
            return update_setting(**{k: v for k, v in args.items() if k in allowed})
        return {"error": "Unknown tool"}


def _create_reply(result: Dict) -> str:
    status = result.get("status")
    if status == "created":
        return f"Created {result.get('key') or 'the issue'}."
    if status == "linked":
        return f"Linked {result.get('issue_key')} to epic {result.get('epic_key')}."
    if status == "transitioned":
        return f"Moved {result.get('issue_key')} to {result.get('target')}."
    if status == "commented":
        return f"Comment {result.get('comment_id')} on {result.get('issue_key')}."
    if status == "expired":
        return "That confirmation expired. Ask again to create the issue."
    if status == "unconfigured":
        return result.get("message") or "Jira is not configured."
    if status == "unauthorized":
        return result.get("message") or "Jira rejected the credentials."
    return result.get("message") or "Jira did not create the issue."
