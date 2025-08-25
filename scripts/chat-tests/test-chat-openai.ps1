param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Author = "Plato",
  [string]$Message = "In two sentences, summarize Plato's theory of Forms.",
  [int]$TimeoutSec = 60,
  [string]$ComposeFile = "docker-compose.yml",
  [switch]$SkipIfNoKey
)

function Test-OpenAIKeyPresent($ComposeFile) {
  try {
    $val = (& docker compose -f $ComposeFile exec -T backend printenv OPENAI_API_KEY 2>$null)
    if ($LASTEXITCODE -ne 0) { return $false }
    return [bool]$val
  } catch { return $false }
}

if ($SkipIfNoKey) {
  if (-not (Test-OpenAIKeyPresent -ComposeFile $ComposeFile)) {
    Write-Host "[chat-openai] Skipping (OPENAI_API_KEY not set in backend container)" -ForegroundColor Yellow
    exit 0
  }
}

Write-Host "[chat-openai] POST /api/v1/chat/message?mcp_server=openai" -ForegroundColor Cyan
try {
  $payload = @{ message = $Message; author = $Author } | ConvertTo-Json -Depth 6
  $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/chat/message?mcp_server=openai" -ContentType 'application/json' -Body $payload -TimeoutSec $TimeoutSec -ErrorAction Stop
  if ($resp -and $resp.response) {
    $len = ($resp.response | Out-String).Length
    Write-Host "[chat-openai] OK - author=$($resp.author) response_len=$len" -ForegroundColor Green
    $resp | ConvertTo-Json -Depth 8
    exit 0
  } else {
    Write-Warning "[chat-openai] No response body or missing 'response' field"
    $resp | ConvertTo-Json -Depth 8
    exit 2
  }
}
catch {
  Write-Error "[chat-openai] Request failed: $($_.Exception.Message)"
  Write-Host "Hints: Ensure OPENAI_API_KEY is set and backend was recreated; check MCP_DEBUG logs." -ForegroundColor Yellow
  exit 1
}
