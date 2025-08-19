# 🛠️ Daemonium Technical Stack Documentation

## System Architecture Overview

The Daemonium is built on a microservices architecture using Docker containers with the following components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Ingestion     │────▶│  Data Storage   │────▶│   Processing    │
│   Service       │     │    Layer        │     │    Layer        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      User       │◀────│   Knowledge     │◀────│   Vector        │
│   Interface     │     │     Graph       │     │   Embeddings    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Core Technologies

### Infrastructure & Containerization
- **Docker**: All services containerized for isolation and portability
- **Docker Compose**: Multi-container orchestration for local development
- **Python 3.11**: Core programming language (slim container variant)
- **UV Package Manager**: Fast Python dependency management
- **Git**: Version control system

### Messaging System
- **Redis 7 (Docker)**: In-memory store for chat session state and orchestrator datasets
  - **Backend**: FastAPI endpoints in `backend/routers/chat.py` use `redis>=5.0.0` (asyncio client) to store/retrieve chat events
  - **Frontend**: Web UI pushes `session_start`, `user_message`, and `session_end` via backend Redis endpoints
  - **Orchestrator**: `chat_orchestrator/master_combiner.js` writes combined datasets to Redis keys (e.g., `master_orchestrator`, `master_orchestrator_active`)
  - **Configuration**: Values loaded from `config/default.yaml` under `redis` (host, port, password, db)
  - **Security**: Password-authenticated Redis per docker-compose; avoid exposing Redis beyond Docker network in production

### Frontend (Web UI)
- **Framework**: Next.js 15 + React 18
- **Styling**: Tailwind CSS
- **Authentication**: Firebase Authentication (Google Sign-In)
  - Provider wraps app in `web-ui/src/app/layout.tsx` via `FirebaseAuthProvider`
  - Context hook `useFirebaseAuth()` → `{ user, loading, signInWithGoogle, signOutUser }`
  - Firebase init in `web-ui/src/lib/firebase.ts`
  - Env: `NEXT_PUBLIC_FIREBASE_*` in `web-ui/.env.example`
- **Identity Usage**: `user.uid` (preferred) or `user.email` used as `userId` for Redis endpoints and chat session lifecycle in `web-ui/src/components/chat/chat-interface.tsx`
- **Backend API URL**: `NEXT_PUBLIC_BACKEND_API_URL` (default `http://localhost:8000`)

### Backend Authentication (Firebase Admin SDK)
- **Purpose**: Server-side verification of Firebase ID tokens and authorization enforcement for Redis chat endpoints.
- **Implementation**:
  - `backend/auth.py` provides Firebase Admin initialization and `verify_firebase_id_token` FastAPI dependency.
  - Initialized during app lifespan in `backend/main.py`.
  - Applied to Redis chat endpoints in `backend/routers/chat.py` that include `user_id`:
    - POST `/api/v1/chat/redis/{user_id}/{chat_id}`
    - GET `/api/v1/chat/redis/{user_id}/summaries`
    - GET `/api/v1/chat/redis/{user_id}/{chat_id}`
- **Configuration**:
  - YAML: `config/default.yaml` → `firebase.enabled`, `firebase.project_id`, `firebase.credentials.file`, `firebase.credentials.base64`.
  - Env overrides: `FIREBASE_ENABLED`, `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_FILE`, `FIREBASE_CREDENTIALS_BASE64`.
  - Behavior: if disabled, dependency is a no-op for backward compatibility.
- **Dependencies**: `firebase-admin>=6.5.0` (see `requirements.txt`).
- **Testing (PowerShell)**:
  ```powershell
  $token = '<paste_firebase_id_token>'
  $u = '<firebase_uid>'
  $c = '<chatId>'
  $base = 'http://localhost:8000'
  Invoke-RestMethod -Method Get -Headers @{ Authorization = "Bearer $token" } -Uri "$base/api/v1/chat/redis/$($u)/$($c)"
  ```

