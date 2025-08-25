param(
  [string]$BaseUrl = "http://localhost:8000",
  [int]$TimeoutSec = 15
)

Write-Host "[backend] Checking health at $BaseUrl/health ..." -ForegroundColor Cyan
try {
  $resp = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
  $json = $null
  try { $json = $resp.Content | ConvertFrom-Json } catch {}
  if ($resp.StatusCode -eq 200 -and $json -and $json.status -eq "healthy") {
    Write-Host "[backend] Healthy (database=$($json.database))" -ForegroundColor Green
    exit 0
  } else {
    Write-Warning "[backend] Unexpected response: $($resp.StatusCode) $($resp.Content)"
    exit 2
  }
}
catch {
  Write-Error "[backend] Health check failed: $($_.Exception.Message)"
  Write-Host "Hint: Service may still be starting or DB is not ready (503 is expected early)." -ForegroundColor Yellow
  exit 1
}
