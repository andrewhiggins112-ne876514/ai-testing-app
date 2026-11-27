# Run evidence UX — Studio Slice-0 (+ deep view)

**Mode:** Redesign (thin mockpack) for Designer pick.  
**CR:** 2026-11-27 readable run steps + pass/fail evidence.  
**Tickets:** **KAN-496**/497 Option A aside; **KAN-498**/499 deep view; epic **KAN-383**.  
**Deep view doors (Designer):** **More evidence** + **thumb expand**. Not folded into KAN-496 AC. Build 496 first unless elevated.  
**Not** OPERATE-3 (**KAN-379**). Not product code. Not the Build Active slice.

**Preferred (Cases aside):** Option A — vertical run story in the existing Plans → Cases aside. **Accepted** for Build KAN-496.

**Preferred (additional deep view):** Full Plans work surface opened from the aside via **More evidence** / thumb expand. Cases list stays; Back to case returns. Captured page shots only — no Trace embed.

**Frozen (do not restyle):** theme tokens, orb styles, home/chat, App nav. In-area Plans tabs stay. No second rail. No new App nav item.

Synthetic fixture names only (`shop.fixture.local`, oak lamp, £42.00). One security level on the chrome: OFFICIAL.

## Files

| File | What it is |
|------|------------|
| `00-before.html` | Baseline. Last-result line, filesystem paths, JSON-ish step dump. No thumbnail. |
| `01-option-a-smoke-pass.html` | **Accepted · Option A.** Pass status, four plain-language steps, one captured confirmation page, Open Trace. |
| `02-option-a-intentional-fail.html` | **Accepted · Option A.** Same story. Failed expect shows the error. One captured fail page. Open Trace. |
| `03-option-a-honest-empty.html` | **Accepted · Option A.** Fail with no PNG. The slot says **None captured** and why. No green stand-in. Trace zip can still open. |
| `04-rejected-page-gallery.html` | **Rejected as primary Cases replacement / Trace embed.** Full-page filmstrip + embedded Trace Viewer columns (network/console/DOM inside the shell). Keep for contrast — do **not** mark Accepted as the Cases screen. |
| `05-deep-view-fail.html` | **In-scope deep view.** Fail case: selectable steps, large fail shot, compact strip of **captured** thumbs only, Back to case, Open Trace external. |
| `06-deep-view-pass.html` | **In-scope deep view.** Smoke pass: same chrome; success shot(s); strip omits steps with no PNG. |
| `07-deep-view-entry.html` | **In-scope entry.** Option A aside showing **More evidence** + thumb-expand affordance → 05/06. |
| `run_evidence.css` | Structure styles only (aside story + deep stage). Tokens from `settings_layout_grammar/grammar.css`. |

Shell reuse: Plans Cases split from `docs/mockups/layout_enhancement_pack/01c-themed-plans-cases.html` (grammar + rest + enhance CSS). Option A changes the **Run / last-result block** inside the aside. Deep view is an **additional** in-area surface over that same Plans chrome.

## Option A (build this — KAN-496)

Order in the aside, top of the focused case:

1. **Status** — Pass or Fail, duration, tag or failure class, time. Read-only text.
2. **Steps** — ordered list: verb + target in plain language (Open, Click, Fill, Expect), pass/fail, short duration. The failed step shows the error sentence under the verb.
3. **One thumb** — the representative captured page for a smoke/golden pass or for a fail. Caption names the step. For **KAN-496**, click opens that PNG (in-panel zoom or the file). After the **deep-view story** ships, the same thumb **also expands** into deep view focused on that shot (Designer 2026-11-27). It is a picture of the page, not a generated success icon.
4. **Open Trace** — existing external open. DOM, network, console, and the action filmstrip stay out of this panel.

Success shots default **on** for smoke / golden path and **off** (configurable) for other runs. Off, or a fail with no file, uses the honest-empty slot.

## Deep view (05–07 — additional page, not Cases replacement)

Opens from Case aside via **More evidence** / thumb expand as a full Plans work surface (in-area panel) while Cases chrome stays reachable (**Back to case** / Close).

Layout:

1. **Header** — case name, Pass/Fail, duration, Back to case, Open Trace (external).
2. **Left** — readable step list (same narrative as Option A). Selecting a step focuses that step’s shot. No whole-row toggle / checkbox.
3. **Main** — larger evidence stage: one selected page shot (or honest empty).
4. **Optional strip** — compact **captured** thumbs only (no network / console / DOM tiles).
5. **Rejected in this page** — embedded Trace Viewer columns; network/console/DOM tiles inside the shell (those stay in Trace Viewer via Open Trace / OPERATE-1).

Do **not** steal or replace the Cases master–detail list. Do **not** add an App nav item. Do **not** embed Playwright Trace Viewer or hosted `trace.playwright.dev`.

## Rejected

| Option | Why |
|--------|-----|
| Page gallery / filmstrip **as Cases screen** (`04`) | Replaces the case list. Many tiles hide the sentence the tester came to read. |
| Embed Trace Viewer (`04`) | Duplicates OPERATE-1, heavy for this PC, and is the wrong density for Case detail **and** for the deep view. |
| Hosted `trace.playwright.dev` | Needs the network. Local-first Open Trace stays. |
| Green placeholder when no PNG | Reads as a pass. Forbidden by FR-TEST-4. |
| New “Evidence” App nav item | App nav is locked. Prior layout pack already rejected a gallery area (`layout_enhancement_pack/03-rejected.html`). Option A is one shot **inside** the aside; deep view stays under Plans chrome without a new nav item. |
| Raw JSON step dump as the UI | Baseline. Keep JSON on the run record; do not show it as the narrative. |
| Network / console / DOM tiles in deep strip | Forensic panes belong in Open Trace, not the shell filmstrip. |

