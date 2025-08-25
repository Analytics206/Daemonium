# Daemonium

## Overview

This document tracks the system design features, architectural decisions, and implementation details of the Daemonium. It serves as a reference for design patterns, configuration options, and system behaviors that may not be explicitly documented in the BRD or PRD.

## Document Purpose

Unlike the Business Requirements Document (BRD) and Product Requirements Document (PRD), this document focuses on:

1. Technical implementation details
2. System architecture decisions
3. Design patterns used in the codebase
4. Configuration options and their impacts
5. Data flow between system components

## System Design Features

### Configuration Management

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| Centralized YAML Configuration | All system settings stored in `config/default.yaml` | Initial |
| Environment Variable Override | Environment variables can override configuration settings (e.g., `MONGO_URI`) | Initial |
| Configuration Loading Utilities | Common utilities for loading configuration across services | May 2025 |

### Data Organization

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| Category-Based Book Storage | Books are automatically organized in subdirectories by primary arXiv category | May 3, 2025 |

### Database Integration

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| MongoDB Storage | Book metadata stored in MongoDB | Initial |
| Neo4j Graph Database | Book relationships represented in Neo4j | Initial |
| Qdrant Vector Database | Book content vectorized and stored in Qdrant | Initial |

### System Monitoring

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| Prometheus Metrics | Time series database for metrics collection and storage | May 4, 2025 |
| Grafana Dashboards | Visualization platform for metrics with preconfigured dashboards | May 4, 2025 |
| Container Monitoring | Container metrics collection using cAdvisor | May 4, 2025 |
| System Metrics | Host system metrics collection using Node Exporter | May 4, 2025 |
| MongoDB Metrics | Database-specific monitoring using MongoDB Exporter | May 4, 2025 |
| Custom Application Metrics | Python Prometheus client for application-specific metrics | May 4, 2025 |
| Separate Docker Compose | Isolated monitoring stack via docker-compose.monitoring.yml | May 4, 2025 |

### Pipeline Components

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| Neo4j Synchronizer | Synchronizes MongoDB data to Neo4j graph | Initial |
| Web UI | Browser-based interface for exploring data | Initial |

### Jupyter Notebooks

| Feature | Description | Implementation Date |
|---------|-------------|---------------------|
| Database Connectivity Testing | Notebook for testing connections to MongoDB, Neo4j, and Qdrant | May 4, 2025 |
| Connection Status Visualization | Visual reporting of database connectivity status | May 4, 2025 |
| Database Schema Exploration | Interactive exploration of database schemas and contents | May 4, 2025 |
| Environment Variable Configuration | Support for environment variables and .env file for connection settings | May 4, 2025 |

## Design Decisions

### Module-Based Execution

The system supports both direct script execution and module-based execution patterns:
- Module execution pattern (`python -m src.module.script`) is preferred
- This pattern properly handles package imports and dependencies
- The system is designed as a proper Python package structure

### Docker Containerization

- Each service runs in its own Docker container
- Data persistence handled via Docker volumes
- Inter-service communication via Docker network
- Configuration mounted from host to containers

### Book Processing Flow

1. 
## Monitoring Architecture

The monitoring system follows a sidecar pattern with the following components:

1. **Prometheus**: Central metrics collection service
   - Scrapes metrics from all system components
   - Stores time-series data with retention policies
   - Configuration in `config/prometheus/prometheus.yml`

2. **Grafana**: Visualization and dashboard platform
   - Auto-provisioned dashboards in `config/grafana/dashboards/`
   - Preconfigured Prometheus datasource
   - Accessible on port 3001 to avoid conflict with Web UI

3. **Exporters**: Purpose-built metrics collectors
   - cAdvisor: Container resource usage metrics
   - Node Exporter: Host system metrics
   - MongoDB Exporter: Database performance metrics

4. **Application Metrics**: Custom instrumentation points
   - Processing time measurements
   - Success/failure rate tracking

### Web UI: Chat Architecture (MCP default)

