# Charter outside-window — options gallery

**Mode:** Design Studio gallery. Not product code.  
**Status:** **Designer review — no preferred.** No option is Accepted. Do not treat a frame as Build-ready until the Designer picks one.  
**Open:** [`index.html`](index.html) — “Charter outside-window — all design options (pick one)”.

**Designer lean (review, not Accepted):** Option G with the south dock replaced by a 48px side tray. Gallery: [`g-tray-index.html`](g-tray-index.html). Pattern notes: [`RESEARCH_G_TRAY.md`](RESEARCH_G_TRAY.md). Frames `g-tray-01` … `g-tray-07` and `g_tray.css`. Options A–H stay available.

**Bugs:** **KAN-510** and **KAN-511** stay deferred until after the redesign ships. This pack does not close them and does not start Build.

**Frozen (do not restyle):** theme tokens, orb styles, home/chat, App nav. Manual chrome in these frames reuses the locked tokens. The fake IDE chat is a foreign window, not our home/chat.

**Out of this pack:** FR-MAN-2 live circles, voice, keylog, clipboard, mic, continuous / silent video, Gradio OS float, theme/orb/home CR.

Synthetic fixture only (`shop.fixture.local`, oak lamp, £42.00). One security level: OFFICIAL.

## How to look

Open `docs/mockups/charter_outside_window/index.html` in a browser. Each option has a short note, a one-line tradeoff, a link, and a scaled preview. Use **Open full mock** to read drag targets and annotations. If a preview pane is blank, the browser blocked the frame — the link still opens the full mock.

## Options (no preferred until the Designer picks)

| Option | Frame | One line |
|--------|--------|----------|
| **A** OS ring + thin edge-glued dock | `option-a.html` (same idle picture as `01-idle-armed.html`) | One hollow ring and one dock glued to its bottom edge, so controls stay on the hole — the dock can cover the bottom of the framed chat. |
| **B** Hybrid dual chrome | `option-b.html` | OS ring over the IDE, Still/End only on that dock, Manual rect kept as a read-only ghost — two cyan shapes, and the ghost looks live. |
| **C** Ring only, controls in Manual | `option-c.html` | Ring moves and resizes on the IDE, Still/Note/End stay on the Manual toolbar, no OS dock — you leave the framed app to act. |
| **D** In-app only (trapped) | `option-d.html` (same picture as `00-before-trapped.html`) | Current pain / baseline: everything inside the main window — the foreign IDE is unreachable. |
| **E** Fat second WebView float | `option-e.html` | Hollow ring plus a tall window (hint, nudge arrows, ±), desk148-ish; Manual rect shown off, then on, as one option — a second tall window beside the ring. |
| **F** Free dock | `option-f.html` | Like A, but the strip floats and can park on another corner — the hole stays clear, and the dock can drift away. |
| **G** Manual steps back | `option-g.html` | Like A, with Manual collapsed to a “Session on Charter” chip — the IDE is the focus, and snap/annotate wait behind Restore. |
| **H** One-shot snip | `option-h.html` | No persistent armed frame: momentary region, Still, then gone; Manual keeps the notes — nothing left to nudge between stills. |

**G + tray lean (not Accepted):** [`g-tray-index.html`](g-tray-index.html) — the same chip and a hollow stroke, with a 48px side rail in place of the south dock. Notes in [`RESEARCH_G_TRAY.md`](RESEARCH_G_TRAY.md).

## Option A states (not separate paths)

| State | File |
|-------|------|
| Idle / armed | `option-a.html` · `01-idle-armed.html` |
| Recording (session clock, not video) | `02-recording.html` |
| Paused | `03-resume-paused.html` |
| Edge clamp | `04-edge-clamp.html` |
| Still beat | `05-still-beat.html` |

`06-rejected-dual-chrome.html` is an earlier combined sheet. Those pictures are now Option B and Option E. It is not a verdict.

## What the annotations mean

Studio `.anno` labels are not product chrome.

- **Drag header** moves the ring (and, on A and G, the glued dock).
- **Drag edges and corners** resize the hole.
- **Hole** is click-through. It is not a drag target.
- **Checkboxes** (Assist, Mist) are dedicated hits. On A, F, and G they are shown off.
- **Primary** Still / End (and Note, where that option puts it) vs **secondary** Window / Monitor / Page / Annotate.
- On B the Manual rect is labeled **read-only ghost**.
- On H the dashed region is momentary. Beat 2 has no frame.

## Explicit

This folder does **not** implement product UI. No Jira writes from this gallery. Pick happens in Designer review, then a later Bridge chat can write Spec and tickets.