### Monitoring & Observability
- **Prometheus**: Time series database for metrics collection and storage
  - Metrics: container performance, system resources, application metrics
  - Targets: containers, host system, MongoDB, application services
- **Grafana**: Visualization platform for metrics dashboards
  - Preconfigured dashboards for Docker containers and system metrics
  - Customizable alerts and notifications
- **cAdvisor**: Container metrics collector
- **Node Exporter**: Host system metrics collector
- **MongoDB Exporter**: MongoDB-specific metrics collector
- **Prometheus Client**: Python library for custom application metrics

### Ingestion Layer
- **Requests**: HTTP client library
- **ElementTree**: XML parsing for ArXiv response data
- **Rate limiting**: Configurable throttling to respect API constraints

### Data Storage Layer
- **MongoDB**: NoSQL document database for paper metadata storage
  - Collections: 
  - Indexes for efficient querying
  - Deployment options:
    - Docker container: Standard deployment within main pipeline
    - External Docker: Standalone deployment on separate machine with persistent storage
- **Docker volumes**: Persistent storage for database contents

### Graph Representation
- **Neo4j**: Graph database for representing paper-author-category relationships
  - Nodes: 
  - Relationships: 
  - Cypher query language
  - Deployment options:
    - Docker container: Standard deployment within main pipeline
    - External Docker: Standalone deployment on separate machine with persistent storage
- **Neo4j Python Driver**: Interface for graph operations

### Vector Embeddings
- **Hugging Face Transformers**: Machine learning models for text embeddings
- **PyTorch with CUDA**: GPU-accelerated embeddings generation
- **Ollama**: Local LLM server for text analysis and embedding generation
  - Deployment options:
    - Local instance: Run directly on the host machine
    - Docker container: Standard deployment within main pipeline
    - External Docker: Standalone deployment on separate machine with model management
- **Qdrant**: Vector database for similarity search
  - Collections: book_embeddings
  - Storage of metadata with vectors
  - Deployment options:
    - Docker container: Standard deployment
    - External Docker: Standalone deployment on separate machine
    - WSL2 GPU-accelerated: Enhanced performance with CUDA support
    - Standalone with GPU: Direct installation with CUDA support
    - Remote WSL2 with GPU: Dedicated vector server on separate machine
  - Vector optimization: Native GPU acceleration through Rust with CUDA
  - Benchmarking tools for performance testing
- **Embedding models**: Sentence transformers for semantic representation
- **MongoDB Tracking**: Prevents duplicate PDF processing

### PDF Processing
- **PDF Download**: Direct file retrieval from ArXiv
- **Storage**: Local filesystem storage (E:\AI Research)

### Configuration & Utilities
- **YAML**: Configuration file format
- **Environment Variables**: Runtime configuration
- **Logging**: Standard Python logging

## API Integrations
- **

## Development Tools
- **Python Virtual Environment**: Isolated dependency management
- **Docker Compose**: Local environment orchestration

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Monitoring Environment                  │
│                                                          │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐       │
│   │Prometheus│────▶│ Grafana  │     │  cAdvisor  │       │
│   │          │     │          │     │            │       │
│   └─────────┘     └──────────┘     └────────────┘       │
│        │                               │                 │
│        │          ┌──────────┐         │                 │
│        └──────────│Node      │─────────┘                 │
│                   │Exporter  │                           │
│                   └──────────┘                           │
│                        │                                 │
└────────────────────────│─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Docker Environment                     │
│  (Application containers, databases, and services)       │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

The system supports four deployment architectures:

### 1. Full Docker Deployment with Monitoring

```
┌─────────────────────────────────────────────────────────┐
│                  Monitoring Environment                  │
│                                                          │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐       │
│   │Prometheus│────▶│ Grafana  │     │  cAdvisor  │       │
│   │          │     │          │     │            │       │
│   └─────────┘     └──────────┘     └────────────┘       │
│        │                │              │                 │
└────────│────────────────│──────────────│─────────────────┘
         │                │              │
         ▼                ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                     Docker Environment                   │
└─────────────────────────────────────────────────────────┘
```

