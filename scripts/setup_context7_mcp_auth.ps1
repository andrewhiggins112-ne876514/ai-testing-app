# Configures Cursor user MCP for Context7 via API key (HTTP remote).
# Writes ONLY to %USERPROFILE%\.cursor\mcp.json (not the git repo).
# Merges into existing mcpServers (preserves atlassian, supermemory, etc.).
# Never prints the API key. Fully quit and reopen Cursor after.
#
# Why: Marketplace Context7 plugin uses OAuth only (no token field). Local reliability
# uses HTTP MCP server name `context7` on https://mcp.context7.com/mcp (API key).
#
# Usage:
#   $env:CONTEXT7_API_KEY = '<paste-key-from-context7.com/dashboard>'
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup_context7_mcp_auth.ps1
#
# Optional: store key in %LOCALAPPDATA%\ai_testing_app\settings.json as context7_api_key
# (local-only; never commit). Env var wins when both are set.

$ErrorActionPreference = "Stop"
$mcpPath = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$settingsPath = Join-Path $env:LOCALAPPDATA "ai_testing_app\settings.json"
# Name matches `npx ctx7 setup --cursor --mcp` so Tools & MCP shows one API-key server.
# Marketplace plugin OAuth remains a separate plugin namespace; Local Error there is OK.
$serverName = "context7"
$mcpUrl = "https://mcp.context7.com/mcp"

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

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "FAIL: set `$env:CONTEXT7_API_KEY or settings.json context7_api_key (local only)."
    Write-Host "HINT: create/copy key at https://context7.com/dashboard"
    exit 1
}

$mcpDir = Split-Path $mcpPath -Parent
if (-not (Test-Path $mcpDir)) {
    New-Item -ItemType Directory -Path $mcpDir | Out-Null
}

# Load existing user mcp.json and merge (do not wipe atlassian/supermemory).
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

$entry = [pscustomobject]@{
    url     = $mcpUrl
    headers = [pscustomobject]@{
        Authorization = "Bearer $key"
    }
}

# Replace or add context7-api-key without dropping other servers.
$serversHash = [ordered]@{}
foreach ($prop in $root.mcpServers.PSObject.Properties) {
    if ($prop.Name -ne $serverName) {
        $serversHash[$prop.Name] = $prop.Value
    }
}
$serversHash[$serverName] = $entry
$root.mcpServers = [pscustomobject]$serversHash

$json = $root | ConvertTo-Json -Depth 8
# PowerShell ConvertTo-Json can flatten single-property objects oddly; write via .NET for stable UTF8 no BOM issues.
[System.IO.File]::WriteAllText($mcpPath, $json)

# Probe MCP initialize (never print Authorization).
$initFile = Join-Path $env:TEMP "context7_mcp_init.json"
$outFile = Join-Path $env:TEMP "context7_mcp_init_out.txt"
Set-Content -Path $initFile -Value '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"setup-probe","version":"0.1.0"}}}' -Encoding ascii
$curlArgs = @(
    "-sS", "-o", $outFile, "-w", "%{http_code}",
    "-X", "POST", $mcpUrl,
    "-H", "Authorization: Bearer $key",
    "-H", "Accept: application/json, text/event-stream",
    "-H", "Content-Type: application/json",
    "-H", "MCP-Protocol-Version: 2024-11-05",
    "--data-binary", "@$initFile"
)
$codeStr = & curl.exe @curlArgs
$code = 0
[int]::TryParse($codeStr, [ref]$code) | Out-Null

Write-Host "OK: key source = $source"
Write-Host "OK: merged $serverName into $mcpPath (user-only; keep out of git)"
Write-Host "PROBE: mcp initialize POST -> HTTP $code"
if ($code -eq 200) {
    Write-Host "NEXT: fully quit Cursor and reopen."
    Write-Host "NEXT: Tools & MCP — confirm '$serverName' is connected (green)."
    Write-Host "NEXT: plugin OAuth 'context7' Local Error can be ignored if '$serverName' works."
} else {
    Write-Host "HINT: HTTP $code — check key at https://context7.com/dashboard and re-run."
    exit 1
}
