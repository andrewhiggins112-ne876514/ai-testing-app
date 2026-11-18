# H1 — Plan manual session capture (design only)

**Story:** KAN-241 (test KAN-242) · **FR:** FR-MAN-1 · **Band:** FUTURE  
**Status:** Design complete — **no recorder ships in this story.**  
**Council CR (2026-11-18):** Charter Frame MVP + toggles — see **§9**. Implement via **new** Build stories (do not reopen KAN-241 as “recorder shipped”). Live mist-watch / circles = **FR-MAN-2** (parked) — see **§10**.

This note is the build contract for a later implementation slice. B7 case/run notes (`plans/notes.py`) stay as today’s exploratory home; H1 extends that into a **session** that can propose ticket updates after confirm.

---

## 1. Charter start

A manual / exploratory session begins only when the tester explicitly starts one.

| Field | Required | Notes |
|-------|----------|--------|
| Charter (goal text) | yes | What the tester intends to explore (max ~2k chars). |
| Linked plan id | optional | Active-level plan; session stays under that level. |
| Linked case id | optional | Focus case inside the plan when known. |
| Linked Jira key | optional | Story/bug under exploration; read-only until confirm. |
| Security level | implicit | Always the **active** OFFICIAL or SECRET level at start. |

**Start rules**

- Off by default — no background capture.
- Starting a session does not write to Jira.
- Only one **open** session per security level at a time (later start must end or cancel the previous).
- Cancel discards an uncommitted session after confirm; end keeps a local draft for review.

---

## 2. What is recorded

Local, level-scoped session draft only. Nothing leaves the machine until a later confirm path.

| Capture | Default | Detail |
|---------|---------|--------|
| Timestamped notes | on | Tester-typed entries (same spirit as B7). |
| Opt-in screenshots | off | Explicit “attach screenshot” only; paths under the level store. |
| Page context | when known | URL + document title from the headed AUT / Playwright context if the lab already has one — never a global keylogger. |
| Linked case/run ids | when set | Ties findings to the in-app suite. |
| Failure class hint | optional | product_bug / test_defect / environment / known_issue (FR-HEAL-4). |

**Never recorded (this design)**

- Keystrokes, clipboard, mic/voice (G10 / KAN-81 remain separate).
- Continuous silent video or always-on screen recording.
- Secrets, tokens, passwords (redact like evidence export / E3).
- Cross-level session merge.

Storage sketch (later implement):  
`%LOCALAPPDATA%/ai_testing_app/plans/{OFFICIAL|SECRET}/sessions/{session_id}.json`  
(+ optional `…/sessions/{session_id}/` for screenshot files).

---

## 3. How a bug (or ticket update) is proposed

On **End session**, the app opens a **review** of the draft (timeline + attachments). From review the tester may choose **Propose**:

1. **Create Bug** — build a defect packet from selected session notes + screenshots (reuse `plans/defect_packet.py` / FR-JIRA-4 shape: Symptom, Expected, Actual, Environment, numbered Replication, Evidence paths). Only when failure class is `product_bug` (or tester explicitly picks Bug).
2. **Comment on linked story** — propose a comment body from selected notes (FR-JIRA-5 confirm).
3. **Attach note to case/run** — write local B7-style notes only (no Jira).

Proposals are **previews**. Cancel leaves the local session draft unchanged and writes nothing to Jira.

---

## 4. Confirm

All Jira side effects stay on the existing two-step path (FR-AGENT-4, FR-JIRA-5):

1. Agent/UI shows the full proposed payload (no tokens).
2. Tester replies **yes / confirm** (or Cancel).
3. Only then call `create_bug` / comment / status tools; append `jira_write_audit.jsonl` as today (KAN-99).
4. After a successful confirm, mark proposed items on the session as `submitted` with issue key; do not delete the local draft.

No YOLO / auto-file. No silent status transitions.

---

## 5. OFFICIAL / SECRET separation

| Rule | Behaviour |
|------|-----------|
| Isolation | Sessions listed and opened only for the **active** security level. |
| Paths | Separate folders under `plans/OFFICIAL` vs `plans/SECRET` (same pattern as plans store). |
| Level switch | Requires existing confirm (FR-SEC-3); open session on the old level is not visible on the new level. |
| Credentials | Session files never store Jira tokens or passwords; use level-scoped credentials store only. |
| Export | Session evidence in report/export packs follows E3 redaction; SECRET packs stay on that level’s backup path. |
| GDPR | Local delete / lab wipe includes session drafts for that level. |

---

## 6. Out of scope (this story and near follow-ons)

- **Shipping a recorder UI or API in KAN-241** (explicit AC).
- Voice capture (G10 / KAN-81 — deferred).
- Cloud sync of sessions (H3 is a separate design).
- Replacing B7 notes — H1 builds on them.
- CI / pipelines (H2 design).

---

## 7. Later implementation checklist (not this slice)

When a Build story picks up FR-MAN-1 for real:

1. Session start/end/cancel APIs + desktop Plans control (charter form).
2. Level-scoped session store + screenshot attach.
3. Review → Propose → Confirm wiring to defect packet / create_bug / comment.
4. Tests: isolation, no write without confirm, redaction, B7 coexistence.
5. Do **not** enable continuous silent recording.

---

## 8. Acceptance trace (KAN-241)

| Catalogue AC | Covered in |
|--------------|------------|
| Charter start | §1 |
| What is recorded | §2 |
| How bug is proposed | §3 |
| Confirm | §4 |
| OFFICIAL/SECRET separation | §5 |
| Does not ship a recorder | Entire doc; `plans/manual_session_design.py` → `recorder_shipped=False` |
| Council CR Charter Frame (2026-11-18) | §9 |
| Live assist parked (FR-MAN-2) | §10 |