- **API Route (default)**: The web UI uses a server-only Next.js route at `web-ui/src/app/api/chat/route.ts` to proxy requests to the backend MCP chat endpoint `POST /api/v1/chat/message`.
  - Purpose: avoid CORS, forward Firebase auth, centralize response normalization, and ensure assistant message persistence.
  - Request from UI: `{ message, chatId?, userId?, philosopher? }` → forwarded to backend as `{ message, author?, context? }` with headers `Authorization?` and `X-User-ID`.
  - Response to UI: normalized `{ response: string, ... }` from backend `ChatResponse`.
- **Assistant Persistence**: After receiving the backend response, the route asynchronously posts an `assistant_message` to the FastAPI Redis endpoint:
  - `POST {BACKEND_API_URL}/api/v1/chat/redis/{user_id}/{chat_id}`
  - Includes `Authorization` when present; backend schedules background MongoDB writes (assistant → `chat_reponse_history`).
- **Environment Variables (Web UI)**:
  - Primary: `BACKEND_API_URL` (server-side) and `NEXT_PUBLIC_BACKEND_API_URL` (browser-side)
- **Chat Page**: `web-ui/src/app/chat/page.tsx` renders `ChatInterface` with `endpoint="/api/chat"` by default.
- **Reusable Component**: `web-ui/src/components/chat/chat-interface.tsx` accepts an optional `endpoint` prop (default `/api/chat`) enabling backend/LLM swapping without changing UI code.
- **Fallback (Ollama Proxy)**: `web-ui/src/app/api/ollama/route.ts` remains available for local testing and proxies directly to Ollama `POST /api/generate`.

### MCP Server: Ollama Tools & stdio data flow

 - **Implementation**: `mcp-service/mcp_server.py` exposes two MCP tools using the Python MCP server:
   - `ollama.chat` — chat completions via Ollama `/api/chat`
   - `ollama.health` — connectivity + model listing via `/api/tags`
 - **Transport**: stdio. Clients (e.g., MCP Inspector) launch inside Docker: `docker exec -i daemonium-mcp python /app/mcp_server.py`.
 - **URL selection (fallback order)**: `OLLAMA_BASE_URL` (env) → `server.url` from `config/ollama_models.yaml` → `http://ollama:11434` → `http://host.docker.internal:11434` → `http://localhost:11434`.
 - **Model selection & timeouts**:
   - Default model: `OLLAMA_MODEL` env or centralized `general_kg` model from `config/ollama_config.py`/`config/ollama_models.yaml`.
   - Optional `task_type` lets the server choose a model via centralized config.
   - Timeouts derived from centralized config per model/task (fallback ~60s). Streaming responses are aggregated to a single string.
 - **Docker Compose**: services `ollama` (profile `ollama`, container `daemonium-ollama`) and `mcp` (profile `mcp`, container `daemonium-mcp`).
 - **Data flow (stdio → Ollama)**:
   1) MCP client calls `ollama.chat`/`ollama.health` over stdio.
   2) Server resolves healthy Ollama base URL using the fallback list.
   3) For chat, server resolves model/timeout via env + centralized config, then POSTs to `/api/chat` (aiohttp).
   4) If `stream=true`, server aggregates streamed chunks; returns the full assistant message as text.
   5) Health lists models from `/api/tags` and returns `{ ok, base_url, models }`.

#### MCP Docker Startup Behavior (MCP_AUTORUN=0)

- **Idle by default**: The MCP container starts with `MCP_AUTORUN=0` to avoid restart loops. On startup, `mcp-service/entrypoint.sh` logs that the container is idling and how to start the stdio server manually.
- **Manual launch (stdio server)**: Start the MCP server inside the container when needed. Recommended approaches:

```powershell
# Start stdio server in the background and write output to a log file inside the container
docker exec -d daemonium-mcp sh -lc '/app/entrypoint.sh >> /app/data/mcp-stdio.log 2>&1'

# Confirm the server process is running
docker exec daemonium-mcp pgrep -a python

# Tail recent server logs
docker exec daemonium-mcp sh -lc 'tail -n 80 /app/data/mcp-stdio.log'
```

- **Compose profiles**: `docker-compose.yml` defines `ollama` and `mcp` profiles. Typical startup:

