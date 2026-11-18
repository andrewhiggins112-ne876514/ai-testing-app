---
name: context7-use
description: Fetch version-matched library docs before inventing FastAPI/Playwright/Gradio/etc APIs. Use when adding or changing third-party library calls.
---

# Context7 / library docs (pointer skill)

Do **not** invent third-party APIs from training memory. Full gate: `AGENTS.md` (Cursor tooling preferences) and `.cursor/rules/tooling-use.mdc`.

## When

Before adding or changing calls to **FastAPI, Pydantic, Playwright, Gradio, pywebview, Ollama HTTP API, or httpx**, or when a compile/runtime/type error names a library symbol. Also for auth, CORS, browser profiles, and credential-path APIs.

Skip for Python builtins, in-repo modules, and copying an already-working call on the same surface in this repo.

## How

1. Prefer **existing working usage in this repo** and project security rules.
2. Confirm the **installed** package: `.\venv\Scripts\pip.exe show <pkg>` (or read its files). Host Python ≠ venv Python.
3. Follow the Cursor plugin skill **`context7-mcp`**: `resolve-library-id` → `query-docs`, scoped to the **installed** version when possible. One resolve + one query per library per slice.
4. If Context7 MCP errors: use the installed package source or official docs for that version. Continue the slice — do not invent “latest.”
5. Cite package + version + source once on the story/test ticket when the API was version-sensitive.

## Do not

- Copy the full plugin skill body into this repo (pointer only — avoid drift).
- Call Context7 on every turn or for builtins.
- Put secrets, `settings.json`, tokens, Jira payloads, AUT customer data, or credential paths in a docs query.
- Let “latest” docs override the installed venv or project security rules.
- Call Context7 from the **product** runtime (desktop/Gradio/FastAPI app) — build-time IDE only.
- Import Playwright `sync_api` into `plugins/playwright_runner.py` (that runner is `async_api`).
