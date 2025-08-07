
# 🧠 Daimonion
## Overview
Daimonion is an AI-powered conversational platform that brings philosophy to life through interactive dialogues with historical thinkers. This innovative application enables users to explore philosophical concepts, engage in thought-provoking conversations, and gain deeper insights into the works of great philosophers.

### 🎯 Core Objectives
- **Interactive Learning**: Make philosophy accessible and engaging through AI-powered conversations
- **Modular Design**: Support various interaction modes including individual philosophers, thematic explorations, and multi-philosopher debates
- **Educational Depth**: Provide rich, contextual understanding of philosophical concepts
- **Local-First Architecture**: Containerized services for reproducibility and offline development

### ✨ Key Features
- **Multiple Interaction Modes**:
  - Converse with individual philosophers (e.g., Nietzsche, Plato, Kant)
  - Explore philosophical themes (e.g., Free Will, Ethics, Meaning of Life)
  - Participate and moderated debates between philosophers with conflicting viewpoints

- **Rich Philosophical Context**:
  - Detailed philosopher profiles with core beliefs and philosophical schools
  - Thematic exploration of philosophical concepts
  - References to original works and related thinkers

- **Technical Architecture**:
  - **FastAPI REST API**: Comprehensive backend API with 30+ endpoints for all MongoDB collections
  - **Neo4j Enterprise Edition**: Multi-database graph database for modeling relationships between philosophers, concepts, and themes
  - **Qdrant Vector Database**: High-performance vector database for semantic search and retrieval-augmented generation with 768-dimensional embeddings
  - **MongoDB Document Store**: Normalized storage for philosophical texts, summaries, and metadata
  - **Redis Cache**: High-performance in-memory cache with AOF persistence for session management and caching
  - **Node.js 20 LTS Runtime**: JavaScript runtime environment with Redis 4.6+ integration and persistent storage
  - **PostgreSQL Database**: Relational database for structured data and analytics
  - **Containerized Services**: Docker-based deployment for all components with health monitoring
  - **Interactive Documentation**: Auto-generated API docs with Swagger UI and ReDoc
  - **Modular Design**: Easily extensible for future features and content

#### 🗄️ Neo4j Enterprise Edition Multi-Database Support

Daimonion leverages Neo4j Enterprise Edition's multi-database capabilities to provide isolated environments for comparison and experimental work:

**Available Databases:**
- **`daemonium-primary`** - Primary knowledge graph for production data
- **`daemonium-comparison`** - Comparison knowledge graph for A/B testing
- **`daemonium-experimental`** - Experimental features and development

**Database Management Commands:**

```bash
# Setup all configured databases
python scripts/manage_neo4j_databases.py setup

# List all databases with status
python scripts/manage_neo4j_databases.py list

# Show database statistics
python scripts/manage_neo4j_databases.py stats daemonium-primary

# Clear database content (use with caution)
python scripts/manage_neo4j_databases.py clear daemonium-experimental
```

**Knowledge Graph Building with Centralized Multi-Model Configuration:**

The enhanced Neo4j knowledge graph builder features a **centralized configuration system** with specialized 3-model support, robust timeout handling, and intelligent model loading. All timeout and model loading issues have been resolved with the new configuration-driven approach.

**🎯 Model Specialization with Centralized Config:**
- **General KG Tasks** (`deepseek-r1:latest`): Relationship analysis, philosophical influence analysis, argument extraction, thematic analysis
- **Semantic Similarity** (`granite-embedding:278m`): Embeddings generation, similarity calculations, conceptual similarity analysis  
- **Concept Clustering** (`llama3.2:latest`): Concept extraction, concept clustering, philosophical content categorization

**⚙️ Centralized Configuration System:**
- **Configuration File**: `config/ollama_models.yaml` - Central YAML config for all model settings
- **Model-Specific Timeouts**: DeepSeek-R1 (120s), Llama3.2 (60s), Embeddings (60s)
- **Intelligent Retry Logic**: Exponential backoff with configurable attempts
- **Model Loading Detection**: Progressive wait intervals with status checks
- **Startup Model Warmup**: Preloads models to eliminate loading delays
- **Fallback Models**: Alternative models for each task type
- **Environment Overrides**: `OLLAMA_MODEL_*` environment variables

**🚀 Usage Examples:**

```bash
# Build knowledge graph with default centralized config (recommended)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py

# Build knowledge graph in specific database
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --database daemonium-primary
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --database daemonium-comparison

# Use custom configuration file
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --ollama-config /path/to/custom_ollama_config.yaml

# Override specific models (overrides config file)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --general-kg-model "custom-reasoning-model" \
  --semantic-similarity-model "custom-embedding-model" \
  --concept-clustering-model "custom-clustering-model"

# Use environment variables for model overrides
OLLAMA_MODEL_GENERAL_KG=custom-model \
OLLAMA_MODEL_SEMANTIC_SIMILARITY=custom-embedding \
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py

# Legacy compatibility (still supported)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --ollama-model "llama3.1:latest" \
  --embedding-model "snowflake-arctic-embed"

# Custom server URL (overrides config)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --ollama-url http://custom-server:11434

# Switch back to SentenceTransformer for embeddings
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --use-sentence-transformer

# Full command with config and database options
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --database daemonium-primary \
  --ollama-config config/custom_models.yaml \
  --general-kg-model "deepseek-r1:latest"
```

**🔧 Enhanced Command Line Options:**

**Configuration Parameters:**
- `--ollama-config` - Path to Ollama models configuration file (YAML)
- `--config` - Path to main configuration file
- `--database`, `-d` - Target Neo4j database name (e.g., daemonium-primary)
- `--ollama-url` - Ollama server URL (overrides config file)

