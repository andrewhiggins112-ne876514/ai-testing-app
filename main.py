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
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from agent.agent import Agent
from plugins.desktop_runner import (
    plugin_status as desktop_plugin_status,
    run_desktop,
    set_plugin_enabled as set_desktop_plugin_enabled,
)
from plugins.doc_ingest import apply_proposal, decline_proposal, ingest_document
from plugins.doc_uploads import list_uploads
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
from plans.coverage import plan_coverage_gaps
from plans.defect_packet import defect_packet_preview
from plans.draft import (
    add_document_draft_cases,
    draft_plan_from_issue,
    draft_plan_from_project,
)
from plans.drift import (
    check_acceptance_drift,
    keep_acceptance_drafts,
    refresh_acceptance_drafts,
)
from plans.import_playwright import import_playwright_project
from plans.history import compare_suite_runs, list_suite_history
from plans.quarantine import (
    DEFAULT_FLAKE_WINDOW,
    clear_quarantine as plan_clear_quarantine,
    set_quarantine as plan_set_quarantine,
    suite_flake_report,
)
from plans.offline_read import offline_plan_view, offline_read_status
from plans.search import search_plans
from plans.traceability import plan_traceability_matrix
from plans.pause_session import get_session, public_session, signal_decision
from plans.parallel import parallel_cap_info
from plans.duration import duration_info
from plans.run_notify import notify_info, set_notify_enabled
from plans.timeouts import step_timeout_info
from plans.rerun_failed import rerun_failed_cases
from plans.run_by_tag import run_cases_by_tag, select_cases_for_tag
from plans.run_case import case_detail, run_single_case
from plans.desktop_case import add_desktop_case
from plans.api_case import add_api_case, add_contract_case
from plans.seed_case import add_seed_case
from plans.visual_case import add_visual_case, update_case_baseline
from plans.a11y_case import add_a11y_browser_case, enable_a11y_on_case
from plans.run_report import export_plan_run, list_exportable_runs
from plans.starter import create_starter_plan, lab_home_status
from plans.home_checklist import home_checklist_summary
from plans.coverage_hud import coverage_hud_summary
from plans.manager_hud import manager_hud_summary
from plans.release_hud import release_hud_summary
from plans.tester_hud import tester_hud_summary
from plans.store import (
    add_case as plan_add_case,
    add_run as plan_add_run,
    cases_for_run as plan_cases_for_run,
    create_plan,
    get_plan,
    list_plans,
    reorder_cases as plan_reorder_cases,
    set_known_issue_link as plan_set_known_issue_link,
    set_plan_notes as plan_set_plan_notes,
    set_run_failure_class as plan_set_run_failure_class,
    update_case as plan_update_case,
)
from settings.degraded import degraded_status, ollama_chat_blocked
from plugins.registry import list_plugins
from reports.exporter import (
    get_saved_report,
    latest_summary as latest_report_summary,
    list_saved_reports,
    screenshot_path_for_report,
)
from reports.export_pack import (
    create_export_pack,
    export_pack_status,
    last_export_pack,
)
from reports.sections import load_report_sections, normalize_sections, save_report_sections
from settings.connection_health import connection_health
from settings.credential_status import (
    clear_secret as clear_credential_secret,
    credential_field_status,
    set_target_secret,
    test_connection as test_credential_connection,
)
from settings.environments import (
    activate_environment,
    delete_environment,
    list_environments,
    upsert_environment,
)
from settings.ollama_models import list_ollama_models
from settings.local_audit import list_local_audit
from settings.privacy import delete_local_data, privacy_status, telemetry_enabled
from settings.backup import backup_status, create_backup, list_backups, restore_backup
from reports.redact import redaction_status
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
    known_issues: bool = True
    traceability: bool = True
    documents: bool = False


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
    session_id: str = "desktop"


class LabBackupCreateRequest(BaseModel):
    include_settings: bool = False
    include_secrets: bool = False


class LabBackupRestoreRequest(BaseModel):
    path: str = ""
    filename: str = ""
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
    ollama_model: str | None = None
    run_finish_notify_enabled: bool | None = None


class RunNotifyRequest(BaseModel):
    """Turn local run-finish notices on or off (KAN-189 / D6)."""

    enabled: bool = True


class ClearSecretRequest(BaseModel):
    key: str
    confirm: bool = False


class TargetSecretRequest(BaseModel):
    value: str = ""
    confirm: bool = True


class NamedEnvironmentRequest(BaseModel):
    """Create/update a named target under the active security level (KAN-183 / D3)."""

    name: str = ""
    target_url: str = ""
    target_app_path: str = ""
    api_endpoint: str = ""
    env_id: str | None = None
    activate: bool = False


class ActivateEnvironmentRequest(BaseModel):
    env_id: str = ""


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
    test_file: str = ""
    timeout_s: float = 300.0


