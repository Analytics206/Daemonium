
# 🧠 Daemonium
## Overview

Daemonium is an AI-powered conversational platform that brings philosophy to life through interactive dialogues with historical thinkers. This innovative application enables users to explore philosophical concepts, engage in thought-provoking conversations, and gain deeper insights into the works of great philosophers.

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
  - **Neo4j Enterprise Edition**: Multi-database graph database for modeling relationships between philosophers, concepts, and themes
  - **Qdrant Vector Database**: For semantic search and retrieval-augmented generation
  - **Containerized Services**: Docker-based deployment for all components
  - **Modular Design**: Easily extensible for future features and content

#### 🗄️ Neo4j Enterprise Edition Multi-Database Support

Daemonium leverages Neo4j Enterprise Edition's multi-database capabilities to provide isolated environments for comparison and experimental work:

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

**Knowledge Graph Building with Embedding Model Selection:**

Both scripts now support flexible embedding model selection based on evaluation results. By default, they use `llama3.1:latest` for both embeddings and semantic analysis, which performed best in our comprehensive evaluation.

```bash
# Build knowledge graph with default settings (llama3.1:latest for both embeddings and semantic analysis)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py
python scripts/build_neo4j_metadata/improved_neo4j_kg_build.py

# Build knowledge graph in specific database
python scripts/build_neo4j_metadata/improved_neo4j_kg_build.py --database daemonium-primary
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --database daemonium-comparison

# Use different models for embeddings vs semantic analysis
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --embedding-model llama3.1:latest --ollama-model llama3.2:latest
python scripts/build_neo4j_metadata/improved_neo4j_kg_build.py --embedding-model snowflake-arctic-embed --ollama-model llama3.1:latest

# Switch back to SentenceTransformer for embeddings (if needed)
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py --use-sentence-transformer
python scripts/build_neo4j_metadata/improved_neo4j_kg_build.py --use-sentence-transformer --database daemonium-experimental

# Use environment variable for database selection
set NEO4J_TARGET_DATABASE=daemonium-experimental
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py
python scripts/build_neo4j_metadata/improved_neo4j_kg_build.py

# Full command with all options
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py \
  --database daemonium-primary \
  --ollama-url http://localhost:11434 \
  --ollama-model llama3.1:latest \
  --embedding-model llama3.1:latest
```

**Available Command Line Options (both scripts):**
- `--database`, `-d` - Target Neo4j database name (e.g., daemonium-primary)
- `--ollama-url` - Ollama server URL (default: http://localhost:11434)
- `--ollama-model` - Ollama model for semantic analysis (default: llama3.1:latest)
- `--embedding-model` - Ollama model for embeddings (default: llama3.1:latest)
- `--use-sentence-transformer` - Use SentenceTransformer instead of Ollama for embeddings

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

Daemonium includes a comprehensive evaluation system for selecting the best embedding models for knowledge graph construction. Based on our evaluation results, **`llama3.1:latest` is now the default embedding model** for both knowledge graph builder scripts.

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
Daemonium is designed to run locally using Docker, making it easy to set up and start exploring philosophical ideas. The system supports both local LLM models (via Ollama) and cloud-based models (like GPT-4), giving you flexibility in how you interact with the philosophical content.

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

### Running the Import Script

#### Prerequisites
- Docker and Docker Compose must be running
- Python environment with dependencies installed (see above)
- The PostgreSQL container (`daemonium-postgresql`) should be running

#### Start Docker Desktop

  if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
      Start-Process $DockerDesktopPath
      Write-Host "Docker Desktop is starting..."
  } else {
      Write-Host "Docker Desktop is already running."
  }

#### Using the Python Script (Cross-platform)

1. Ensure Docker is running and the PostgreSQL container is up:
   ```bash
   docker-compose up -d postgresql
   ```

2. Run the import script:
   ```bash
   # Basic usage (uses default CSV path: data/philosophers.csv)
   python scripts/import_philosophers.py data/philosophers.csv
   
   # Or specify a custom CSV file
   python scripts/import_philosophers.py data/philosopher_schools.csv

    python scripts/import_schools.py data/philosopher_schools.csv
   ```

#### Using the Batch File (Windows)

The batch file simplifies the process on Windows:

```batch
# From the project root
scripts\import_philosophers.bat
```

Or by double-clicking the batch file in Windows Explorer.

#### What the Script Does
1. Creates a temporary table in the database
2. Imports data from the CSV file
3. Updates existing records or inserts new ones based on the philosopher's name
4. Shows the number of records processed

