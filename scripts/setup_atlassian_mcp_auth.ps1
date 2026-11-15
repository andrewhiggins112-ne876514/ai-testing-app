# Configures Cursor user MCP for Atlassian via API-token (Basic auth).
# Writes ONLY to %USERPROFILE%\.cursor\mcp.json (not the git repo).
# Never prints the token or Base64 value. Fully quit and reopen Cursor after.
#
# Prefer a Rovo MCP scoped token (agent-interface). Classic Jira tokens often get HTTP 401 here.
# Create one: https://id.atlassian.com/manage-profile/security/api-tokens?autofillToken&expiryDays=max&appId=mcp&selectedScopes=all
# Admin must allow API-token auth: admin.atlassian.com → Security → Rovo MCP server.
#
# Usage:
#   .\scripts\setup_atlassian_mcp_auth.ps1
#     → uses jira_email + jira_api_token from local app settings (or jira_mcp_api_token if set)
#   $env:ATLASSIAN_MCP_API_TOKEN = '<scoped-token>'; .\scripts\setup_atlassian_mcp_auth.ps1
#     → uses that token + jira_email from settings (keeps app classic token untouched)

$ErrorActionPreference = "Stop"
$settingsPath = Join-Path $env:LOCALAPPDATA "ai_testing_app\settings.json"
$mcpPath = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$site = "ai-testing-lab.atlassian.net"

if (-not (Test-Path $settingsPath)) {
    Write-Host "FAIL: missing $settingsPath"
    exit 1
}

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
$email = [string]$settings.jira_email
$token = $null
$source = $null

if (-not [string]::IsNullOrWhiteSpace($env:ATLASSIAN_MCP_API_TOKEN)) {
    $token = [string]$env:ATLASSIAN_MCP_API_TOKEN
    $source = "session env ATLASSIAN_MCP_API_TOKEN"
} elseif ($settings.PSObject.Properties.Name -contains "jira_mcp_api_token" -and -not [string]::IsNullOrWhiteSpace([string]$settings.jira_mcp_api_token)) {
    $token = [string]$settings.jira_mcp_api_token
    $source = "settings jira_mcp_api_token"
} else {
    $token = [string]$settings.jira_api_token
    $source = "settings jira_api_token (classic — may fail MCP scopes)"
}

if ([string]::IsNullOrWhiteSpace($email) -or [string]::IsNullOrWhiteSpace($token)) {
    Write-Host "FAIL: need jira_email and a token (ATLASSIAN_MCP_API_TOKEN, jira_mcp_api_token, or jira_api_token)"
    exit 1
}

$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${email}:${token}"))

# Persist Base64 for optional reuse; do not print it
[Environment]::SetEnvironmentVariable("ATLASSIAN_MCP_BASIC", $basic, "User")
$env:ATLASSIAN_MCP_BASIC = $basic

$mcpDir = Split-Path $mcpPath -Parent
if (-not (Test-Path $mcpDir)) {
    New-Item -ItemType Directory -Path $mcpDir | Out-Null
}

# Literal Basic value in user mcp.json — Cursor header env interpolation is unreliable.
# This file is outside the repo; do not copy it into git.
$mcpObj = [ordered]@{
    mcpServers = [ordered]@{
        atlassian = [ordered]@{
            url = "https://mcp.atlassian.com/v2/mcp?site=$site"
            headers = [ordered]@{
                Authorization = "Basic $basic"
            }
        }
    }
}
$mcpObj | ConvertTo-Json -Depth 6 | Set-Content -Path $mcpPath -Encoding UTF8

# HEAD often returns 400 even when auth is fine. Probe with MCP initialize instead.
$initFile = Join-Path $env:TEMP "atlassian_mcp_init.json"
$outFile = Join-Path $env:TEMP "atlassian_mcp_init_out.txt"
Set-Content -Path $initFile -Value '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"setup-probe","version":"0.1.0"}}}' -Encoding ascii
$curlArgs = @(
    "-sS", "-o", $outFile, "-w", "%{http_code}",
    "-X", "POST", "https://mcp.atlassian.com/v2/mcp",
    "-H", "Authorization: Basic $basic",
    "-H", "Accept: application/json, text/event-stream",
    "-H", "Content-Type: application/json",
    "-H", "MCP-Protocol-Version: 2024-11-05",
    "--data-binary", "@$initFile"
)
$codeStr = & curl.exe @curlArgs
$code = 0
[int]::TryParse($codeStr, [ref]$code) | Out-Null

Write-Host "OK: token source = $source"
Write-Host "OK: wrote $mcpPath (user-only; contains secret — keep out of git)"
Write-Host "PROBE: mcp initialize POST -> HTTP $code (ignore HEAD 400 — that is normal)"
if ($code -eq 200) {
    Write-Host "NEXT: disable Cursor Marketplace Atlassian plugin OAuth (avoid dual auth), fully quit Cursor, reopen."
    Write-Host "NEXT: in Tools & MCP confirm 'atlassian' is on and does not ask for browser OAuth."
} else {
    Write-Host "HINT: HTTP $code usually means admin API-token auth is off, or token lacks agent-interface scopes."
    Write-Host "HINT: create scoped MCP token, set `$env:ATLASSIAN_MCP_API_TOKEN, re-run this script, restart Cursor."
}
