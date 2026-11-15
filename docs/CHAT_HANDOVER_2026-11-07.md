# AI Testing App — Full Project Handover (2026-11-07)

## Project Goal
Build a local-first AI Testing Agent that can test browser and desktop applications, integrate with Jira (read/write with confirmation), generate reports, and present a high-quality conversational UI with a central energy orb. The long-term vision is a polished desktop application that can eventually replace or sit alongside existing testing tools for software companies.

## Architecture
- **Backend**: FastAPI (`main.py`) with `/chat` and `/health`.
- **Agent**: `agent/agent.py` — Ollama tool-calling loop with session history.
- **Plugins**:
  - `plugins/playwright_runner.py` — step-based Playwright runner with self-healing clicks, screenshots, and report export.
  - `plugins/jira_plugin.py` — read-only list + confirmed write tools (create, transition, comment, epic link).
- **Settings**: `settings/store.py` — local JSON under `%LOCALAPPDATA%\ai_testing_app\settings.json` (no secrets in repo).
- **UI**:
  - Gradio UI (`ui/gradio_app.py`) — original interface.
  - Desktop window (`desktop_app.py` + `ui/desktop/`) — pywebview shell with dual drawers.
- **Orb**: WebGL (Three.js) for mystic / aether / neural / apex. Classic styles remain canvas.

## Current Feature State
- Conversational chat agent with session history.
- Playwright runner: steps, self-healing clicks, screenshots, JSON + Markdown report export.
- Jira: list issues (with type filter), create with confirmation, epic linking, transitions, comments.
- Settings tab / local settings store.
- Reports tab.
- Desktop shell with full-window orb, bottom chat bar, and dual drawers (screen widgets vs app sections).
- Four orb styles: mystic, aether, neural, apex (apex paused).

## Orb Status
- **Mystic**: Accepted (FBM ridge filaments, soft bloom).
- **Aether**: Accepted (orange-gold fiery plasma).
- **Neural**: Accepted (translucent blue glass, dark centre).
- **Apex**: Paused at `66be196`. Continuous arcs exist but are still too faint on dark background. Multiple rim/glow attempts reverted.

## Process Rules
- Use Composer for visual orb passes. Do not escalate to Grok 4.7 unless explicitly asked.
- One attempt only. Revert if not clearly closer.
- Always attach the approved mockup and compare directly.
- Screenshot on the same machine / WebView2 path as the previous good capture.
- Run `scripts/compare_orb.py` and report the score.
- Keep other orb styles untouched when working on one style.
- Prefer free / Auto / Composer models for routine work.

## Earlier History
The original three shared chats (feature design, architecture, and early prototypes) were compiled into documents earlier in the project. If those files still exist in the repo or in Downloads, they remain the source for the full original feature list and design decisions. This handover covers the state as of 2026-11-07.

## Next Step (when tokens allow)
Start a **new chat**.  
Paste this file + the short next prompt.  
Do not continue the long previous thread.