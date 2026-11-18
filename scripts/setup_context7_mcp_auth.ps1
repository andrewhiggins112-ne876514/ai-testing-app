# Configures Cursor user MCP for Context7 via API key.
# Writes ONLY to %USERPROFILE%\.cursor\mcp.json (not the git repo).
# Merges into existing mcpServers (preserves atlassian, supermemory, etc.).
# Never prints the API key. Fully quit and reopen Cursor after.
#
# WHERE TO PUT YOUR KEY (pick one):
#   A) Paste into this PowerShell session, then run the script:
#        $env:CONTEXT7_API_KEY = 'ctx7sk-...'   # from https://context7.com/dashboard
#        powershell -ExecutionPolicy Bypass -File .\scripts\setup_context7_mcp_auth.ps1
#   B) Or save once in local app settings (never commit):
#        %LOCALAPPDATA%\ai_testing_app\settings.json  →  "context7_api_key": "ctx7sk-..."
#      then run the script with no env var.
#
# Default transport: local stdio (avoids Cursor streamableHttp "terminated" on Windows).
# Optional: -Http to use remote https://mcp.context7.com/mcp instead.
#
# Why: Marketplace Context7 plugin is OAuth-only (no token field). Use this entry named
# `context7` for a reliable local connection.

param(
    [switch]$Http
)

$ErrorActionPreference = "Stop"
$mcpPath = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$settingsPath = Join-Path $env:LOCALAPPDATA "ai_testing_app\settings.json"
$serverName = "context7"
$mcpUrl = "https://mcp.context7.com/mcp"
$nortonPem = Join-Path $env:LOCALAPPDATA "ai_testing_app\norton-web-mail-shield-root.pem"

function Get-ExistingContext7Key {
    param($root)
    if ($null -eq $root -or $null -eq $root.mcpServers) { return $null }
    $existing = $root.mcpServers.PSObject.Properties | Where-Object { $_.Name -eq $serverName }
    if (-not $existing) { return $null }
    $val = $existing.Value
    if ($val.headers -and $val.headers.Authorization) {
        $auth = [string]$val.headers.Authorization
        if ($auth -match '^(?i)Bearer\s+(.+)$') { return $Matches[1].Trim() }
    }
    if ($val.headers -and $val.headers.'Context7-API-Key') {
        return [string]$val.headers.'Context7-API-Key'
    }
    if ($val.env -and $val.env.CONTEXT7_API_KEY) {
        return [string]$val.env.CONTEXT7_API_KEY
    }
    if ($val.args) {
        $argsList = @($val.args)
        for ($i = 0; $i -lt $argsList.Count; $i++) {
            if ($argsList[$i] -eq '--api-key' -and ($i + 1) -lt $argsList.Count) {
                return [string]$argsList[$i + 1]
            }
        }
    }
    return $null
}

$key = $null
$source = $null

if (-not [string]::IsNullOrWhiteSpace($env:CONTEXT7_API_KEY)) {
    $key = [string]$env:CONTEXT7_API_KEY
    $source = "session env CONTEXT7_API_KEY"
} elseif (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    if ($settings.PSObject.Properties.Name -contains "context7_api_key" -and -not [string]::IsNullOrWhiteSpace([string]$settings.context7_api_key)) {
        $key = [string]$settings.context7_api_key
        $source = "settings context7_api_key"
    }
}

$mcpDir = Split-Path $mcpPath -Parent
if (-not (Test-Path $mcpDir)) {
    New-Item -ItemType Directory -Path $mcpDir | Out-Null
}

$root = $null
if (Test-Path $mcpPath) {
    try {
        $root = Get-Content $mcpPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Host "FAIL: could not parse $mcpPath — fix or move it aside, then re-run."
        exit 1
    }
}
if ($null -eq $root) {
    $root = [pscustomobject]@{ mcpServers = [pscustomobject]@{} }
}
if (-not ($root.PSObject.Properties.Name -contains "mcpServers") -or $null -eq $root.mcpServers) {
    $root | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) -Force
}

if ([string]::IsNullOrWhiteSpace($key)) {
    $key = Get-ExistingContext7Key $root
    if (-not [string]::IsNullOrWhiteSpace($key)) {
        $source = "existing mcp.json context7 entry (reused, not printed)"
    }
}

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "FAIL: no API key found."
    Write-Host ""
    Write-Host "Get a key: https://context7.com/dashboard  (looks like ctx7sk-...)"
    Write-Host "Then either:"
    Write-Host "  1) `$env:CONTEXT7_API_KEY = 'ctx7sk-...' ; re-run this script"
    Write-Host "  2) Add `"context7_api_key`": `"ctx7sk-...`" to $settingsPath and re-run"
    Write-Host ""
    Write-Host "Do NOT put the key in the git repo or workspace .cursor/mcp.json"
    exit 1
}

if ($Http) {
    $entry = [pscustomobject]@{
        url     = $mcpUrl
        headers = [pscustomobject]@{
            Authorization = "Bearer $key"
        }
    }
    $mode = "HTTP remote (may log streamableHttp terminated on Windows — toggle off/on if red)"
} else {
    # Windows-friendly stdio: cmd /c npx … ; key in env (not argv) so it is less likely to leak in process lists.
    $envMap = [ordered]@{
        CONTEXT7_API_KEY = $key
    }
    if (Test-Path $nortonPem) {
        $envMap["NODE_EXTRA_CA_CERTS"] = $nortonPem
    }
    $entry = [pscustomobject]@{
        command = "cmd"
        args    = @("/c", "npx", "-y", "@upstash/context7-mcp@latest", "--transport", "stdio")
        env     = [pscustomobject]$envMap
    }
    $mode = "local stdio (recommended on this PC — avoids streamableHttp terminated)"
}

$serversHash = [ordered]@{}
foreach ($prop in $root.mcpServers.PSObject.Properties) {
    if ($prop.Name -ne $serverName) {
        $serversHash[$prop.Name] = $prop.Value
    }
}
$serversHash[$serverName] = $entry
$root.mcpServers = [pscustomobject]$serversHash
[System.IO.File]::WriteAllText($mcpPath, ($root | ConvertTo-Json -Depth 8))

Write-Host "OK: key source = $source"
Write-Host "OK: mode = $mode"
Write-Host "OK: merged $serverName into $mcpPath (user-only; keep out of git)"
Write-Host "NEXT: fully quit Cursor and reopen."
Write-Host "NEXT: Tools & MCP — enable '$serverName' (stdio). Ignore Marketplace plugin OAuth Local Error."
Write-Host "HINT: if stdio fails, re-run with -Http after confirming the key at the dashboard."
