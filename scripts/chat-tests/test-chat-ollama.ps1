param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Author = "Friedrich Wilhelm Nietzsche",
  [string]$Message = "Hello, Nietzsche. In one sentence, define the will to power.",
  [int]$TimeoutSec = 60
)

Write-Host "[chat-ollama] POST /api/v1/chat/message?mcp_server=ollama" -ForegroundColor Cyan
try {
  $payload = @{ message = $Message; author = $Author } | ConvertTo-Json -Depth 6
  $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/chat/message?mcp_server=ollama" -ContentType 'application/json' -Body $payload -TimeoutSec $TimeoutSec -ErrorAction Stop
  if ($resp -and $resp.response) {
    $len = ($resp.response | Out-String).Length
    Write-Host "[chat-ollama] OK - author=$($resp.author) response_len=$len" -ForegroundColor Green
    $resp | ConvertTo-Json -Depth 8
    exit 0
  } else {
    Write-Warning "[chat-ollama] No response body or missing 'response' field"
    $resp | ConvertTo-Json -Depth 8
    exit 2
  }
}
catch {
  Write-Error "[chat-ollama] Request failed: $($_.Exception.Message)"
  Write-Host "Hints: Check backend health, MCP_DEBUG logs, and Ollama health." -ForegroundColor Yellow
  exit 1
}
