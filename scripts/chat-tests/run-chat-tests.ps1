param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$OllamaUrl = "http://localhost:11434",
  [string]$ComposeFile = "docker-compose.yml",
  [switch]$SkipOpenAI
)

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$results = @()
function Invoke-Step($name, [scriptblock]$action, [bool]$required=$true) {
  Write-Host "==== $name ====" -ForegroundColor Magenta
  try {
    & $action
    $code = $LASTEXITCODE
  } catch { $code = 1 }
  $status = if ($code -eq 0) { 'PASS' } elseif (-not $required -and $code -eq 0) { 'SKIP' } elseif (-not $required -and $code -ne 0) { 'SKIP' } else { 'FAIL' }
  $results += [pscustomobject]@{ Step=$name; ExitCode=$code; Status=$status }
}

Invoke-Step 'Backend health' { & (Join-Path $here 'test-backend-health.ps1') -BaseUrl $BaseUrl } $true
Invoke-Step 'Ollama health'  { & (Join-Path $here 'test-ollama-health.ps1')  -BaseUrl $OllamaUrl } $true
Invoke-Step 'Backend env'    { & (Join-Path $here 'test-backend-env.ps1')    -ComposeFile $ComposeFile } $true
Invoke-Step 'MCP scripts present (backend container)' { & (Join-Path $here 'test-mcp-scripts-present.ps1') } $true
Invoke-Step 'MCP container env' { & (Join-Path $here 'test-mcp-container-env.ps1') -ComposeFile $ComposeFile } $true
Invoke-Step 'Chat via Ollama' { & (Join-Path $here 'test-chat-ollama.ps1')   -BaseUrl $BaseUrl } $true

if ($SkipOpenAI) {
  Write-Host "Skipping OpenAI chat test as requested." -ForegroundColor Yellow
} else {
  Invoke-Step 'Chat via OpenAI (skips if no key)' { & (Join-Path $here 'test-chat-openai.ps1') -BaseUrl $BaseUrl -ComposeFile $ComposeFile -SkipIfNoKey } $false
}

Invoke-Step 'Backend MCP logs (last 5m)' { & (Join-Path $here 'test-backend-logs.ps1') -SinceMin 5 -ComposeFile $ComposeFile } $true

Write-Host "\n==== SUMMARY ==== " -ForegroundColor Cyan
$results | Format-Table -AutoSize

# Determine overall exit code (ignore optional OpenAI step)
$requiredFailures = ($results | Where-Object { $_.Status -eq 'FAIL' }).Count
if ($requiredFailures -gt 0) { exit 1 } else { exit 0 }