**Model Override Parameters (override config file):**
- `--general-kg-model` - Model for general knowledge graph tasks and relationship analysis
- `--semantic-similarity-model` - Model for semantic similarity and embedding tasks
- `--concept-clustering-model` - Model for concept extraction and clustering tasks
- `--use-sentence-transformer` - Use SentenceTransformer instead of Ollama for embeddings

**Legacy Parameters (backward compatibility):**
- `--ollama-model` - Legacy: Ollama model to use (overrides general-kg-model and config)
- `--embedding-model` - Legacy: Model for embeddings (overrides semantic-similarity-model and config)

**🛠️ Configuration Hierarchy (highest priority first):**
1. **CLI Arguments** - Command line parameters
2. **Environment Variables** - `OLLAMA_MODEL_GENERAL_KG`, `OLLAMA_MODEL_SEMANTIC_SIMILARITY`, etc.
3. **Configuration File** - `config/ollama_models.yaml`
4. **Built-in Defaults** - Fallback values

**⚡ Performance Features:**
- **Model Warmup**: All models preloaded at startup (eliminates loading delays)
- **Intelligent Timeouts**: Model-specific timeouts prevent failures
- **Retry Logic**: Progressive backoff with configurable attempts
- **Caching**: Embedding and response caching for efficiency
- **Batch Processing**: Optimized batch handling with rate limiting

**🔍 Troubleshooting:**
- **Timeout Issues**: Resolved with model-specific timeouts and retry logic
- **Model Loading**: Progressive wait intervals with status feedback
- **Configuration**: Use `--ollama-config` to specify custom config files
- **Legacy Scripts**: All existing CLI parameters still work for backward compatibility

**Embedding Model Recommendations (based on evaluation):**
- **Best Overall**: `llama3.1:latest` (composite score: 0.324)
- **Best for Semantic Similarity**: `llama3.1:latest` (score: 0.171)
- **Best for Clustering**: `llama3.1:latest` (score: 0.363)
- **Best for Entity Recognition**: `snowflake-arctic-embed` (score: 0.431)
- **Best for Knowledge Graphs**: `snowflake-arctic-embed` (score: 0.377)

**Note:** Both knowledge graph building scripts automatically display comprehensive statistics at the end of execution, including:
- Node types and counts
- Relationship types and counts  
- AI-generated relationships
- Total nodes and relationships
- Philosopher information (enhanced script)
- Concept nodes (enhanced script)

**Knowledge Graph Quality Evaluation:**

```bash
# Evaluate single database with all reports
python scripts/build_neo4j_metadata/evaluate_knowledge_graphs.py --databases daemonium-primary --all-reports

# Compare multiple databases with comprehensive analysis
python scripts/build_neo4j_metadata/evaluate_knowledge_graphs.py --databases daemonium-primary daemonium-comparison --compare --all-reports

# Generate specific report types
python scripts/build_neo4j_metadata/evaluate_knowledge_graphs.py --databases daemonium-primary --text-report
python scripts/build_neo4j_metadata/evaluate_knowledge_graphs.py --databases daemonium-primary --visual-report
```

**Evaluation Features:**
- 📊 **Research-Based Metrics** - Structural, completeness, consistency, and chatbot-specific quality dimensions
- 📈 **Multiple Report Formats** - Terminal output, JSON data, detailed text analysis, and visual PDF charts
- 🔍 **Comparative Analysis** - Side-by-side evaluation of multiple knowledge graph databases
- 💡 **Actionable Recommendations** - Specific suggestions for improving knowledge graph quality
- 📁 **Organized Output** - All reports saved to `scripts/build_neo4j_metadata/reports/` directory

**Quality Metrics Evaluated:**
- **Structural**: Graph density, clustering coefficient, degree distribution
- **Completeness**: Schema coverage, property completeness, linkability
- **Consistency**: Temporal and semantic coherence
- **Chatbot-Specific**: AI enhancement ratio, content accessibility, philosophical domain coverage

#### 🔍 Embedding Model Evaluation & Integration

Daimonion includes a comprehensive evaluation system for selecting the best embedding models for knowledge graph construction. Based on our evaluation results, **`llama3.1:latest` is now the default embedding model** for both knowledge graph builder scripts.

**Quick Start:**
```bash
# Setup required Ollama models
python llm_evaluation/setup_ollama_models.py

# Evaluate all embedding models
python llm_evaluation/main_sentence_transformers.py

# View evaluation results
cat llm_evaluation/eval_results/st_comparison_results.txt
```

**Integration with Knowledge Graph Builders:**
The evaluation results are automatically integrated into both `enhanced_neo4j_kg_build.py` and `improved_neo4j_kg_build.py` scripts:

```bash
# Scripts now default to the best-performing model (llama3.1:latest)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py

# Override with specific embedding model if needed
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --embedding-model snowflake-arctic-embed

# Compare different embedding approaches
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --database daemonium-primary --embedding-model llama3.1:latest
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --database daemonium-comparison --use-sentence-transformer
```

**Evaluation Results Summary:**
- **🏆 Overall Winner**: `llama3.1:latest` (composite score: 0.324)
- **🎯 Best for Semantic Similarity**: `llama3.1:latest` (score: 0.171)
- **🔗 Best for Clustering**: `llama3.1:latest` (score: 0.363)
- **📝 Best for Entity Recognition**: `snowflake-arctic-embed` (score: 0.431)
- **🧠 Best for Knowledge Graphs**: `snowflake-arctic-embed` (score: 0.377)

**Evaluation Features:**
- 🎯 **Specialized Metrics** - Semantic similarity, clustering quality, entity recognition, relation extraction
- 📊 **Comprehensive Analysis** - Evaluates multiple embedding models simultaneously
- 🏆 **Model Ranking** - Automatic ranking and recommendations for best-performing models
- 📈 **Detailed Reports** - JSON results and comparative analysis reports
- 🧠 **Philosophy-Focused** - Test datasets specifically designed for philosophical content
- 🔄 **Auto-Integration** - Results automatically inform knowledge graph builder defaults

