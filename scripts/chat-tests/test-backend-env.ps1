param(
  [string]$ComposeFile = "docker-compose.yml"
)

Write-Host "[backend-env] Inspecting environment variables in backend container..." -ForegroundColor Cyan

$vars = @(
  'LOG_LEVEL','MCP_DEBUG','MCP_INIT_TIMEOUT','MCP_OVERALL_TIMEOUT',
  'OLLAMA_BASE_URL','OLLAMA_MODEL_GENERAL_KG',
  'OPENAI_MODEL','OPENAI_TIMEOUT','OPENAI_API_KEY'
)

try {
  $output = & docker compose -f $ComposeFile exec -T backend printenv 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[backend-env] docker compose exec failed: $output"
    exit 1
  }

  $envMap = @{}
  foreach ($line in $output) {
    if ($line -match '^[A-Za-z0-9_]+=') {
      $k,$v = $line.Split('=',2)
      if ($vars -contains $k) { $envMap[$k] = $v }
    }
  }

  foreach ($k in $vars) {
    if ($envMap.ContainsKey($k)) {
      $val = $envMap[$k]
      if ($k -eq 'OPENAI_API_KEY' -and $val) {
        $masked = if ($val.Length -ge 8) { $val.Substring(0,4) + '***' + $val.Substring($val.Length-4) } else { '***' }
        Write-Host ("{0}={1}" -f $k, $masked)
      } else {
        Write-Host ("{0}={1}" -f $k, $val)
      }
    } else {
      Write-Host ("{0}=<not set>" -f $k) -ForegroundColor Yellow
    }
  }
  exit 0
}
catch {
  Write-Error "[backend-env] Failed: $($_.Exception.Message)"
  exit 1
}
