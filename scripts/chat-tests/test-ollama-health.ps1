param(
  [string]$BaseUrl = "http://localhost:11434",
  [int]$TimeoutSec = 15
)

Write-Host "[ollama] Checking tags at $BaseUrl/api/tags ..." -ForegroundColor Cyan
try {
  $resp = Invoke-WebRequest -Uri "$BaseUrl/api/tags" -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    try { $json = $resp.Content | ConvertFrom-Json } catch { $json = $null }
    Write-Host "[ollama] OK ($($resp.StatusCode))" -ForegroundColor Green
    if ($json) { $json | ConvertTo-Json -Depth 5 }
    exit 0
  } else {
    Write-Warning "[ollama] Unexpected status: $($resp.StatusCode)"
    exit 2
  }
}
catch {
  Write-Error "[ollama] Health check failed: $($_.Exception.Message)"
  Write-Host "Hint: ensure Ollama container is running (docker compose --profile ollama up -d ollama)." -ForegroundColor Yellow
  exit 1
}
