
# 🧠 Brain Daemonium
# 📗 Product Requirements Document (PRD)

## Functional Requirements

### 3.0 Dockerization (DCK)
- **DCK-01**: System shall provide Dockerfiles for each service (ingestion, db, embedding, etc.)
- **DCK-02**: System shall include a `docker-compose.yml` file to orchestrate local setup

### 3.1 Ingestion (ING)
- **ING-01**: 

### 3.2 Data Management (DAT)
- **DAT-01**: Store raw and normalized metadata in MongoDB
- **DAT-02**: Allow retrieval/inspection of MongoDB documents

### 3.3 Graph Database (Neo4j) (GPH)
- **GPH-01**: Convert MongoDB data into Neo4j nodes/relationships
- **GPH-02**: Represent papers with properties (title, abstract, date)

### 3.4 Vector Embeddings (Qdrant) (VEC)
- **VEC-01**: Use Hugging Face embedding models
- **VEC-02**: Embed title + abstract as text input

### 3.5 Configuration & Modularity (CON)
- **CON-01**: Centralized settings file
- **CON-02**: Modular execution of pipeline components

### 3.6 Logging & Monitoring (LOG)
- **LOG-01**: Log ingestion/storage/indexing steps
- **LOG-02**: Log network and processing errors

### 3.7 System Monitoring (MON)
- **MON-01**: Collect container metrics with Prometheus
- **MON-02**: Collect system metrics with Node Exporter

### 3.8 Web UI (UI)
- **UI-01**: Web UI to explore neo4j graph/search

### 3.9 Jupyter Notebooks (REP)
- **REP-01**: Provide sample notebooks for general usage and exploration
- **REP-02**: Create connectivity testing notebooks for all databases (MongoDB, Neo4j, Qdrant)

### 3.10 AI Agent Platform (AGT)
- **AGT-01**: Configurable AI Agent platform for research paper analysis and exploration

### 3.11 Data Validation and Analysis (VAL)
- **VAL-01**: Interactive dashboards for validating data loaded across different systems
- **VAL-02**: Temporal analysis of paper publications by year, month, and day

### 3.12 Advanced Analytics (ANL)
- **ANL-01**: Category-based publication trend analysis with interactive filtering
- **ANL-02**: Visual representation of publication volume across time dimensions

### Optional/Nice-to-Have Features
- **PDF-01**: 

