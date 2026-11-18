# H2 — Plan the pipelines section (design only)

**Story:** KAN-243 (test KAN-244) · **FR:** FR-CI-1 · **Band:** FUTURE  
**Status:** Design complete — **no CI integration ships in this story.**

This note is the build contract for a later implementation slice. The **in-app plan/suite** remains the place tests are authored, reviewed, and run locally. Pipelines are a **separate App area** for release visibility into external CI — never the primary authoring surface.

---

## 1. What a pipeline record shows

A **pipeline record** is a local, level-scoped mirror of one named CI job / workflow the tester opts in to watch. It is not a case and not a suite run.

| Field | Required | Notes |
|-------|----------|--------|
| Display name | yes | Human label (e.g. “main smoke”). |
| Provider kind | yes | Enum for later plugins: `github_actions` / `azure_devops` / `jenkins` / `other` (stub until wired). |
| External id / slug | yes | Provider-specific workflow or job id (no secrets). |
| Link-out URL | optional | Opens the CI run in an external browser; never embeds CI UI in the orb home. |
| Linked plan id | optional | Active-level plan this job roughly corresponds to. |
| Linked tag | optional | Suite tag filter (same spirit as G12 / C7) when the job runs a subset. |
| Last known status | yes | `unknown` / `queued` / `running` / `passed` / `failed` / `cancelled` / `not_synced`. |
| Last sync at | optional | Local timestamp of last successful status fetch. |
| Last external run ref | optional | Commit SHA, build number, or run URL fragment — display only. |
| Security level | implicit | Always the **active** OFFICIAL or SECRET level that owns the record. |

**UI home (later implement)**

- Dedicated **Pipelines** App area (full-window surface from the App menu), not a HUD that replaces Plans.
- List + detail of pipeline records for the active level only.
- Deep-link from Release / Reports HUD may *point at* Pipelines; it must not turn home into a CI dashboard.

Storage sketch (later implement):  
`%LOCALAPPDATA%/ai_testing_app/plans/{OFFICIAL|SECRET}/pipelines/{pipeline_id}.json`

---

## 2. What it will not do

| Will not | Why |
|----------|-----|
| Replace the in-app suite as the authoring / review place | FR-CI-1 and catalogue OOS. |
| Auto-import CI YAML as cases without review | Cases stay plan-owned; import remains explicit (C8 spirit). |
| Treat a green CI job as a local case **pass** | Local runs and CI status stay separate result models. |
| Host or run headed browser AUT work in the cloud | Local-first; G12 schedules stay on this PC. |
| Embed a full CI console inside the desktop shell | Link-out only. |
| Silent webhooks that write Jira or heal without confirm | FR-AGENT-4 / FR-JIRA-5 still apply. |
| Cross-level merge of pipeline records or tokens | OFFICIAL / SECRET isolation. |
| Ship live CI sync, OAuth, or provider plugins in **KAN-243** | Design only. |

Scheduled **local** tagged runs (G12) remain distinct: they execute on this PC with the sequential cap; they are not pipeline records.

---

## 3. Secrets stay local

| Rule | Behaviour |
|------|-----------|
| Credential store | CI tokens / PATs live only in the **level-scoped** credentials store (same pattern as Jira), never in pipeline JSON, git, chat, or installer packs. |
| Pipeline file contents | Ids, URLs, status, and refs only — no `Authorization` headers, no raw tokens. |
| Sync (later) | Fetches use credentials loaded at call time for the active level; failures surface as `not_synced` / error, never by logging the secret. |
| Export / F6 packs | Pipeline status summaries may be included as redacted metadata; tokens never. SECRET packs stay on that level’s backup path. |
| Second-PC installer (G11) | Remains secret-free; each PC enters its own CI credentials after install. |
| GDPR wipe | Level wipe deletes pipeline records **and** that level’s CI credentials. |

---

## 4. Relationship to Plans / runs / reports

- **Author & review:** Plans App area (unchanged).
- **Local execute:** Plan/suite run model (A7 / D1 / G12).
- **Observe CI:** Pipelines App area (this design) — read-mostly status + link-out.
- **Release story:** Release / Reports HUD may show “last local run” and, later, “last CI status” as **separate** chips — never collapsed into one pass/fail that hides which system produced it.

Optional later mapping: pipeline → plan id / tag is for human orientation only; it does not rewrite case results.

---

## 5. OFFICIAL / SECRET separation

| Rule | Behaviour |
|------|-----------|
| Isolation | Pipeline list/detail only for the **active** security level. |
| Paths | Separate folders under `plans/OFFICIAL` vs `plans/SECRET`. |
| Credentials | CI secrets never shared across levels; level switch uses existing confirm (FR-SEC-3). |
| Link-out | Opening an external CI URL does not copy SECRET evidence into OFFICIAL stores. |

---

## 6. Out of scope (this story and near follow-ons)

- **Shipping CI integration, sync APIs, or a Pipelines screen in KAN-243** (explicit AC).
- Choosing a single mandatory CI vendor.
- Replacing in-app suite with CI (catalogue OOS).
- Cloud-hosted schedules (already OOS for G12).
- Multi-PC shared pipeline service (H3 is a separate design).
- Manual session capture (H1 — already designed; recorder not shipped).

---

## 7. Later implementation checklist (not this slice)

When a Build story picks up FR-CI-1 for real:

1. Pipelines App area + level-scoped store (fields in §1).
2. Credential keys for chosen provider(s) in level store; never in pipeline files.
3. Opt-in sync job → update last status / ref; mark `not_synced` on failure.
4. Link-out only; dual chips on Release HUD (local vs CI).
5. Tests: isolation, no tokens in records/export, suite authoring unchanged, no CI pass → local pass.
6. Do **not** remove or hollow out the in-app plan/suite.

---

## 8. Acceptance trace (KAN-243)

| Catalogue AC | Covered in |
|--------------|------------|
| What pipeline record shows | §1 |
| What it will not do | §2 |
| Secrets stay local | §3 |
| Does not ship CI integration | Entire doc; `plans/pipelines_design.py` → `ci_integration_shipped=False` |