---

## 9. Council CR — Charter Frame MVP (2026-11-18)

Human track **1** (Plans IA tidy + stub honesty → thin H1). Extends §§1–5; does **not** replace them. **No product recorder in this design-only doc** — Build stories implement later.

### 9.1 Locked product choices

| ID | Choice |
|----|--------|
| A3 | **Manual** is a **Primary** App menu area **and** Plans has **Start manual on this case** deep-link. Esc/Back from Manual → orb home (one home). |
| B1 | Capture frame = free **region** (snipping-tool rectangle). Window/monitor snap = **Track 2** completion story (not MVP). |
| C3 | **Story key** required when binding to Jira; **test ticket optional**. Charter-only explore still allowed when not ticket-bound. |
| D1 | Build order: **Plans IA + stub honesty first**, then H1 Charter Frame. |
| E2 | Optional light mist **inside the frame** when session is armed; **mist on/off** (must not block testing). |
| Assist | **Agent assist on/off** — tester can simply record without agent proposals/cues. |

### 9.2 Charter Frame (visual)

- Calm **snip-style** rectangle over the chosen region; soft outer dim; orb accent stroke (`--cyan` / active style).
- Optional **inner mist** only inside the frame when armed **and** mist toggle is on — never Cursor full-desktop purple fog as product chrome.
- Frame chrome (edges, session chip, toggles) is the only hit target; default **click-through** to the AUT.
- Overlay appears **only after** explicit Start; off = no frame, no capture.

### 9.3 Start fields (delta from §1)

| Field | Required | Notes |
|-------|----------|--------|
| Charter | yes | Unchanged. |
| Jira story key | when ticket-bound | Required if tester chose “link to Jira”; optional for charter-only. |
| Jira test key | optional | `issuetype=test` when known; read-only until confirm. |
| Plan / case | optional | Deep-link from Plans pre-fills. |
| **Agent assist** | toggle | **Recommended default: off** — pure record (notes + opt-in stills). On = local draft proposals only (still no live Jira). |
| **Armed mist** | toggle | **Recommended default: off** — calm frame only. On = light mist inside frame. |

### 9.4 Agent assist off vs on

| Assist | During Record | On End → Review |
|--------|---------------|-----------------|
| **Off** | Notes + opt-in stills + annotate-still (human). No AI cues, no auto draft steps/bugs. | Human builds proposals from selected notes/stills (defect packet / comment / local note) as §3. |
| **On** | Same capture; may maintain **local unpublished** proposed step drafts / possible-bug **hints** (never silent Jira). | Review shows AI drafts + human edits; Propose → confirm still required (§4). |

Assist never enables continuous silent video, keylog, clipboard, mic, or live pixel OCR (those stay §2 never-list / FR-MAN-2).

### 9.5 Evidence (MVP)

Unchanged from §2: notes on; screenshots **opt-in** (snip inside frame); page URL/title only if lab already knows headed AUT; E3 redaction; level-scoped store.

### 9.6 Propose (MVP delta)

§3 plus optional: **test-step update preview** for linked case / test ticket (local `pending_review`; never auto-commit; never weaken assertions). Jira writes stay one **confirm batch** at End (§4).

### 9.7 IA placement

1. App menu **Primary → Manual** — session start, frame controls, review.
2. Plans — **Start manual on this case** (pre-fill plan/case/story when known).
3. Chat may clarify and start; Manual area owns overlay + review.

### 9.8 Build sequence (Track 1)

1. **Plans IA tidy** — Cases-first landing; six sections / tabs; sticky toolbar; one Add-case menu.
2. **Stub honesty** — Playwright ready; Selenium/Cypress labelled not-implemented; disable Run; never default Selenium.
3. **H1 implement** — session APIs + Manual area + Charter Frame + toggles + review/confirm.
4. **FR-MAN-2** — parked until H1 ships + DPIA (see §10).

### 9.9 Still out of MVP

Silent video; keylogger; live OCR/vision circles; YOLO Jira; click-blocking glass; overlay as second home; cloud frames; real Selenium/Cypress runners.

---

## 11. Council Track 2 — FR-MAN-1 completion (2026-11-18)

MVP shipped **KAN-277** (desk91). Do **not** reopen KAN-277 as failed. Remaining Build stories (epic Council Track 2):

1. Non-overlapping area chrome (FR-UI-9) — fixes sticky occlusion first.
2. Trustworthy headed Manual loop (Computer Use proven).
3. Real agent-assist local Ollama drafts (honest unavailable state).
4. Window/monitor snap (B1).
5. Page context from headed AUT + annotate still.
6. Session library + GDPR session wipe.
7. Propose/confirm harden (failure class + Confirm visibility).
8. Enterprise layout research note (docs) → tokens only after human accepts.

FR-MAN-2 and voice stay out.

---

## 10. Parked — live assist overlay (FR-MAN-2)

Do **not** smuggle into H1 implement or Track 2 completion stories.

| Later capability | Gate |
|------------------|------|
| Sparse event-driven region grab (≤1–2 fps or on pause) | New FR + **DPIA** + human sign-off |
| Click-through draw layer for circles | Never hit-tests AUT; never snapshots passwords/OTP |
| Missed-field circles | Annotate-mode; max ~3; each cites AC/spec/guide line; confirm to keep |
| Full Cursor-style mist / Computer Use as product watcher | **Never** (IDE tooling ≠ product) |