**Supported Models:**
- `llama3.1:latest` - **Default** - Best overall performance for philosophical content
- `snowflake-arctic-embed` - Excellent for entity recognition and knowledge graphs
- `nomic-embed-text` - Nomic's high-quality text embedding model
- `mxbai-embed-large` - MixedBread AI's large embedding model
- `all-minilm` - MiniLM embedding model
- `all-MiniLM-L6-v2` - Compact MiniLM variant (SentenceTransformer fallback)

**For detailed documentation, see:** [`llm_evaluation/README.md`](llm_evaluation/README.md)

**Benefits:**
- 🎯 **Optimized Model Selection** - Choose the best embedding model for your specific use case
- 📊 **Quantitative Evaluation** - Data-driven model selection based on comprehensive metrics
- 🔄 **Reproducible Results** - Consistent evaluation framework for comparing models
- 🚀 **Performance Insights** - Understand model strengths and weaknesses for different tasks
- 🎛️ **Flexible Integration** - Easy integration with existing knowledge graph builders
- 📈 **Continuous Improvement** - Framework for evaluating new models as they become available

#### 🔍 Qdrant Vector Database Integration

Daimonion includes a comprehensive Qdrant vector database integration for semantic search and retrieval-augmented generation across philosophical content.

**Vector Database Features:**
- **High-Quality Embeddings**: Uses sentence-transformers (all-mpnet-base-v2) for 768-dimensional embeddings
- **Multiple Collections**: Processes 5 MongoDB collections with specialized text extraction
- **Batch Processing**: Efficient 50-document batches with comprehensive error handling
- **Automatic Collection Creation**: COSINE distance similarity with proper vector configuration
- **Unique Point IDs**: MD5 hashing for consistent point identification
- **Text Preprocessing**: Automatic truncation and cleaning for token limits

**Supported Collections:**
- `book_summaries` - Detailed summaries of philosophical works
- `aphorisms` - Philosophical aphorisms and quotes
- `idea_summaries` - Individual philosophical concept summaries
- `philosopher_summaries` - Comprehensive philosopher overviews
- `top_ten_ideas` - Top 10 philosophical ideas and concepts

**Usage:**
```bash
# Upload all MongoDB collections to Qdrant
python scripts/build_qdrant_metadata/upload_mongodb_to_qdrant.py

# Test Qdrant connection and dependencies
python scripts/build_qdrant_metadata/test_qdrant_connection.py

# Simple connectivity test
python scripts/build_qdrant_metadata/simple_test.py
```

**Configuration Integration:**
- Reads from `config/default.yaml` for database connections
- Automatic MongoDB URL encoding for special characters
- Qdrant REST API (port 6343) and GRPC (port 6344) support
- Configurable text field extraction and metadata preservation

**Dependencies:**
- `qdrant-client>=1.7.0` - Vector database client
- `sentence-transformers>=2.2.2` - High-quality embedding generation

**Benefits:**
- 🔍 **Semantic Search** - Find philosophically related content across all collections
- 🎯 **RAG Integration** - Enable retrieval-augmented generation for chatbot responses
- ⚡ **High Performance** - Optimized vector similarity search with COSINE distance
- 🔄 **Batch Processing** - Efficient handling of large philosophical text collections
- 🛡️ **Error Resilience** - Comprehensive error handling and logging
- 📊 **Metadata Preservation** - Maintains original document structure and metadata

#### 🚀 FastAPI Backend for MongoDB

Daimonion includes a comprehensive REST API backend built with FastAPI, providing programmatic access to all philosophical content stored in MongoDB. This API serves as the foundation for frontend applications and enables integration with external systems.

**API Features:**
- **30+ REST Endpoints** - Complete CRUD operations across all MongoDB collections
- **Interactive Documentation** - Automatic Swagger UI at `/docs` and ReDoc at `/redoc`
- **Async MongoDB Integration** - High-performance operations using Motor driver
- **Docker Containerization** - Fully integrated with existing Docker Compose stack
- **Health Monitoring** - Database connection monitoring and API statistics
- **CORS Support** - Ready for frontend integration with configurable origins
- **Comprehensive Error Handling** - Detailed error responses and logging
- **Pydantic v2 Models** - Complete data validation and serialization

**Available Endpoints:**
- **Philosophers** (`/api/v1/philosophers/`) - Search, filtering, related philosophers discovery
- **Books** (`/api/v1/books/`) - Full text access, summaries, author filtering, chapter navigation
- **Aphorisms** (`/api/v1/aphorisms/`) - Random selection, philosopher/theme filtering
- **Ideas** (`/api/v1/ideas/`) - Top ten philosophical concepts, idea summaries
- **Summaries** (`/api/v1/summaries/`) - Philosophy themes, modern adaptations, discussion hooks
- **Chat** (`/api/v1/chat/`) - Mock chatbot endpoints, personality profiles, conversation starters
- **Search** (`/api/v1/search/`) - Global search, suggestions, collection-specific queries
- **Health & Stats** (`/health`, `/api/v1/stats`) - API monitoring and database statistics

**Quick Start:**
```bash
# Start the API with Docker Compose
docker-compose up backend -d

# Access interactive API documentation
open http://localhost:8000/docs

# Test API health
curl http://localhost:8000/health

# Get API statistics
curl http://localhost:8000/api/v1/stats

# Search philosophers
curl "http://localhost:8000/api/v1/philosophers/search/?query=Nietzsche&limit=5"

# Get random aphorisms
curl "http://localhost:8000/api/v1/aphorisms/random?count=3"
```

