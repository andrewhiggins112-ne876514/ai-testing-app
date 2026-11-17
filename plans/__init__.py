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
from plans.traceability import plan_traceability_matrix
from plans.starter import create_starter_plan, lab_home_status
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
    "add_case",
    "add_document_draft_cases",
    "add_run",
    "append_run_evidence",
    "cases_for_run",
    "check_acceptance_drift",
    "keep_acceptance_drafts",
    "refresh_acceptance_drafts",
    "set_known_issue_link",
    "set_plan_notes",
    "set_run_failure_class",
    "create_plan",
    "create_starter_plan",
    "draft_plan_from_issue",
    "draft_plan_from_project",
    "get_plan",
    "lab_home_status",
    "list_plans",
    "plan_coverage_gaps",
    "plan_traceability_matrix",
    "plans_dir",
    "reorder_cases",
    "update_case",
    "upsert_jira_snapshot",
]