```powershell
docker compose --profile ollama --profile mcp up -d ollama mcp backend mongodb redis
docker compose ps
docker logs daemonium-mcp --tail 80   # expect idle message when MCP_AUTORUN=0
```

- **Environment**: MCP resolves Ollama via `OLLAMA_BASE_URL` or falls back to Docker network `http://ollama:11434` and other hosts as documented above.

#### Backend: MCP Client Result Parsing and Sanitization

- **Goal**: Ensure only clean assistant text is returned to clients; never leak raw MCP metadata into the API/UI.
- **Implementation**: `backend/mcp_client.py::_try_call_with()` safely extracts text from diverse MCP tool results:
  - Handles list-shaped results and objects exposing `.content` arrays (e.g., MCP CallToolResult content items).
  - Supports dict-shaped results with `content` arrays or direct `text` fields.
  - Falls back to `.text` attribute when present.
  - Aggregates all discovered text parts into a single response string.
- **Benefit**: `/api/v1/chat/message` returns a `ChatResponse` with a clean `response` string; the Web UI chat shows readable assistant messages without MCP metadata artifacts.

##### Verification (PowerShell)

```powershell
# Health checks
Invoke-RestMethod -Uri "http://localhost:8000/health"
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"

# End-to-end chat via MCP (Ollama)
$body = @{ message = "In one sentence, what is your view on truth?"; author = "Nietzsche" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/chat/message?mcp_server=ollama" -Body $body -ContentType "application/json"
# Expect `response` to be clean text with no embedded MCP metadata
```

#### MCP Client: Overall Timeout & Subprocess Launch Debug Logging (v0.3.24-p5)

- **Problem addressed**: rare indefinite hangs during MCP stdio server spawn or handshake.
- **Solution**: `backend/mcp_client.py` wraps the entire stdio lifecycle (spawn → `session.initialize()` → tool call) in an overall timeout and emits detailed debug logs of launch command candidates.
- **Behavior**:
  - Handshake guarded by `MCP_INIT_TIMEOUT` (default 10s).
  - Entire call wrapped by `MCP_OVERALL_TIMEOUT` (default `max(15, MCP_INIT_TIMEOUT + call_timeout + 5)`).
  - Debug logs (when `MCP_DEBUG=1`) show subprocess command candidates, args, and timing, plus success/failure context.
- **Environment variables** (set in `docker-compose.yml` under `backend.environment`):
  - `LOG_LEVEL` (default `INFO`): global logging level.
  - `MCP_DEBUG` (default `0`): set to `1` to enable verbose MCP client logs.
  - `MCP_INIT_TIMEOUT` (default `10`): seconds for handshake `session.initialize()`.
  - `MCP_OVERALL_TIMEOUT` (default `45` here via Compose; runtime default is `max(15, MCP_INIT_TIMEOUT + call_timeout + 5)`).
  - `MCP_SERVER_CMD`, `MCP_SERVER_ARGS` (optional): override stdio server launch command/args when needed.

##### Verification (PowerShell)

```powershell
# Enable verbose logs and set a bounded overall timeout
$env:MCP_DEBUG = '1'
$env:MCP_OVERALL_TIMEOUT = '30'

# Restart backend to apply environment changes (if running via Compose defaults, this overrides at runtime)
docker compose up -d backend

# Send a prompt; expect response within the overall timeout and see debug logs in backend container
$body = @{ message = "Test MCP timeout+debug" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/chat/message?mcp_server=ollama" -Body $body -ContentType "application/json"

# Inspect logs for subprocess launch attempts and timing
docker logs daemonium-backend --tail 200 | Select-String "backend.mcp_client"
```

#### Backend: MCP stdio server scripts (bind mount into container)

- **Why**: The backend spawns MCP stdio servers itself (e.g., `mcp_server.py`, `mcp_server_openai.py`). These scripts must exist inside the backend container under `/app/mcp-service` so the client can resolve absolute paths like `/app/mcp-service/mcp_server.py`.
- **Compose change**: `docker-compose.yml` mounts the host directory `./mcp-service` into the backend container:
  - `services.backend.volumes`: `- ./mcp-service:/app/mcp-service`