**Technical Stack:**
- **FastAPI 0.116.1** - Modern Python web framework with automatic API documentation
- **Motor 3.7.1** - Async MongoDB driver for high-performance database operations
- **Pydantic 2.5.0** - Data validation with pydantic-settings for configuration management
- **Docker Integration** - Python 3.11-slim base image with optimized build process
- **Modular Architecture** - Organized endpoints across multiple router modules
- **Configuration Management** - YAML-based config with Docker environment overrides

**API Benefits:**
- 🔌 **Frontend Ready** - Complete backend API for React/Vue/Angular frontends
- 📊 **Data Access** - Programmatic access to all philosophical content
- 🔍 **Advanced Search** - Global search with suggestions and filtering
- 💬 **Chat Integration** - Mock endpoints ready for LLM integration
- 📈 **Monitoring** - Health checks and performance statistics
- 🐳 **Containerized** - Easy deployment with Docker Compose
- 📖 **Self-Documenting** - Interactive API documentation with examples

**Neo4j Integration Benefits:**
- ✅ **True Data Isolation** - Complete separation between different knowledge graph versions
- ✅ **Easy A/B Testing** - Compare different data processing approaches across databases
- ✅ **Experimental Safety** - Test new features in isolated experimental database
- ✅ **Version Control** - Maintain multiple versions of knowledge graphs simultaneously
- ✅ **Quality Assurance** - Comprehensive evaluation and improvement recommendations
- ✅ **Free for Development** - Neo4j Enterprise Edition is free for local development use

- **Learning Tools**:
  - "Pause and explain" feature for complex concepts
  - In-app philosophical dictionary
  - Conversation history and learning progress tracking
  - Knowledge assessment through quizzes and tests

- **Future-Ready**:
  - Voice interaction support (planned)
  - Mobile-responsive design
  - User authentication and subscription management

### 🚀 Getting Started
Daimonion is designed to run locally using Docker, making it easy to set up and start exploring philosophical ideas. The system supports both local LLM models (via Ollama) and cloud-based models (like GPT-4), giving you flexibility in how you interact with the philosophical content.

## 🛠 Development Setup