#### Expected Output
```
Starting import from data/philosophers.csv
Added unique constraint on name column
Processed 2 philosopher records
- Socrates (ID: 1) - Updated: 2025-06-23 01:05:30.123456+00:00
- Plato (ID: 2) - Updated: 2025-06-23 01:05:30.123456+00:00
Import completed successfully
```

#### Troubleshooting
- If you get connection errors, ensure the PostgreSQL container is running
- Check that the CSV file exists at the specified path
- Verify the CSV format matches the expected columns: `name|dob|dod|summary|content|school_id|tag_id`

### Development Tools
- Format code: `black .`
- Sort imports: `isort .`
- Lint code: `pylint scripts/`
- Run tests: `pytest`

---

## 🚀 Key Features

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
| **MongoDB**                | Stores normalized paper metadata and paper processing tracking    |
| **Neo4j**                  | Stores the author-paper-category graph       |
| **Qdrant**                 | Stores paper vector embeddings for semantic search with metrics tracking |
| **Config Manager**         | Central config for category, limits, model   |
| **User Interface**         | Web UI for interaction with graphs           |
| **Logger**                 | Tracks events, errors, and skipped entries   |
| **Docker Compose**         | Brings it all together for local use         |
| **Prometheus**             | Time series database for system metrics collection  |

---

## 📥 MongoDB Data Upload Scripts

Daemonium includes a comprehensive suite of MongoDB uploader scripts for populating the database with philosophical content. All scripts are located in `scripts/build_mongodb_metadata/` and follow consistent patterns for error handling, logging, and configuration.

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
- **Offline Semantic Paper Search**: Find relevant papers without relying on online search engines
- **Research Gap Identification**: Analyze research areas to identify unexplored topics and opportunities

### Data Science & Analysis
- **Research Trend Analysis**: 
- **Citation Impact Visualization**: 

### AI-Assisted Research
- **Paper Summarization**: 
- **Research Agent**: 

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


## 2. Managing Pipeline Service Containers
   * pipelines do not have to run in order if you have previously run them or starting where you left off
   * manual services (Jupyter, Kafka, etc.) are only started when needed with the `--profile manual` flag
  ### a. Run sync_mongodb pipeline to fetch papers from ArXiv API and store in MongoDB:
  ```bash
  # Run the sync-mongodb pipeline container
  docker compose up --build sync-mongodb
  or
   echo $env:MONGO_URI
   $env:MONGO_URI="mongodb://localhost:27017/config"
   python -m src.pipeline.sync_mongodb --config config/default.yaml
  ```

  ### b. Run sync-neo4j pipeline for new pdf metadata inserted from MongoDB:

  ### c. Run sync_qdrant pipeline to process downloaded PDFs and store as vector embeddings in Qdrant:

## 3. (optional) Managing Monitoring Containers with Prometheus & Grafana
a. **Start the monitoring stack:**
   ```bash
   docker compose -f docker-compose.monitoring.yml up -d
   ```
  or
  **For monitoring containers, use the monitoring compose file:**
  ```bash
  # Start Prometheus
  docker compose -f docker-compose.monitoring.yml start prometheus
  # Start Grafana
  docker compose -f docker-compose.monitoring.yml start grafana
  # View Grafana logs
  docker compose -f docker-compose.monitoring.yml logs grafana
  ```
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
   - `config/grafana/dashboards/basic_test_dashboard.json` - Basic connectivity testing dashboard
   - `config/grafana/dashboards/arxiv_data_science_dashboard.json` - Core monitoring for ArXiv pipeline
   - `config/grafana/dashboards/arxiv_advanced_analytics_dashboard.json` - Advanced system correlation metrics
   - `config/grafana/dashboards/arxiv_vector_embedding_dashboard.json` - Vector database performance metrics

   * These dashboards provide visualization for MongoDB operations, system resources, container performance, 
   and vector embedding generation metrics critical for the research paper processing pipeline.

e. **Prometheus Query Documentation**
   Comprehensive documentation for Prometheus queries is available in:
   - `docs/prometheus_basic_queries.md` - Simple queries for troubleshooting
   - `docs/prometheus_queries.md` - General purpose monitoring queries
   - `docs/prometheus_custom_queries.md` - ArXiv pipeline specific metrics
   - `docs/prometheus_working_queries.md` - Verified working queries for dashboards

f. **Monitoring Diagnostics**
   Use the diagnostic script to verify your monitoring setup:
   ```bash
   python scripts/check_prometheus_metrics.py
   ```
   * This script analyzes your Prometheus setup and verifies that critical metrics
   for the ArXiv pipeline are available and functioning correctly.

