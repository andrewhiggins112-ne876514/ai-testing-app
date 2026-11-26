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
    from plans.known_issue import is_known_labelled

    runs = list(case.get("runs") or [])
    if not runs:
        return None
    last = runs[-1]
    res = str(last.get("result") or "pending")
    dur = last.get("duration_ms")
    parts = [res]
    if dur is not None:
        parts.append(f"{dur}ms")
    if last.get("mock"):
        parts.append("mock")
    if is_known_labelled(last) or is_known_labelled(case):
        parts.append("known")
    else:
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
    trace = pw.get("trace")
    if trace:
        evidence.append(str(trace))
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
    from plans.timeouts import is_timeout_error

    failure_class = classification or (
        "environment" if is_timeout_error(err) else "product_bug"
    )
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
    from plans.quarantine import is_actively_quarantined, quarantine_status

    if is_actively_quarantined(target_case):
        q = quarantine_status(target_case)
        return {
            "status": "error",
            "error": "case_quarantined",
            "message": (
                "Quarantined cases are skipped (not counted as pass). "
                f"Reason: {q.get('reason') or 'quarantine'}; "
                f"expires {q.get('expires_at') or '—'}."
            ),
            "security_level": level,
            "case_id": cid,
            "quarantine": q,
            "counted_as_pass": False,
        }
    return {
        "status": "ok",
        "plan": plan,
        "case": target_case,
        "security_level": level,
    }


def _source_kind(case: dict[str, Any]) -> str:
    src = case.get("source") if isinstance(case.get("source"), dict) else {}
    return str(src.get("kind") or "manual-draft").strip().lower()


def _map_suite_result(suite_out: dict[str, Any]) -> tuple[str, str | None, list[str]]:
    """Map playwright_suite.run_suite output to plan run result."""
    status = str(suite_out.get("status") or "fail").lower()
    evidence: list[str] = []
    for item in suite_out.get("evidence") or []:
        text = str(item)
        if text and text not in evidence:
            evidence.append(text)
    err = (suite_out.get("error") or suite_out.get("message") or "").strip()
    if status == "pass":
        return "pass", None, evidence
    if "npx" in err.lower() or "not found" in err.lower() or "timed out" in err.lower():
        return "error", "environment", evidence
    if status == "fail":
        return "fail", "product_bug", evidence
    return "error", "tool", evidence


def _map_desktop_result(desk: dict[str, Any]) -> tuple[str, str | None, list[str]]:
    """Map desktop_runner output to plan run result + failure_class."""
    status = str(desk.get("status") or "fail").lower()
    err = (desk.get("error") or desk.get("message") or "").strip()
    if status == "pass":
        return "pass", None, []
    if status == "disabled":
        return "error", "tool", []
    low = err.lower()
    if (
        "no exe path" in low
        or "path not found" in low
        or "not a file" in low
        or "windows-only" in low
    ):
        return "error", "environment", []
    if status == "fail":
        return "fail", "product_bug", []
    return "error", "tool", []


def _map_api_result(api: dict[str, Any]) -> tuple[str, str | None]:
    """Map api_messaging_runner / contract_mock output to result + failure_class."""
    status = str(api.get("status") or "fail").lower()
    err = (api.get("error") or api.get("message") or "").strip()
    if status == "pass":
        return "pass", None
    low = err.lower()
    if (
        "no messaging/api endpoint" in low
        or "no host" in low
        or "invalid endpoint" in low
        or "unsupported endpoint scheme" in low
        or "timed out" in low
        or "timeout" in low
        or "name or service not known" in low
        or "getaddrinfo" in low
        or "connection refused" in low
        or "failed to establish" in low
        or "tcp connect" in low
        or "no port for scheme" in low
        or "mock fixture not found" in low
        or "no mock fixture" in low
        or "invalid mock fixture" in low
        or "mock fixture unreadable" in low
    ):
        return "error", "environment"
    if status == "fail":
        # HTTP status mismatch / 4xx/5xx — class like other product failures.
        return "fail", "product_bug"
    return "error", "tool"


