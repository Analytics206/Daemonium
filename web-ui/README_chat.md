# Daemonium Web-UI — Chat Quick Start

This guide explains how to run the basic chat UI in the Next.js web app using the MCP-backed default chat route and how to optionally test the Ollama fallback proxy locally.

## Overview
- The chat page lives at `/chat` and uses `ChatInterface` with endpoint `/api/chat` by default.
- The server-side route `src/app/api/chat/route.ts` proxies to the backend FastAPI MCP endpoint `POST /api/v1/chat/message`, forwarding Firebase Authorization when present.
- Assistant messages are persisted asynchronously to Redis/MongoDB by the `/api/chat` route calling backend Redis endpoints (fire-and-forget).
- The Ollama proxy `src/app/api/ollama/route.ts` remains as a fallback for local tests that hit a local Ollama server directly.

## Prerequisites
- Node.js 18+ (recommended Node 20)
- Backend services running (Docker Compose recommended): FastAPI backend, MCP server, and Ollama
  - Backend base URL typically `http://localhost:8000` (browser) or `http://backend:8000` (inside Docker)
  - MCP server bridges to Ollama (model and timeouts are centrally configured via `config/ollama_config.py`)
- Optional (for fallback route `/api/ollama`): Local Ollama running at `http://localhost:11434`

## Configuration
- Copy `.env.example` to `.env` in the `web-ui/` directory and adjust as needed:
```
# Backend API base URL (for server-side and to expose to browser)
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000

# Optional fallback: direct Ollama proxy (used only by /api/ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Optional legacy variables for fallback route compatibility
OLLAMA_API_URL=http://localhost
OLLAMA_API_PORT=11434
```

## Install and Start (Development)
Run from the `web-ui/` folder:

```powershell
# Install dependencies
npm install

# Start Next.js dev server
npm run dev
```

Notes:
- If port 3000 is busy, Next.js will auto-select a fallback (e.g., 3002). Check the console output, e.g. `http://localhost:3002`.
- Open the chat UI at: `http://localhost:<PORT>/chat`

## Test the default MCP-backed API via PowerShell
Test the Next.js `/api/chat` route which proxies to the backend MCP endpoint and asynchronously persists assistant messages.

```powershell
# Set port printed by Next.js (e.g., 3000 or 3002)
$port = 3000

# Optional: include Firebase ID token to enable Redis persistence
$token = $env:FIREBASE_TEST_ID_TOKEN  # or paste a valid token string

# Send a test prompt to /api/chat
$body = @{ message = "Say hello as a philosopher."; chatId = [guid]::NewGuid().ToString(); userId = "<firebase_uid>"; philosopher = "Friedrich Nietzsche" } | ConvertTo-Json -Depth 5
$headers = @{ 'Content-Type' = 'application/json' }
if ($token) { $headers.Authorization = "Bearer $token" }
Invoke-RestMethod -Method POST -Uri "http://localhost:$port/api/chat" -Headers $headers -Body $body
```

You should receive a JSON response like:
```
{
  "response": "...model output..."
}
```

## Optional: Test the fallback Ollama proxy via PowerShell
Use this only when you want to bypass the backend MCP path and call your local Ollama server directly.

```powershell
# Set port printed by Next.js (e.g., 3000 or 3002)
$port = 3000

# Send a test prompt to /api/ollama
$body = @{ message = "Say hello as a philosopher." } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:$port/api/ollama" -ContentType "application/json" -Body $body
```

Optional: Quick Ollama health checks (direct to Ollama, not through Next.js):
```powershell
# List available models
Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET
```

## Change Model / Server
- Default model selection and timeouts are set centrally in the backend (`config/ollama_config.py`).
- For fallback `/api/ollama`, you can change `OLLAMA_MODEL` and/or `OLLAMA_BASE_URL` in `.env` and restart the dev server.
- Example (temporary for current session):
```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3:latest"
npm run dev
```

## Troubleshooting
- 404 on `/chat`: ensure the dev server is running and the path is correct (`/chat`).
- 502 from `/api/chat`: verify the backend FastAPI service is reachable at `BACKEND_API_URL` and MCP/Ollama are healthy.
- 502 from `/api/ollama`: verify the local Ollama server is reachable and the model is available.
- Port conflicts: Next.js picks a fallback port automatically; use the printed URL in logs.

## File References
- Default chat route (MCP-backed): `src/app/api/chat/route.ts`
- Fallback Ollama proxy: `src/app/api/ollama/route.ts`
- Chat page: `src/app/chat/page.tsx`
- Chat component: `src/components/chat/chat-interface.tsx`
- Env example: `.env.example`

## Stop the Server
- Press `Ctrl + C` in the terminal running `npm run dev`.
