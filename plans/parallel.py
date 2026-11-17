"""Suite parallel cap (KAN-179 / D1 / FR-PLAN-2).

Default is sequential (parallel_count=1). This stage caps at 2 so headed
browsers do not stall the home PC. Suite run records store the count used;
requests above the cap are refused.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

# Visible stage cap — keep small on this PC (one headed browser default).
DEFAULT_PARALLEL = 1
MAX_PARALLEL = 2


def resolve_parallel_count(requested: Any = None) -> dict[str, Any]:
    """Validate parallel count. Default 1; refuse above MAX_PARALLEL."""
    if requested is None or requested == "":
        count = DEFAULT_PARALLEL
    else:
        try:
            count = int(requested)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "error": "parallel_invalid",
                "message": (
                    f"Parallel count must be an integer from {DEFAULT_PARALLEL} "
                    f"to {MAX_PARALLEL}."
                ),
                "parallel_max": MAX_PARALLEL,
                "parallel_default": DEFAULT_PARALLEL,
            }
    if count < 1:
        return {
            "status": "error",
            "error": "parallel_invalid",
            "message": (
                f"Parallel count must be at least 1 (sequential). "
                f"Got {count}."
            ),
            "parallel_max": MAX_PARALLEL,
            "parallel_default": DEFAULT_PARALLEL,
        }
    if count > MAX_PARALLEL:
        return {
            "status": "error",
            "error": "parallel_above_cap",
            "message": (
                f"Parallel count {count} is above the local cap of "
                f"{MAX_PARALLEL}. Lower it to {MAX_PARALLEL} or less."
            ),
            "parallel_max": MAX_PARALLEL,
            "parallel_default": DEFAULT_PARALLEL,
            "requested": count,
        }
    return {
        "status": "ok",
        "parallel_count": count,
        "sequential": count == 1,
        "parallel_max": MAX_PARALLEL,
        "parallel_default": DEFAULT_PARALLEL,
    }


def parallel_cap_info() -> dict[str, Any]:
    """Public cap values for UI / API."""
    return {
        "status": "ok",
        "parallel_default": DEFAULT_PARALLEL,
        "parallel_max": MAX_PARALLEL,
        "message": (
            f"Suite runs are sequential by default (parallel={DEFAULT_PARALLEL}). "
            f"Max parallel this stage: {MAX_PARALLEL}."
        ),
    }


async def map_cases_with_parallel(
    case_ids: list[str],
    parallel_count: int,
    run_one: Callable[[str], Awaitable[Any]],
) -> list[Any]:
    """Run ``run_one`` for each case id, capped at ``parallel_count`` workers.

    Preserves input order in the returned list. parallel_count=1 is sequential.
    """
    if not case_ids:
        return []
    workers = max(1, min(int(parallel_count), MAX_PARALLEL))
    if workers == 1:
        out: list[Any] = []
        for cid in case_ids:
            out.append(await run_one(cid))
        return out

    sem = asyncio.Semaphore(workers)
    results: list[Any] = [None] * len(case_ids)

    async def _wrapped(index: int, cid: str) -> None:
        async with sem:
            results[index] = await run_one(cid)

    await asyncio.gather(
        *(_wrapped(i, cid) for i, cid in enumerate(case_ids))
    )
    return list(results)
