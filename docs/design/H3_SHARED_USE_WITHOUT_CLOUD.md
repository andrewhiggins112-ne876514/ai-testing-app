# H3 — Plan shared use without a cloud (design only)

**Story:** KAN-245 (test KAN-246) · **FR:** FR-SEC-1 · **Band:** FUTURE  
**Status:** Design complete — **no network / share service ships in this story.**

This note is the build contract for how **two testers on two Windows PCs** collaborate without a mandatory cloud multi-tenant product. Today they already have F6 export packs, E4 backup/restore, and G11 second-PC install. H3 names the options, security limits, and what stays out of scope — it does **not** pick a vendor or ship sync.

---

## 1. Local / on-prem options

Three paths cover “share without a cloud.” All stay under the active OFFICIAL or SECRET level; none invent a second security model.

| Option | Status today | What it is for | What moves | What does not move |
|--------|--------------|----------------|------------|--------------------|
| **Export pack (F6)** | Shipped | Hand someone a **read-only** run story (report / matrix / evidence) without installing the app. | Redacted pack folder labelled with level + time. | Live plans, credentials, browser profiles, heal approve. |
| **Backup copy (E4)** | Shipped | Move or recover **this lab** on the same or another PC the tester controls. | Plans, runs, evidence index; optional settings; secrets **off by default**. | Cross-level merge; automatic cloud backup. Restore requires confirm and refuses mixing OFFICIAL ↔ SECRET folders. |
| **Future shared folder** | Design only | Later: drop a **level-scoped, redacted** pack into an on-prem folder (USB, mapped drive, or corporate file share the org already runs). Another install **imports** that pack after confirm. | Same family of artefacts as F6/E4 (plans/runs/reports metadata + redacted evidence). | Live credentials, continuous sync, agent auto-write, or treating the folder as a multi-tenant cloud. |

**Also related (not a share channel by itself)**

- **Second-PC installer (G11)** — gets another Windows machine onto the desktop app with a secret-free pack. Each PC enters its **own** connections afterward. Sharing artefacts still uses export / backup / future folder — not a shared account.
- **Jira (already configured)** — remains the team’s ticket system of record. Defect packets and story links go through existing confirm gates; Jira is not a substitute for sharing local evidence stores.

Storage sketch for a later shared-folder implement (not this story):  
`%LOCALAPPDATA%/ai_testing_app/plans/{OFFICIAL|SECRET}/share_outbox/` and an explicit **Import shared pack** confirm path — never a background watcher that writes without consent.

---

## 2. Security limits

| Limit | Behaviour |
|-------|-----------|
| OFFICIAL / SECRET isolation | Packs, backups, and any future shared folder are **level-labelled**. Restore/import refuses to mix levels (FR-SEC-1 / E4 spirit). |
| No shared credentials | Tokens, PATs, and passwords stay in each PC’s **level-scoped** credentials store. Never inside export packs, installer packs, or shared-folder blobs by default. |
| Redaction | Shared artefacts pass E3-style redaction; SECRET packs stay on that level’s path and are not “downgraded” into OFFICIAL. |
| Confirm before apply | Import / restore / merge on the receiving PC requires explicit confirm (FR-SEC-3 / FR-AGENT-4 spirit). No silent overwrite of plans or runs. |
| No cloud multi-tenant | There is no shared cloud account, hosted sync, or SaaS “team workspace” as a product requirement. |
| No mandatory network service | H3 does **not** choose or ship LAN discovery, relay servers, or always-on sync daemons. |
| GDPR wipe | Level wipe / delete-local-data remains per PC; a shared folder the org owns is outside this app’s wipe — packs must not be the only copy of secrets (they should not contain them). |
| Telemetry | Remains off by default; share paths do not phone home. |

---

## 3. What it will not do

| Will not | Why |
|----------|-----|
| Pick or ship a network / share service in **KAN-245** | Explicit catalogue AC. |
| Mandate cloud multi-tenant collaboration | Catalogue OOS; contradicts local-first vision. |
| Auto-sync two PCs in the background | Confirm-before-act; no silent merge. |
| Put secrets in packs or installers | FR-SEC-5; G11 / F6 / E4 already forbid this by default. |
| Collapse OFFICIAL and SECRET on one share path | FR-SEC-1. |
| Replace Jira as the bug tracker | Defect propose stays two-step; share is for lab artefacts. |
| Replace the in-app plan/suite as the authoring place | Same OOS spirit as H2. |
| Treat “folder green” or “backup present” as a test **pass** | Results stay on local runs. |

---

## 4. Relationship to shipped pieces

| Piece | Role vs H3 |
|-------|------------|
| F6 export pack | Primary **read-only hand-off** today. |
| E4 backup / restore | Primary **lab move / recover** today. |
| G11 second-PC pack | Gets a second install running; not a sync channel. |
| H1 / H2 designs | Manual sessions and pipelines stay local; sharing them later uses the same pack rules (redact, level label, confirm import). |
| G12 schedules | Stay on **this** PC; not cloud-hosted and not auto-mirrored. |

Recommended later UX (implement story, not this one): Settings or Security surfaces a short **“Share without cloud”** help that lists these three options and the limits in §2 — no new always-on service.

---

## 5. Out of scope (this story and near follow-ons)

- **Shipping** a shared-folder watcher, LAN sync, or any network service in KAN-245.
- Choosing a single commercial sync vendor.
- Mandatory cloud multi-tenant (catalogue OOS).
- Company-wide MDM / fleet rollout claims (beyond G11’s second-PC install pack).
- Changing OFFICIAL/SECRET isolation rules.
- Shipping H1 recorder or H2 CI integration.

---

## 6. Later implementation checklist (not this slice)

When a Build story picks up multi-PC share for real:

1. Keep F6 + E4 as the default paths; document them in-app under Security / Settings.
2. Optional **shared folder** outbox/inbox: level-scoped, redacted packs only; import with confirm; refuse cross-level.
3. Never embed credentials; never background-merge plans.
4. Tests: isolation, no tokens in packs, refuse mix, confirm required, no network service required for core path.
5. Do **not** remove Gradio, orb, layouts, voice stubs, desktop plugin, sandboxes, or framework stubs.

---

## 7. Acceptance trace (KAN-245)

| Catalogue AC | Covered in |
|--------------|------------|
| Lists local/on-prem options (export pack, backup copy, future shared folder) and security limits | §1, §2 |
| Does not pick or ship a network service | Entire doc; `plans/shared_use_design.py` → `network_service_shipped=False` |
| OOS: mandatory cloud multi-tenant | §3, §5 |
