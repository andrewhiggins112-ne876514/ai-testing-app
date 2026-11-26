# Daily test-all loop (OPERATE)

**Purpose:** One golden path a colleague can watch start-to-finish on a **home PC**.  
**Maturity:** Prototype coherence milestone — not enterprise-complete.

## Home-PC AUT (not company browser)

This project runs on the Designer’s **home computer**. There is **no** employer browser AUT available.

**Golden-path AUT = local demo target:**

1. Prefer a **local fixture page** under the repo (seeded by OPERATE stories) or a public demo site the machine can open (e.g. Playwright’s demo / a static HTML served locally).
2. Optional **Jira project KAN** for ticket-bound draft / bug flows (same site already used for product backlog) — this is **lab dogfood**, not “testing the company product.”
3. Never require VPN or employer credentials.

“Self-dogfood KAN” meant: use **this lab’s Jira + a local AUT**, not your workplace app.

## Golden path (pass criteria)

1. **Connect** — Settings health: Ollama reachable; target URL set to the local demo AUT; security level OFFICIAL (re-walk SECRET later).
2. **Plan** — Starter plan or draft from KAN (capped) / from seeded Documents; open **Plans → Cases**.
3. **Run** — Run one `smoke`-tagged case (or single case) headed Playwright against the demo AUT.
4. **Fail usefully** — Force or use a failing step; case detail shows screenshot + **Open Playwright trace** (path / reveal / `playwright show-trace`) — not text-only.
5. **Triage** — Set failure class; open heal pending **or** preview defect packet (confirm-gated; no silent Jira).
6. **Report** — Export / open Reports library entry for the run (markdown baseline until REP-CHARTS lands).

**Pass:** ~15-minute human walkthrough on OFFICIAL + pytest on evidence/open-trace paths.  
**Fail:** Soft-pass on “opened orb home”; missing trace affordance; Jira write without confirm.

## Out of scope for OPERATE

Voice (KAN-81 deferred), FR-MAN-2 live circles (DPIA), full CI OAuth, H3 network *service*, theme/orb/home restyle, ISO27001 certification *claim*. Optional Trace Viewer embed / higher parallel / Docker = later settings-gated plugins (not OPERATE scope).

## Follow-on (after OPERATE)

**OPERATE-3** (Designer 2026-11-26): Plans Run disclosure, Manual idle, evidence affordance, **plus** case-detail triage strip, run→report link, App-menu Heal pending badge. Then CR backlog: GAP-CR / HOME / FULL-REVIEW (`GAP_FULL_REVIEW_KEYS.json`).