- **Effect**: Prevents stdio spawn timeouts due to missing server scripts at runtime when image contents are shadowed by volume mounts.

##### Verification (PowerShell)

```powershell
# Recreate backend to ensure the new mount is applied
docker compose up -d --force-recreate backend

# Verify stdio server scripts are present in the container
docker compose exec backend sh -lc 'ls -la /app/mcp-service | head -n 50'

# Optional: quick health check via backend MCP client (Ollama)
$body = @{ message = "Hello from MCP" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/chat/message?mcp_server=ollama" -Body $body -ContentType "application/json"
```

### Backend: Firebase ID Token Validation

- **Purpose**: Secure Redis chat endpoints by validating Firebase ID tokens and enforcing per-user authorization.
- **Initialization**: `backend/auth.py` initializes Firebase Admin SDK during app startup from `backend/main.py` lifespan.
  - Credentials sources (priority): `FIREBASE_CREDENTIALS_FILE` → `FIREBASE_CREDENTIALS_BASE64` → Application Default Credentials.
  - Config path: `config/default.yaml` → `firebase` section with env overrides: `FIREBASE_ENABLED`, `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_FILE`, `FIREBASE_CREDENTIALS_BASE64`.
- **FastAPI dependency**: `verify_firebase_id_token` in `backend/auth.py`:
  - Extracts `Authorization: Bearer <ID_TOKEN>`.
  - Verifies token via Firebase Admin and checks `uid` matches the `user_id` path param.
  - Errors: `401 Unauthorized` (missing/invalid token), `403 Forbidden` (UID mismatch), `503 Service Unavailable` (init failure).
  - If Firebase is disabled (`firebase.enabled=false`), it no-ops for backward compatibility.
- **Protected endpoints** (`backend/routers/chat.py`):
  - `POST /api/v1/chat/redis/{user_id}/{chat_id}`
  - `GET  /api/v1/chat/redis/{user_id}/summaries`
  - `GET  /api/v1/chat/redis/{user_id}/{chat_id}`
- **Observability & Safety**:
  - Robust logging without exposing tokens or credentials.
  - Initialization failures logged but do not crash startup; dependency responds with 503 while degraded.
- **Verification (PowerShell)**:
  1) Sign in on the Web UI (Firebase Google Sign-In).
  2) Obtain an ID token from the signed-in user (e.g., add a temporary debug log in the Web UI to call `getIdToken()` or use browser devtools and app code to retrieve it).
  3) Test protected endpoints with the token:
  ```powershell
  $u = '<firebase_uid>'
  $c = '<chatId>'
  $token = '<paste_firebase_id_token>'
  $base = 'http://localhost:8000'

  # GET chat history
  Invoke-RestMethod -Method Get -Headers @{ Authorization = "Bearer $token" } -Uri "$base/api/v1/chat/redis/$($u)/$($c)"

  # POST a user message (JSON payload via query param)
  $payload = @{ type='user_message'; text='Hello from PowerShell' } | ConvertTo-Json -Depth 5
  $enc = [System.Web.HttpUtility]::UrlEncode($payload)
  Invoke-RestMethod -Method Post -Headers @{ Authorization = "Bearer $token" } -Uri "$base/api/v1/chat/redis/$($u)/$($c)?input=$enc&ttl_seconds=0"
  ```

### Web UI: Redis Chat Session State

- **Purpose**: Persist per-session chat events in Redis for analytics, continuity, and server coordination.
- **Lifecycle**:
  - `session_start` on component mount with state: `userId`, `chatId` (UUID), `date`, `startTime`, `endTime=null`.
  - `user_message` on each user send.
  - `assistant_message` for each model response, pushed by the Next.js Ollama proxy route after successful generation. The UI does not push assistant messages to avoid duplicates; the API route is the single source of truth for assistant persistence.
  - `session_end` on component unmount with `endTime`.