async def _execute_api_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
) -> dict[str, Any]:
    """Run one API/messaging case via api_messaging_runner or local mock (G3)."""
    from plans.api_case import parse_api_ref, write_api_evidence
    from plugins.api_messaging_runner import run_api_check
    from plugins.contract_mock import run_mock_response
    from plans.timeouts import case_step_timeout_ms
    from settings.store import load_settings

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    parsed = parse_api_ref(str(src.get("ref") or ""))
    mock_fixture = str(parsed.get("mock_fixture") or "").strip()
    settings = load_settings()
    endpoint = (parsed.get("endpoint") or "").strip() or str(
        settings.get("api_endpoint") or ""
    ).strip()
    timeout_ms = case_step_timeout_ms(target_case)
    timeout_s = max(0.5, min(float(timeout_ms) / 1000.0, 60.0))

    if mock_fixture:
        # Mocks only when the case selects one — no live call.
        api = await asyncio.to_thread(
            run_mock_response,
            fixture=mock_fixture,
            expect_status=parsed.get("expect_status"),
            method=str(parsed.get("method") or "GET"),
            level=level,
        )
        runner = "contract_mock"
        used_mock = True
    else:
        api = await asyncio.to_thread(
            run_api_check,
            endpoint=endpoint,
            method=str(parsed.get("method") or "GET"),
            timeout_s=timeout_s,
            expect_status=parsed.get("expect_status"),
            body=parsed.get("body"),
        )
        runner = "api_messaging_runner"
        used_mock = False

    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class = _map_api_result(api)
    evidence = write_api_evidence(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        api=api,
    )
    note_parts = []
    if used_mock:
        note_parts.append("mock")
        if api.get("fixture"):
            note_parts.append(f"fixture={api.get('fixture')}")
    note_parts.append(str(api.get("message") or api.get("error") or ""))
    note_parts.append(f"body={api.get('body_summary') or ''}"[:400])
    note = " | ".join(p for p in note_parts if p)[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        mock=used_mock,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": None,
        "target_up": bool(endpoint) if not used_mock else True,
        "only_case_id": cid,
        "runner": runner,
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "api": {
            "status": api.get("status"),
            "error": api.get("error"),
            "http_status": api.get("http_status"),
            "endpoint_label": api.get("endpoint_label"),
            "redaction_hits": api.get("redaction_hits"),
            "body_summary": api.get("body_summary"),
            "plugin": api.get("plugin") or runner,
            "mock": used_mock,
            "fixture": api.get("fixture"),
            "transport": api.get("transport"),
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


async def _execute_desktop_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
) -> dict[str, Any]:
    """Run one desktop-typed case via desktop_runner (not Playwright)."""
    from plans.desktop_case import parse_desktop_ref, write_desktop_evidence
    from plugins.desktop_runner import run_desktop
    from plans.timeouts import case_step_timeout_ms
    from settings.store import load_settings

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    parsed = parse_desktop_ref(str(src.get("ref") or ""))
    settings = load_settings()
    exe_path = (parsed.get("exe_path") or "").strip() or str(
        settings.get("target_app_path") or ""
    ).strip()
    steps = parsed.get("steps")
    timeout_ms = case_step_timeout_ms(target_case)
    timeout_s = max(0.5, min(float(timeout_ms) / 1000.0, 120.0))

    desk = await asyncio.to_thread(
        run_desktop,
        exe_path=exe_path,
        timeout_s=timeout_s,
        steps=steps,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class, _ = _map_desktop_result(desk)
    evidence = write_desktop_evidence(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        desktop=desk,
    )
    note = str(desk.get("error") or desk.get("message") or desk.get("logs") or "")[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": None,
        "target_up": bool(exe_path),
        "only_case_id": cid,
        "runner": "desktop_runner",
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "desktop": {
            "status": desk.get("status"),
            "error": desk.get("error"),
            "exe_path": desk.get("exe_path"),
            "plugin": desk.get("plugin") or "desktop_runner",
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


def _map_seed_result(seed: dict[str, Any]) -> tuple[str, str | None]:
    """Map seed_fixture output to plan run result + failure_class."""
    status = str(seed.get("status") or "fail").lower()
    cls = str(seed.get("classification") or "").strip().lower() or None
    err = str(seed.get("error") or seed.get("message") or "").lower()
    if status == "pass":
        return "pass", None
    if cls == "environment" or any(
        needle in err
        for needle in (
            "seed fixture not found",
            "no seed fixture",
            "invalid seed fixture",
            "seed fixture unreadable",
            "seed fixture name required",
            "no silent injection",
        )
    ):
        return "error", "environment"
    if status == "fail":
        return "fail", cls or "product_bug"
    return "error", cls or "tool"


async def _execute_seed_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
) -> dict[str, Any]:
    """Run one seed/fixture case via seed_fixture plugin (KAN-223 / G4)."""
    from plans.seed_case import parse_seed_ref, write_seed_evidence
    from plugins.seed_fixture import apply_seed_fixture

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    parsed = parse_seed_ref(str(src.get("ref") or ""))
    fixture_name = str(parsed.get("fixture") or "").strip()
    steps = parsed.get("steps")

    seed = await asyncio.to_thread(
        apply_seed_fixture,
        fixture=fixture_name,
        steps=steps,
        level=level,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class = _map_seed_result(seed)
    evidence = write_seed_evidence(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        seed=seed,
    )
    stored_name = str(seed.get("fixture") or fixture_name or "").strip() or None
    note_parts = []
    if stored_name:
        note_parts.append(f"seed_fixture={stored_name}")
    note_parts.append(str(seed.get("message") or seed.get("error") or ""))
    note = " | ".join(p for p in note_parts if p)[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        seed_fixture=stored_name,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": None,
        "target_up": True,
        "only_case_id": cid,
        "runner": "seed_fixture",
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "seed": {
            "status": seed.get("status"),
            "error": seed.get("error"),
            "fixture": seed.get("fixture"),
            "plugin": seed.get("plugin") or "seed_fixture",
            "steps": seed.get("steps") or [],
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


async def _execute_framework_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
) -> dict[str, Any]:
    """Run one framework-selection case (KAN-233 / G9). Same run model."""
    from plans.framework_case import parse_framework_ref, write_framework_evidence
    from plugins.framework_switch import plan_run_result

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    parsed = parse_framework_ref(str(src.get("ref") or ""))
    fw = str(parsed.get("framework") or "playwright")

    fw_payload = await asyncio.to_thread(
        plan_run_result,
        framework=fw,
        action="run_case",
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    evidence = write_framework_evidence(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        framework_result=fw_payload,
    )
    result = str(fw_payload.get("result") or "error")
    # Hard guarantee: Selenium/Cypress never mark passed (G9 AC).
    if fw != "playwright" and result == "pass":
        result = "error"
        fw_payload = {
            **fw_payload,
            "result": "error",
            "passed": False,
            "failure_class": "tool",
        }
    failure_class = fw_payload.get("failure_class")
    if result != "pass" and not failure_class:
        failure_class = "tool"
    note = str(fw_payload.get("message") or "")[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class if result != "pass" else None,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        framework=fw,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": None,
        "target_up": True,
        "only_case_id": cid,
        "runner": "framework_switch",
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "framework": {
            "status": fw_payload.get("status"),
            "framework": fw,
            "implemented": bool(fw_payload.get("implemented")),
            "plugin": fw_payload.get("plugin") or "framework_switch",
            "message": fw_payload.get("message"),
            "passed": bool(fw_payload.get("passed")) and result == "pass",
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


def _map_visual_result(visual: dict[str, Any]) -> tuple[str, str | None]:
    """Map visual_baseline output to plan run result + failure_class."""
    status = str(visual.get("status") or "fail").lower()
    cls = str(visual.get("classification") or "").strip().lower() or None
    if status == "pass":
        return "pass", None
    if cls == "environment":
        return "error", "environment"
    if status == "fail":
        return "fail", cls or "product_bug"
    return "error", cls or "tool"


async def _execute_visual_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
    update_baseline: bool = False,
    current_path: str | None = None,
) -> dict[str, Any]:
    """Run one opt-in visual baseline case (KAN-225 / G5). One browser at a time."""
    from plans.visual_case import parse_visual_ref, write_visual_evidence
    from plugins.visual_baseline import apply_visual_baseline, capture_page_screenshot
    from settings.store import load_settings

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    parsed = parse_visual_ref(str(src.get("ref") or ""))
    baseline_name = str(parsed.get("baseline") or "").strip()
    page_url = str(parsed.get("url") or "").strip() or str(
        load_settings().get("target_url") or ""
    ).strip()

    shot_path = (current_path or "").strip() or None
    capture: dict[str, Any] | None = None
    if not shot_path:
        if not page_url:
            duration_ms = int((time.monotonic() - started) * 1000)
            visual = {
                "plugin": "visual_baseline",
                "status": "fail",
                "error": "No URL for visual capture.",
                "message": "No URL for visual capture.",
                "classification": "environment",
                "baseline": baseline_name or None,
                "matched": False,
                "updated": False,
            }
            evidence = write_visual_evidence(
                run_id=reserved_run_id,
                plan_id=plan_id,
                case_id=cid,
                visual=visual,
            )
            recorded = add_run(
                plan_id,
                cid,
                result="error",
                duration_ms=duration_ms,
                failure_class="environment",
                evidence=evidence,
                note=visual["error"],
                suite_run_id=suite_run_id,
                run_id=reserved_run_id,
                visual_baseline=baseline_name or None,
                level=level,
            )
            return {
                "status": "ok",
                "message": visual["error"],
                "security_level": level,
                "playwright_mode": None,
                "target_up": False,
                "only_case_id": cid,
                "runner": "visual_baseline",
                "pause_on_fail": False,
                "suite_run_id": suite_run_id,
                "visual": visual,
                "plan": recorded.get("plan"),
                "case": recorded.get("case"),
                "run": recorded.get("run"),
            }
        capture = await capture_page_screenshot(
            page_url,
            security_level=level,
            run_id=reserved_run_id,
            headless=True,
        )
        shot_path = str(capture.get("screenshot") or "").strip() or None
        if not shot_path:
            duration_ms = int((time.monotonic() - started) * 1000)
            err = str(capture.get("error") or "Visual capture failed.")[:500]
            visual = {
                "plugin": "visual_baseline",
                "status": "fail",
                "error": err,
                "message": err,
                "classification": "environment",
                "baseline": baseline_name or None,
                "matched": False,
                "updated": False,
            }
            evidence = write_visual_evidence(
                run_id=reserved_run_id,
                plan_id=plan_id,
                case_id=cid,
                visual=visual,
            )
            recorded = add_run(
                plan_id,
                cid,
                result="error",
                duration_ms=duration_ms,
                failure_class="environment",
                evidence=evidence,
                note=err,
                suite_run_id=suite_run_id,
                run_id=reserved_run_id,
                visual_baseline=baseline_name or None,
                level=level,
            )
            return {
                "status": "ok",
                "message": err,
                "security_level": level,
                "playwright_mode": (capture.get("playwright") or {}).get("playwright_mode"),
                "target_up": True,
                "only_case_id": cid,
                "runner": "visual_baseline",
                "one_browser": True,
                "pause_on_fail": False,
                "suite_run_id": suite_run_id,
                "visual": visual,
                "plan": recorded.get("plan"),
                "case": recorded.get("case"),
                "run": recorded.get("run"),
            }

    visual = await asyncio.to_thread(
        apply_visual_baseline,
        baseline=baseline_name,
        current_path=shot_path,
        update_baseline=bool(update_baseline),
        level=level,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class = _map_visual_result(visual)
    evidence = write_visual_evidence(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        visual=visual,
    )
    stored_name = str(visual.get("baseline") or baseline_name or "").strip() or None
    note_parts = []
    if stored_name:
        note_parts.append(f"visual_baseline={stored_name}")
    if update_baseline:
        note_parts.append("update_baseline=explicit")
    note_parts.append(str(visual.get("message") or visual.get("error") or ""))
    note = " | ".join(p for p in note_parts if p)[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        visual_baseline=stored_name,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": (
            (capture or {}).get("playwright") or {}
        ).get("playwright_mode")
        if capture
        else None,
        "target_up": True,
        "only_case_id": cid,
        "runner": "visual_baseline",
        "one_browser": True,
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "visual": {
            "status": visual.get("status"),
            "error": visual.get("error"),
            "baseline": visual.get("baseline"),
            "baseline_path": visual.get("baseline_path"),
            "current_path": visual.get("current_path"),
            "matched": visual.get("matched"),
            "updated": visual.get("updated"),
            "plugin": visual.get("plugin") or "visual_baseline",
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


async def _execute_playwright_imported_case(
    plan_id: str,
    target_case: dict[str, Any],
    *,
    level: str,
    suite_run_id: str | None,
    reserved_run_id: str,
    started: float,
) -> dict[str, Any]:
    """Run one imported Playwright case via npx (does not invent JSON steps)."""
    from plans.import_playwright import decode_playwright_ref
    from plugins.playwright_suite import run_suite

    cid = target_case["id"]
    src = target_case.get("source") if isinstance(target_case.get("source"), dict) else {}
    ref = decode_playwright_ref(str(src.get("ref") or ""))
    suite_path = ref.get("suite_path") or ""
    if not suite_path:
        duration_ms = int((time.monotonic() - started) * 1000)
        recorded = add_run(
            plan_id,
            cid,
            result="error",
            duration_ms=duration_ms,
            failure_class="tool",
            evidence=[],
            note="Imported Playwright case is missing suite_path in source ref.",
            suite_run_id=suite_run_id,
            run_id=reserved_run_id,
            level=level,
        )
        return {
            "status": "ok",
            "message": "Imported Playwright case is missing suite path.",
            "security_level": level,
            "playwright_mode": "headed",
            "target_up": True,
            "only_case_id": cid,
            "runner": "playwright_suite",
            "suite_run_id": suite_run_id,
            "plan": recorded.get("plan"),
            "case": recorded.get("case"),
            "run": recorded.get("run"),
        }

    suite_out = await asyncio.to_thread(
        run_suite,
        suite_path=suite_path,
        grep=ref.get("grep") or ref.get("title") or "",
        test_file=ref.get("file") or "",
        timeout_s=300.0,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class, evidence = _map_suite_result(suite_out)
    note = str(suite_out.get("error") or suite_out.get("message") or "")[:500]
    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_run_id,
        run_id=reserved_run_id,
        level=level,
    )
    return {
        "status": "ok",
        "message": f"Case {cid} finished: {result}.",
        "security_level": level,
        "playwright_mode": suite_out.get("playwright_mode") or "headed",
        "target_up": True,
        "only_case_id": cid,
        "runner": "playwright_suite",
        "pause_on_fail": False,
        "suite_run_id": suite_run_id,
        "playwright_suite": {
            "status": suite_out.get("status"),
            "error": suite_out.get("error"),
            "passed": suite_out.get("passed"),
            "failed": suite_out.get("failed"),
            "suite_path": suite_out.get("suite_path"),
        },
        "plan": recorded.get("plan"),
        "case": recorded.get("case"),
        "run": recorded.get("run"),
    }


async def _execute_case(
    plan_id: str,
    case_id: str,
    *,
    level: str,
    session_id: str,
    pause_on_fail: bool = False,
    pause_decision: Callable[[dict[str, Any]], Awaitable[str]] | None = None,
    suite_run_id: str | None = None,
    update_baseline: bool = False,
    current_path: str | None = None,
    sandbox_id: str | None = None,
) -> dict[str, Any]:
    from plans.sandbox_run import resolve_run_sandbox
    from plans.store import new_run_id
    from plugins.heal_policy import heal_run_context
    from settings.store import load_settings

    resolved = _resolve_case(plan_id, case_id, level=level)
    if resolved.get("status") != "ok":
        return resolved

    sandbox_res = resolve_run_sandbox(sandbox_id)
    if sandbox_res.get("status") != "ok":
        return {
            **sandbox_res,
            "security_level": level,
            "plan_id": plan_id,
            "case_id": (case_id or "").strip(),
        }
    sandbox_name = sandbox_res.get("sandbox_name")
    sandbox_profile = sandbox_res.get("profile_dir")
    sandbox_url = sandbox_res.get("url")

    target_case = resolved["case"]
    cid = target_case["id"]
    started = time.monotonic()
    suite_rid = (suite_run_id or "").strip() or None
    # Pre-allocate so locator heals during Playwright stamp this run (KAN-159).
    reserved_run_id = new_run_id()

    if _source_kind(target_case) == "playwright":
        return await _execute_playwright_imported_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
        )

    if _source_kind(target_case) == "desktop":
        return await _execute_desktop_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
        )

    if _source_kind(target_case) == "api":
        return await _execute_api_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
        )

    if _source_kind(target_case) == "seed":
        return await _execute_seed_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
        )

    if _source_kind(target_case) == "visual":
        return await _execute_visual_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
            update_baseline=bool(update_baseline),
            current_path=current_path,
        )

    if _source_kind(target_case) == "framework":
        return await _execute_framework_case(
            plan_id,
            target_case,
            level=level,
            suite_run_id=suite_rid,
            reserved_run_id=reserved_run_id,
            started=started,
        )

    # G9: settings-level Selenium/Cypress must not mark browser cases passed.
    from plugins.framework_switch import (
        DEFAULT_FRAMEWORK,
        get_framework,
        plan_run_result,
    )

    active_fw = get_framework()
    if active_fw != DEFAULT_FRAMEWORK:
        from plans.framework_case import write_framework_evidence

        fw_payload = plan_run_result(framework=active_fw, action="run_case")
        duration_ms = int((time.monotonic() - started) * 1000)
        evidence = write_framework_evidence(
            run_id=reserved_run_id,
            plan_id=plan_id,
            case_id=cid,
            framework_result=fw_payload,
        )
        note = str(fw_payload.get("message") or "")[:500]
        recorded = add_run(
            plan_id,
            cid,
            result=str(fw_payload.get("result") or "error"),
            duration_ms=duration_ms,
            failure_class=fw_payload.get("failure_class") or "tool",
            evidence=evidence,
            note=note,
            suite_run_id=suite_rid,
            run_id=reserved_run_id,
            framework=active_fw,
            level=level,
        )
        return {
            "status": "ok",
            "message": note or f"Framework {active_fw} is not implemented.",
            "security_level": level,
            "playwright_mode": None,
            "target_up": False,
            "only_case_id": cid,
            "runner": "framework_switch",
            "pause_on_fail": False,
            "suite_run_id": suite_rid,
            "framework": {
                "status": fw_payload.get("status"),
                "framework": active_fw,
                "implemented": False,
                "plugin": "framework_switch",
                "message": fw_payload.get("message"),
            },
            "plan": recorded.get("plan"),
            "case": recorded.get("case"),
            "run": recorded.get("run"),
        }

    # G8: sandbox URL overrides default target when the sandbox names one.
    settings_url = (load_settings().get("target_url") or "").strip()
    sandbox_url_s = str(sandbox_url or "").strip()
    target_url = sandbox_url_s or settings_url
    if sandbox_url_s and sandbox_url_s != settings_url:
        if not (
            sandbox_url_s.startswith("https://") or sandbox_url_s.startswith("http://")
        ):
            target_probe = {
                "up": False,
                "message": "Sandbox URL must start with http:// or https://.",
            }
        else:
            # Lightweight reachability for the named sandbox URL.
            try:
                import httpx

                with httpx.Client(timeout=httpx.Timeout(5.0, connect=3.0), follow_redirects=True) as client:
                    resp = client.get(sandbox_url_s)
                target_probe = {
                    "up": True,
                    "message": f"Sandbox URL reachable (HTTP {resp.status_code}).",
                }
            except Exception as exc:  # noqa: BLE001 — environment failure
                target_probe = {
                    "up": False,
                    "message": f"Sandbox URL unreachable: {str(exc)[:160]}",
                }
    else:
        target_probe = _check_target()

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
            suite_run_id=suite_rid,
            run_id=reserved_run_id,
            sandbox=sandbox_name,
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
            "suite_run_id": suite_rid,
            "sandbox": sandbox_name,
            "plan": recorded.get("plan"),
            "case": recorded.get("case"),
            "run": recorded.get("run"),
        }

    from plugins.playwright_runner import run_playwright
    from plans.timeouts import (
        case_step_timeout_ms,
        is_timeout_error,
        timeout_failure_message,
    )

    spec = _case_spec(target_case)
    generated = generate_steps_from_spec(spec, url=target_url)
    steps = list(generated.get("steps") or [])
    url = target_url or str(generated.get("url") or "")
    step_timeout_ms = case_step_timeout_ms(target_case)
    # Runner click_timeout is milliseconds; retry is half the budget (min 500).
    click_timeout = step_timeout_ms
    retry_timeout = max(500, step_timeout_ms // 2)

    with heal_run_context(
        run_id=reserved_run_id,
        plan_id=plan_id,
        case_id=cid,
        suite_run_id=suite_rid,
    ):
        pw = await run_playwright(
            url=url,
            mode="run",
            steps=steps,
            security_level=level,
            request_text=spec,
            session_id=session_id,
            headless=False,
            reject_incomplete=False,
            click_timeout=click_timeout,
            retry_timeout=retry_timeout,
            pause_on_fail=bool(pause_on_fail),
            pause_decision=pause_decision if pause_on_fail else None,
            profile_dir=sandbox_profile,
        )
    duration_ms = int((time.monotonic() - started) * 1000)
    result, failure_class, evidence = _map_playwright_result(pw)
    if pw.get("error") and result == "pass":
        result = "fail"

    raw_err = str(pw.get("error") or "")
    if is_timeout_error(raw_err):
        note = timeout_failure_message(raw_err, step_timeout_ms=step_timeout_ms)
        if failure_class not in {"tool"}:
            failure_class = failure_class or "environment"
    else:
        note = raw_err[:500]
    if pw.get("pause_decision") == "stop" and not note:
        note = "Stopped after pause on fail."

    # G6: optional a11y sidecar — attaches violations; never replaces functional result.
    from plans.a11y_case import case_has_a11y_check, write_a11y_evidence
    from plugins.accessibility_checks import run_accessibility_check

    a11y_payload: dict[str, Any] | None = None
    if case_has_a11y_check(target_case):
        a11y_out = await asyncio.to_thread(
            run_accessibility_check,
            url=url,
            opted_in=True,
        )
        a11y_paths = write_a11y_evidence(
            run_id=reserved_run_id,
            plan_id=plan_id,
            case_id=cid,
            a11y=a11y_out,
            functional_result=result,
        )
        for path in a11y_paths:
            if path not in evidence:
                evidence = list(evidence) + [path]
        vcount = int(a11y_out.get("violation_count") or 0)
        a11y_note = str(a11y_out.get("message") or "")
        if a11y_note:
            note = (f"{note} | a11y: {a11y_note}" if note else f"a11y: {a11y_note}")[:500]
        a11y_payload = {
            "checked": True,
            "opted_in": True,
            "status": a11y_out.get("status"),
            "violation_count": vcount,
            "violations": a11y_out.get("violations") or [],
            "error": a11y_out.get("error"),
            "message": a11y_out.get("message"),
            "replaces_functional": False,
        }
        # Functional result stays as mapped from Playwright (AC: does not replace).

    recorded = add_run(
        plan_id,
        cid,
        result=result,
        duration_ms=duration_ms,
        failure_class=failure_class,
        evidence=evidence,
        note=note,
        suite_run_id=suite_rid,
        run_id=reserved_run_id,
        sandbox=sandbox_name,
        a11y=a11y_payload,
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
        "suite_run_id": suite_rid,
        "sandbox": sandbox_name,
        "default_profile": bool(sandbox_res.get("default_profile")),
        "step_timeout_ms": step_timeout_ms,
        "playwright": {
            "status": pw.get("status"),
            "error": pw.get("error"),
            "screenshot": pw.get("screenshot"),
            "trace": pw.get("trace"),
            "browser_profile": pw.get("browser_profile"),
        },
        "a11y": a11y_payload,
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
    update_baseline: bool = False,
    current_path: str | None = None,
    sandbox_id: str | None = None,
) -> dict[str, Any]:
    from settings.store import get_security_level

    lvl = (level or get_security_level()).strip().upper()
    from plans.run_notify import attach_standalone_case_notice

    if not pause_on_fail:
        return attach_standalone_case_notice(
            await _execute_case(
                plan_id,
                case_id,
                level=lvl,
                session_id=session_id,
                pause_on_fail=False,
                update_baseline=bool(update_baseline),
                current_path=current_path,
                sandbox_id=sandbox_id,
            )
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
                update_baseline=bool(update_baseline),
                current_path=current_path,
                sandbox_id=sandbox_id,
                pause_decision=pause_decision,
            )
            session.result_payload = attach_standalone_case_notice(payload)
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
        from plans.api_case import parse_api_ref
        from plans.known_issue import is_known_labelled
        from plans.timeouts import case_step_timeout_ms

        last = (case.get("runs") or [])[-1] if case.get("runs") else None
        known = is_known_labelled(last) or is_known_labelled(case)
        from plans.quarantine import flake_score, quarantine_status

        flake = flake_score(case)
        qstat = quarantine_status(case)
        mock_fixture = ""
        seed_fixture = ""
        visual_baseline = ""
        framework = ""
        if kind == "api":
            mock_fixture = str(
                parse_api_ref(str(src.get("ref") or "")).get("mock_fixture") or ""
            ).strip()
        if kind == "seed":
            from plans.seed_case import parse_seed_ref

            seed_fixture = str(
                parse_seed_ref(str(src.get("ref") or "")).get("fixture") or ""
            ).strip()
        if kind == "visual":
            from plans.visual_case import parse_visual_ref

            visual_baseline = str(
                parse_visual_ref(str(src.get("ref") or "")).get("baseline") or ""
            ).strip()
        if kind == "framework":
            from plans.framework_case import parse_framework_ref

            framework = str(
                parse_framework_ref(str(src.get("ref") or "")).get("framework") or ""
            ).strip()
        if kind == "api":
            runner_name = "contract_mock" if mock_fixture else "api_messaging_runner"
        elif kind == "desktop":
            runner_name = "desktop_runner"
        elif kind == "seed":
            runner_name = "seed_fixture"
        elif kind == "visual":
            runner_name = "visual_baseline"
        elif kind == "framework":
            runner_name = "framework_switch"
        elif kind == "playwright":
            runner_name = "playwright_suite"
        else:
            runner_name = "playwright"
        return {
            "status": "ok",
            "case_id": cid,
            "name": case.get("name"),
            "note": case.get("note") or "",
            "jira_key": case.get("jira_key") or "",
            "tags": list(case.get("tags") or []),
            "priority": int(case.get("priority") or 0),
            "step_timeout_ms": case_step_timeout_ms(case),
            "enabled": bool(case.get("enabled", True)),
            "archived": bool(case.get("archived", False)),
            "quarantined": bool(qstat.get("quarantined")),
            "quarantine": qstat,
            "flake": flake,
            "flake_label": flake.get("flake_label"),
            "source_kind": kind,
            "source_ref": src.get("ref") or "",
            "manual_draft": kind == "manual-draft" and not (case.get("jira_key") or "").strip(),
            "desktop_case": kind == "desktop",
            "api_case": kind == "api",
            "seed_case": kind == "seed",
            "visual_case": kind == "visual",
            "framework_case": kind == "framework",
            "framework": framework,
            "mock_fixture": mock_fixture,
            "seed_fixture": seed_fixture,
            "visual_baseline": visual_baseline,
            "a11y_check": bool(case.get("a11y_check"))
            or any(
                str(t or "").strip().lower() in {"a11y", "accessibility"}
                for t in (case.get("tags") or [])
            ),
            "performance_budget_ms": case.get("performance_budget_ms"),
            "runner": runner_name,
            "last_run": last,
            "last_run_summary": _last_run_summary(case),
            "last_failure": flake.get("last_failure"),
            "tester_note": (last.get("tester_note") if isinstance(last, dict) else "") or "",
            "known_issue": case.get("known_issue")
            or (last.get("known_issue") if isinstance(last, dict) else None),
            "known_label": "known" if known else None,
            "run_count": len(case.get("runs") or []),
            "case": case,
        }
    return {"status": "error", "error": "case_not_found", "message": f"Case {cid!r} not found."}