class PlanImportPlaywrightRequest(BaseModel):
    """Import Playwright project tests as in-app suite cases (KAN-171 / C8)."""

    suite_path: str = ""
    plan_id: str = ""
    plan_name: str = ""


class PlanDesktopCaseRequest(BaseModel):
    """Add a desktop-typed case to the open suite (KAN-217 / G1)."""

    name: str = ""
    exe_path: str = ""
    note: str = ""
    tags: list[str] | None = None


class PlanApiCaseRequest(BaseModel):
    """Add an API/messaging case to the open suite (KAN-219 / G2)."""

    name: str = ""
    endpoint: str = ""
    method: str = "GET"
    expect_status: int | None = None
    note: str = ""
    tags: list[str] | None = None
    body: str | None = None
    mock_fixture: str = ""


class PlanContractCaseRequest(BaseModel):
    """Add a contract/mock API case pointing at a local fixture (KAN-221 / G3)."""

    name: str = ""
    mock_fixture: str = ""
    expect_status: int | None = None
    note: str = ""
    tags: list[str] | None = None


class PlanSeedCaseRequest(BaseModel):
    """Add a seed/fixture case naming a local level-scoped fixture (KAN-223 / G4)."""

    name: str = ""
    fixture: str = ""
    note: str = ""
    tags: list[str] | None = None


class PlanVisualCaseRequest(BaseModel):
    """Add an opt-in visual baseline case (KAN-225 / G5)."""

    name: str = ""
    baseline: str = ""
    url: str = ""
    note: str = ""
    tags: list[str] | None = None


class PlanVisualBaselineUpdateRequest(BaseModel):
    """Explicit update-baseline only (never auto on mismatch)."""

    current_path: str = ""


class PlanA11yCaseRequest(BaseModel):
    """Add a browser case with accessibility check opted in (KAN-227 / G6)."""

    name: str = ""
    note: str = ""
    tags: list[str] | None = None


class PlanA11yEnableRequest(BaseModel):
    """Enable/disable a11y sidecar on an existing browser case (KAN-227 / G6)."""

    enabled: bool = True


class JiraIssueRequest(BaseModel):
    issue_key: str = ""


class PlanCreateRequest(BaseModel):
    name: str = "Untitled plan"
    intent: str = ""
    jira_keys: list[str] | None = None
    documents: list[str] | None = None


class PlanDraftRequest(BaseModel):
    issue_key: str = ""
    document_text: str = ""
    document_name: str = ""


class PlanProjectDraftRequest(BaseModel):
    """Project-wide draft in batches (KAN-161 / C3). batch_size is a visible cap."""

    batch_size: int = 5
    project: str = ""
    issue_types: list[str] | None = None


class PlanAcceptanceDriftRequest(BaseModel):
    """Optional subset of linked keys for check / keep / refresh (KAN-165 / C5)."""

    keys: list[str] | None = None


class PlanStarterRequest(BaseModel):
    name: str = "Starter plan"


class PlanDocumentDraftRequest(BaseModel):
    document_text: str = ""
    document_name: str = "uploaded-document"
    jira_key: str = ""


class PlanCaseRequest(BaseModel):
    name: str = "Untitled case"
    jira_key: str = ""
    tags: list[str] | None = None
    priority: int = 0
    note: str = ""
    enabled: bool = True
    source_kind: str = "manual-draft"
    source_ref: str = ""


class PlanCaseUpdateRequest(BaseModel):
    name: str | None = None
    note: str | None = None
    enabled: bool | None = None
    archived: bool | None = None
    order: int | None = None
    priority: int | None = None
    tags: list[str] | None = None
    step_timeout_ms: int | None = None
    session_id: str = "desktop"


class PlanQuarantineRequest(BaseModel):
    """Quarantine requires reason + expiry (KAN-181 / D2). Never counted as pass."""

    reason: str = ""
    expires_at: str = ""
    session_id: str = "desktop"


class PlanReorderRequest(BaseModel):
    case_ids: list[str] = Field(default_factory=list)


class PlanRunRequest(BaseModel):
    result: str = "pending"
    duration_ms: int | None = None
    failure_class: str | None = None
    evidence: list[str] | None = None
    note: str = ""


class PlanFailureClassRequest(BaseModel):
    failure_class: str = ""


class PlanKnownIssueRequest(BaseModel):
    """Link known-issue note + optional Jira key (KAN-153). No Jira writes."""

    note: str = ""
    jira_key: str = ""
    run_id: str = ""
    clear: bool = False


class PlanNotesRequest(BaseModel):
    """Local exploratory notes on a case and/or run (KAN-155). Level-scoped."""

    case_note: str | None = None
    run_note: str | None = None
    run_id: str = ""


