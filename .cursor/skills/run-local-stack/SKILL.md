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

This starts FastAPI on `127.0.0.1:8765` and opens the **native pywebview window**. Verify that window with **Computer Use**. Do not open `/ui/desktop/` in Chrome/IronBee as the product.

1. venv / deps: `py -3 -m pip install -r requirements.txt` then `py -3 -m playwright install chromium` if needed.
2. Ollama running; default model `qwen2.5-coder:7b` (override with `OLLAMA_MODEL`).
3. Desktop app (default): step above. Health: `Invoke-RestMethod http://127.0.0.1:8765/health`.
4. API-only (no UI): `py -3 -m uvicorn main:app --reload` then `Invoke-RestMethod http://127.0.0.1:8000/health`.
5. Gradio only when the slice targets Gradio: `.\venv\Scripts\python.exe run_ui.py` (port 7860); IronBee OK for Gradio only.

Never print or request raw API tokens. Settings live under `%LOCALAPPDATA%\ai_testing_app\settings.json`.
