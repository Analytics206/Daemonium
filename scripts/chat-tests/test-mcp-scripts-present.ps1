Write-Host "[mcp-scripts] Checking /app/mcp-service in backend container..." -ForegroundColor Cyan
try {
  $ls = & docker compose exec -T backend sh -lc "ls -la /app/mcp-service" 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[mcp-scripts] Failed to list directory: $ls"
    exit 1
  }
  $ls | Out-String | Write-Host
  $required = @('mcp_server.py','mcp_server_openai.py')
  $missing = @()
  foreach ($file in $required) {
    $exists = (& docker compose exec -T backend sh -lc "test -f /app/mcp-service/$file && echo present || echo missing" 2>$null)
    if (($exists | Out-String).Trim() -ne 'present') { $missing += $file }
  }
  if ($missing.Count -gt 0) {
    Write-Host ("[mcp-scripts] Missing: {0}" -f ($missing -join ', ')) -ForegroundColor Yellow
    exit 2
  } else {
    Write-Host "[mcp-scripts] All required scripts present." -ForegroundColor Green
    exit 0
  }
}
catch {
  Write-Error "[mcp-scripts] Error: $($_.Exception.Message)"
  exit 1
}
