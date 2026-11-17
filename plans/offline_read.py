"""Read last plan while Jira is down (KAN-201 / E5 / FR-CONN-1 + FR-PLAN-1).

Search and the traceability matrix stay on local stored keys and results.
Network (Jira) actions are listed as disabled with a reason when Jira is down.
Stored snapshots and run results are labelled with their fetch / finish time.
Writing to Jira while offline is out of scope for this slice.
"""
from __future__ import annotations

from typing import Any

from plans.store import get_plan, _normalize_jira_snapshots
from settings.degraded import degraded_status

# UI / API ids for Jira-dependent controls (desktop matches these).
NETWORK_ACTIONS: list[dict[str, str]] = [
    {
        "id": "draft_from_story",
        "label": "Draft from story",
        "reason_when_down": "Needs a live Jira read — use the last saved plan instead.",
    },
    {
        "id": "draft_from_project",
        "label": "Draft from project",
        "reason_when_down": "Needs a live Jira project list — search and matrix stay on stored keys.",
    },
    {
        "id": "acceptance_drift_check",
        "label": "Check acceptance drift",
        "reason_when_down": "Needs a live Jira re-read — open the matrix on last stored AC.",
    },
    {
        "id": "acceptance_drift_refresh",
        "label": "Refresh drafts from Jira",
        "reason_when_down": "Needs a live Jira re-read — prior cases and runs stay local.",
    },
    {
        "id": "read_jira_issue",
        "label": "Read Jira story",
        "reason_when_down": "Needs a live Jira read — use stored snapshots labelled with fetch time.",
    },
    {
        "id": "jira_write",
        "label": "Write to Jira",
        "reason_when_down": "Writing to Jira while offline is not supported.",
    },
]


def _run_sort_key(run: dict[str, Any]) -> str:
    return str(run.get("finished_at") or run.get("started_at") or "")


