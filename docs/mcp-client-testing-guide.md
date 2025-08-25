# MCP Client End-to-End Testing Guide (PowerShell + Docker)

This guide verifies the Daemonium backend MCP client over stdio with both Ollama and OpenAI MCP servers. It covers environment setup, enabling MCP debug logs, service health checks, sending chat messages, inspecting backend logs, and troubleshooting timeouts/hangs.

Prereqs:
- Docker Desktop with Compose
- Windows PowerShell
- Project root: repository top-level directory (contains `docker-compose.yml`)
- Optional: `OPENAI_API_KEY` for OpenAI path


## 1) Configure environment (Compose overrides)

Use the project `.env` file to override backend env vars. Example entries:

```
# Logging + MCP debug/timeout controls
LOG_LEVEL=DEBUG
MCP_DEBUG=1
MCP_INIT_TIMEOUT=10
MCP_OVERALL_TIMEOUT=45

# Ollama defaults (backend uses container hostname `ollama`)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL_GENERAL_KG=llama3.1:latest

# OpenAI defaults (set your key)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=60
```

Verify the values load into the backend container after (re)create.


## 2) Start/refresh services

PowerShell (run in repository root):

```powershell
# Start DBs and backend; include Ollama profile when testing Ollama
# Option A: bring everything you need
# (MongoDB + Redis + Backend + Ollama)
docker compose --profile ollama up -d mongodb redis backend ollama

# If you edited .env, force-recreate backend to pick up changes
docker compose up -d --force-recreate backend

# (Optional) build if Python deps changed
docker compose build backend
```

Check containers:

```powershell
docker compose ps
```


## 3) Health checks

- Backend HTTP health (503 during initial DB warmup is expected):

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

- Ollama tags (if using local Ollama container on port 11434):

```powershell
Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing | Select-Object -ExpandProperty Content
```

- Confirm backend env values inside the running container:

```powershell
# Print selected envs in the backend container
docker compose exec backend printenv LOG_LEVEL MCP_DEBUG MCP_INIT_TIMEOUT MCP_OVERALL_TIMEOUT OLLAMA_BASE_URL OLLAMA_MODEL_GENERAL_KG OPENAI_MODEL OPENAI_TIMEOUT | sort
```


## 4) Enable/verify MCP debug logs

The backend enables verbose MCP logs when `MCP_DEBUG=1` (see `backend/main.py`). Inspect logs:

```powershell
# tail backend logs (Ctrl+C to stop)
docker compose logs -f --since 5m backend
```

You should see debug entries from logger `backend.mcp_client` like:
- "Starting MCP stdio server" with command/args and timeouts
- "MCP stdio call succeeded" or a timeout warning


## 5) Send chat via backend API (Ollama MCP server)

Endpoint: `POST /api/v1/chat/message` with JSON body per `backend/models.py::ChatMessage`.

```powershell
# Prepare request body as PowerShell object
$body = @{ 
  message = "Hello, Nietzsche. In one sentence, define the will to power."; 
  author  = "Friedrich Wilhelm Nietzsche" 
} | ConvertTo-Json

# Send request to backend (select Ollama MCP)
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/chat/message?mcp_server=ollama" `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 6
```

Expected JSON includes fields of `ChatResponse`: `response`, `author`, optionally `confidence`, `sources`.

If the call succeeds, backend logs show MCP stdio server spawn and tool call.


## 6) Send chat via backend API (OpenAI MCP server)

Requirements:
- `OPENAI_API_KEY` present in `.env` (or set in your shell before `up -d --force-recreate backend`)
- Backend image contains `openai` Python SDK (see `requirements.txt`) and MCP server script is available at `/app/mcp-service/mcp_server_openai.py` (auto-copied by Dockerfile).

```powershell
# (Optionally export for this session before recreate)
$env:OPENAI_API_KEY = "sk-...your-key..."

# Recreate backend so env applies
docker compose up -d --force-recreate backend

# Prepare request body
$body = @{ 
  message = "In two sentences, summarize Plato's theory of Forms."; 
  author  = "Plato" 
} | ConvertTo-Json

# Send request to backend (select OpenAI MCP)
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/chat/message?mcp_server=openai" `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 6
```

If unauthorized, ensure `OPENAI_API_KEY` is set and the backend was recreated.


## 7) Verify bounded timeout behavior

- Configure a short overall timeout to observe the protective bound:

```powershell
# Set a low timeout in .env (e.g., MCP_OVERALL_TIMEOUT=5), then:
docker compose up -d --force-recreate backend

# Send a chat request again (ollama or openai)
# Watch logs for the timeout warning while the request returns promptly
```

Expected backend log warning (example):
- `MCP stdio overall timeout exceeded (cmd=... overall=5s)`

This confirms `MCP_OVERALL_TIMEOUT` is applied around server spawn, handshake, and tool call.


## 8) Troubleshooting

- Backend health shows 503: DB may still be initializing. Wait and retry.
- No MCP debug lines:
  - Ensure `.env` has `MCP_DEBUG=1` and `LOG_LEVEL=DEBUG`, then `docker compose up -d --force-recreate backend`.
- Ollama errors/timeouts:
  - Ensure Ollama is running: `docker compose --profile ollama up -d ollama`
  - Check tags endpoint on host: `Invoke-WebRequest http://localhost:11434/api/tags`
  - Confirm backend sees the right URL: `OLLAMA_BASE_URL=http://ollama:11434`
- OpenAI path fails:
  - Confirm `OPENAI_API_KEY` inside container: `docker compose exec backend printenv OPENAI_API_KEY`
  - Recreate backend after setting .env
- MCP server scripts missing:
  - Verify files exist: `docker compose exec backend ls -la /app/mcp-service`
  - If missing, rebuild backend: `docker compose build backend && docker compose up -d --force-recreate backend`
- Inspect recent logs for MCP messages:

```powershell
docker compose logs --since 2m backend | Select-String -Pattern "MCP stdio|Starting MCP stdio|overall timeout"
```


## 9) Useful references

- Endpoint: `backend/routers/chat.py` -> `POST /api/v1/chat/message`
- Models: `backend/models.py` -> `ChatMessage`, `ChatResponse`
- MCP client logic: `backend/mcp_client.py`
- Compose env defaults: `docker-compose.yml` (backend service)


## 10) Quick cleanup

```powershell
# Stop services (keep volumes)
docker compose stop backend ollama

# Full down (removes containers, keeps named volumes)
docker compose down
```