### 2. Standard Docker Deployment
```
┌─────────────────────────────────────────────────────────┐
│                     Docker Environment                   │
│                                                          │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐       │
│   │  app    │────▶│ mongodb  │────▶│ sync-neo4j │       │
│   │         │     │          │     │            │       │
│   └─────────┘     └──────────┘     └────────────┘       │
│        │                │                 │              │
│        ▼                ▼                 ▼              │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐       │
│   │ qdrant  │◀────│  neo4j   │◀────│web-interface│       │
│   │         │     │          │     │            │       │
│   └─────────┘     └──────────┘     └────────────┘       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Hybrid Deployment with GPU Acceleration
```
┌─────────────────────────────────────────────────────────┐
│                     Docker Environment                   │
│                                                          │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐       │
│   │  app    │────▶│ mongodb  │────▶│ sync-neo4j │       │
│   │         │     │          │     │            │       │
│   └─────────┘     └──────────┘     └────────────┘       │
│        │                │                 │              │
│        ▼                ▼                 ▼              │
│                   ┌──────────┐     ┌────────────┐       │
│                   │  neo4j   │◀────│web-interface│       │
│                   │          │     │            │       │
│                   └──────────┘     └────────────┘       │
└─────────────────────│──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 Host Environment                      │
│                                                       │
│ ┌─────────┐                                           │
│ │ Qdrant  │ GPU-accelerated vector storage            │
│ │         │ and similarity search                     │
│ └─────────┘                                           │
│      ▲                                                │
│      │                                                │
│ ┌────┴────┐                                           │
│ │PyTorch   │ GPU-accelerated                          │
│ │Embeddings│ vector generation                        │
│ └─────────┘                                           │
└──────────────────────────────────────────────────────┘
```

### 4. Distributed Services Deployment
```
┌────────────────────────────────────────────┐     ┌────────────────────────────────────────────┐
│          Machine 1 (Main Pipeline)         │     │          Machine 2 (MongoDB)               │
│                                            │     │                                            │
│ ┌─────────┐     ┌──────────┐     ┌──────┐ │     │ ┌──────────┐                               │
│ │  app    │────▶│sync-neo4j│────▶│web-ui│ │     │ │ mongodb  │◀─────────────────────────────┤
│ │         │     │          │     │      │ │     │ │          │                               │
│ └─────────┘     └──────────┘     └──────┘ │     │ └──────────┘                               │
└────────────────────────────────────────────┘     └────────────────────────────────────────────┘
                       ▲
                       │
                       ▼
┌────────────────────────────────────────────┐     ┌────────────────────────────────────────────┐
│          Machine 3 (Neo4j)                 │     │          Machine 4 (Qdrant GPU)            │
│                                            │     │                                            │
│ ┌──────────┐                               │     │ ┌─────────┐                                │
│ │  neo4j   │◀─────────────────────────────┤     │ │ qdrant  │◀─────────────────────────────┤
│ │          │                               │     │ │ (GPU)   │                                │
│ └──────────┘                               │     │ └─────────┘                                │
└────────────────────────────────────────────┘     └────────────────────────────────────────────┘
```

## Database Schema

### MongoDB Collections
- **books**: Research paper metadata
  - 
- **vector_processed_books**: book processing tracking for Qdrant vector storage
  - 

### Neo4j Graph Model
- **Nodes**:
  - 
- **Relationships**:
  - 

### Qdrant Collections
- **book_embeddings** ():
  - Vector dimension: Model-dependent (768 default)
  - 

- **book_embeddings** (books):
  - Vector dimension: Model-dependent (768 default)
  - 
  - Source: Book summary/abstract from MongoDB
  - Tracking: summary_processed_papers collection in MongoDB

## Security Considerations
- Docker isolation for service components
- No exposed credentials in code
- Grafana access protected by authentication

## Scaling Considerations
- Container-based architecture supports horizontal scaling
- Database services can be scaled independently
- Modular components allow selective enhancement
- Monitoring stack provides visibility into resource usage for capacity planning
