# Daily test-all loop (OPERATE)

**Purpose:** One golden path a colleague can watch start-to-finish on a **home PC**.  
**Maturity:** Prototype coherence milestone — not enterprise-complete.

## Home-PC AUT (not company browser)

This project runs on the Designer’s **home computer**. There is **no** employer browser AUT available.

**Golden-path AUT = local demo target:**

1. **Preferred:** repo fixture `fixtures/operate_demo/` served by the desktop app at
   `http://127.0.0.1:8765/demo-aut/` (KAN-377). Marker: `data-operate-demo-aut="1"`.
2. Optional **Jira project KAN** for ticket-bound draft / bug flows (same site already used for product backlog) — this is **lab dogfood**, not “testing the company product.”
3. Never require VPN or employer credentials.

“Self-dogfood KAN” meant: use **this lab’s Jira + a local AUT**, not your workplace app.

## Exact start commands (home PC)

From `D:\Projects\ai_testing_app` (or your clone):

```powershell
# 1) Seed OFFICIAL target_url + plan "OPERATE golden path" (idempotent)
.\venv\Scripts\python.exe scripts\seed_operate_demo.py

# 2) Native product window (serves /demo-aut/ and the desktop shell)
.\venv\Scripts\python.exe desktop_app.py
```

After seed + app start:

- Settings → confirm **target URL** is `http://127.0.0.1:8765/demo-aut/` (OFFICIAL).
- Plans → open **OPERATE golden path**.
- Run the **smoke** case — **expected pass** (page shows “Operate Demo AUT”).
- For open-trace: run **Intentional fail: missing banner text** — **expected fail** (missing text on purpose), then case detail → Open Playwright Trace / Reveal / Copy path.
- If both cases show `Target timed out` / failure class `environment`, restart `desktop_app.py` (local demo AUT must be served by the same app; nested self-probe was fixed in KAN-494).

Do **not** open the desktop shell URL in a browser tab as the product; use `desktop_app.py`.

## Golden path (pass criteria)

1. **Connect** — Settings health: Ollama reachable; target URL set to the local demo AUT above; security level OFFICIAL (re-walk SECRET later).
2. **Plan** — Seeded OPERATE golden path (or starter / draft from KAN capped / Documents); open **Plans → Cases**.
3. **Run** — Run one `smoke`-tagged case (or single case) headed Playwright against the demo AUT.
4. **Fail usefully** — Run the intentional-fail case (or force a failing step); case detail shows screenshot + **Open Playwright trace** (path / reveal / `playwright show-trace`) — not text-only.
5. **Triage** — Set failure class; open heal pending **or** preview defect packet (confirm-gated; no silent Jira).
6. **Report** — Export / open Reports library entry for the run (markdown baseline until REP-CHARTS lands).

**Pass:** ~15-minute human walkthrough on OFFICIAL + pytest on evidence/open-trace / demo-AUT seed paths.  
**Fail:** Soft-pass on “opened orb home”; missing trace affordance; Jira write without confirm; requiring employer AUT.

## Out of scope for OPERATE

Voice (KAN-81), FR-MAN-2 live circles, full CI sync, H3 network share, embedded Trace Viewer SPA, theme/orb/home restyle, ISO27001 certification claim.

## Follow-on (after OPERATE)

Loop-hit polish only where the path touches: Plans Run disclosure, Manual idle layout, light evidence affordance (**OPERATE-3**).  

**CR 2026-11-27 (Council+Studio+Creative agreed):** deeper **readable step-by-step run narrative + pass/fail evidence gallery** (FR-TEST-4 / FR-PLAN-4) — Studio Slice-0 then Build after OPERATE-3; see `docs/ops/CR_RUN_EVIDENCE_UX_KEYS.json`. Not absorbed into OPERATE-3.  

Then CR backlog: Reports charts, floating Manual snip, Documents demo pack, stub deepen + fixtures, compliance design (ISO27001 etc.).