* Refer to `docs/grafana_dashboard_guide.md` for details on customizing and extending these dashboards.**

## 4. Managing Manual Services

The following services are configured with the `manual` profile in Docker Compose, which means they will only start when explicitly requested:

### a. Jupyter Notebooks for Data Analysis
```bash
# Start Jupyter SciPy notebook server
docker compose --profile manual up jupyter-scipy
# Stop Jupyter SciPy notebook server
docker compose --profile manual down jupyter-scipy
```
* Access at: http://localhost:8888 (check console for token)
* Note: If token access is lost, restart the Jupyter docker container to get a new token

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
  connection_string: "mongodb://mongodb:27017/" # or http://localhost:27017
  db_name: "arxiv_papers"
  
neo4j:
  url: "bolt://neo4j:7687"  # or http://localhost:7474
  user: "neo4j"
  password: "password"

qdrant:
  url: "http://localhost:6333" #Access Qdrant UI http://localhost:6333/dashboard
  collection_name: "arxiv_papers"

# Qdrant API Metrics
# The database dashboard displays the following Qdrant metrics:
# - Papers: Number of vector embeddings stored in Qdrant (paper count)
# - Authors: Vector dimensions (typically 768 for research paper embeddings)
  vector_size: 768  # For all-MiniLM-L6-v2 model
```
## 6. Web UI
* To restart Web UI docker service, starts with docker-compose up above:
   ```bash
   docker-compose up -d web-ui
   ```
* Access the web interface at: http://localhost:3000

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

## 7. Data Visualization and Analysis Dashboards

**Key Features:**
- **Time-based Analysis**: 
- **Multi-dimensional Filtering**: 
- **Dynamic Category Selection**: 

**How to Access:**
1. Navigate to the web UI (http://localhost:3000) when services are running
2. Click on "MongoDB Reports" in the navigation menu

## 8. Data Validation and Analysis Utilities

### Data Integrity Checking
```python

```

### Formatted Reports
```python

```

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

## 6. Optional: GPU-Accelerated Qdrant Setup on Remote Windows Machine

* For enhanced vector search performance, you can set up Qdrant with GPU acceleration on a separate Windows machine within the same network. This configuration is beneficial for:
- Processing large volumes of papers with faster embedding searches

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

```bash
```

#### The guide includes:
- Full installation procedures
- Configuration optimized for 768-dimensional embeddings (typical for research papers)
- Testing and benchmarking tools
- Maintenance and backup procedures
- Security recommendations

## Updating Configuration

* After setting up GPU-accelerated Qdrant, update your configuration:

```yaml

# In config/config.yaml

qdrant:
  host: "192.168.1.x"  # Replace with your Qdrant server's IP
  port: 6333
  collection_name: "arxiv_papers"

```

* **New Feature:** The sync_qdrant pipeline now includes **MongoDB tracking** to prevent duplicate processing of PDFs. Each processed PDF is recorded in the `vector_processed_pdfs` collection with metadata including file hash, processing date, and chunk count.

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
  - E:/AI Research:/app/data/pdfs  # Maps Windows path to container path
```
Config changes take effect when services are restarted. See `docs/system_design.md` for detailed information about configuration impact on system behavior.

## Qdrant Deployment Options

This pipeline supports two options for running Qdrant (vector database):

### Option 1: Running Qdrant in Docker (Default)

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
   from pymongo import MongoClient
   client = MongoClient('mongodb://localhost:27017/')
   db = client['arxiv_papers']
   print(f"Connected to MongoDB: {client.server_info()['version']}")
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
## 📊 Optional Future Enhancements
The following features are 'planned' for future development to enhance the research pipeline:
### Data Analysis and Visualization
- **Topic Modeling**: Implement BERTopic or LDA for automatic discovery of research themes
- **Time-Series Analysis**: Track the evolution of research topics over time

### Research Enhancement Tools
- **PDF Section Parsing**: Intelligently extract structured sections from research papers (abstract, methods, results, etc.)
- **Citation Parsing**: Extract and normalize citations from paper references
- **Mathematical Model Extraction**: Identify and extract mathematical formulas and models from papers

### Infrastructure Improvements
- **LangChain-based Research Assistant**: Natural language interface to query the database
- **Hybrid Search**: Combine keyword and semantic search for better results
- **Export Tools**: Add BibTeX and PDF collection exports

## To-Do List
- [ ] **Short-term Tasks**
  - [ ] 
- [ ] **Medium-term Tasks**
  - [ ] 
---
For more details about project and status, see the `docs/` directory.