### Prerequisites
- Python 3.11+
- [UV](https://github.com/astral-sh/uv) (recommended) or pip
- Docker and Docker Compose

### Setting Up the Environment

#### Option 1: Using UV (Recommended)

1. Install UV (if not already installed):
   ```bash
   pip install uv
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On Unix/macOS
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt  # Production
   uv pip install -r requirements-dev.txt  # Development
   ```

#### Option 2: Using pip

1. ## Windows (PowerShell):
  ```powershell
  # if needed to rebuild .venv
  Remove-Item -Recurse -Force .venv
  # Run the setup script
  python3.11 -m venv .venv

  # Activate the virtual environment
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  python.exe -m pip install --upgrade pip

   # or
   source .venv/bin/activate  # On Unix/macOS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt  # Production
   pip install -r requirements-dev.txt  # Development
   ```
---

## 🚀 Key Features
| Feature                  | Description |
| ------------------------ |-------------|
| 🏠 **Local-first** | Everything runs offline with no cloud dependencies on local network with multi machine support. |
| 💾 **Data Ingestion** | Import philosophical texts. |
| 🗒 **MongoDB Storage** | Stores structured metadata, paper information, and download statuses. |
| 💡 **Semantic Embeddings** | Creates vector embeddings using Hugging Face models, stored in Qdrant for similarity search. |
| 🔧 **Configurable & Modular** | Centralized settings allow switching categories, models, and components. |
| 👀 **User Interface** | User-friendly interface for exploring datasets, knowledge graphs, and similarity search. |
| 📦 **Containerized** | Mostly Dockerized with persistent volumes for reliable data storage and consistent execution. |
---

### Neo4j Graph Database

---

## 📦 System Components
| Component                  | Purpose                                      |
| -------------------------- | -------------------------------------------- |
| **MongoDB**                | Stores philosophical metadata, paper information, and download statuses.   |
| **Neo4j**                  | Stores the author-paper-category graph for knowledge graph analysis. |
| **Qdrant**                 | Stores paper vector embeddings for semantic search with metrics tracking |
| **Config Manager**         | Central config for category, limits, model   |
| **User Interface**         | Web UI for interaction with chatbots and knowledge graph analysis.        |
| **Logger**                 | Tracks events, errors, and skipped entries   |
| **Docker Compose**         | Brings it all together for local use         |
| **Prometheus**             | Time series database for system metrics collection  |

---

## 📥 MongoDB Data Upload Scripts

Daimonion includes a comprehensive suite of MongoDB uploader scripts for populating the database with philosophical content. All scripts are located in `scripts/build_mongodb_metadata/` and follow consistent patterns for error handling, logging, and configuration.

### Available Uploaders

| Script | Collection | Purpose |
|--------|------------|----------|
| `upload_books_to_mongodb.py` | `books` | Core philosophical texts and works |
| `upload_book_summaries_to_mongodb.py` | `book_summaries` | Detailed summaries of philosophical works |
| `upload_philosopher_bios_to_mongodb.py` | `philosopher_bios` | Biographical information about philosophers |
| `upload_philosopher_summaries_to_mongodb.py` | `philosopher_summaries` | Comprehensive philosophical overviews |
| `upload_bibliography_to_mongodb.py` | `bibliography` | Author bibliographies with works and themes |
| `upload_aphorisms_to_mongodb.py` | `aphorisms` | Philosophical aphorisms and quotes |
| `upload_philosophy_themes_to_mongodb.py` | `philosophy_themes` | Core philosophical themes |
| `upload_top_10_ideas_to_mongodb.py` | `top_ten_ideas` | Ranked philosophical concepts |
| `upload_idea_summaries_to_mongodb.py` | `idea_summaries` | Detailed analysis of philosophical ideas |
| `upload_modern_adaptations_to_mongodb.py` | `modern_adaptations` | Contemporary applications of philosophy |
| `upload_persona_cores_to_mongodb.py` | `persona_cores` | Philosopher persona definitions |
| `upload_philosopher_bots_to_mongodb.py` | `philosopher_bots` | Bot persona configurations |
| `upload_chat_blueprints_to_mongodb.py` | `chat_blueprints` | Chat templates and response patterns |
| `upload_conversation_logic_to_mongodb.py` | `conversation_logic` | Conversation flow strategies |
| `upload_discussion_hooks_to_mongodb.py` | `discussion_hooks` | Discussion prompts and questions |

### Universal Features

- **Template File Filtering**: All scripts automatically skip files starting with 'template'
- **Document Merging**: Intelligent updates that preserve existing data while adding new content
- **Comprehensive Logging**: Detailed logs with separate files for each uploader
- **Error Handling**: Robust error handling for connection failures and malformed data
- **Statistics Reporting**: Detailed upload statistics including processed, uploaded, updated, and skipped counts
- **YAML Configuration**: Uses centralized `config/default.yaml` for database connections
- **URL Encoding**: Proper handling of special characters in MongoDB credentials

### Running Individual Uploaders

```bash
# Run a specific uploader
python scripts/build_mongodb_metadata/upload_bibliography_to_mongodb.py

# Run all uploaders in sequence
python scripts/build_mongodb_metadata/run_all_uploaders.py

# Run with options
python scripts/build_mongodb_metadata/run_all_uploaders.py --stop-on-error
python scripts/build_mongodb_metadata/run_all_uploaders.py --dry-run
```

### Data Sources
All uploader scripts read from corresponding directories in `json_bot_docs/`:
- `json_bot_docs/bibliography/` - Author bibliographies
- `json_bot_docs/aphorisms/` - Philosophical aphorisms
- `json_bot_docs/book_summaries/` - Book summaries
- `json_bot_docs/philosopher_bios/` - Philosopher biographies
- And more...

### Prerequisites

1. **MongoDB Container Running**:
   ```bash
   docker-compose up -d mongodb
   ```

2. **Virtual Environment Activated**:
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix/macOS
   ```

3. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   ```
| **Grafana**                | Visualization platform for system metrics dashboards |
| **Kafka**                  | Distributed event streaming platform for messaging |
| **Zookeeper**              | Coordinates the Kafka cluster                |
| **Kafka UI**               | Web interface for Kafka management and monitoring |

---
## 🧵 High Level Overview
 - 

For more deep dive into project and status, see the `docs/` directory.

---
## 💡 Use Cases
### Research & Knowledge Management

### Data Science & Analysis

### AI-Assisted Research

### Education & Learning
- **Personalized Learning Paths**: 
- **Concept Visualization**: 
---
# 🛠️ Setup Instructions
  ### This system runs on a single machine but recommend a multiple machine setup.*
  - System minimum requirements: 16GB RAM, 8GB GPU, 512GB SSD
  - Developer runs on laptop with 16GB RAM, 16GB GPU, 1TB SSD *Not recommended!
---

# ⚠️ Prerequisites
- Git
- Python 3.11+ (Python 3.11 recommended)
- [UV](https://github.com/astral-sh/uv) (for fast Python dependency management)
- Docker and Docker Compose (for containerized deployment)

---

### Installation (Local)
* Note: installs all dependencies in a virtual environment 
## Linux/macOS/WSL:
```bash
# Make the setup script executable
chmod +x scripts/setup_uv.sh

# Run the setup script
./scripts/setup_uv.sh

# Activate the virtual environment
source .venv/bin/activate
```

## Windows (PowerShell):
```powershell
# Remove previous venv if it exists
Remove-Item -Recurse -Force venv
# Create new venv
py -3.11 -m venv venv
python --version
python -m pip install -U pip
# Run the setup script
# ??

# Activate the virtual environment
venv\Scripts\Activate.ps1
```

# Dockerized Deployment - Docker Desktop Running
## 0. Suggested run in venv from scripts above for your operating system

## 1. **Build and start all basic required services:** 196,293
   ```bash
    docker compose up -d
    # or to rebuild
    docker compose up -d --build api
   ```
 - ✔ Network arxiv_pipeline_default         Started     
 - ✔ Container arxiv_pipeline-neo4j-1       Started     

## 3. (optional) Managing Monitoring Containers with Prometheus & Grafana
a. **Start the monitoring stack:**

b. **Access monitoring services:**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (default login: admin/password)

c. **Explore metrics** for:
   - System resources
   - Docker containers
   - MongoDB performance
   - Application-specific metrics

d. **Monitoring Dashboards**
   Pre-configured Grafana dashboards are available in the repository:

   * These dashboards provide visualization for MongoDB operations, system resources, container performance, 
   and vector embedding generation metrics critical for the research paper processing pipeline.

e. **Prometheus Query Documentation**
   Comprehensive documentation for Prometheus queries is available in:

f. **Monitoring Diagnostics**

## 4. Managing Manual Services

### b. Kafka Messaging System
```bash
# Start Kafka with required Zookeeper service
docker compose --profile manual up zookeeper kafka
# Stop Kafka and Zookeeper services
docker compose --profile manual down zookeeper kafka
```
* Kafka broker accessible at: localhost:9092 (from host) or kafka:9092 (from other containers)

### c. Kafka UI Management Interface
```bash
# Start complete Kafka stack with UI
docker compose --profile manual up zookeeper kafka kafka-ui
# Stop complete Kafka stack
docker compose --profile manual down zookeeper kafka kafka-ui
```
* Access Kafka UI at: http://localhost:8080

## 5. Database Connection Settings
```yaml
mongo:

neo4j:

qdrant:

# Qdrant API Metrics
# The database dashboard displays the following Qdrant metrics:
# - Papers: Number of vector embeddings stored in Qdrant (paper count)
# - Authors: Vector dimensions (typically 768 for research paper embeddings)
  vector_size: 768  # For all-MiniLM-L6-v2 model
```
## 6. Web UI


### Web UI Development Setup

* The web interface uses React with the Neo4j JavaScript driver. If you want to develop the web UI locally:
a. **Navigate to the web-ui directory**:
   ```bash
   cd src/web-ui
   ```

b. **Install dependencies including Neo4j JavaScript driver**:
   ```bash
   npm install
   # Or to install Neo4j driver specifically:
   npm install neo4j-driver@5.13.0
   ```
c. **Start the development server**:
   ```bash
   npm start
   ```
* The web UI connects to Neo4j using environment variables defined in the docker-compose.yml file.


**How to Access:**
1. 

## 9. Managing Individual Docker Containers
* For more fine-grained control over system components, you can start, stop, restart, and inspect specific containers:

### a. Starting Individual Required Containers
* Services: 
```bash
# Start MongoDB
docker compose start mongodb

# Start Neo4j
docker compose start neo4j
```

### b. Restarting Individual Containers

```bash
# Restart MongoDB
docker compose restart mongodb

# Restart Neo4j
docker compose restart neo4j

# View MongoDB logs
docker compose logs mongodb
docker compose logs web-ui

# Follow logs (real-time updates)
docker compose logs --follow mongodb

```

### d. Inspecting Container Status
```bash
# Check status of all containers
docker compose ps
``` 

## 10. Optional: GPU-Accelerated Qdrant Setup on Remote Windows Machine

### Quick Overview

a. **Hardware Requirements**:
   - Windows 11 with WSL2 enabled
   - NVIDIA GPU with CUDA 12.x support (8GB VRAM minimum)
   - 16GB RAM (32GB recommended)
   - IP address on your local network

b. **Setup Approach**:
   - Install WSL2 with Ubuntu
   - Configure CUDA in WSL2
   - Build Qdrant from source with GPU support
   - Configure for optimal performance with research paper embeddings


c. **Integration with NEW PROJECT NAME**:
   - After setup, update the Qdrant connection settings in your config/default.yaml
   - Run the pipeline as usual, with vector operations now GPU-accelerated

### Detailed Instructions
* Complete step-by-step instructions are available in the `qdrant_setup` directory:

#### The guide includes:
- Full installation procedures

## Updating Configuration

* After setting up GPU-accelerated Qdrant, update your configuration:

---

### Configuration

The application is configured using YAML files in the `config/` directory. The default configuration is in `config/default.yaml`.

Key configuration options:

## Recent Feature Additions
### 1. MongoDB Tracking for Qdrant Vector Processing
* The sync_qdrant pipeline now includes a tracking system to prevent duplicate processing and provide synchronization with Qdrant:

```yaml

# In config/config.yaml

qdrant:
  # ... other settings ...
  tracking:
    enabled: true # Whether to track processed PDFs
```

### This system:
- 

### 2. GPU Acceleration for Vector Operations
The pipeline now supports GPU acceleration for both:

#### A. Qdrant Vector Database
```yaml
# In config/config.yaml
qdrant:
  # ... other settings ...
  gpu_enabled: true # Enable GPU for vector operations
  gpu_device: 1 # GPU device index (0 for first GPU, 1 for second, etc.)
```

#### B. Standalone Qdrant with GPU
For better performance with large vector collections, you can run Qdrant as a standalone application with GPU support as documented in the "Qdrant Deployment Options" section.
---
## Ollama Integration (Optional)

The `sync_qdrant` pipeline uses [Ollama](https://ollama.ai/) app for analyzing images extracted from PDFs if available:
- **What Ollama does**: Enhances the vector database by adding AI-generated descriptions of diagrams and figures in papers
- **Installation Options**:
  - **Desktop App**: Download and install Ollama from [ollama.ai](https://ollama.ai/)
  - **Docker Container**: Run Ollama in a Docker container for easier integration with the ArXiv pipeline (see `docs/ollama_docker.md` for detailed instructions)
- **Required model**: Run `ollama pull llama3` to download the required model
- **Without Ollama**: The pipeline still functions normally without Ollama, but image descriptions will be placeholders

## NEW PROJECT NAME Configuration Settings

The system is configured through `config/config.yaml`. Key configuration sections included

### Important Note About PDF Paths in Docker

When running the `sync_qdrant` service in Docker, the PDF directory path specified in `config/config.yaml` is overridden by the volume mapping in `docker-compose.yml`:

```yaml

# In docker-compose.yml

volumes:

Config changes take effect when services are restarted. See `docs/system_design.md` for detailed information about configuration impact on system behavior.

## Qdrant Deployment Options
In the `docker-compose.yml` file, we provide a pre-configured Qdrant container:

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant_data:/qdrant/storage
  restart: unless-stopped
```

### Option 2: Running Qdrant Locally with GPU Support

For better performance with large vector collections, you can run Qdrant as a standalone application with GPU acceleration:

1. **Download Qdrant** from [GitHub Releases](https://github.com/qdrant/qdrant/releases)
2. **Create a config file** at `config/qdrant_config.yaml` with GPU settings:

```yaml
storage:
  # Path to the directory where collections will be stored
  storage_path: ./storage
  # Vector data configuration with GPU support
  vector_data:
    # Enable CUDA support
    enable_cuda: true
    # GPU device index (0 for first GPU, 1 for second, etc.)
    cuda_device: 0
```

3. **Run Qdrant with the config**:

```
qdrant.exe --config-path config/qdrant_config.yaml
```

4. **Update the docker-compose.yml file** to comment out the Qdrant service but keep other services:
```yaml
# Comment out the Qdrant service
#qdrant:
#  image: qdrant/qdrant:latest
#  ...
# Update service connections to use host.docker.internal
app:
  environment:
    - QDRANT_URL=http://host.docker.internal:6333
```

## GPU Support for Embeddings Generation
1. **Install PyTorch with CUDA support**:
```bash

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

```

* Choose the appropriate CUDA version (cu118, cu121, etc.) based on your system. Check with `nvidia-smi`.

2. **Enable GPU in configuration**:
```yaml
# In config/config.yaml
qdrant:
  gpu_enabled: true  # Enable GPU for vector operations
  gpu_device: 0      # GPU device index (0 for first GPU)
```

3. **Verify GPU detection** by checking script output when running:
```

Using GPU for embeddings: cuda:0

```
## Database Installation & Connection Settings
### MongoDB Installation
#### Option 1: With Docker (recommended)
The Docker setup includes MongoDB, so no additional installation is needed if using Docker Compose.
#### Option 2: Standalone MongoDB Installation
1. **Download MongoDB Community Server**: [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. **Install Python driver**:
   ```bash
   pip install pymongo>=4.3.0
   ```

3. **Test your connection**:
   ```python

   ```

### Neo4j Installation

#### Option 1: With Docker (recommended)
* The Docker setup includes Neo4j, so no additional installation is needed if using Docker Compose.
* Neo4j Desktop is recommended for local development and data exploration.

#### Option 2: Standalone Neo4j Installation
1. **Download Neo4j Desktop**: [https://neo4j.com/download/](https://neo4j.com/download/)
2. **Create a new database** with password 'password' to match configuration
3. **Install Python driver**:

   ```bash
   pip install neo4j>=5.5.0
   ```

4. **Test your connection**:

   ```python

   ```

---

## Notes
- **Python Versions**: 
  - Docker containers use `python:3.11-slim`
  - Local development 'requires' Python ≥3.11 as specified in pyproject.toml
  - All dependencies are managed through pyproject.toml for consistent environments

- **Data Persistence**:
  - All persistent data (MongoDB, Neo4j, Qdrant) is stored in Docker volumes or local directories
  - PDF files are stored in the configured local directory

- **Development Approach**:
  - Either use the Python virtual environment with `python -m` commands
  - Or use Docker Compose for containerized execution
  - Both methods use the same configuration and produce consistent results
  - Deveoper commonly uses both methods running in python env, docker compose and standalone databases

---

## Troubleshooting

- If you see `ModuleNotFoundError: No module named 'pymongo'`, ensure you have activated your virtual environment and installed dependencies.
- For Docker issues, ensure Docker Desktop is running and you have sufficient permissions.

---

## External Tools for Data Exploration

* The following tools are recommended for exploring the data outside the pipeline:

### MongoDB

- **MongoDB Compass** - A GUI for MongoDB that allows you to explore databases, collections, and documents
- Download: [https://www.mongodb.com/products/compass](https://www.mongodb.com/products/compass)
- **Connection Details**:
  - Host: `localhost`
  - Port: `27018` (mapped from container port 27017)
  - Username: `admin`
  - Password: `ch@ng3m300`
  - Database: `daemonium`
- **Connection String**: `mongodb://admin:ch@ng3m300@localhost:27018/daemonium`
- **Python Connection Example**:
  ```python
  from pymongo import MongoClient
  
  client = MongoClient('mongodb://admin:ch@ng3m300@localhost:27018/')
  db = client['daemonium']
  print(f"Connected to MongoDB: {client.server_info()['version']}")
  ```

### PostgreSQL

- **pgAdmin** - A comprehensive PostgreSQL administration and development platform
- Download: [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)
- **Connection Details**:
  - Host: `localhost`
  - Port: `5433` (mapped from container port 5432)
  - Username: `postgres`
  - Password: `ch@ng3m300`
  - Database: `daemonium`
- **Connection String**: `postgresql://postgres:ch@ng3m300@localhost:5433/daemonium`
- **Python Connection Example**:
  ```python
  import psycopg2
  from sqlalchemy import create_engine
  
  # Using psycopg2
  conn = psycopg2.connect(
      host="localhost",
      port=5433,
      database="daemonium",
      user="postgres",
      password="ch@ng3m300"
  )
  
  # Using SQLAlchemy
  engine = create_engine('postgresql://postgres:ch@ng3m300@localhost:5433/daemonium')
  print("Connected to PostgreSQL successfully")
  ```

### Neo4j
- **Neo4j Browser** - Web interface for querying and visualizing graph data
- Access at: http://localhost:7475/ (Docker container port mapping)
- **Connection Details**:
  - HTTP Port: `7475` (mapped from container port 7474)
  - Bolt Port: `7688` (mapped from container port 7687)
  - Username: `neo4j`
  - Password: `ch@ng3m300`
  - Database: `neo4j`
- **Neo4j Desktop** - Complete development environment for Neo4j projects
- Download: [https://neo4j.com/download/](https://neo4j.com/download/)
- **Python Connection Example**:
  ```python
  from neo4j import GraphDatabase
  
  driver = GraphDatabase.driver(
      "bolt://localhost:7688",
      auth=("neo4j", "ch@ng3m300")
  )
  
  def test_connection():
      with driver.session() as session:
          result = session.run("RETURN 'Hello Neo4j!' as message")
          print(result.single()["message"])
  
  test_connection()
  driver.close()
  ```

### Qdrant
- **Qdrant Web UI** - A built-in web interface for exploring vector collections
- Access at: http://localhost:6343/dashboard (Docker container port mapping)
- **Connection Details**:
  - REST API Port: `6343` (mapped from container port 6333)
  - GRPC API Port: `6344` (mapped from container port 6334)
  - Host: `localhost`
- **Python Connection Example**:
  ```python
  from qdrant_client import QdrantClient
  
  client = QdrantClient(
      host="localhost",
      port=6343
  )
  
  # Test connection
  collections = client.get_collections()
  print(f"Connected to Qdrant. Collections: {collections}")
  ```
- Also consider **Qdrant Cloud Console** for more advanced features if you're using Qdrant Cloud
- Check Jupyter notebooks for more advanced features
These tools provide graphical interfaces to explore, query, and visualize the data stored in each component of the pipeline.

---

## 🔌 MCP Servers (Model Context Protocol)

Daimonion includes custom MCP servers that extend Windsurf IDE capabilities with specialized tools for document processing and text-to-speech functionality.

### 📄 Document Reader MCP Server

The Document Reader MCP provides tools to read and analyze markdown and text files within your project.

**Location**: `scripts/mcp_document_reader.py`

#### Available Tools:
1. **`read_document`** - Read complete file content with metadata
   ```json
   {
     "name": "read_document",
     "arguments": {
       "file_path": "README.md",
       "max_size": 1048576
     }
   }
   ```

2. **`list_documents`** - List all supported documents in a directory
   ```json
   {
     "name": "list_documents",
     "arguments": {
       "directory": "./docs",
       "recursive": true
     }
   }
   ```

3. **`get_document_info`** - Get file metadata without reading content
   ```json
   {
     "name": "get_document_info",
     "arguments": {
       "file_path": "docs/guide.txt"
     }
   }
   ```

4. **`get_supported_extensions`** - List supported file types
   ```json
   {
     "name": "get_supported_extensions",
     "arguments": {}
   }
   ```

#### Supported File Types:
- `.md` (Markdown)
- `.txt` (Plain text)
- `.markdown` (Markdown variant)
- `.text` (Text variant)

#### Features:
- **Multi-encoding support**: UTF-8, UTF-8-BOM, Latin-1, CP1252
- **File size protection**: Configurable maximum file size (default 1MB)
- **Recursive directory search**: Search subdirectories for documents
- **Comprehensive error handling**: Detailed error messages and logging
- **Cross-platform compatibility**: Works on Windows, Linux, and macOS

#### Windsurf IDE Configuration:
Add to your Windsurf MCP settings:

```json
{
  "mcpServers": {
    "document-reader": {
      "command": "python",
      "args": ["c:\\path\\to\\daemonium\\scripts\\mcp_document_reader.py"]
    }
  }
}
```

### 🔊 Windows TTS MCP Server

The Windows TTS MCP provides text-to-speech functionality using Windows built-in SAPI.

**Location**: `scripts/mcp_tts_windows.py`

#### Available Tools:

1. **`windows_tts`** - Convert text to speech
   ```json
   {
     "name": "windows_tts",
     "arguments": {
       "text": "Hello, this is a test",
       "voice": "Microsoft Zira Desktop",
       "rate": 0
     }
   }
   ```

2. **`list_voices`** - List available Windows TTS voices
   ```json
   {
     "name": "list_voices",
     "arguments": {}
   }
   ```

#### Features:
- **Windows SAPI integration**: Uses built-in Windows text-to-speech
- **Voice selection**: Choose from available system voices
- **Speech rate control**: Adjust speaking speed (-10 to 10)
- **No API keys required**: Completely free using Windows built-in TTS
- **PowerShell integration**: Leverages Windows PowerShell for TTS execution

#### Windsurf IDE Configuration:

Add to your Windsurf MCP settings:

```json
{
  "mcpServers": {
    "windows-tts": {
      "command": "python",
      "args": ["c:\\path\\to\\daemonium\\scripts\\mcp_tts_windows.py"]
    }
  }
}
```

### 🚀 Usage Examples

#### Document Reader Examples:

```bash
# In Windsurf IDE chat, you can use:
"Please read the contents of README.md"
"List all markdown files in this project"
"What file types does the document reader support?"
"Show me information about the config file"
"List all text files in the docs directory"
"Read the contents of the main configuration file"
```

**Quick Test Commands:**
After restarting Windsurf IDE, test the new functionality by asking in chat:
- `"Please read the contents of README.md"`
- `"List all markdown files in this project"`
- `"What file types does the document reader support?"`

#### Windows TTS Examples:

```bash
# In Windsurf IDE chat, you can use:
"Read this text aloud: 'Welcome to Daimonion'"
"What voices are available for text-to-speech?"
"Speak this text with a slower rate"
```

### 🔧 MCP Server Management

#### Testing MCP Servers:

```bash
# Test Document Reader MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python scripts/mcp_document_reader.py

# Test Windows TTS MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python scripts/mcp_tts_windows.py
```

#### Debugging:
- MCP servers log to stderr for debugging
- Check Windsurf IDE logs for MCP connection issues
- Ensure Python paths are correct in MCP configuration
- Verify file permissions for script execution

#### Requirements:
- **Document Reader**: Python 3.11+ (no additional dependencies)
- **Windows TTS**: Windows OS with PowerShell and SAPI support
- **Windsurf IDE**: Latest version with MCP support

---

## 📊 Optional Future Enhancements
The following features are 'planned' for future development to enhance the research pipeline:
### Data Analysis and Visualization
- **Topic Modeling**: Implement BERTopic or LDA for automatic discovery of research themes
- **Time-Series Analysis**: Track the evolution of research topics over time

### Research Enhancement Tools
- **PDF Section Parsing**: 
- **Citation Parsing**: 
- **Mathematical Model Extraction**: 

### Infrastructure Improvements
- **LangChain-based Research Assistant**: 
- **Hybrid Search**: 
- **Export Tools**: 

## To-Do List
- [ ] **Short-term Tasks**
  - [ ] 
- [ ] **Medium-term Tasks**
  - [ ] 
---
For more details about project and status, see the `docs/` directory.