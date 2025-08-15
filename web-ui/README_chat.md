# Daemonium Web-UI — Chat Quick Start

This guide explains how to run the basic chat UI in the Next.js web app and test the Ollama proxy API locally.

## Overview
- The chat page lives at `/chat` and uses `ChatInterface` with endpoint `/api/ollama`.
- The server-side proxy `src/app/api/ollama/route.ts` forwards requests to your local Ollama server.
- Default model is `llama3:latest` (configurable).

## Prerequisites
- Node.js 18+ (recommended Node 20)
- Ollama installed and running locally
  - Default server: `http://localhost:11434`
  - Ensure the model exists or allow Ollama to pull it on first use (e.g., `llama3:latest`).

## Configuration
- Copy `.env.example` to `.env` in the `web-ui/` directory and adjust as needed:
```
# Ollama server and model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
```
- Legacy variables are supported if needed:
```
# Optional legacy configuration
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

## Test the API via PowerShell
Test the proxy endpoint directly to verify connectivity with your Ollama server.

```powershell
# Set port printed by Next.js (e.g., 3000 or 3002)
$port = 3002

# Send a test prompt to /api/ollama
$body = @{ message = "Say hello as a philosopher." } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:$port/api/ollama" -ContentType "application/json" -Body $body
```

You should receive a JSON response like:
```
{
  "response": "...model output..."
}
```

Optional: Quick Ollama health checks (direct to Ollama, not through Next.js):
```powershell
# List available models
Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET
```

## Change Model / Server
- Change `OLLAMA_MODEL` and/or `OLLAMA_BASE_URL` in `.env` and restart the dev server.
- Example (temporary for current session):
```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3:latest"
npm run dev
```

## Troubleshooting
- 404 on `/chat`: ensure the dev server is running and the path is correct (`/chat`).
- 502 from `/api/ollama`: verify the Ollama server is reachable and the model is available.
- Port conflicts: Next.js picks a fallback port automatically; use the printed URL in logs.

## File References
- API proxy: `src/app/api/ollama/route.ts`
- Chat page: `src/app/chat/page.tsx`
- Chat component: `src/components/chat/chat-interface.tsx`
- Env example: `.env.example`

## Stop the Server
- Press `Ctrl + C` in the terminal running `npm run dev`.
