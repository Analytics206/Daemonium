# 🧠 Daemonium
# 📗 Product Requirements Document (PRD)

## Functional Requirements

### 3.0 Dockerization (DCK)
- **DCK-01**: System shall provide Dockerfiles for each service (graph database, vector database, UI, etc.)
- **DCK-02**: System shall include a `docker-compose.yml` file to orchestrate local setup
- **DCK-03**: System shall support offline development environment with all components running locally

### 3.1 Interaction Modes (INT)
- **INT-01**: System shall enable conversations with individual philosophers (e.g., Nietzsche, Plato)
- **INT-02**: System shall support exploration of philosophical themes (e.g., Free Will, Ethics, Meaning of Life)
- **INT-03**: System shall facilitate multi-philosopher dialogues with conflicting viewpoints
- **INT-04**: System shall support both text chat with text response and speech-to-text/text-to-speech interactions

### 3.2 Data Management (DATA)
- **DATA-01**: System shall store philosophical text chunks organized by concept rather than paragraph
- **DATA-02**: System shall tag content metadata: philosophers, themes, difficulty, source, interpretation
- **DATA-03**: System shall use public domain and open-access sources for philosophical content
- **DATA-04**: System shall maintain a curated knowledge base with concept-tagged philosophical ideas

### 3.3 Database - Graph (DB)
- **DB-01**: System shall use Neo4j to model entity relationships between philosophers, concepts, themes
- **DB-02**: System shall store and query relationships among concepts, themes, and philosophers
- **DB-03**: System shall use Qdrant for semantic search of idea chunks and conversational grounding

### 3.4 Embeddings (EMB)
- **EMB-01**: System shall use HuggingFace sentence transformers models for local embedding
- **EMB-02**: System shall store embedded data in Qdrant with metadata for filtering and retrieval

### 3.5 Configuration & Modularity (CON)
- **CON-01**: System shall provide centralized YAML configuration files
- **CON-02**: System shall support environment variable overrides for configuration values

### 3.6 Logging & Error Handling (LOG)
- **LOG-01**: System shall log conversation interactions and system events
- **LOG-02**: System shall handle and log network and processing errors
- **LOG-03**: System shall provide detailed error messages for debugging purposes

### 3.7 System Monitoring (MON)
- **MON-01**: System shall collect container metrics with Prometheus
- **MON-02**: System shall collect system metrics with Node Exporter
- **MON-03**: System shall include pre-configured Grafana dashboards for monitoring

### 3.8 User Interface (UI)
- **UI-01**: System shall provide a web-based user interface for conversation interactions
- **UI-02**: System shall implement a modern, minimalistic web UI that mimics the look and feel of ChatGPT
- **UI-03**: System shall be responsive and mobile-friendly
- **UI-04**: System shall be designed with architecture that considers future Android and iOS app development
- **UI-05**: System shall support mode switching between philosopher, theme, and dialogue modes
- **UI-06**: System shall display philosophical profiles with core beliefs, works, and style

### 3.9 User Experience (UX)
- **UX-01**: System shall allow users to save and retrieve conversation history
- **UX-02**: System shall track user's philosophical interests and leanings based on interactions
- **UX-03**: System shall provide a "pause and explain" feature for complex philosophical concepts

### 3.10 AI Integration (AI)
- **AI-01**: System shall support retrieval-augmented generation (RAG) for grounded conversations
- **AI-02**: System shall provide LLM selection between GPT-4o API and local Ollama models
- **AI-03**: System shall support configurable integration with both Ollama (local) and ChatGPT (cloud) for LLMs
- **AI-04**: System shall construct prompts based on philosopher profiles and conversational context

### 3.11 Learning Tools (LRN)
- **LRN-01**: System shall include an in-app philosophical dictionary for key terms and concepts
- **LRN-02**: System shall provide feature to save philosophical learning development
- **LRN-03**: System shall provide feature to save philosophical dictionary
- **LRN-04**: System shall implement knowledge learning test/quiz functionality
- **LRN-05**: System shall provide summaries of complex ideas during conversations
- **LRN-06**: System shall reference related thinkers and works during discussions

### 3.12 Voice Integration (VOICE)
- **VOICE-01**: System shall support synthetic voices with appropriate accents for philosophers
- **VOICE-02**: System shall provide configurable TTS integration with support for both local models and ElevenLabs
- **VOICE-03**: System shall provide configurable ASR integration with support for both local models and OpenAI
- **VOICE-04**: System shall provide optional speech-to-text interaction capabilities

### 3.13 Philosophical Content (PHIL)
- **PHIL-01**: System shall include at least 4 philosopher profiles for the MVP
- **PHIL-02**: System shall support at least 4 philosophical themes for the MVP
- **PHIL-03**: System shall include core works, quotes, and philosophical schools for each philosopher

### Optional/Nice-to-Have Features
- **OPT-01**: Gamified exploration of philosophical systems
- **OPT-02**: AI-augmented learning paths based on user interests and interactions
- **OPT-03**: Multi-modal output including visual aids and diagrams
