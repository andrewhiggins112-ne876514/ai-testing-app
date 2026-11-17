"""In-app test plan / suite / case / run model (FR-PLAN-1 / FR-PLAN-2)."""

from plans.coverage import plan_coverage_gaps
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
from plans.desktop_case import add_desktop_case
from plans.api_case import add_api_case, add_contract_case
from plans.seed_case import add_seed_case
from plans.visual_case import add_visual_case
from plans.a11y_case import add_a11y_browser_case, enable_a11y_on_case
from plans.perf_case import add_perf_budget_case, set_performance_budget
from plans.framework_case import add_framework_case
from plans.sandbox_run import list_run_sandboxes, resolve_run_sandbox
from plans.duration import duration_info
from plans.history import compare_suite_runs, list_suite_history
from plans.quarantine import (
    DEFAULT_FLAKE_WINDOW,
    clear_quarantine,
    flake_score,
    is_actively_quarantined,
    set_quarantine,
    suite_flake_report,
)
from plans.offline_read import offline_plan_view, offline_read_status
from plans.search import search_plans
from plans.timeouts import (
    DEFAULT_STEP_TIMEOUT_MS,
    case_step_timeout_ms,
    resolve_step_timeout_ms,
    step_timeout_info,
    timeout_failure_message,
)
from plans.traceability import plan_traceability_matrix
from plans.run_by_tag import WELL_KNOWN_TAGS, run_cases_by_tag, select_cases_for_tag
from plans.starter import create_starter_plan, lab_home_status
from plans.home_checklist import home_checklist_summary
from plans.coverage_hud import coverage_hud_summary
from plans.manager_hud import manager_hud_summary
from plans.release_hud import release_hud_summary
from plans.tester_hud import tester_hud_summary
from plans.store import (
    add_case,
    add_run,
    append_run_evidence,
    cases_for_run,
    set_known_issue_link,
    set_plan_notes,
    set_run_failure_class,
    create_plan,
    get_plan,
    list_plans,
    plans_dir,
    reorder_cases,
    update_case,
    upsert_jira_snapshot,
)

__all__ = [
    "DEFAULT_FLAKE_WINDOW",
    "DEFAULT_STEP_TIMEOUT_MS",
    "add_case",
    "add_api_case",
    "add_contract_case",
    "add_seed_case",
    "add_visual_case",
    "add_a11y_browser_case",
    "enable_a11y_on_case",
    "add_perf_budget_case",
    "set_performance_budget",
    "add_framework_case",
    "list_run_sandboxes",
    "resolve_run_sandbox",
    "add_desktop_case",
    "case_step_timeout_ms",
    "resolve_step_timeout_ms",
    "step_timeout_info",
    "timeout_failure_message",
    "add_document_draft_cases",
    "add_run",
    "append_run_evidence",
    "cases_for_run",
    "check_acceptance_drift",
    "clear_quarantine",
    "keep_acceptance_drafts",
    "refresh_acceptance_drafts",
    "import_playwright_project",
    "compare_suite_runs",
    "duration_info",
    "flake_score",
    "is_actively_quarantined",
    "list_suite_history",
    "offline_plan_view",
    "offline_read_status",
    "search_plans",
    "set_known_issue_link",
    "set_plan_notes",
    "set_quarantine",
    "set_run_failure_class",
    "create_plan",
    "create_starter_plan",
    "draft_plan_from_issue",
    "draft_plan_from_project",
    "get_plan",
    "lab_home_status",
    "home_checklist_summary",
    "coverage_hud_summary",
    "manager_hud_summary",
    "release_hud_summary",
    "tester_hud_summary",
    "list_plans",
    "plan_coverage_gaps",
    "plan_traceability_matrix",
    "plans_dir",
    "reorder_cases",
    "run_cases_by_tag",
    "select_cases_for_tag",
    "suite_flake_report",
    "update_case",
    "upsert_jira_snapshot",
    "WELL_KNOWN_TAGS",
]
