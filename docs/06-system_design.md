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

### Web UI: Redis Chat Session State

- **Purpose**: Persist per-session chat events in Redis for analytics, continuity, and server coordination.
- **Lifecycle**:
  - `session_start` on component mount with state: `userId`, `chatId` (UUID), `date`, `startTime`, `endTime=null`.
  - `user_message` on each user send.
  - `assistant_message` for each model response, pushed by Next.js Ollama proxy route after successful generation.
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
  - Generates `chatId` on mount; uses placeholder `userId='analytics206@gmail'` until auth is added.
  - Sends `session_start` immediately; pushes each `user_message` on send; sends `session_end` on unmount.
  - Reads backend base URL from `NEXT_PUBLIC_BACKEND_API_URL` (default `http://localhost:8000`).
  - Next.js API route `/api/ollama` accepts `{ message, chatId, userId, philosopher }` and, after calling Ollama, fire-and-forget pushes `{ type: 'assistant_message', text, model, source: 'ollama', context }` to the FastAPI Redis endpoint.
  - **Verification (PowerShell)**:
  - `$u='analytics206@gmail'`
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

## Future Design Considerations
- Asynchronous processing pipeline
- Event-driven architecture for better component decoupling
- Improved error handling and retry mechanisms
- Performance optimization for large-scale book collections
- Automated alerts based on monitoring thresholds

---

*This document is maintained alongside code changes to track design decisions and system architecture evolution.*
