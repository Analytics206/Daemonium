# Chat Component Test Scripts (PowerShell)

Location: `scripts/chat-tests/`

These scripts validate the chat stack end-to-end: backend health, Ollama health, environment variables inside the backend container, chat via Ollama/OpenAI MCP paths, and MCP debug logs.

Requirements:
- Windows PowerShell
- Docker Desktop with Compose
- Run from the repository root (where `docker-compose.yml` is), unless you specify `-ComposeFile` to point at it

## Quick start

```powershell
# Run the full suite (skips OpenAI if no key is present in backend container)
./scripts/chat-tests/run-chat-tests.ps1

# Or skip OpenAI explicitly
./scripts/chat-tests/run-chat-tests.ps1 -SkipOpenAI
```

## Individual scripts

- `test-backend-health.ps1` — Checks `GET /health`.
- `test-ollama-health.ps1` — Checks Ollama `GET /api/tags` on 11434 by default.
- `test-backend-env.ps1` — Prints key env vars from the backend container (masking `OPENAI_API_KEY`).
- `test-mcp-scripts-present.ps1` — Verifies `/app/mcp-service/` in the backend container contains `mcp_server.py` and `mcp_server_openai.py`.
- `test-mcp-container-env.ps1` — Prints key env vars inside the `mcp` container (`OLLAMA_BASE_URL`, `OPENAI_API_KEY` masked, `MCP_AUTORUN`, `MCP_PORT`).
- `test-chat-ollama.ps1` — Sends a chat request to `POST /api/v1/chat/message?mcp_server=ollama`.
- `test-chat-openai.ps1` — Sends a chat request to `POST /api/v1/chat/message?mcp_server=openai`; use `-SkipIfNoKey` to skip when no key is set.
- `test-backend-logs.ps1` — Shows recent backend logs filtered for MCP-related lines.

## Notes

- For verbose MCP logs, set `MCP_DEBUG=1` in `.env` and recreate the backend: `docker compose up -d --force-recreate backend`.
- OpenAI path requires `OPENAI_API_KEY` in backend env.
- Run Ollama container when testing the Ollama path: `docker compose --profile ollama up -d ollama`.