- **Endpoints** (`backend/routers/chat.py`):
  - POST `/api/v1/chat/redis/{user_id}/{chat_id}?input=<STRING>&ttl_seconds=<INT>`
    - Appends an item to Redis list key `chat:{user_id}:{chat_id}:messages`.
    - `ttl_seconds` optional; if `> 0`, sets/refreshes key TTL.
    - Stored item shape (normalized):
      - Always includes: `{ user_id, chat_id, timestamp: <ISO UTC>, date: <YYYY-MM-DD>, ... }`
      - If `input` is JSON (recommended): elevates common fields to top-level when present:
        - `type` (e.g., `session_start`, `user_message`, `session_end`)
        - `text` (for user message text)
        - `state` (for session_start/end payload)
      - Also keeps `original` with the raw parsed JSON for traceability
      - If `input` is plain string: stores it under `message`
  - GET `/api/v1/chat/redis/{user_id}/{chat_id}` → returns `{ success, key, count, data: [ ... ] }` in insertion order.
- **Front-end integration** (`web-ui/src/components/chat/chat-interface.tsx`):
  - Obtains authenticated identity from Firebase via `useFirebaseAuth()` and sets `userId = user.uid`.
  - Waits for auth readiness: defers history load and `session_start` until `loading === false` and `userId` exists.
  - UI gating: unauthenticated state renders a Google sign-in prompt; authenticated state renders the chat UI.
  - Generates `chatId` for new chats; loads history for existing `chatId`.
  - Push guards: Redis POST/GET calls only execute when both `userId` and `chatId` are present.
  - Reads backend base URL from `NEXT_PUBLIC_BACKEND_API_URL` (default `http://localhost:8000`).
  - Next.js API route `/api/ollama` accepts `{ message, chatId, userId, philosopher }` and, after calling Ollama, fire-and-forget pushes `{ type: 'assistant_message', text, model, source: 'ollama', context }` to the FastAPI Redis endpoint. The UI no longer performs a second assistant push.
  - **Verification (PowerShell)**:
  - `$u='<firebase_uid_or_email>'`
  - `$c='<chatId from browser console>'`
  - `Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/chat/redis/$($u)/$($c)"`
  - Expect to see the initial `session_start` item, followed by `user_message` items; a `session_end` appears after navigating away.
- **Configuration**:
  - Backend Redis connection from `config/default.yaml` (host, port, password, db).
  - Python dependency: `redis>=5.0.0` (async client).

 ### Backend: Async MongoDB Chat History Persistence

- **Purpose**: Durably persist chat events to MongoDB without impacting live Redis performance.
- **Trigger**: After a successful Redis `RPUSH` in `backend/routers/chat.py` endpoint `push_chat_message_to_redis()`.
- **Mechanism**: Schedules a FastAPI `BackgroundTasks` job (fallback: `asyncio.create_task`) to insert into MongoDB collection `chat_history` via `DatabaseManager`.
- **Routing**: Target collection is selected based on message `type`:
  - `assistant_message` → `chat_reponse_history`
  - all other types (e.g., `session_start`, `user_message`, `session_end`) → `chat_history`
- **Document Shape**: Reuses the normalized Redis payload (fields: `user_id`, `chat_id`, `timestamp`, `date`, `type|text|state|message`, `original`) and adds `redis_key` for traceability.
- **Resilience**: Mongo insert errors are logged and do not affect the HTTP response or Redis path.
- **Configuration**:
  - `chat_history` and `chat_reponse_history` registered in `backend/database.py` collections.
  - No new environment variables; uses existing Mongo connection settings.
- **Verification (PowerShell)**:
  - POST a user message to Redis endpoint; immediately GET confirms Redis storage.
  - Check MongoDB `chat_history` to see the user/session payload appear shortly after.
  - POST an assistant payload (`type='assistant_message'`); verify MongoDB `chat_reponse_history` contains the document shortly after.

### Backend: Philosophy Keywords Ingestion v2

- **Purpose**: Ingest curated philosophy themes/keywords for search and ontology support.
- **Source File**: `json_bot_docs/philosophy_keywords/philosophy_keywords.json`
- **JSON Schema (array of entries)**:
  - `theme: string`
  - `definition: string`
  - `keywords: string[]` (normalized: trimmed, case-insensitive deduplication, order preserved)
