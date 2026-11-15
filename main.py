import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

"""
FastAPI entry point.
Run with: py -3 -m uvicorn main:app --reload
"""
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from agent.agent import Agent
from plugins.desktop_runner import (
    plugin_status as desktop_plugin_status,
    run_desktop,
    set_plugin_enabled as set_desktop_plugin_enabled,
)
from plugins.doc_ingest import apply_proposal, decline_proposal, ingest_document
from plugins.multi_sandbox import (
    orchestrate as multi_sandbox_orchestrate,
    plugin_status as multi_sandbox_plugin_status,
    set_plugin_enabled as set_multi_sandbox_plugin_enabled,
)
from plugins.playwright_suite import (
    discover_suite,
    list_suite_tests,
    run_suite as run_playwright_suite,
    set_suite_path,
    suite_status as playwright_suite_status,
)
from plugins.registry import list_plugins
from reports.sections import load_report_sections, normalize_sections, save_report_sections
from settings.store import (
    load_settings,
    security_status,
    set_security_level,
    settings_path,
    update_setting,
)

_UI_DIR = Path(__file__).resolve().parent / "ui"

app = FastAPI(title="AI Testing Agent")
agent = Agent()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class OrbConfigRequest(BaseModel):
    style: str = "mystic"
    calm_color: str = "#50cdff"
    thinking_color: str = "#b388ff"
    size: int = Field(default=360, ge=200, le=480)
    shape: str = "sphere"
    spin_speed: float = 1.0
    turbulence: float = 1.0
    pulse: float = 1.0
    glow: float = 1.0


class ReportSectionsRequest(BaseModel):
    summary: bool = True
    stories: bool = True
    bugs: bool = True
    evidence: bool = True


class DocIngestRequest(BaseModel):
    text: str = ""
    path: str = ""
    filename: str = ""
    session_id: str = "desktop"


class DocIngestApplyRequest(BaseModel):
    proposal_id: str
    keys: list[str] | None = None
    confirm: bool = False
    session_id: str = "desktop"


class DocIngestDeclineRequest(BaseModel):
    proposal_id: str
    session_id: str = "desktop"


class SecurityLevelRequest(BaseModel):
    security_level: str
    confirm: bool = False


class DesktopPluginRequest(BaseModel):
    plugin_desktop_enabled: bool = True


class DesktopSmokeRequest(BaseModel):
    exe_path: str = ""
    timeout_s: float = 1.5


class MultiSandboxPluginRequest(BaseModel):
    plugin_multi_sandbox_enabled: bool = False


class MultiSandboxOrchestrateRequest(BaseModel):
    action: str = "list"


class PlaywrightSuitePathRequest(BaseModel):
    suite_path: str = ""
    confirm: bool = True


class PlaywrightSuiteRunRequest(BaseModel):
    suite_path: str = ""
    grep: str = ""
    timeout_s: float = 300.0


def _orb_from_settings() -> dict:
    s = load_settings()
    return {
        "style": s.get("orb_style") or "mystic",
        "calm_color": s.get("orb_calm_color") or "#50cdff",
        "thinking_color": s.get("orb_thinking_color") or "#b388ff",
        "size": int(s.get("orb_size") or 360),
        "shape": s.get("orb_shape") or "sphere",
        "spin_speed": float(s.get("orb_spin_speed") if s.get("orb_spin_speed") is not None else 1.0),
        "turbulence": float(s.get("orb_turbulence") if s.get("orb_turbulence") is not None else 1.0),
        "pulse": float(s.get("orb_pulse") if s.get("orb_pulse") is not None else 1.0),
        "glow": float(s.get("orb_glow") if s.get("orb_glow") is not None else 1.0),
    }

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


@app.get("/api/orb")
async def get_orb():
    return _orb_from_settings()


