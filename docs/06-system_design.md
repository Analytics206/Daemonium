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

### Web UI: Ollama Chat Architecture

- **API Proxy Pattern**: The web UI uses a server-only Next.js route at `web-ui/src/app/api/ollama/route.ts` to proxy requests to a local Ollama server.
  - Purpose: avoid CORS, keep local server details hidden from the browser, and normalize response shape for the UI.
  - Request: `{ message: string }` → forwards to `{ model, prompt, stream: false }` at `${OLLAMA_BASE_URL}/api/generate`.
  - Response: normalized to `{ response: string }` to match `ChatInterface` expectations.
- **Environment Variables**:
  - Primary: `OLLAMA_BASE_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3:latest`).
  - Legacy compatibility: `OLLAMA_API_URL` + `OLLAMA_API_PORT` are supported when `OLLAMA_BASE_URL` is not set.
- **Chat Page**: `web-ui/src/app/chat/page.tsx` renders `ChatInterface` with `endpoint="/api/ollama"` for a minimal, fixed chat route used in local testing.
- **Reusable Component**: `web-ui/src/components/chat/chat-interface.tsx` accepts an optional `endpoint` prop (default `/api/chat`) enabling backend/LLM swapping without changing UI code.
 - **Security**: No auth required for the Ollama proxy in local dev; add middleware/auth if exposed beyond localhost.
 - **Future**: Consider streaming responses, auth/session checks, and per-model selection from UI.

### Web UI: Authentication (Firebase)

- **Provider**: `FirebaseAuthProvider` wraps the app in `web-ui/src/app/layout.tsx`.
- **Hook**: `useFirebaseAuth()` exposes `{ user, loading, signInWithGoogle, signOutUser }`.
 - **Identity**: Use `user.uid` only as `userId` across the chat session lifecycle and Redis API calls. Emails are not accepted by backend auth; Firebase token UID must match the `user_id` path parameter.
- **UI gating**: While `loading` is true, render loading state; if `user` is null, show Google sign-in prompt.
- **Env**: `NEXT_PUBLIC_FIREBASE_*` variables configured in `web-ui/.env.example`; Firebase init in `web-ui/src/lib/firebase.ts`.

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

### Backend: Philosophy Schools Ingestion v2

 - **Purpose**: Ingest curated philosophy schools with explicit keywords for search and joins.
 - **Source File**: `json_bot_docs/philosophy_school/philosophy_school.json`
 - **JSON Schema (array of entries)**:
   - `schoolID: number` (primary identifier)
   - `school: string`
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

## Future Design Considerations
- Asynchronous processing pipeline
- Event-driven architecture for better component decoupling
- Improved error handling and retry mechanisms
- Performance optimization for large-scale book collections
- Automated alerts based on monitoring thresholds

---

*This document is maintained alongside code changes to track design decisions and system architecture evolution.*