- **Uploader Script**: `scripts/build_mongodb_metadata/upload_philosophy_keywords_to_mongodb.py` (v2.0.0)
  - Processes only the new array format; legacy formats removed.
  - Upserts one document per theme into MongoDB collection `philosophy_keywords`.
  - `_id = slugified(theme)`; fields include `category`, `filename`, `theme`, `definition`, `keywords`, and `metadata` with `keyword_count`, `upload_timestamp`, `last_updated`, `source_file`.
- **Indexing**:
  - Single-field: `idx_theme`, `idx_filename`, `idx_keywords`.
  - Text index: `philosophy_keywords_text_v2` over `theme`, `definition`, `keywords`.
  - Safety: drops any existing text index before creating the unified text index (Mongo supports one text index per collection).
- **Error Handling & Stats**:
  - Skips non-dict entries or entries missing required fields (`theme`, `keywords`) or invalid `_id`.
  - Logs to `philosophy_keywords_upload.log` and console.
  - Aggregates stats: `processed`, `uploaded`, `updated`, `errors`.
- **Configuration**:
  - Uses `config/default.yaml` → `mongodb` section: `host`, `port`, `database`, `username`, `password` (auth via `authSource=admin` when credentials provided).
- **Execution (PowerShell)**:
  ```powershell
  # From project root
  python scripts/build_mongodb_metadata/upload_philosophy_keywords_to_mongodb.py
  ```

### Backend: Summaries — Philosophy Keywords API (v0.3.17)

- **Purpose**: Expose curated philosophy themes/definitions/keywords for browsing and search.
- **Collection**: `philosophy_keywords` (no `author` field; keyed by slugified `theme`).
- **Schema**: `{ _id: string, theme: string, definition: string, keywords: string[] }` (+ optional uploader metadata fields).
- **Endpoints**:
  - `GET /api/v1/summaries/philosophy-keywords?skip=<int>&limit=<int>` — direct paginated access.
  - `GET /api/v1/summaries/by-collection/philosophy_keywords?limit=<int>` — generic summaries access by collection.
  - `GET /api/v1/summaries/search/philosophy_keywords?query=<string>&limit=<int>` — regex across `theme`, `definition`, `keywords` (leverages text index when available).
 - **Pagination**: `skip` default `0`, `limit` default `100` (max `1000` for direct endpoint; generic routes cap at `100`).
 - **Response**: Consistent with summaries: `{ success, data: [...], total_count, message }` with `_id` stringified.
 - **Error Handling**: Logged exceptions with `HTTPException` responses aligned with other summaries endpoints.
 - **Indexes**: Single text index over `theme`, `definition`, `keywords` from ingestion v2 for efficient search.
 - **Verification**: See release notes v0.3.17 for PowerShell examples.

### Backend: Aphorisms Ingestion v2

- **Purpose**: Preserve nested aphorisms structure from source JSON for accurate theming and search.
- **Source Files**: `json_bot_docs/aphorisms/*.json`
- **Uploader Script**: `scripts/build_mongodb_metadata/upload_aphorisms_to_mongodb.py` (v2.0.0)
  - Document shape:
    - Top-level: `{ _id, filename, author, category, subject: Subject[], metadata }`
    - `subject` is an array of objects: `{ theme?: string, keywords: string[], aphorisms: string[] }` (normalized: trimmed, deduped, order preserved)
    - `_id = "<slug_author>_<slug_category>"`
    - `metadata`: `{ upload_timestamp, last_updated, source_file, theme_count, keyword_count, aphorism_count }`
  - No legacy flattened `keywords` or `aphorisms` at the top level.
- **Indexing** (created on run):
  - Single-field: `idx_author`, `idx_filename`, `idx_category`
  - Nested fields: `idx_subject_theme` (on `subject.theme`), `idx_subject_keywords` (on `subject.keywords`), `idx_subject_aphorisms` (on `subject.aphorisms`)
  - Text index: `aphorisms_text_index` over `author`, `category`, `subject.theme`, `subject.keywords`, `subject.aphorisms` (drops any existing text indexes first to ensure a single text index)