class PlanCaseRunRequest(BaseModel):
    """Optional run flags. pause_on_fail is off by default (KAN-149).

    update_baseline is explicit opt-in for visual cases only (KAN-225 / G5).
    """

    pause_on_fail: bool = False
    update_baseline: bool = False
    current_path: str = ""


class PlanRerunFailedRequest(BaseModel):
    """Optional source suite run for rerun-failed (KAN-151) + parallel (KAN-179)."""

    source_suite_run_id: str = ""
    parallel: int = 1


class PlanRunByTagRequest(BaseModel):
    """Run all cases carrying a tag (KAN-169 / C7); parallel capped (KAN-179 / D1)."""

    tag: str = ""
    parallel: int = 1


class PlanExportRunRequest(BaseModel):
    """Export a chosen plan case run with optional section overrides (KAN-159)."""

    summary: bool | None = None
    stories: bool | None = None
    bugs: bool | None = None
    evidence: bool | None = None
    known_issues: bool | None = None
    traceability: bool | None = None
    documents: bool | None = None
    session_id: str = "plan-export"


class ExportPackRequest(BaseModel):
    """Read-only export pack for a plan case run (KAN-213 / F6)."""

    plan_id: str = ""
    case_id: str = ""
    run_id: str = ""
    summary: bool | None = None
    stories: bool | None = None
    bugs: bool | None = None
    evidence: bool | None = None
    known_issues: bool | None = None
    traceability: bool | None = None
    documents: bool | None = None


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
    blocked = ollama_chat_blocked()
    if blocked:
        return blocked
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


@app.get("/api/reports")
async def get_reports_library(limit: int = 50):
    """List saved report files for the Reports library (FR-REP-4)."""
    return list_saved_reports(limit=limit)


@app.get("/api/reports/{report_id}")
async def get_report_detail(report_id: str):
    detail = get_saved_report(report_id)
    if not detail.get("found"):
        raise HTTPException(status_code=404, detail="Report not found")
    return detail


