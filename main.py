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
from plugins.heal_policy import approve_heal, list_pending_heals, reject_heal
from plugins.framework_switch import (
    attempt_run as framework_attempt_run,
    framework_status,
    reject_if_unsupported,
    set_framework,
)
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
from plans.store import (
    add_case as plan_add_case,
    add_run as plan_add_run,
    create_plan,
    get_plan,
    list_plans,
)
from plugins.registry import list_plugins
from reports.exporter import latest_summary as latest_report_summary
from reports.sections import load_report_sections, normalize_sections, save_report_sections
from settings.connection_health import connection_health
from settings.privacy import delete_local_data, privacy_status, telemetry_enabled
from settings.store import (
    app_settings_status,
    load_settings,
    save_app_settings,
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


class HealReviewRequest(BaseModel):
    proposal_id: str
    reviewer: str = "local_user"


class SecurityLevelRequest(BaseModel):
    security_level: str
    confirm: bool = False


class DeleteLocalDataRequest(BaseModel):
    categories: list[str] | None = None
    confirm: bool = False


class AppSettingsRequest(BaseModel):
    jira_url: str | None = None
    jira_project: str | None = None
    target_url: str | None = None
    target_app_path: str | None = None
    api_endpoint: str | None = None
    test_framework: str | None = None
    playwright_mode: str | None = None
    playwright_headless: bool | None = None


class TestFrameworkRequest(BaseModel):
    test_framework: str = "playwright"


class TestFrameworkRunRequest(BaseModel):
    action: str = "run"
    framework: str = ""


class DesktopPluginRequest(BaseModel):
    plugin_desktop_enabled: bool = True


class DesktopSmokeRequest(BaseModel):
    exe_path: str = ""
    timeout_s: float = 1.5
    steps: list | None = None
    demo: bool = False


class MultiSandboxPluginRequest(BaseModel):
    plugin_multi_sandbox_enabled: bool = False


class MultiSandboxOrchestrateRequest(BaseModel):
    action: str = "list"
    sandbox_id: str = ""
    label: str = ""
    url: str = ""
    profile_key: str = ""


class PlaywrightSuitePathRequest(BaseModel):
    suite_path: str = ""
    confirm: bool = True


class PlaywrightSuiteRunRequest(BaseModel):
    suite_path: str = ""
    grep: str = ""
    timeout_s: float = 300.0


class JiraIssueRequest(BaseModel):
    issue_key: str = ""


class PlanCreateRequest(BaseModel):
    name: str = "Untitled plan"
    intent: str = ""
    jira_keys: list[str] | None = None
    documents: list[str] | None = None


class PlanCaseRequest(BaseModel):
    name: str = "Untitled case"
    jira_key: str = ""
    tags: list[str] | None = None
    priority: int = 0
    note: str = ""
    enabled: bool = True
    source_kind: str = "manual-draft"
    source_ref: str = ""


class PlanRunRequest(BaseModel):
    result: str = "pending"
    duration_ms: int | None = None
    failure_class: str | None = None
    evidence: list[str] | None = None
    note: str = ""


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
    """Chat entrypoint — always returns a reply string; ok=false on agent/tool failure (KAN-97)."""
    try:
        reply = await agent.chat(req.message, req.session_id)
    except httpx.HTTPError:
        return {
            "ok": False,
            "error": "ollama_unreachable",
            "reply": "Ollama is not reachable. Start Ollama and check that the model is pulled.",
        }
    except Exception as exc:  # noqa: BLE001 — surface agent failures clearly (NFR §4.6 / FR-AGENT-5)
        name = type(exc).__name__
        detail = str(exc).strip() or name
        # Never echo credentials if an unexpected exception string ever contained them.
        lowered = detail.lower()
        if "token" in lowered or "password" in lowered or "authorization" in lowered:
            detail = name
        return {
            "ok": False,
            "error": "agent_error",
            "reply": f"Agent error ({name}): {detail}",
        }
    return {"ok": True, "reply": reply}

@app.get("/health")
async def health():
    settings = load_settings()
    configured = bool(settings.get("jira_url") and settings.get("jira_api_token"))
    return {
        "status": "ok",
        "model": "local-ollama",
        "jira_configured": configured,
        "settings_path": str(settings_path()),
        "telemetry_enabled": telemetry_enabled(),
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


@app.get("/api/reports/latest-summary")
async def get_latest_report_summary():
    return latest_report_summary()


@app.get("/api/security-level")
async def get_security_level_api():
    return security_status()


@app.post("/api/security-level")
async def post_security_level_api(req: SecurityLevelRequest):
    return set_security_level(req.security_level, confirm=bool(req.confirm))


@app.get("/api/privacy")
async def get_privacy_api():
    return privacy_status()


@app.post("/api/privacy/delete")
async def post_privacy_delete_api(req: DeleteLocalDataRequest):
    return delete_local_data(req.categories, confirm=bool(req.confirm))


@app.get("/api/app-settings")
async def get_app_settings_api():
    return app_settings_status()


@app.post("/api/app-settings")
async def post_app_settings_api(req: AppSettingsRequest):
    kwargs: dict = {}
    if req.jira_url is not None:
        kwargs["jira_url"] = req.jira_url
    if req.jira_project is not None:
        kwargs["jira_project"] = req.jira_project
    if req.target_url is not None:
        kwargs["target_url"] = req.target_url
    if req.target_app_path is not None:
        kwargs["target_app_path"] = req.target_app_path
    if req.api_endpoint is not None:
        kwargs["api_endpoint"] = req.api_endpoint
    if req.test_framework is not None and str(req.test_framework).strip():
        kwargs["test_framework"] = req.test_framework.strip()
    if req.playwright_mode is not None and str(req.playwright_mode).strip():
        kwargs["playwright_mode"] = req.playwright_mode.strip()
    elif req.playwright_headless is not None:
        kwargs["playwright_headless"] = req.playwright_headless
    return save_app_settings(**kwargs)


@app.get("/api/connection-health")
async def get_connection_health_api():
    """Connect-once health: Jira, Ollama, target — no secrets (KAN-127 / FR-CONN-1)."""
    return connection_health()


@app.get("/api/test-framework")
async def get_test_framework_api():
    return framework_status()


@app.post("/api/test-framework")
async def post_test_framework_api(req: TestFrameworkRequest):
    return set_framework(req.test_framework or "playwright")


@app.post("/api/test-framework/run")
async def post_test_framework_run_api(req: TestFrameworkRunRequest):
    return framework_attempt_run(
        framework=(req.framework or "").strip() or None,
        action=req.action or "run",
    )


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


@app.get("/api/heal/proposals")
async def api_heal_proposals():
    return list_pending_heals()


@app.post("/api/heal/approve")
async def api_heal_approve(req: HealReviewRequest):
    return approve_heal(req.proposal_id, reviewer=req.reviewer or "local_user")


@app.post("/api/heal/reject")
async def api_heal_reject(req: HealReviewRequest):
    return reject_heal(req.proposal_id, reviewer=req.reviewer or "local_user")


@app.get("/api/jira-issue/{issue_key}")
async def get_jira_issue(issue_key: str):
    """Read-only: summary, description, and acceptance criteria for one issue."""
    from plugins.jira_plugin import read_issue

    return await read_issue(issue_key)


@app.post("/api/jira-issue")
async def post_jira_issue(req: JiraIssueRequest):
    from plugins.jira_plugin import read_issue

    return await read_issue(req.issue_key or "")


@app.get("/api/desktop-plugin")
async def get_desktop_plugin():
    return desktop_plugin_status()


@app.post("/api/desktop-plugin")
async def post_desktop_plugin(req: DesktopPluginRequest):
    return set_desktop_plugin_enabled(bool(req.plugin_desktop_enabled))


@app.post("/api/desktop-smoke")
async def post_desktop_smoke(req: DesktopSmokeRequest):
    from plugins.desktop_runner import demo_notepad_steps

    steps = req.steps
    if req.demo and not steps:
        steps = demo_notepad_steps()
        exe = (req.exe_path or "").strip() or r"C:\Windows\System32\notepad.exe"
        return run_desktop(
            exe_path=exe,
            timeout_s=float(req.timeout_s or 8.0),
            steps=steps,
        )
    return run_desktop(
        exe_path=req.exe_path or "",
        timeout_s=float(req.timeout_s or 1.5),
        steps=steps,
    )


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
    return multi_sandbox_orchestrate(
        action=req.action or "list",
        sandbox_id=req.sandbox_id or "",
        label=req.label or "",
        url=req.url or "",
        profile_key=req.profile_key or "",
    )


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
    blocked = reject_if_unsupported(action="run_suite")
    if blocked is not None:
        return blocked
    return run_playwright_suite(
        suite_path=req.suite_path or "",
        grep=req.grep or "",
        timeout_s=float(req.timeout_s or 300.0),
    )


@app.get("/api/plans")
async def get_plans():
    """List in-app plans for the active security level (KAN-125 / FR-PLAN-1/2)."""
    return list_plans()


@app.post("/api/plans")
async def post_plan(req: PlanCreateRequest):
    return create_plan(
        name=req.name or "Untitled plan",
        intent=req.intent or "",
        sources={
            "jira_keys": list(req.jira_keys or []),
            "documents": list(req.documents or []),
        },
    )


@app.get("/api/plans/{plan_id}")
async def get_plan_by_id(plan_id: str):
    return get_plan(plan_id)


@app.post("/api/plans/{plan_id}/cases")
async def post_plan_case(plan_id: str, req: PlanCaseRequest):
    return plan_add_case(
        plan_id,
        req.name or "Untitled case",
        jira_key=req.jira_key or "",
        tags=list(req.tags or []),
        priority=int(req.priority or 0),
        note=req.note or "",
        enabled=bool(req.enabled),
        source_kind=req.source_kind or "manual-draft",
        source_ref=req.source_ref or "",
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/runs")
async def post_plan_run(plan_id: str, case_id: str, req: PlanRunRequest):
    return plan_add_run(
        plan_id,
        case_id,
        result=req.result or "pending",
        duration_ms=req.duration_ms,
        failure_class=req.failure_class,
        evidence=list(req.evidence or []),
        note=req.note or "",
    )


app.mount("/ui", StaticFiles(directory=str(_UI_DIR)), name="ui")

