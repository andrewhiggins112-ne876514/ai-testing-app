# Cursor My Machines (local worker)

Lets a Cloud/PM agent run terminals on your Windows PC.

## Important: use Cursor agent, not Grok agent

Grok also installs an `agent` on PATH. Always call Cursor explicitly:

```powershell
$CursorAgent = "$env:LOCALAPPDATA\cursor-agent\agent.cmd"
& $CursorAgent --version
```

## 1. Finish login (if stuck waiting)

The CLI pauses until you complete the browser login.

1. Copy the full `https://cursor.com/loginDeepControl?...` URL from PowerShell.  
2. Paste it into Chrome.  
3. Sign in with the **same** Cursor account as the Cursor app.  
4. Approve the device.  
5. Return to PowerShell — it should finish login (not hang forever after approval).

Check:

```powershell
$CursorAgent = "$env:LOCALAPPDATA\cursor-agent\agent.cmd"
& $CursorAgent status
```

You want signed-in / your email.

## 2. Start the worker (leave window open)

```powershell
cd C:\Users\User\ai_testing_app
$CursorAgent = "$env:LOCALAPPDATA\cursor-agent\agent.cmd"
& $CursorAgent worker start --name "home-pc"
```

Or double-click `scripts\start_worker.cmd`.

Success looks like the process **stays running** (connected / worker running). Closing the window disconnects.

## 3. Where is "My Machines"? (easy to miss)

It is **not** a big section on the main https://cursor.com/agents home page.

It appears only in the **Run on / environment picker** when starting or configuring an agent, **and only after** a logged-in worker is running.

### On the website
1. Keep `worker start` running.  
2. Open https://cursor.com/agents → **New agent**.  
3. Find **Run on** / environment / location control (near the compose box).  
4. Open it → **My Machines** or **Remote Control** → choose `home-pc`.

### In Cursor Desktop
1. Open Agents window.  
2. Under the input, open the **Cloud / Run on / location** dropdown.  
3. **My Machines** / **Remote Control** → `home-pc`.

If the machine is missing: worker not running, wrong account, or login never finished.

## 4. Optional PATH fix

Put `C:\Users\User\AppData\Local\cursor-agent` **before** any Grok agent folder in User PATH, or always use `agent.cmd` as above.