@app.get("/api/reports/{report_id}/screenshot")
async def get_report_screenshot(report_id: str):
    path = screenshot_path_for_report(report_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(path)


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
    return delete_local_data(
        req.categories,
        confirm=bool(req.confirm),
        session_id=req.session_id or "desktop",
    )


@app.get("/api/local-audit")
async def get_local_audit_api(limit: int = 100):
    """Local side-effects audit for Security (KAN-195 / E2). No tokens/bodies."""
    return list_local_audit(limit=limit)


@app.get("/api/redaction")
async def get_redaction_api():
    """Export/evidence redaction policy (KAN-197 / E3). Never echoes secrets."""
    return redaction_status()


@app.get("/api/export-pack")
async def get_export_pack_api():
    """Read-only export pack status + last pack time (KAN-213 / F6). Local only."""
    return export_pack_status()


@app.get("/api/export-pack/last")
async def get_export_pack_last_api():
    """Last export pack summary for the home HUD widget (KAN-213)."""
    return last_export_pack()


@app.post("/api/export-pack")
async def post_export_pack_api(req: ExportPackRequest):
    """Write a read-only pack folder: report, matrix, evidence (KAN-213 / F6)."""
    overrides = {
        key: getattr(req, key)
        for key in (
            "summary",
            "stories",
            "bugs",
            "evidence",
            "known_issues",
            "traceability",
            "documents",
        )
        if getattr(req, key) is not None
    }
    sections = normalize_sections(overrides) if overrides else None
    return create_export_pack(
        (req.plan_id or "").strip(),
        (req.case_id or "").strip(),
        (req.run_id or "").strip(),
        sections=sections,
    )


@app.get("/api/backup")
async def get_lab_backup_api(limit: int = 20):
    """Lab backup status + recent local zips (KAN-199 / E4). No cloud."""
    status = backup_status()
    status["recent_backups"] = list_backups(limit=limit)
    return status


@app.post("/api/backup")
async def post_lab_backup_api(req: LabBackupCreateRequest):
    """Create a local level-scoped lab backup zip. Secrets off by default."""
    return create_backup(
        include_settings=bool(req.include_settings),
        include_secrets=bool(req.include_secrets),
    )


@app.post("/api/backup/restore")
async def post_lab_backup_restore_api(req: LabBackupRestoreRequest):
    """Restore a lab backup. Requires confirm; refuses OFFICIAL/SECRET mix."""
    path = (req.path or "").strip()
    if not path and (req.filename or "").strip():
        from settings.backup import backups_dir

        path = str(backups_dir() / req.filename.strip())
    return restore_backup(path, confirm=bool(req.confirm))


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
    if req.ollama_model is not None:
        kwargs["ollama_model"] = req.ollama_model
    if req.run_finish_notify_enabled is not None:
        kwargs["run_finish_notify_enabled"] = req.run_finish_notify_enabled
    return save_app_settings(**kwargs)


@app.get("/api/ollama-models")
async def get_ollama_models_api():
    """List local Ollama models and the selected agent model (KAN-129)."""
    return list_ollama_models()


@app.get("/api/connection-health")
async def get_connection_health_api():
    """Connect-once health: Jira, Ollama, target — no secrets (KAN-127 / FR-CONN-1)."""
    return connection_health()


@app.get("/api/credentials/status")
async def get_credentials_status_api():
    """Set/missing for Jira email, token, target secret — never values (KAN-185 / D4)."""
    return credential_field_status()


@app.post("/api/credentials/test-connection")
async def post_credentials_test_connection_api():
    """Test Jira with stored secrets; success or human-readable auth error (KAN-185)."""
    return test_credential_connection()


@app.post("/api/credentials/clear")
async def post_credentials_clear_api(req: ClearSecretRequest):
    """Clear one secret after confirm. Audit never stores the old value (KAN-185)."""
    return clear_credential_secret(req.key, confirm=bool(req.confirm))


@app.post("/api/credentials/target-secret")
async def post_credentials_target_secret_api(req: TargetSecretRequest):
    """Save target secret to level store. Response never echoes the value (KAN-185)."""
    return set_target_secret(req.value, confirm=bool(req.confirm))


@app.get("/api/environments")
async def get_environments_api():
    """Named targets under the active security level (KAN-183 / D3)."""
    return list_environments()


@app.post("/api/environments")
async def post_environments_api(req: NamedEnvironmentRequest):
    """Create or update a named target. Credentials stay in the level store."""
    return upsert_environment(
        name=req.name,
        target_url=req.target_url,
        target_app_path=req.target_app_path,
        api_endpoint=req.api_endpoint,
        env_id=req.env_id,
        activate=bool(req.activate),
    )


@app.post("/api/environments/activate")
async def post_environments_activate_api(req: ActivateEnvironmentRequest):
    """Switch active named target without changing security level."""
    return activate_environment(req.env_id)


@app.post("/api/environments/{env_id}/delete")
async def post_environments_delete_api(env_id: str):
    """Remove a named target. Does not echo or move secrets into plans."""
    return delete_environment(env_id)


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


@app.get("/api/doc-uploads")
async def api_doc_uploads(include_bodies: bool = False):
    """E1: list local upload metadata (bodies off by default; no cloud sync)."""
    return list_uploads(include_bodies=bool(include_bodies))


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
async def api_heal_proposals(run_id: str = ""):
    """Pending heals; optional ``run_id`` filters to that plan run (KAN-159)."""
    return list_pending_heals(run_id=run_id or None)


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
        test_file=req.test_file or "",
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


@app.get("/api/degraded-mode")
async def get_degraded_mode():
    """Dependency-down hints — saved plans stay readable (KAN-139)."""
    return degraded_status()


@app.post("/api/plans/draft")
async def post_plan_draft(req: PlanDraftRequest):
    """Draft a plan from one Jira issue (+ optional document). Never writes to Jira (KAN-131)."""
    out = await draft_plan_from_issue(
        req.issue_key or "",
        document_text=req.document_text or "",
        document_name=req.document_name or "",
    )
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.post("/api/plans/draft-project")
async def post_plan_draft_project(req: PlanProjectDraftRequest):
    """Draft a plan from the configured Jira project in a capped batch (KAN-161 / C3).

    Read-only. Does not auto-run — person reviews then uses A7 run path.
    After draft, response includes coverage_gaps (KAN-163 / C4) without creating cases.
    """
    out = await draft_plan_from_project(
        batch_size=req.batch_size,
        project=req.project or None,
        issue_types=req.issue_types,
    )
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.post("/api/plans/import-playwright")
async def post_plan_import_playwright(req: PlanImportPlaywrightRequest):
    """Import Playwright project tests as suite cases (KAN-171 / C8).

    External project files are never deleted. Suites-area npx run stays available.
    """
    return import_playwright_project(
        suite_path=req.suite_path or "",
        plan_id=(req.plan_id or "").strip() or None,
        plan_name=req.plan_name or "",
    )


@app.get("/api/plans/search")
async def get_plans_search(q: str = "", limit: int = 50):
    """Search plans, cases, and failures in the active security level (KAN-173 / C9).

    Matches plan name, case name, Jira key, tag, and failure class.
    Does not search across OFFICIAL/SECRET. Works offline on stored data (KAN-201 / E5).
    """
    return search_plans(q or "", limit=limit)


@app.get("/api/plans/offline-read")
async def get_plans_offline_read():
    """E5: last plan readable while Jira is down — local search/matrix; network actions gated."""
    return offline_read_status(probe=True)


@app.get("/api/plans/parallel-cap")
async def get_plan_parallel_cap():
    """Visible parallel default and max for suite runs (KAN-179 / D1)."""
    return parallel_cap_info()


@app.get("/api/plans/step-timeout")
async def get_plan_step_timeout():
    """Visible step timeout default matching the current runner (KAN-187 / D5)."""
    return step_timeout_info()


@app.get("/api/plans/run-notify")
async def get_plan_run_notify():
    """Local run-finish notice preference (KAN-189 / D6). No email or cloud push."""
    return notify_info()


@app.post("/api/plans/run-notify")
async def post_plan_run_notify(body: RunNotifyRequest):
    """Turn local run-finish notices on or off (KAN-189 / D6)."""
    return set_notify_enabled(bool(body.enabled))


@app.get("/api/plans/duration")
async def get_plan_duration_info():
    """D7 duration on run/case — local only, no upload (KAN-191)."""
    return duration_info()


@app.get("/api/plans/{plan_id}/coverage-gaps")
async def get_plan_coverage_gaps(
    plan_id: str,
    q: str = "",
    project: str = "",
    list_max: int = 50,
):
    """List stories with no case / all cases disabled (KAN-163 / C4). Never creates cases."""
    out = await plan_coverage_gaps(
        plan_id,
        filter_text=q or "",
        project=project or None,
        list_max=list_max,
    )
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.get("/api/plans/{plan_id}/traceability")
async def get_plan_traceability(plan_id: str, q: str = ""):
    """C6 traceability matrix: story → cases → last result → bugs → known (KAN-167).

    Local-only; works while Jira is down with fetch-time labels (KAN-201 / E5).
    """
    out = plan_traceability_matrix(plan_id, filter_text=q or "")
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.get("/api/plans/{plan_id}/offline-read")
async def get_plan_offline_read(plan_id: str):
    """E5: open one plan's last stored keys and results while Jira is down."""
    return offline_plan_view(plan_id)


@app.get("/api/plans/{plan_id}/suite-history")
async def get_plan_suite_history(plan_id: str):
    """C10 suite history: past runs with time, duration, pass/fail, tag (KAN-175).

    Local to the active security level only — never cross-level.
    """
    return list_suite_history(plan_id)


@app.get("/api/plans/{plan_id}/suite-compare")
async def get_plan_suite_compare(plan_id: str, a: str = "", b: str = ""):
    """C10/D7 compare two suite runs: result changes + duration changes (KAN-175 / KAN-191)."""
    return compare_suite_runs(plan_id, a, b)


@app.get("/api/plans/{plan_id}/flake")
async def get_plan_flake(plan_id: str, window: int = DEFAULT_FLAKE_WINDOW):
    """D2 flake scores (fail count in last N runs) + quarantine status (KAN-181)."""
    loaded = get_plan(plan_id)
    if loaded.get("status") != "ok":
        return loaded
    report = suite_flake_report(loaded["plan"], window=window)
    return {**report, "security_level": loaded.get("security_level")}


@app.post("/api/plans/{plan_id}/cases/{case_id}/quarantine")
async def post_plan_case_quarantine(
    plan_id: str,
    case_id: str,
    req: PlanQuarantineRequest,
):
    """Quarantine a case — reason + expiry required; skipped on runs, not a pass (KAN-181)."""
    return plan_set_quarantine(
        plan_id,
        case_id,
        reason=req.reason or "",
        expires_at=req.expires_at or "",
        session_id=req.session_id or "desktop",
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/quarantine/clear")
async def post_plan_case_quarantine_clear(
    plan_id: str,
    case_id: str,
    req: PlanQuarantineRequest = PlanQuarantineRequest(),
):
    """Clear quarantine early so the case returns to the selectable set (KAN-181)."""
    return plan_clear_quarantine(
        plan_id,
        case_id,
        session_id=req.session_id or "desktop",
    )


@app.post("/api/plans/{plan_id}/acceptance-drift")
async def post_plan_acceptance_drift(
    plan_id: str, req: PlanAcceptanceDriftRequest = PlanAcceptanceDriftRequest()
):
    """Re-read linked issues; mark stale if summary/AC differ (KAN-165 / C5)."""
    out = await check_acceptance_drift(plan_id, keys=req.keys)
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.post("/api/plans/{plan_id}/acceptance-drift/keep")
async def post_plan_acceptance_drift_keep(
    plan_id: str, req: PlanAcceptanceDriftRequest = PlanAcceptanceDriftRequest()
):
    """Keep current drafts; re-baseline snapshots (KAN-165). No case overwrite."""
    out = await keep_acceptance_drafts(plan_id, keys=req.keys)
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.post("/api/plans/{plan_id}/acceptance-drift/refresh")
async def post_plan_acceptance_drift_refresh(
    plan_id: str, req: PlanAcceptanceDriftRequest = PlanAcceptanceDriftRequest()
):
    """Refresh drafts from live AC; never deletes cases or runs (KAN-165)."""
    out = await refresh_acceptance_drafts(plan_id, keys=req.keys)
    if out.get("status") != "ok" or not degraded_status().get("jira_up"):
        out = {**out, "degraded": degraded_status()}
    return out


@app.get("/api/plans/home")
async def get_plans_home():
    """Orb-home empty state + checklist when no plans exist (KAN-135)."""
    return lab_home_status()


@app.get("/api/plans/home-checklist")
async def get_plans_home_checklist():
    """First-hour home checklist: connection, first plan, first run (KAN-215 / F7)."""
    return home_checklist_summary()


@app.get("/api/plans/tester-hud")
async def get_plans_tester_hud():
    """Tester HUD pack: connection, last run, fails, quarantine (KAN-203 / F1)."""
    return tester_hud_summary()


@app.get("/api/plans/manager-hud")
async def get_plans_manager_hud():
    """Manager HUD pack: pass rate, known issues, gaps, bugs (KAN-205 / F2)."""
    return manager_hud_summary()


@app.get("/api/plans/release-hud")
async def get_plans_release_hud():
    """Release HUD pack: env, last run, uncovered, open bugs (KAN-207 / F3)."""
    return release_hud_summary()


@app.get("/api/plans/coverage-hud")
async def get_plans_coverage_hud(story_key: str | None = None):
    """Coverage HUD pack: open-story AC lines covered/partial/missing (KAN-209 / F4)."""
    return coverage_hud_summary(story_key=story_key)


@app.post("/api/plans/starter")
async def post_plan_starter(req: PlanStarterRequest):
    """Create a starter template plan with editable cases (KAN-135). No Jira writes."""
    return create_starter_plan(name=req.name or "Starter plan")


@app.get("/api/plans/exportable-runs")
async def get_plans_exportable_runs(limit: int = 50):
    """Recent case runs for the Reports section picker export (KAN-159)."""
    return list_exportable_runs(limit=limit)


@app.get("/api/plans/{plan_id}")
async def get_plan_by_id(plan_id: str):
    return get_plan(plan_id)


@app.get("/api/plans/{plan_id}/runnable")
async def get_plan_runnable(plan_id: str):
    """Cases later runs should execute — disabled cases are skipped (KAN-133)."""
    return plan_cases_for_run(plan_id)


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


@app.post("/api/plans/{plan_id}/cases/desktop")
async def post_plan_desktop_case(plan_id: str, req: PlanDesktopCaseRequest):
    """Add a desktop-typed case; runs via desktop_runner, not Playwright (KAN-217)."""
    return add_desktop_case(
        plan_id,
        req.name or "",
        exe_path=req.exe_path or "",
        note=req.note or "",
        tags=list(req.tags or []),
    )


@app.post("/api/plans/{plan_id}/cases/api")
async def post_plan_api_case(plan_id: str, req: PlanApiCaseRequest):
    """Add an API/messaging case; calls saved endpoint with redacted body (KAN-219)."""
    return add_api_case(
        plan_id,
        req.name or "",
        endpoint=req.endpoint or "",
        method=req.method or "GET",
        expect_status=req.expect_status,
        note=req.note or "",
        tags=list(req.tags or []),
        body=req.body,
        mock_fixture=req.mock_fixture or "",
    )


@app.post("/api/plans/{plan_id}/cases/contract")
async def post_plan_contract_case(plan_id: str, req: PlanContractCaseRequest):
    """Add a contract/mock case pointing at a local fixture (KAN-221 / G3)."""
    return add_contract_case(
        plan_id,
        req.name or "",
        mock_fixture=req.mock_fixture or "",
        expect_status=req.expect_status,
        note=req.note or "",
        tags=list(req.tags or []),
    )


@app.post("/api/plans/{plan_id}/cases/seed")
async def post_plan_seed_case(plan_id: str, req: PlanSeedCaseRequest):
    """Add a seed/fixture case naming a local fixture (KAN-223 / G4)."""
    return add_seed_case(
        plan_id,
        req.name or "",
        fixture=req.fixture or "",
        note=req.note or "",
        tags=list(req.tags or []),
    )


@app.post("/api/plans/{plan_id}/cases/visual")
async def post_plan_visual_case(plan_id: str, req: PlanVisualCaseRequest):
    """Add an opt-in visual baseline case (KAN-225 / G5). Off unless case opts in."""
    return add_visual_case(
        plan_id,
        req.name or "",
        baseline=req.baseline or "",
        url=req.url or "",
        note=req.note or "",
        tags=list(req.tags or []),
    )


@app.post("/api/plans/{plan_id}/cases/a11y")
async def post_plan_a11y_case(plan_id: str, req: PlanA11yCaseRequest):
    """Add a browser case with accessibility check opted in (KAN-227 / G6)."""
    return add_a11y_browser_case(
        plan_id,
        req.name or "",
        note=req.note or "",
        tags=list(req.tags or []),
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/a11y")
async def post_plan_a11y_enable(
    plan_id: str,
    case_id: str,
    req: PlanA11yEnableRequest | None = None,
):
    """Enable/disable a11y sidecar on a browser case (KAN-227 / G6). Off by default."""
    body = req or PlanA11yEnableRequest()
    return enable_a11y_on_case(
        plan_id,
        case_id,
        enabled=bool(body.enabled),
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/visual-baseline")
async def post_plan_visual_baseline_update(
    plan_id: str,
    case_id: str,
    req: PlanVisualBaselineUpdateRequest | None = None,
):
    """Explicitly store/update the visual baseline image (KAN-225 / G5)."""
    body = req or PlanVisualBaselineUpdateRequest()
    path = (body.current_path or "").strip()
    if path:
        return update_case_baseline(plan_id, case_id, current_path=path)
    # Capture then store when no path provided (explicit update action).
    out = await run_single_case(
        plan_id,
        case_id,
        session_id="desktop",
        update_baseline=True,
    )
    out["explicit_update"] = True
    return out


@app.post("/api/plans/{plan_id}/cases/{case_id}")
async def post_plan_case_update(plan_id: str, case_id: str, req: PlanCaseUpdateRequest):
    """Rename / note / enable-disable / archive / order / step timeout a case (KAN-133 / KAN-177 / KAN-187)."""
    return plan_update_case(
        plan_id,
        case_id,
        name=req.name,
        note=req.note,
        enabled=req.enabled,
        archived=req.archived,
        order=req.order,
        priority=req.priority,
        tags=list(req.tags) if req.tags is not None else None,
        step_timeout_ms=req.step_timeout_ms,
        session_id=req.session_id or "desktop",
    )


@app.post("/api/plans/{plan_id}/reorder")
async def post_plan_reorder(plan_id: str, req: PlanReorderRequest):
    return plan_reorder_cases(plan_id, list(req.case_ids or []))


@app.post("/api/plans/{plan_id}/draft-document")
async def post_plan_draft_document(plan_id: str, req: PlanDocumentDraftRequest):
    """Upload/document text adds draft cases only — no Jira writes (KAN-131)."""
    return add_document_draft_cases(
        plan_id,
        document_text=req.document_text or "",
        document_name=req.document_name or "uploaded-document",
        jira_key=req.jira_key or "",
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


@app.post("/api/plans/{plan_id}/cases/{case_id}/run")
async def post_plan_case_run(
    plan_id: str,
    case_id: str,
    req: PlanCaseRunRequest | None = None,
):
    """Run a single case headed with Playwright; record evidence on that case (KAN-137).

    Optional pause_on_fail (KAN-149): on step failure leave headed browser open until
    continue or stop. Off by default.
    """
    body = req or PlanCaseRunRequest()
    return await run_single_case(
        plan_id,
        case_id,
        session_id="desktop",
        pause_on_fail=bool(body.pause_on_fail),
        update_baseline=bool(body.update_baseline),
        current_path=(body.current_path or "").strip() or None,
    )


@app.post("/api/plans/{plan_id}/rerun-failed")
async def post_plan_rerun_failed(
    plan_id: str,
    req: PlanRerunFailedRequest | None = None,
):
    """Rerun only failed cases; new suite_run id on same suite (KAN-151 / KAN-179).

    Disabled and quarantined candidates are skipped with reasons shown.
    Default parallel=1 (sequential); refuse above local cap.
    """
    body = req or PlanRerunFailedRequest()
    return await rerun_failed_cases(
        plan_id,
        source_suite_run_id=(body.source_suite_run_id or "").strip() or None,
        session_id="desktop",
        parallel=body.parallel,
    )


@app.get("/api/plans/{plan_id}/run-by-tag")
async def get_plan_run_by_tag_preview(plan_id: str, tag: str = ""):
    """Preview which cases a tag run would execute (KAN-169 / C7)."""
    loaded = get_plan(plan_id)
    if loaded.get("status") != "ok":
        return loaded
    selection = select_cases_for_tag(loaded["plan"], tag)
    if selection.get("status") != "ok":
        return {**selection, "plan_id": plan_id, "security_level": loaded.get("security_level")}
    cap = parallel_cap_info()
    return {
        **selection,
        "plan_id": plan_id,
        "security_level": loaded.get("security_level"),
        "parallel_default": cap.get("parallel_default"),
        "parallel_max": cap.get("parallel_max"),
    }


@app.post("/api/plans/{plan_id}/run-by-tag")
async def post_plan_run_by_tag(
    plan_id: str,
    req: PlanRunByTagRequest | None = None,
):
    """Run all cases with a chosen tag; store suite_run id + tag + parallel (KAN-169 / KAN-179).

    Untagged cases are omitted and listed as not_selected.
    Default parallel=1 (sequential); refuse above local cap.
    """
    body = req or PlanRunByTagRequest()
    return await run_cases_by_tag(
        plan_id,
        body.tag or "",
        session_id="desktop",
        parallel=body.parallel,
    )


@app.get("/api/plans/pause/{pause_id}")
async def get_plan_pause(pause_id: str):
    """Pause-on-fail session status (KAN-149)."""
    session = get_session(pause_id)
    if session is None:
        return {
            "status": "error",
            "error": "pause_not_found",
            "message": f"No pause session {pause_id!r}.",
        }
    return public_session(session)


@app.post("/api/plans/pause/{pause_id}/continue")
async def post_plan_pause_continue(pause_id: str):
    """Continue after pause-on-fail (remaining steps; browser stays open) (KAN-149)."""
    return await signal_decision(pause_id, "continue")


@app.post("/api/plans/pause/{pause_id}/stop")
async def post_plan_pause_stop(pause_id: str):
    """Stop after pause-on-fail and record a failed run (KAN-149)."""
    return await signal_decision(pause_id, "stop")


@app.get("/api/plans/{plan_id}/cases/{case_id}")
async def get_plan_case(plan_id: str, case_id: str):
    """Case view with source links and last run (KAN-141)."""
    loaded = get_plan(plan_id)
    if loaded.get("status") != "ok":
        return loaded
    return case_detail(loaded["plan"], case_id)


@app.post("/api/plans/{plan_id}/cases/{case_id}/runs/{run_id}/failure-class")
async def post_plan_run_failure_class(
    plan_id: str,
    case_id: str,
    run_id: str,
    req: PlanFailureClassRequest,
):
    """Set failure class on a run — create-bug only when product_bug (KAN-145)."""
    return plan_set_run_failure_class(
        plan_id,
        case_id,
        run_id,
        req.failure_class,
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/known-issue")
async def post_plan_case_known_issue(
    plan_id: str,
    case_id: str,
    req: PlanKnownIssueRequest,
):
    """Link known-issue note + optional Jira key; run stays red (KAN-153). No Jira writes."""
    return plan_set_known_issue_link(
        plan_id,
        case_id,
        note=req.note,
        jira_key=req.jira_key,
        run_id=req.run_id or None,
        clear=bool(req.clear),
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/notes")
async def post_plan_case_notes(
    plan_id: str,
    case_id: str,
    req: PlanNotesRequest,
):
    """Save local exploratory notes on a case and/or run (KAN-155). Level-scoped."""
    return plan_set_plan_notes(
        plan_id,
        case_id,
        case_note=req.case_note,
        run_note=req.run_note,
        run_id=req.run_id or None,
    )


@app.get("/api/plans/{plan_id}/cases/{case_id}/defect-preview")
async def get_plan_defect_preview(plan_id: str, case_id: str, run_id: str = ""):
    """Preview defect packet before Jira create — confirm still required (KAN-147)."""
    return defect_packet_preview(plan_id, case_id, run_id=run_id or None)


@app.post("/api/plans/{plan_id}/cases/{case_id}/runs/{run_id}/export")
async def post_plan_run_export(
    plan_id: str,
    case_id: str,
    run_id: str,
    req: PlanExportRunRequest = PlanExportRunRequest(),
):
    """Export a chosen run using the Reports section picker (KAN-159 / FR-REP-2)."""
    overrides = {
        key: getattr(req, key)
        for key in (
            "summary",
            "stories",
            "bugs",
            "evidence",
            "known_issues",
            "traceability",
            "documents",
        )
        if getattr(req, key) is not None
    }
    sections = normalize_sections(overrides) if overrides else None
    return export_plan_run(
        plan_id,
        case_id,
        run_id,
        sections=sections,
        session_id=req.session_id or "plan-export",
    )


@app.post("/api/plans/{plan_id}/cases/{case_id}/runs/{run_id}/export-pack")
async def post_plan_run_export_pack(
    plan_id: str,
    case_id: str,
    run_id: str,
    req: PlanExportRunRequest = PlanExportRunRequest(),
):
    """Write a read-only pack folder for a chosen run (KAN-213 / F6 / FR-REP-3)."""
    overrides = {
        key: getattr(req, key)
        for key in (
            "summary",
            "stories",
            "bugs",
            "evidence",
            "known_issues",
            "traceability",
            "documents",
        )
        if getattr(req, key) is not None
    }
    sections = normalize_sections(overrides) if overrides else None
    return create_export_pack(
        plan_id,
        case_id,
        run_id,
        sections=sections,
    )


app.mount("/ui", StaticFiles(directory=str(_UI_DIR)), name="ui")

