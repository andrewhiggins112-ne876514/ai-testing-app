# Option G + side tray — pattern notes

**Status:** Designer lean, under review. **Not Accepted.** Options A–H stay in [`index.html`](index.html). This note does not close a story and does not start Build.

**Frames:** [`g-tray-index.html`](g-tray-index.html).

Tokens stay the settings grammar (`--cyan` `#50cdff`). The foreign IDE is graphite so the capture stroke is the only loud cyan.

## What this route is

Manual steps back to a session chip (Restore only). The only overlay is one rounded shell: a hollow click-through hole, and a 48px icon tray on one side. The note sheet and the still receipt grow **outward** (+240px) so the hole keeps its size. End confirms in a chip on the tray side.

## Sources

### Windows Snipping Tool — reject the top pill as primary

Win+Shift+S dims the whole desktop and parks a small mode toolbar along the top (rectangle, window, full screen, freeform). The selection itself is a bright region stroke with a size readout.

- **Reject** the full-desktop dim, and reject that top pill as the home for Still, Note, and End.
- **Adopt** a stroke that describes a region. Ours stays hollow and stays up for the session, so the IDE chat remains readable.

### ShareX — controls that follow the region

ShareX region capture hands off to after-capture tasks that live in the main workflow, away from the region. The long-running request from people who capture all day is a toolbar that stays with the region instead of a distant window.

- **Adopt** the demand: the verbs travel with the hole.
- **Adapt** the shape. A text strip glued to the south edge covers the bottom of the framed chat. This route uses a narrow icon rail on the side, so the south edge of the hole stays clear.

### VS Code Activity Bar and secondary sidebar

The Activity Bar is a 48px icon rail: icon-only buttons, tooltips, a dark fill, a separator, and a second cluster toward the bottom. The secondary sidebar can sit on the right of the editor and open beside that rail.

- **Adopt** 48px, icon-only, tooltips, a `#161b22` fill, and the top-cluster / hairline / bottom-cluster order.
- **Adapt** the rail into one shell with the capture hole. It is not an editor panel. Collapsed width stays 48px while the hole resizes. The note sheet is the part that grows outward, the way a sidebar opens beside an activity rail.

### Accessibility Insights — hollow highlight

Accessibility Insights draws a rectangle around the target element and leaves the rest of the UI visible and clickable. There is no dim veil.

- **Adopt** the hollow stroke: about 1.5–2px, a soft glow, click-through inside.
- **Adapt** the color to `--cyan` (`#50cdff`) and the radius to the shell (12px). The Insights highlight color is not our token.

### qTest and Xray — session verbs

Exploratory session tools (qTest Explorer, the Xray exploratory app) keep a short verb set: session state, pause and resume, a note, evidence or a screenshot, and end.

- **Adopt** that set: Armed / Rec / Pause, Still, Note, End, Cancel.
- **Adapt** the verbs into icon slots. Assist and Mist are ours. Whether they stay on the rail or move to an overflow is still open.

### Xbox Game Bar — quiet dark widget

Win+G widgets are dark, rounded, and compact. They sit over the game without dimming it. Capture is a small control cluster, not a page of instructions.

- **Adopt** the material: `#161b22` fill, about a 12px radius, a soft elevation shadow, no lesson copy on the shell.
- **Reject** a widget gallery, achievement chrome, and any fat hint window (nudge arrows, ±).

## Adopt / adapt / reject

| | This route |
|--|--|
| **Adopt** | Hollow stroke with a soft cyan glow. 48px icon rail, tooltips, dark fill, hairline, End and Cancel at the foot. Session verbs. Manual as a chip. Quiet dark shell, 12px radius. |
| **Adapt** | Snipping’s region stroke, without the dim or the top pill. ShareX’s “stay with the region,” as a side rail. VS Code’s activity rail, fused to the hole. Insights’ hollow box, in our cyan. qTest/Xray verbs, as icons. Game Bar materials, as one shell. |
| **Reject** | South text dock as the primary control. Full-screen dim. Fat WebView hint with ±. A second cyan Manual rect. Purple, cream, or card-style “AI” chrome. |

## Frames

| Frame | File | What it is for |
|--|--|--|
| Armed | `g-tray-01-armed.html` | Collapsed east tray, chip, drag / resize / hit annotations |
| Recording | `g-tray-02-recording.html` | Status slot becomes Pause, rec pip, stroke pulse, clock in the tooltip |
| Paused | `g-tray-03-paused.html` | Amber stroke, Resume |
| Note | `g-tray-04-note-expanded.html` | Tray grows +240px to the right; hole size held; Esc collapses |
| Edge | `g-tray-05-edge-flip.html` | Hole on the right screen edge; tray flips west; same icon order |
| Still | `g-tray-06-still-beat.html` | Shell hidden, then restored with a hole-only crop in the outward sheet |
| End | `g-tray-07-end-confirm.html` | Confirm chip on the tray side; the chat under the hole stays clear |

## Open for the Designer

1. **Side.** Default the tray to the right, or remember the last side? Frame 05 shows an automatic flip when the hole meets the right edge. That behavior is a proposal.
2. **Assist and Mist.** Keep both on the rail, or move them to an overflow? These frames keep them on the rail, off, so the stack can be judged.
3. **Pause.** Its own icon, or the status glyph becoming Pause / Resume? Frames 02 and 03 use the status slot (pause bars plus a rec pip, then a play glyph). That is a proposal.

## Materials (so Build can match later)

- Shell radius 12px. Stroke 1.75px `var(--cyan)`. Glow `var(--cyan-dim)`. No full-desktop veil.
- Tray collapsed 48px, fill `#161b22`, hairline `var(--cyan-border)` shared with the shell.
- Icon hit 36×32, gap 5px. Hover and focus: `var(--accent-soft)` and a cyan edge. Tooltips are `title` attributes.
- Order: status, Still, Note, Assist, Mist, hairline, End, Cancel.
- Drag: thin north cap (grip). Resize: corners and west / east / south edges. Collapsed tray width stays 48px.
- Note and still receipt: +240px outward. Esc collapses the note sheet.
- Manual: one pill chip, Restore only, one level (OFFICIAL).

Not product code. No Jira write from this note.