**Note:** The *spirit* of richer multi-shot viewing from `04` is recovered in **05–06** as a **separate** deep view — without replacing Cases or embedding Trace.

## Click targets

### Option A aside (01–03, entry 07)

| Control | Hit | Does not |
|---------|-----|----------|
| Case row | Focus / open that case | Toggle Enabled or Archived |
| Show archived | Compact checkbox in the toolbar | Use the row as the checkbox |
| Step row | Read-only. No checkbox | Select, toggle, or approve |
| Thumbnail (01–03) | Open the one PNG | Open a filmstrip or the trace |
| Thumbnail expand (07) | Open deep view | Embed Trace Viewer |
| More evidence (07) | Open deep view (05/06) | Replace Cases list |
| Open Trace | External trace (OPERATE-1) | Embed the viewer |
| Save / Run | Existing pinned actions | Move into the story |

### Deep view (05–06)

| Control | Hit | Does not |
|---------|-----|----------|
| Back to case | Return to Cases aside | Close Plans / leave App |
| Open Trace | External trace (OPERATE-1) | Embed Trace Viewer in the stage |
| Step row | Focus that step’s shot on the stage | Toggle, approve, or checkbox-select |
| Captured thumb chip | Focus that shot on the stage | Open network/console/DOM tiles |
| Plans area tabs / toolbar | Existing Plans chrome (reachable) | New App nav item |

Keyboard: case scan keeps ↑ ↓ focus, Enter detail, Space only on a real checkbox. Deep-view steps focus evidence; they are not a second selection grid for Enabled/Archived.

## Field research (adopt / adapt / reject)

| Source | Pattern | Call |
|--------|---------|------|
| [Playwright HTML reporter](https://playwright.dev/docs/test-reporters) | Step list with pass/fail and attachments on the test; Trace Viewer is a separate surface the report links out to | **Adapt** the step list + one attachment into the aside; **adapt** multi-attachment into deep view. **Reject** shipping the HTML report or copying its viewer. |
| Playwright 1.60 HTML notes (2026) | Parent steps can show that a child has an attachment; traces/screenshots need not be inlined into one giant page | **Adapt** “one indicator + the file”. **Reject** inlining every artifact into Case detail. |
| [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer) | Actions, DOM snapshots, network, console, source | **Adopt** Open Trace as the door. **Reject** embedding that UI (aside and deep view). |
| [Allure attachments](https://allurereport.org/docs/attachments/) | Screenshot on failure (and optionally per step) so a glance answers “what did the page look like?” | **Adapt** one representative shot on fail and on smoke/golden pass in the aside; multi captured thumbs in deep view. **Reject** a shot on every step inside the aside panel. |
| Allure 3 vs Allure 2 trace behaviour (same attachments doc) | Allure 3 opens Trace Viewer in a new tab. Allure 2 embeds it. Both can load `trace.playwright.dev` | **Adopt** “open elsewhere”. **Reject** embed and **reject** the hosted viewer (offline / local-first). |
| [Allure TestOps result page](https://docs.qameta.io/use-testops/results-and-analytics/test-results/) | One attempt: status, scenario/steps, attachments. Attachments are a tab, not a replacement for the case list | **Adapt** status + steps + evidence on the focused case; deep view as additional detail. **Reject** a launch-wide gallery as the Plans Cases screen. |

Repo baseline already recorded in `docs/ops/ENTERPRISE_GAP_RESEARCH.md`: open the real `trace.zip`; do not embed the viewer in OPERATE.

## Code surface (Build)

### KAN-496 — Option A aside only

Touch the Case aside only:

- `ui/desktop/index.html` — `#plan-case-evidence-first` and the Run section (`#plan-case-sec-run`). Replace path-only last result with the story. Keep triage strip, Edit, Quarantine, Known issue, and the Save/Run pin.
- `ui/desktop/desktop.js` — `refreshCaseDetail` / `fillPlanEvidence`. Render ordered steps and one shot or the none-captured reason. Do not invent a green bitmap.
- Run record (FR-PLAN-4) — persist ordered step outcomes (action, status, short label, error snippet) and evidence paths (png, trace.zip) on the same run. Case detail reads that. Reports may reuse the narrative later; this slice does not restyle Reports.
- Open Trace — existing operate open-trace control. Do not add a viewer route.

Do not touch orb shaders, theme tokens, home/chat, or App nav. Do not fold this into OPERATE-3.

### Deep view (**KAN-498** / **KAN-499** — after KAN-496 unless elevated)

Frames **05–07**. Entry: **More evidence** + **thumb expand**. No Trace embed. No Cases list replacement.

## AC holes to keep visible

- Fail with zero PNG must show the reason, never a success image.
- Smoke/golden pass shows one real shot when capture succeeded.
- Non-smoke pass with success shots off uses the same empty reason, not a blank green card.
- Step list is plain language even when the shot is missing.
- On KAN-496: thumbnail opens the one PNG; Open Trace is a different hit.
- On KAN-498: More evidence / thumb expand open deep view; Open Trace stays separate.
- Deep strip: captured page thumbs only — never network/console/DOM tiles.
- No whole-row toggle on cases or steps.

## Verdict

**Accepted 2026-11-27 (Designer + Council):**  
- **KAN-496** / **KAN-497** — Option A frames **01 / 02 / 03**.  
- **KAN-498** / **KAN-499** — deep view frames **05 / 06 / 07**; thumb also expands.

**Rejected (primary Cases screen):** frame **04** — filmstrip + embedded Trace Viewer as the Cases screen. Contrast only.
