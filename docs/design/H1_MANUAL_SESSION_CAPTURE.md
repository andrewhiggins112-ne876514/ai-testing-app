# H1 — Plan manual session capture (design only)

**Story:** KAN-241 (test KAN-242) · **FR:** FR-MAN-1 · **Band:** FUTURE  
**Status:** Design complete — **no recorder ships in this story.**

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
