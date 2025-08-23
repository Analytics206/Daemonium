# Daemonium MCP Server (Ollama)

This service exposes a Model Context Protocol (MCP) server that provides Ollama-backed LLM tools. It runs in Docker and is accessed by MCP-compatible clients (e.g., MCP Inspector, Claude Desktop, Windsurf).

- Source: [mcp-service/mcp_server.py](cci:7://file:///c:/Users/mad_p/OneDrive/Desktop/Py%20Projects/daemonium/mcp-service/mcp_server.py:0:0-0:0)
- Transport: stdio (spawn via `docker exec -i daemonium-mcp python /app/mcp_server.py`)
- Client config (example): [mcp-service/mcp.config.json](cci:7://file:///c:/Users/mad_p/OneDrive/Desktop/Py%20Projects/daemonium/mcp-service/mcp.config.json:0:0-0:0)
- Image: [mcp-service/Dockerfile](cci:7://file:///c:/Users/mad_p/OneDrive/Desktop/Py%20Projects/daemonium/mcp-service/Dockerfile:0:0-0:0)

## What is MCP Inspector and where does it come from?

- MCP Inspector is the official testing UI for the Model Context Protocol.
- Distributed on npm as `@modelcontextprotocol/inspector`.
- It launches a local proxy and connects to an MCP server over stdio.
- In this project, we connect by running:  
  `docker exec -i daemonium-mcp python /app/mcp_server.py`

## Features

- Centralized config integration via [config/ollama_config.py](cci:7://file:///c:/Users/mad_p/OneDrive/Desktop/Py%20Projects/daemonium/config/ollama_config.py:0:0-0:0) and `config/ollama_models.yaml`:
  - Per-task model selection: `general_kg`, `semantic_similarity`, `concept_clustering`
  - Model/task-based timeouts, retry/backoff, warmup
  - Fallback models and server URL selection
- URL resolution order for Ollama:
  1. `OLLAMA_BASE_URL` env
  2. `server.url` from `config/ollama_models.yaml`
  3. `http://ollama:11434` (compose service)
  4. `http://host.docker.internal:11434`
  5. `http://localhost:11434`
- Defaults align with web-ui proxy behavior:
  - `OLLAMA_MODEL=llama3.1:latest` by default
  - Fallback to `host.docker.internal` when loopback fails

## Exposed Tools

- `ollama.chat`
  - Chat completions via Ollama `/api/chat`
  - Args:
    - `messages`: array of `{ role: system|user|assistant, content: string }` (required)
    - `task_type`: optional; selects model via centralized config
    - `model`: optional; overrides model
    - `temperature`: number (default 0.7)
    - `max_tokens`: integer (default 512)
    - `stream`: boolean (default false)
    - `system_prompt`: optional string added as a system message
- `ollama.health`
  - Connectivity + model listing via `/api/tags`
  - Automatically picks a healthy base URL from the fallback list

## Prerequisites

- Docker + Docker Compose
- Node.js (for MCP Inspector)
- Running containers:
  - `daemonium-ollama` (Ollama)
  - `daemonium-mcp` (this MCP server)

## Build and Run (Docker)

- Build:
  ```powershell
  docker compose --profile ollama build ollama
  docker compose --profile mcp build mcp
  ```

- Start services:
  ```powershell
  docker compose --profile ollama up -d ollama
  docker compose --profile mcp up -d mcp
  ```

- Verify containers:
  ```powershell
  docker ps --filter "name=daemonium-(ollama|mcp)"
  ```

## Client: MCP Inspector (Local Testing)

1. Ensure both containers are running: `daemonium-ollama` and `daemonium-mcp`.
2. Launch Inspector:
   ```powershell
   npx @modelcontextprotocol/inspector
   ```
3. In the Inspector UI, Add Server with command:
   ```sh
   docker exec -i daemonium-mcp python /app/mcp_server.py
   ```
4. Test tools:
   - Run `ollama.health` → expect `{ ok: true, base_url, models }`.
   - Run `ollama.chat` with minimal messages array to receive a response.

## Environment Variables

- `OLLAMA_BASE_URL` — base URL for Ollama. Resolution order used by the server:
  1. `OLLAMA_BASE_URL` (env)
  2. `server.url` in `config/ollama_models.yaml`
  3. `http://ollama:11434` (Docker Compose service)
  4. `http://host.docker.internal:11434`
  5. `http://localhost:11434`
- `OLLAMA_MODEL` — default LLM model (default: `llama3.1:latest`).
- `MCP_PORT` — not used for stdio transport; exposed as 8080 by image but not required.
- Additional envs present in the monorepo (not consumed by this server unless extended): `BACKEND_BASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`, `QDRANT_URL`.

## Docker Compose

- Services and profiles in `docker-compose.yml`:
  - `ollama` service (profile: `ollama`) → container `daemonium-ollama`, port `11434`.
  - `mcp` service (profile: `mcp`) → container `daemonium-mcp`.
- Typical startup (PowerShell):
  ```powershell
  docker compose --profile ollama up -d ollama
  docker compose --profile mcp up -d mcp
  ```

## Tool Reference

- `ollama.chat` request shape:
  ```json
  {
    "messages": [
      { "role": "user", "content": "Hello" }
    ],
    "task_type": "general_kg",
    "model": "llama3.1:latest",
    "temperature": 0.7,
    "max_tokens": 512,
    "stream": false,
    "system_prompt": "You are a helpful assistant"
  }
  ```
- Streaming: when `stream=true`, chunks are aggregated server-side and returned as a single string.
- Timeouts: resolved via centralized config per model/task (fallback 60s).

## Troubleshooting

- `ollama.health` fails with `No reachable Ollama endpoint`:
  - Confirm `daemonium-ollama` is running and Ollama is pulled: `docker compose --profile ollama up -d ollama`.
  - Set `OLLAMA_BASE_URL` explicitly if needed, e.g., `http://host.docker.internal:11434`.
  - From host, you can test the underlying Ollama API:
    ```powershell
    Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags"
    ```
- `ollama.chat` hangs or times out:
  - Increase timeouts in `config/ollama_models.yaml` or use a smaller model.
  - Verify the model is present in Ollama: `Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags"`.

## Security Notes

- MCP server uses stdio; the exposed port `8080` in the image is a placeholder and not required when using Inspector.
- Do not expose Ollama beyond local/dev networks without authentication and rate limiting.

## Appendix: Client Config

- Example client config (`mcp-service/mcp.config.json`) launches the server inside Docker via stdio:
  ```json
  {
    "mcpServers": {
      "daemonium-ollama": {
        "command": "docker",
        "args": ["exec", "-i", "daemonium-mcp", "python", "/app/mcp_server.py"]
      }
    }
  }
  ```