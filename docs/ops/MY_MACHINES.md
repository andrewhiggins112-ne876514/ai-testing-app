# Cursor My Machines (local worker)

Lets a Cloud/PM agent run terminals and edits on your Windows PC (like AFK Pilot could).

## Install (once)

1. PowerShell:
   ```powershell
   irm 'https://cursor.com/install?win32=true' | iex
   ```
2. New PowerShell window:
   ```powershell
   agent --version
   agent login
   ```
   Sign in with the **same** Cursor account as the app.

## Run the worker (each session you want cloud→PC)

```powershell
cd C:\Users\User\ai_testing_app
agent worker start --name "home-pc"
```

Leave that window open. Closing it disconnects the machine.

## Use it

1. Open https://cursor.com/agents (or start an agent that offers a machine picker).
2. Under **My Machines**, choose `home-pc`.
3. Talk to that agent — commands can run on your PC.

## Notes

- Outbound HTTPS only; no inbound ports.
- Windows worker: terminals/files yes; GUI computer-use is macOS/Linux only.
- Same Cursor account on app + CLI.
