"""Run a single plan case with Playwright headed and record evidence (KAN-137).

Only the requested case runs. Disabled or archived cases are refused.
Tool/browser failures are recorded as fail or error — never pass.
Optional pause-on-fail keeps the headed browser open until continue/stop (KAN-149).
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from plans.store import add_run, get_plan
from plugins.playwright_steps import generate_steps_from_spec
from settings.connection_health import _check_target


def _last_run_summary(case: dict[str, Any]) -> str | None:
    runs = list(case.get("runs") or [])
    if not runs:
        return None
    last = runs[-1]
    res = str(last.get("result") or "pending")
    dur = last.get("duration_ms")
    parts = [res]
    if dur is not None:
        parts.append(f"{dur}ms")
    fc = last.get("failure_class")
    if fc:
        parts.append(fc)
    shot = _screenshot_path(last)
    if shot:
        parts.append(shot)
    return " · ".join(parts)


def _screenshot_path(run: dict[str, Any]) -> str | None:
    for item in run.get("evidence") or []:
        text = str(item)
        if text.lower().endswith(".png"):
            return text
    return None


def _case_spec(case: dict[str, Any]) -> str:
    parts = [
        str(case.get("name") or "").strip(),
        str(case.get("note") or "").strip(),
    ]
    src = case.get("source") if isinstance(case.get("source"), dict) else {}
    ref = str(src.get("ref") or "").strip()
    if ref:
        parts.append(ref)
    jira = str(case.get("jira_key") or "").strip()
    if jira:
        parts.append(f"Jira {jira}")
    return "\n".join(p for p in parts if p)


def _map_playwright_result(pw: dict[str, Any]) -> tuple[str, str | None, list[str]]:
    """Map runner output to plan run result + failure_class + evidence paths."""
    status = str(pw.get("status") or "fail").lower()
    err = (pw.get("error") or "").strip()
    evidence: list[str] = []
    screenshot = pw.get("screenshot")
    if screenshot:
        evidence.append(str(screenshot))
    report = pw.get("report_json")
    if report:
        evidence.append(str(report))
    for item in pw.get("evidence") or []:
        if isinstance(item, dict) and item.get("path"):
            path = str(item["path"])
            if path not in evidence:
                evidence.append(path)

    if err and ("invalid" in err.lower() or "rejected" in err.lower() or "steps" in err.lower()):
        return "error", "tool", evidence

    if status == "pass" and not err:
        return "pass", None, evidence

    classification = None
    steps = pw.get("steps") or []
    if isinstance(steps, list):
        for step in reversed(steps):
            if isinstance(step, dict) and step.get("classification"):
                classification = str(step["classification"])
                break
    failure_class = classification or ("environment" if "timeout" in err.lower() else "product_bug")
    if status == "fail":
        return "fail", failure_class, evidence
    return "error", failure_class or "tool", evidence


def _resolve_case(
    plan_id: str,
    case_id: str,
    *,
    level: str,
) -> dict[str, Any]:
    loaded = get_plan(plan_id, level=level)
    if loaded.get("status") != "ok":
        return loaded

    plan = loaded["plan"]
    cid = (case_id or "").strip()
    cases = list((plan.get("suite") or {}).get("cases") or [])
    target_case: dict[str, Any] | None = None
    for case in cases:
        if case.get("id") == cid:
            target_case = case
            break
    if target_case is None:
        return {
            "status": "error",
            "error": "case_not_found",
            "message": f"Case {cid!r} was not found on plan {plan_id!r}.",
            "security_level": level,
        }
    if not target_case.get("enabled", True):
        return {
            "status": "error",
            "error": "case_disabled",
            "message": "Disabled cases are not executed.",
            "security_level": level,
            "case_id": cid,
        }
    if target_case.get("archived"):
        return {
            "status": "error",
            "error": "case_archived",
            "message": "Archived cases are not executed.",
            "security_level": level,
            "case_id": cid,
        }
    return {
        "status": "ok",
        "plan": plan,
        "case": target_case,
        "security_level": level,
    }


async def _execute_case(
    plan_id: str,
    case_id: str,
    *,
    level: str,
    session_id: str,
    pause_on_fail: bool = False,
    pause_decision: Callable[[dict[str, Any]], Awaitable[str]] | None = None,
) -> dict[str, Any]:
    from settings.store import load_settings

    resolved = _resolve_case(plan_id, case_id, level=level)
    if resolved.get("status") != "ok":
        return resolved

    target_case = resolved["case"]
    cid = target_case["id"]
    target_url = (load_settings().get("target_url") or "").strip()
    target_probe = _check_target()
    started = time.monotonic()

    if not target_url or not target_probe.get("up"):
        msg = target_probe.get("message") or "Target URL is not configured or unreachable."
        duration_ms = int((time.monotonic() - started) * 1000)
        recorded = add_run(
            plan_id,
            cid,
            result="error",
            duration_ms=duration_ms,
            failure_class="environment",
            evidence=[],
            note=msg[:500],
            level=level,
        )
        return {
            "status": "ok",
            "message": msg,
            "security_level": level,
            "playwright_mode": "headed",
            "target_up": False,
            "only_case_id": cid,
            "pause_on_fail": bool(pause_on_fail),
            "plan": recorded.get("plan"),
            "case": recorded.get("case"),
            "run": recorded.get("run"),
        }

    from plugins.playwright_runner import run_playwright

    spec = _case_spec(target_case)
    generated = generate_steps_from_spec(spec, url=target_url)
    steps = list(generated.get("steps") or [])
    url = target_url or str(generated.get("url") or "")

    pw = await run_playwright(
        url=url,
        mode="run",
        steps=steps,
        security_level=level,
        request_text=spec,
        session_id=session_id,
        headless=False,
        reject_incomplete=False,
        pause_on_fail=bool(pause_on_fail),
        pause_decision=pause_decision if pause_on_fail else None,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class, evidence = _map_playwright_result(pw)
    if pw.get("error") and result == "pass":
        result = "fail"

    note = str(pw.get("error") or "")[:500]
    if pw.get("pause_decision") == "stop" and not note:
        note = "Stopped after pause on fail."
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        level=level,
    )
    run_id = (recorded.get("run") or {}).get("id")
    if result in {"fail", "error"} and run_id:
        from plans.evidence_bundle import write_failure_bundle
        from plans.store import append_run_evidence

        bundle = write_failure_bundle(
            run_id=run_id,
            plan_id=plan_id,
            case_id=cid,
            playwright=pw,
        )
        extra = [p for p in bundle.get("paths") or [] if p not in evidence]
        if extra:
            recorded = append_run_evidence(plan_id, cid, run_id, extra, level=level)
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": pw.get("playwright_mode") or "headed",
        "target_up": True,
        "only_case_id": cid,
        "pause_on_fail": bool(pause_on_fail),
        "pause_decision": pw.get("pause_decision"),
        "playwright": {
            "status": pw.get("status"),
            "error": pw.get("error"),
            "screenshot": pw.get("screenshot"),
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


async def run_single_case(
    plan_id: str,
    case_id: str,
    *,
    level: str | None = None,
    session_id: str = "plan-run",
    pause_on_fail: bool = False,
) -> dict[str, Any]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    if not pause_on_fail:
        return await _execute_case(
            plan_id,
            case_id,
            level=lvl,
            session_id=session_id,
            pause_on_fail=False,
        )

    from plans.pause_session import (
        create_session,
        make_pause_waiter,
        wait_until_paused_or_done,
    )

    session = create_session(plan_id, case_id, level=lvl)
    pause_decision = await make_pause_waiter(session)

    async def _job() -> None:
        try:
            payload = await _execute_case(
                plan_id,
                case_id,
                level=lvl,
                session_id=session_id,
                pause_on_fail=True,
                pause_decision=pause_decision,
            )
            session.result_payload = payload
            session.message = payload.get("message") or "Run finished."
        except Exception as exc:  # noqa: BLE001 — surface to session
            session.result_payload = {
                "status": "error",
                "error": "run_failed",
                "message": str(exc)[:500],
                "pause_id": session.id,
                "security_level": lvl,
            }
            session.message = str(exc)[:500]
        finally:
            session.state = "done"
            session.state_event.set()

    asyncio.create_task(_job())
    return await wait_until_paused_or_done(session)


def case_detail(plan: dict[str, Any], case_id: str) -> dict[str, Any]:
    """Case view payload: sources + last run (KAN-141 / A9)."""
    cid = (case_id or "").strip()
    for case in (plan.get("suite") or {}).get("cases") or []:
        if case.get("id") != cid:
            continue
        src = case.get("source") if isinstance(case.get("source"), dict) else {}
        kind = str(src.get("kind") or "manual-draft")
        return {
            "status": "ok",
            "case_id": cid,
            "name": case.get("name"),
            "jira_key": case.get("jira_key") or "",
            "source_kind": kind,
            "source_ref": src.get("ref") or "",
            "manual_draft": kind == "manual-draft" and not (case.get("jira_key") or "").strip(),
            "last_run": (case.get("runs") or [])[-1] if case.get("runs") else None,
            "last_run_summary": _last_run_summary(case),
            "case": case,
        }
    return {"status": "error", "error": "case_not_found", "message": f"Case {cid!r} not found."}
