---
name: run-local-stack
description: Boot the desktop app (preferred) or FastAPI/Gradio and verify health on the Windows home PC.
---

# Run local stack

Target OS: Windows home PC. Do not invent cloud deploy steps.

**Preferred product UI — desktop application (not a browser):**

```powershell
.\venv\Scripts\python.exe desktop_app.py
```

This starts FastAPI on `127.0.0.1:8765` and opens the **native pywebview window**. Do not open `/ui/desktop/` in Chrome/IronBee as the product.

1. venv / deps: `py -3 -m pip install -r requirements.txt` then `py -3 -m playwright install chromium` if needed.
2. Ollama running for product chat; default model `qwen2.5-coder:7b` (override with `OLLAMA_MODEL`).
3. Desktop app (default): step above. Health: `Invoke-RestMethod http://127.0.0.1:8765/health`.
4. API-only (no UI): `py -3 -m uvicorn main:app --reload` then `Invoke-RestMethod http://127.0.0.1:8000/health`.
5. Gradio only when the slice targets Gradio: `.\venv\Scripts\python.exe run_ui.py` (port 7860); IronBee OK for Gradio only.

### Pre–Computer Use checklist (agent verify on 1080 Ti)

Use CU only for visual / occlusion / clickable AC (pytest first otherwise). Before a CU window:

1. Pause Ollama for the short agent CU session (human demos that need chat+UI exempt).
2. Prefer **classic** orb — avoid mystic/aether/neural WebGL during CU.
3. Single desktop window focus; dismiss product Manual/Charter Frame unless the slice is about that overlay.
4. Throttle screenshots; one quiet retry if Cursor CU HUD contests clicks; else note **CU skipped — unsafe** / **CU flake** on the test ticket — never soft-pass.

### Human-hands handoff (CU cannot confirm)

When the Designer (or other human) must verify visually:

1. Leave **`desktop_app.py` running** (or give exactly one start command) so they are not bootstrapping the stack.
2. Pre-seed plans/cases/sessions/stubs/fixtures needed for the check — no “create a plan first” unless that *is* the step under test.
3. In chat **and** on the linked test ticket, post a short **numbered script**: open X → click Y → expect Z (pass/fail). Include desk cache version / URL if relevant.
4. Do not ask them to invent steps or find seed data. Story visual/occlusion AC waits on their confirm (or a later successful CU).

Never print or request raw API tokens. Settings live under `%LOCALAPPDATA%\ai_testing_app\settings.json`.