- **Configuration**: Uses `config/default.yaml` → `mongodb` (`host`, `port`, `database`, `username`, `password` with `authSource=admin` when credentials provided). Default port is `27018`.
- **Execution (PowerShell)**:
  ```powershell
  # From project root with your venv active
  python scripts/build_mongodb_metadata/upload_aphorisms_to_mongodb.py
  ```
- **Verification (PowerShell)**:
  ```powershell
  # Verifies indexes, nested structure, and runs smoke queries
  python scripts/build_mongodb_metadata/verify_aphorisms_indexes.py
  ```

#### Backend: Aphorisms Schema Cleanup — Legacy Field Removal (v0.3.22)

- **Purpose**: finalize migration to nested `subject` schema by removing the use of legacy top-level fields from queries and indexes.
- **Affected legacy fields (no longer queried/indexed for aphorisms)**:
  - `themes` (top-level)
  - `text` (top-level)
  - flattened `aphorisms`/`keywords` at top-level (already removed by ingestion v2)
- **Query alignment**:
  - `backend/database.py`:
    - `get_aphorisms()` now filters only by `author`/`philosopher` alias and nested fields: `subject.theme`, `subject.keywords`, `subject.aphorisms`.
    - `global_search()` aphorisms filter excludes legacy `text`/`themes`; retains `author`, `category`, `context`, and nested `subject.*` fields.
    - `ensure_indexes()` drops legacy `aphorisms_themes_idx` if present; no new index is created for top-level `themes`.
  - `backend/routers/aphorisms.py`:
    - `GET /api/v1/aphorisms/by-theme/{theme}` searches `subject.theme` (plus `context` as supplementary text).
    - `GET /api/v1/aphorisms/{keyword}` uses `$or` across `author`, `philosopher` (alias), `category`, `context`, and nested `subject.theme|keywords|aphorisms`.
  - `backend/routers/search.py`:
    - Aphorisms search filter mirrors database changes: nested `subject.*` only; legacy `text`/`themes` removed.
- **Backward compatibility**: requests may still pass `philosopher=` which is mapped to `author` for filtering, but responses normalize to `author`.
- **Tests**: `tests/test_aphorisms_nested_subjects.py` verifies that routes and filters include nested `subject.*` fields only and that legacy fields are not used.

### Backend: Idea Summaries — Keywords Support (v0.3.23)

- **Purpose**: Expose idea-level `keywords` and enable filtering across Idea Summaries.
- **Collection**: `idea_summary` (joins by `author`).
- **Model**: `IdeaSummary` (`backend/models.py`) includes `keywords: string[]` (optional); `_id` aliased to `id` via `populate_by_name`.
- **Endpoints**:
  - `GET /api/v1/ideas/summaries?skip=<int>&limit=<int>&philosopher=<string>&category=<string>&keyword=<string>`
    - In-memory filter when `keyword` is provided: case-insensitive substring match against the document `keywords` array.
    - Also supports `philosopher` (mapped to `author`) and `category` filtering; responses normalize to `author`.
  - `GET /api/v1/summaries/search/idea_summary?query=<string>&limit=<int>`
    - MongoDB regex `$or` includes: `author`, `category`, `title`, `quote`, `summary.section`, `summary.content`, `key_books`, `keywords`.
  - `GET /api/v1/ideas/search/{keyword}`
    - `$or` search over Idea Summaries includes `keywords` as well as other text fields.
- **Pagination**: `skip` default `0`, `limit` default `100` (`le=1000`) for the direct Ideas route; search routes default to `limit=10` (`le=100`).
- **Verification (PowerShell)**:
  ```powershell
  $base = 'http://localhost:8000'
  Invoke-RestMethod -Method Get -Uri "$base/api/v1/ideas/summaries?limit=5"
  Invoke-RestMethod -Method Get -Uri "$base/api/v1/ideas/summaries?keyword=virtue&limit=5"
  Invoke-RestMethod -Method Get -Uri "$base/api/v1/summaries/search/idea_summary?query=virtue&limit=5"
  ```

### Backend: Philosophy Schools Ingestion v2

