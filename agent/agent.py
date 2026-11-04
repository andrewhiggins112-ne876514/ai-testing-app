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
- Always clarify ambiguous requests before acting (e.g. "create new strategy or use existing Jira tests?").
- Never update credentials, create Jira tickets, or run destructive actions without explicit confirmation.
- Prefer structured tool calls over guessing.
- Report results clearly, including failures and suggested next steps.
- Security context is important: respect the current level (OFFICIAL / SECRET).
- For a browse request, call run_playwright with steps, a list of {action, selector?, value?}; action is goto, click, fill, expect_text, or expect_url, and click a visible label with selector text=Label.
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
        history = self.histories.setdefault(
            session_id, [{"role": "system", "content": SYSTEM_PROMPT}]
        )
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
        if name not in {"jira_action", "run_playwright", "update_settings"}:
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
        elif name == "update_settings":
            from settings.store import update_setting
            allowed = {"key", "value", "confirm"}
            return update_setting(**{k: v for k, v in args.items() if k in allowed})
        return {"error": "Unknown tool"}
