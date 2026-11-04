import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

"""
FastAPI entry point.
Run with: py -3 -m uvicorn main:app --reload
"""
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import Agent
from settings.store import load_settings, settings_path

app = FastAPI(title="AI Testing Agent")
agent = Agent()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        reply = await agent.chat(req.message, req.session_id)
    except httpx.HTTPError:
        reply = "Ollama is not reachable. Start Ollama and check that the model is pulled."
    return {"reply": reply}

@app.get("/health")
async def health():
    settings = load_settings()
    configured = bool(settings.get("jira_url") and settings.get("jira_api_token"))
    return {
        "status": "ok",
        "model": "local-ollama",
        "jira_configured": configured,
        "settings_path": str(settings_path()),
    }
