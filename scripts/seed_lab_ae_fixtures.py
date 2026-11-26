"""Seed Lab/Primary fixtures for KAN-366 A–E human confirm. No secrets.

Writes absolute Suites path into settings (playwright_suite_path) and expands
%LOCALAPPDATA% forms. Start desktop_app.py first.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins.heal_policy import HealProposal, evaluate_and_log  # noqa: E402
from plugins import multi_sandbox as ms  # noqa: E402
from plugins.playwright_suite import set_suite_path  # noqa: E402

BASE = "http://127.0.0.1:8765"
SUITE_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "ai_testing_app"
    / "fixtures"
    / "kan366_suite"
)


def _wait_health(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE}/health", timeout=2.0)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError("API not healthy — start desktop_app.py first")


def seed_heal() -> dict:
    decision = evaluate_and_log(
        HealProposal(
            kind="locator",
            original='page.locator("#login")',
            proposed='page.get_by_role("button", name="Log in")',
            classification="test_defect",
            evidence={
                "original": 'page.locator("#login")',
                "proposed": 'page.get_by_role("button", name="Log in")',
                "action": "locator_swap",
            },
        )
    )
    pending = httpx.get(f"{BASE}/api/heal/proposals", timeout=10.0).json()
    first = (pending.get("pending") or [{}])[0]
    return {
        "decision_allowed": decision.allowed,
        "pending_count": pending.get("count"),
        "first_id": first.get("id"),
    }


def seed_sandbox() -> dict:
    httpx.post(
        f"{BASE}/api/multi-sandbox-plugin",
        json={"plugin_multi_sandbox_enabled": True},
        timeout=10.0,
    )
    out = ms.upsert_sandbox(
        "kan366demo",
        label="KAN-366 A–E demo",
        url="https://example.local/aut",
    )
    listed = ms.list_configured_sandboxes(ensure_default=False)
    return {
        "upsert_ok": bool(out.get("ok", True)),
        "count": len(listed),
        "id": "kan366demo",
    }


def seed_manual() -> dict:
    r = httpx.post(
        f"{BASE}/api/manual-sessions/start",
        json={"charter": "KAN-366 Lab A–E density verify"},
        timeout=15.0,
    )
    data = r.json()
    sess = data.get("session") if isinstance(data.get("session"), dict) else {}
    sid = data.get("id") or data.get("session_id") or sess.get("id")
    if sid:
        httpx.post(
            f"{BASE}/api/manual-sessions/{sid}/notes",
            json={"text": "Seed note for occlusion confirm."},
            timeout=10.0,
        )
    return {"session_id": sid}


def seed_plan() -> dict:
    r = httpx.post(
        f"{BASE}/api/plans",
        json={
            "name": "KAN-366 A–E seed plan",
            "intent": "Lab occlusion verify fixtures",
        },
        timeout=15.0,
    )
    plan = r.json()
    nested = plan.get("plan") if isinstance(plan.get("plan"), dict) else {}
    pid = plan.get("id") or plan.get("plan_id") or nested.get("id")
    case: dict | None = None
    if pid:
        c = httpx.post(
            f"{BASE}/api/plans/{pid}/cases",
            json={"name": "KAN-366 seed case", "note": "Occlusion verify row"},
            timeout=15.0,
        )
        case = c.json() if c.status_code < 400 else {"error": c.text[:200]}
    return {"plan_id": pid, "case": case}


def seed_suite_folder() -> dict:
    """Absolute path + minimal Playwright project; persist into settings."""
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    (SUITE_DIR / "package.json").write_text(
        json.dumps(
            {
                "name": "kan366-suite",
                "private": True,
                "devDependencies": {"@playwright/test": "^1.40.0"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (SUITE_DIR / "playwright.config.ts").write_text(
        "import { defineConfig } from '@playwright/test';\n"
        "export default defineConfig({ testDir: '.' });\n",
        encoding="utf-8",
    )
    spec = SUITE_DIR / "kan366_demo.spec.ts"
    spec.write_text(
        "// KAN-366 seed suite\n"
        "import { test, expect } from '@playwright/test';\n"
        "test('kan366 seed login', async ({ page }) => {\n"
        "  await page.goto('https://example.local/');\n"
        "  await expect(page.getByRole('button', { name: 'Log in' })).toBeVisible();\n"
        "});\n",
        encoding="utf-8",
    )
    abs_path = str(SUITE_DIR.resolve())
    imported = set_suite_path(abs_path, confirm=True)
    listed = httpx.post(
        f"{BASE}/api/playwright-suite/list",
        json={"suite_path": abs_path},
        timeout=30.0,
    )
    list_body = listed.json() if listed.status_code < 500 else {"status_code": listed.status_code}
    return {
        "path": abs_path,
        "env_form": r"%LOCALAPPDATA%\ai_testing_app\fixtures\kan366_suite",
        "import": imported,
        "list": {
            "status": list_body.get("status"),
            "count": len(list_body.get("tests") or []),
            "message": list_body.get("message") or list_body.get("error"),
        },
    }


def main() -> int:
    _wait_health()
    summary = {
        "heal": seed_heal(),
        "sandbox": seed_sandbox(),
        "manual": seed_manual(),
        "plan": seed_plan(),
        "suite": seed_suite_folder(),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