@app.post("/api/orb")
async def set_orb(req: OrbConfigRequest):
    update_setting("orb_style", req.style, confirm=True)
    update_setting("orb_calm_color", req.calm_color, confirm=True)
    update_setting("orb_thinking_color", req.thinking_color, confirm=True)
    update_setting("orb_size", req.size, confirm=True)
    update_setting("orb_shape", req.shape, confirm=True)
    update_setting("orb_spin_speed", req.spin_speed, confirm=True)
    update_setting("orb_turbulence", req.turbulence, confirm=True)
    update_setting("orb_pulse", req.pulse, confirm=True)
    update_setting("orb_glow", req.glow, confirm=True)
    return _orb_from_settings()


@app.get("/api/report-sections")
async def get_report_sections():
    return load_report_sections()


@app.post("/api/report-sections")
async def set_report_sections(req: ReportSectionsRequest):
    return save_report_sections(normalize_sections(req.model_dump()))


@app.get("/api/security-level")
async def get_security_level_api():
    return security_status()


@app.post("/api/security-level")
async def post_security_level_api(req: SecurityLevelRequest):
    return set_security_level(req.security_level, confirm=bool(req.confirm))


@app.post("/api/doc-ingest")
async def api_doc_ingest(req: DocIngestRequest):
    kwargs = {"session_id": req.session_id or "desktop"}
    if (req.text or "").strip():
        kwargs["text"] = req.text
    if (req.path or "").strip():
        kwargs["path"] = req.path
    if (req.filename or "").strip():
        kwargs["filename"] = req.filename
    return ingest_document(**kwargs)


@app.post("/api/doc-ingest/apply")
async def api_doc_ingest_apply(req: DocIngestApplyRequest):
    return apply_proposal(
        req.proposal_id,
        session_id=req.session_id or "desktop",
        keys=req.keys,
        confirm=bool(req.confirm),
    )


@app.post("/api/doc-ingest/decline")
async def api_doc_ingest_decline(req: DocIngestDeclineRequest):
    return decline_proposal(req.proposal_id, session_id=req.session_id or "desktop")


@app.get("/api/desktop-plugin")
async def get_desktop_plugin():
    return desktop_plugin_status()


@app.post("/api/desktop-plugin")
async def post_desktop_plugin(req: DesktopPluginRequest):
    return set_desktop_plugin_enabled(bool(req.plugin_desktop_enabled))


@app.post("/api/desktop-smoke")
async def post_desktop_smoke(req: DesktopSmokeRequest):
    return run_desktop(exe_path=req.exe_path or "", timeout_s=float(req.timeout_s or 1.5))


@app.get("/api/plugins")
async def get_plugins():
    return list_plugins()


@app.get("/api/multi-sandbox-plugin")
async def get_multi_sandbox_plugin():
    return multi_sandbox_plugin_status()


@app.post("/api/multi-sandbox-plugin")
async def post_multi_sandbox_plugin(req: MultiSandboxPluginRequest):
    return set_multi_sandbox_plugin_enabled(bool(req.plugin_multi_sandbox_enabled))


@app.post("/api/multi-sandbox/orchestrate")
async def post_multi_sandbox_orchestrate(req: MultiSandboxOrchestrateRequest):
    return multi_sandbox_orchestrate(action=req.action or "list")


@app.get("/api/playwright-suite")
async def get_playwright_suite():
    return playwright_suite_status()


@app.post("/api/playwright-suite/discover")
async def post_playwright_suite_discover(req: PlaywrightSuitePathRequest):
    return discover_suite(suite_path=req.suite_path or "")


@app.post("/api/playwright-suite/import")
async def post_playwright_suite_import(req: PlaywrightSuitePathRequest):
    return set_suite_path(req.suite_path or "", confirm=bool(req.confirm))


@app.post("/api/playwright-suite/list")
async def post_playwright_suite_list(req: PlaywrightSuitePathRequest):
    return list_suite_tests(suite_path=req.suite_path or "")


@app.post("/api/playwright-suite/run")
async def post_playwright_suite_run(req: PlaywrightSuiteRunRequest):
    return run_playwright_suite(
        suite_path=req.suite_path or "",
        grep=req.grep or "",
        timeout_s=float(req.timeout_s or 300.0),
    )


app.mount("/ui", StaticFiles(directory=str(_UI_DIR)), name="ui")

