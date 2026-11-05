---
name: run-local-stack
description: Boot FastAPI (+ optional Gradio) and verify /health on the Windows home PC. Use when starting the app or checking Ollama/Jira config status.
---

# Run local stack

Target OS: Windows home PC. Do not invent cloud deploy steps.

1. venv / deps: `py -3 -m pip install -r requirements.txt` then `py -3 -m playwright install chromium` if needed.
2. Ollama running; default model `qwen2.5-coder:7b` (override with `OLLAMA_MODEL`).
3. Backend: `py -3 -m uvicorn main:app --reload`
4. Health: `Invoke-RestMethod http://127.0.0.1:8000/health` — expect `status=ok`; `jira_configured` may be false.
5. UI (if needed): run Gradio entry from `ui/gradio_app.py` per README / existing scripts.

Never print or request raw API tokens. Settings live under `%LOCALAPPDATA%\ai_testing_app\settings.json`.