- **Purpose**: Ingest curated philosophy schools with explicit keywords for search and joins.
- **Source File**: `json_bot_docs/philosophy_school/philosophy_school.json`
- **JSON Schema (array of entries)**:
  - `schoolID: number` (primary identifier)
{{ ... }}
   - `category: string`
   - `summary: string`
   - `corePrinciples: string`
   - `keywords: string[]` (v2: used directly; normalized by trimming and case-insensitive deduplication, order preserved)
 - **Uploader Script**: `scripts/build_mongodb_metadata/upload_philosophy_schools_to_mongodb.py` (v2.0.0)
   - Computes `_id = "school_{schoolID}"` and stores `school_id` as numeric field.
   - Persists: `school`, `category`, `summary`, `core_principles` (mapped from `corePrinciples`), `keywords`.
   - Derived: `school_normalized` and `category_normalized` for equality/search.
   - Metadata: `metadata.upload_timestamp`, `metadata.last_updated`, `metadata.source_file`.
   - No legacy keyword derivation from `summary` or `corePrinciples`.
 - **Indexing**:
   - Single-field/compound: `idx_school_id_unique` (unique), `idx_school`, `idx_category`, `idx_school_category`, `idx_keywords`.
   - Text index: `philosophy_schools_text_v2` over `school`, `summary`, `core_principles`, `keywords`.
   - Safety: drops any existing text index before creating the unified text index (Mongo allows only one text index per collection).
 - **Configuration**:
   - Uses `config/default.yaml` → `mongodb`: `host`, `port`, `database`, `username`, `password` (auth via `authSource=admin` when credentials provided).
 - **Execution (PowerShell)**:
   ```powershell
   # From project root
   python scripts/build_mongodb_metadata/upload_philosophy_schools_to_mongodb.py
   ```

### Backend: Global Search Coverage and Filters (v0.3.16)

- Added `philosophy_schools` to global search coverage in both `backend/database.py` and `backend/routers/search.py`.
- Implemented collection-specific search filter for `philosophy_schools` using regex across:
  - `name`, `school`, `category`, `summary`, `core_principles`, `corePrinciples`, `keywords`.
- Corrected collection naming to `top_10_ideas` across the search router (was `top_ten_ideas` in some paths) to match database naming.
- Content-only search now uses: `books`, `book_summary`, `aphorisms`, `top_10_ideas`, `idea_summary`.
- Notes:
  - Database `philosophy_schools` text index: `philosophy_schools_text_v2` (weights verified), with keywords supported per ingestion v2.
  - Global search falls back to regex where text indexes are not available; router mirrors this behavior per-collection.

### Backend: Global Search — Philosophy Keywords (v0.3.18)

- Added `philosophy_keywords` to global search coverage in `backend/database.py` and `backend/routers/search.py`.
- Collection-specific filter uses regex across: `theme`, `definition`, `keywords`.
- Index alignment: single text index `philosophy_keywords_text_v2` over `theme/definition/keywords` created by uploader v2.

### Backend: Discussion Hooks Indexes & Verification

- **Purpose**: Robust search and efficient lookups for curated discussion questions per author/category.
- **Collection**: `discussion_hook`.
- **Indexing**:
  - Single-field: `idx_author`, `idx_category`, `idx_filename`, `idx_themes`, `idx_keywords`, `idx_discussion_hooks_theme`, `idx_discussion_hooks_keywords`.
  - Text index: `discussion_hooks_text_v2` over nested fields: `discussion_hooks.theme`, `discussion_hooks.hooks`, `discussion_hooks.keywords`.
  - Safety: uploader drops any existing text index before creating the unified text index (Mongo supports one text index per collection).
- **Configuration**: Uses `config/default.yaml` → `mongodb` settings (`host`, `port`, `database`, `username`, `password`).
- **Verification (PowerShell)**:
  ```powershell
  # From project root with your venv active
  python scripts/build_mongodb_metadata/verify_discussion_hook_indexes.py
  ```

## Future Design Considerations
- Asynchronous processing pipeline
- Event-driven architecture for better component decoupling
- Improved error handling and retry mechanisms
- Performance optimization for large-scale book collections
- Automated alerts based on monitoring thresholds

---

*This document is maintained alongside code changes to track design decisions and system architecture evolution.*
