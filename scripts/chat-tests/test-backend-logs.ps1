param(
  [int]$SinceMin = 5,
  [string]$Pattern = "MCP stdio|Starting MCP stdio|overall timeout|MCP",
  [string]$ComposeFile = "docker-compose.yml"
)

Write-Host "[backend-logs] Collecting backend logs (since ${SinceMin}m) ..." -ForegroundColor Cyan
try {
  $sinceArg = "${SinceMin}m"
  $logs = & docker compose -f $ComposeFile logs --since $sinceArg backend 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[backend-logs] docker compose logs failed: $logs"
    exit 1
  }
  if ($Pattern) {
    $filtered = $logs | Select-String -Pattern $Pattern
  } else {
    $filtered = $logs
  }
  if ($filtered) { $filtered | ForEach-Object { $_.ToString() } }
  else { Write-Host "[backend-logs] No matching log lines." -ForegroundColor Yellow }
  exit 0
}
catch {
  Write-Error "[backend-logs] Failed: $($_.Exception.Message)"
  exit 1
}