def _latest_run(case: dict[str, Any]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_key = ""
    for run in case.get("runs") or []:
        if not isinstance(run, dict):
            continue
        key = _run_sort_key(run)
        if best is None or key >= best_key:
            best = run
            best_key = key
    return best


def _snapshot_times(plan: dict[str, Any]) -> dict[str, str]:
    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    return {
        key: str(val.get("captured_at") or "").strip()
        for key, val in snaps.items()
        if str(val.get("captured_at") or "").strip()
    }


def label_fetch_time(*, snapshot_at: str = "", result_at: str = "") -> str:
    """Human label preferring snapshot capture, then last result finish time."""
    snap = (snapshot_at or "").strip()
    result = (result_at or "").strip()
    if snap and result and snap != result:
        return f"fetched {snap}; result {result}"
    if snap:
        return f"fetched {snap}"
    if result:
        return f"result {result}"
    return "fetch time unknown"


def annotate_trace_rows(plan: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach snapshot / result times to matrix rows (local only)."""
    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = suite.get("cases") if isinstance(suite.get("cases"), list) else []
    by_key: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        key = str(case.get("jira_key") or "").strip().upper()
        if key:
            by_key.setdefault(key, []).append(case)

    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("story_key") or "").strip().upper()
        snap = snaps.get(key) or {}
        snapshot_at = str(snap.get("captured_at") or "").strip()
        # Prefer snapshot summary when local case name is empty.
        summary = str(row.get("summary") or "").strip()
        if not summary and snap.get("summary"):
            summary = str(snap.get("summary") or "")[:240]

        result_at = ""
        for case in by_key.get(key) or []:
            run = _latest_run(case)
            if run:
                stamp = _run_sort_key(run)
                if stamp and stamp >= result_at:
                    result_at = stamp

        annotated = {
            **row,
            "summary": summary,
            "snapshot_captured_at": snapshot_at or None,
            "result_at": result_at or None,
            "fetch_time_label": label_fetch_time(
                snapshot_at=snapshot_at, result_at=result_at
            ),
        }
        out.append(annotated)
    return out


def annotate_search_hits(
    hits: list[dict[str, Any]],
    *,
    level: str | None = None,
) -> list[dict[str, Any]]:
    """Attach fetch-time labels to search hits from stored plans (local only)."""
    cache: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        plan_id = str(hit.get("plan_id") or "").strip()
        plan: dict[str, Any] | None = None
        if plan_id:
            if plan_id not in cache:
                loaded = get_plan(plan_id, level=level)
                cache[plan_id] = (
                    loaded.get("plan")
                    if loaded.get("status") == "ok" and isinstance(loaded.get("plan"), dict)
                    else {}
                )
            plan = cache.get(plan_id) or {}

        snapshot_at = ""
        result_at = ""
        jira_key = str(hit.get("jira_key") or "").strip().upper()
        if plan and jira_key:
            snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
            snap = snaps.get(jira_key) or {}
            snapshot_at = str(snap.get("captured_at") or "").strip()

        case_id = str(hit.get("case_id") or "").strip()
        if plan and case_id:
            suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
            for case in suite.get("cases") or []:
                if not isinstance(case, dict):
                    continue
                if str(case.get("id") or "").strip() != case_id:
                    continue
                run = _latest_run(case)
                if run:
                    result_at = _run_sort_key(run)
                break

        out.append(
            {
                **hit,
                "snapshot_captured_at": snapshot_at or None,
                "result_at": result_at or None,
                "fetch_time_label": label_fetch_time(
                    snapshot_at=snapshot_at, result_at=result_at
                ),
            }
        )
    return out


def network_actions_for(*, jira_up: bool) -> list[dict[str, Any]]:
    """List Jira network actions with enabled flag and explanation when down."""
    rows: list[dict[str, Any]] = []
    for action in NETWORK_ACTIONS:
        enabled = bool(jira_up)
        rows.append(
            {
                "id": action["id"],
                "label": action["label"],
                "enabled": enabled,
                "reason": "" if enabled else action["reason_when_down"],
            }
        )
    return rows


def offline_read_status(*, probe: bool = True) -> dict[str, Any]:
    """Status for E5: local search/matrix work; network actions gated on Jira."""
    snap = degraded_status() if probe else {
        "jira_up": False,
        "messages": {"jira": "Jira probe skipped."},
        "security_level": None,
        "plans_available": True,
    }
    jira_up = bool(snap.get("jira_up"))
    offline = not jira_up
    jira_msg = ""
    if isinstance(snap.get("messages"), dict):
        jira_msg = str(snap["messages"].get("jira") or "").strip()
    if offline and not jira_msg:
        jira_msg = "Jira is unavailable — search and matrix use last stored keys and results."

    actions = network_actions_for(jira_up=jira_up)
    disabled = [a for a in actions if not a.get("enabled")]
    if offline:
        message = (
            jira_msg
            + " Network actions are disabled. Stored results show fetch time. "
            "Writing to Jira while offline is not supported."
        )
    else:
        message = "Jira is reachable. Search and matrix still use local stored keys and results."

    return {
        "status": "ok",
        "jira_available": jira_up,
        "offline": offline,
        "search_works_offline": True,
        "matrix_works_offline": True,
        "jira_write_while_offline": False,
        "plans_available": True,
        "security_level": snap.get("security_level"),
        "network_actions": actions,
        "network_actions_disabled": disabled,
        "message": message.strip(),
        "degraded": snap if probe else None,
    }


def offline_plan_view(plan_id: str, *, level: str | None = None) -> dict[str, Any]:
    """Open one plan for offline reading: keys, snapshots, last results + fetch times."""
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    status = offline_read_status(probe=True)
    snaps = _normalize_jira_snapshots(plan.get("jira_snapshots"))
    suite = plan.get("suite") if isinstance(plan.get("suite"), dict) else {}
    cases = [c for c in (suite.get("cases") or []) if isinstance(c, dict)]

    keys: list[str] = []
    sources = plan.get("sources") if isinstance(plan.get("sources"), dict) else {}
    for raw in sources.get("jira_keys") or []:
        key = str(raw or "").strip().upper()
        if key and key not in keys:
            keys.append(key)
    for case in cases:
        key = str(case.get("jira_key") or "").strip().upper()
        if key and key not in keys:
            keys.append(key)

    stored: list[dict[str, Any]] = []
    for key in keys:
        snap = snaps.get(key) or {}
        matching = [
            c for c in cases if str(c.get("jira_key") or "").strip().upper() == key
        ]
        result = "not_loaded"
        result_at = ""
        case_id = None
        for case in matching:
            run = _latest_run(case)
            if run:
                stamp = _run_sort_key(run)
                if stamp >= result_at:
                    result_at = stamp
                    result = str(run.get("result") or "pending").strip().lower() or "pending"
                    case_id = str(case.get("id") or "") or None
            elif case_id is None and case.get("id"):
                case_id = str(case.get("id"))
        snapshot_at = str(snap.get("captured_at") or "").strip()
        stored.append(
            {
                "jira_key": key,
                "summary": str(snap.get("summary") or "")[:240]
                or (str((matching[0] or {}).get("name") or "")[:240] if matching else ""),
                "case_count": len(matching),
                "last_result": result,
                "case_id": case_id,
                "snapshot_captured_at": snapshot_at or None,
                "result_at": result_at or None,
                "fetch_time_label": label_fetch_time(
                    snapshot_at=snapshot_at, result_at=result_at
                ),
            }
        )

    return {
        "status": "ok",
        "plan_id": plan.get("id"),
        "plan_name": plan.get("name"),
        "security_level": loaded.get("security_level"),
        "offline": status["offline"],
        "jira_available": status["jira_available"],
        "search_works_offline": True,
        "matrix_works_offline": True,
        "jira_write_while_offline": False,
        "network_actions": status["network_actions"],
        "network_actions_disabled": status["network_actions_disabled"],
        "stored_keys": stored,
        "stored_key_count": len(stored),
        "message": status["message"],
    }
