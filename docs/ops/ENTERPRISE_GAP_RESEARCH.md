# Enterprise gap research (Council 2026-11-26)

**Why:** Designer feedback — Review/Studio must compare this product to **current enterprise practice**, not only to our Jira Done rows.  
**Method:** Web research (2025–2026 sources) + map to repo maturity.  
**Not:** a certification claim. Local-first / no mandatory cloud still wins; we adapt patterns, we do not become SaaS.

## Research duty (binding)

On every **Review / Full** Council and every **Audit / Research** Studio that claims “gaps / enterprise / what’s missing”:

1. Run **web research** (or equivalent current docs) for the seated domains — not training memory alone.
2. Cite sources in the verdict under **Research (adopt / adapt / reject)**.
3. Produce **capability gaps vs market** separate from **repo Partial FRs**.
4. Prefer **decision-useful** features over vanity polish.

## Domains researched

| Domain | Sources (examples) | Market expectation | Our state | Adopt / adapt / reject |
|--------|-------------------|--------------------|-----------|------------------------|
| **QA reporting / release readiness** | TestRail eval checklist; QA Tool Guide dashboards; Katalon Release Health; Zephyr/Xray gadgets | Tiered dashboards: release summary, critical-path coverage, failure taxonomy, trends, flake rate, drill-down to evidence | Markdown/JSON library + HUD chips; **no charts**, weak release go/no-go panel | **Adopt** decision charts + release summary; **reject** vanity “tests run” only; **adapt** to local JSON (no cloud BI) → strengthens **KAN-384** |
| **Test management** | TestRail / Xray / Zephyr patterns | Requirement↔case coverage, execution history, defect aging, filterable gadgets | Coverage gaps + matrix APIs exist; UX assembly-heavy; **no Xray sync** | **Adapt** coverage/critical-path views in Reports/Plans; **park** full Xray until after OPERATE; keep confirm-gated Jira |
| **Exploratory / Manual** | SBTM charters; Xray Exploratory App; Tricentis qTest Explorer (desktop + web) | Time-boxed charter, continuous notes, region/full capture, annotate, optional video, session report + debrief; capture **outside** main IDE window | Charter Frame MVP in-app; annotate-still; assist optional; **not** OS-float snip; weak session-report/debrief | **Adopt** OS-level snip + charter-only (**KAN-386**); **adapt** SBTM session report; **reject** silent keylog / always-on video; FR-MAN-2 circles still DPIA |
| **Evidence / traces** | Playwright Trace Viewer docs | `retain-on-failure` traces; open Trace Viewer; DOM/network/console at fail step | Real `trace.zip` (**KAN-372**); open affordance = **OPERATE-1** | **Adopt** open-trace (**KAN-375**); optional later: deep-link `trace.playwright.dev` or CLI; **reject** embedding heavy viewer in OPERATE |
| **Self-heal governance** | 2025–26 heal guides (locator-only, provenance, human approve) | Never heal assertions; classify failure; heal with evidence/provenance; human gate on money/auth | Policy + review UI strong; provenance/diff narrative thin | **Adapt** heal+trace provenance story after OPERATE; **reject** auto-apply / assertion heal |
| **Sandboxes / isolation** | Playwright BrowserContext; Docker PW; ephemeral runner isolation | Per-test clean context; ephemeral profiles; CI isolation | Local sandbox records + profile dirs (internal) — correct product intent | **Clarify** UI copy: local env profiles ≠ cloud farms; **adapt** ephemeral/TTL prepare; **reject** fake “device farm” |
| **Compliance** | ISO 27001 SaaS guides; UK Cyber Essentials; SOC 2 + GDPR crosswalks; local-first compliance trackers | Buyers ask ISO 27001 / SOC 2 / Cyber Essentials **evidence**, not GDPR alone | OFFICIAL/SECRET + GDPR wipe/redact/audit | **Adopt** matrix design (**KAN-392**) covering ISO themes + **Cyber Essentials** + SOC2 crosswalk; **reject** “ISO certified” badge without audit |
| **Agentic QA competitors** | Katalon / UiPath / Perfecto / KaneAI roundups 2026 | Chat→test, heal, CI, **agent governance** (RBAC, token caps, tool audit, human steer) | Chat+tools+confirm; local audit JSONL; no token caps / role RBAC beyond levels | **Adapt** agent session audit export + model/token budget UI later; **reject** cloud agent SaaS; keep clarify-before-act |
| **Documents / fixtures** | Enterprise TM evaluation — sample data / onboarding | Demo content so empty desks don’t kill POC | Uploads work; empty by default | **Adopt** demo pack (**KAN-381**) |
| **Plan as document** | TM tools show readable plans/suites | Human-readable plan narrative | JSON + forms | **Adopt** plan document view (**KAN-388**) |

## Gaps we should have raised without being asked

These are the “Designer had to notice” items — now standing checklist for Review mode:

1. Reports without **decision charts / release summary**  
2. Manual capture trapped in-app vs **Explorer-class** float snip  
3. Empty Documents / Lab without **demo fixtures**  
4. Compliance story = GDPR only (missed **ISO / Cyber Essentials / SOC2** language)  
5. Sandbox wording ambiguous (local vs external)  
6. Plan storage opaque; no **readable plan document**  
7. Trace on disk without **open path**  
8. Stubs without **rich synthetic data** while deepening  
9. Heal without **provenance + trace link**  
10. Agent without **enterprise governance** (budgets, exportable tool audit)  
11. No **critical-path / release readiness** narrative for managers  
12. Session-based exploratory **debrief/report** incomplete vs SBTM

## Sequencing (unchanged intent)

1. **OPERATE** (**KAN-374**, Active **KAN-375**) — loop + open-trace + home-PC AUT  
2. Loop-hit polish (**KAN-379**)  
3. **GAP-CR** (**KAN-383**) — charts, Manual float, plan doc, stubs, compliance matrix  
4. New candidates below — **propose Jira only after Designer confirm**

## Proposed additions (not seeded yet)

| ID | Title | Why (research) |
|----|-------|----------------|
| GAP-CR-REL | Release readiness summary panel (go/no-go + critical path) | QA dashboard practice — not vanity pass% |
| GAP-CR-FLAKE | Flake/quarantine trend chart in Reports | Industry treats flake as first-class |
| GAP-CR-HEAL-PROV | Heal proposal shows locator diff + link to trace action | Heal governance 2026 |
| GAP-CR-SBTM | Manual session report + debrief fields (SBTM) | Exploratory tooling bar |
| GAP-CR-AGENT-GOV | Agent token/tool budget + exportable session audit | Agentic QA enterprise asks |
| GAP-CR-CE | Expand FR-SEC-6 matrix with UK Cyber Essentials + SOC2 crosswalk | UK buyer reality |

## Explicit rejects (local-first)

- Mandatory cloud analytics / telemetry dashboards  
- Silent heal / assertion weaken  
- Cloud device farms as default sandbox  
- Claiming ISO/SOC certification in-product without evidence  
- Replacing confirm-gated Jira with agent auto-write  

## Next

Designer: say **seed research additions** to expand **KAN-383**, or keep as backlog notes only.  
Build: continue **KAN-375** — research does not steal Active slice.
