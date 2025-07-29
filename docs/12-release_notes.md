# Daemonium
---
## Version 0.2.4 (July 29, 2025)

### Major Features

#### Neo4j Enterprise Edition Multi-Database Support
- **Enterprise Edition Upgrade** - Upgraded from Neo4j Community Edition to Enterprise Edition for advanced multi-database capabilities
- **Multiple Database Architecture** - Created three separate databases for comparison and experimental work:
  - `daemonium-primary` - Primary knowledge graph
  - `daemonium-comparison` - Comparison knowledge graph
  - `daemonium-experimental` - Experimental features
- **Free Development License** - Leverages Neo4j Enterprise Edition's free development license for local use

#### Database Management System
- **Database Management Script** - Added `scripts/manage_neo4j_databases.py` for comprehensive database administration
- **Database Utility Library** - Created `scripts/utils/neo4j_database_utils.py` for consistent database selection across all scripts
- **Automated Database Creation** - Scripts automatically create databases if they don't exist
- **Database Statistics and Monitoring** - Built-in tools for monitoring database health and content statistics

#### Flexible Database Selection
- **Multiple Selection Methods** - Support for database selection via:
  - Command-line arguments: `python script.py daemonium-primary`
  - Environment variables: `NEO4J_TARGET_DATABASE=daemonium-comparison`
  - Script-specific mappings in configuration
  - Default database fallback
- **Enhanced Knowledge Graph Builder** - Updated `enhanced_neo4j_kg_build.py` to support target database selection
- **Centralized Configuration** - All database settings managed through `config/default.yaml`

### Database Management Commands

#### Setup and Administration
```bash
# Create all configured databases
python scripts/manage_neo4j_databases.py setup

# List all databases with status
python scripts/manage_neo4j_databases.py list

# Show database statistics
python scripts/manage_neo4j_databases.py stats daemonium-primary

# Clear database content (use with caution)
python scripts/manage_neo4j_databases.py clear daemonium-experimental
```

#### Knowledge Graph Building
```bash
# Build knowledge graph in default database
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py

# Build knowledge graph in specific database
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py daemonium-primary
python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py daemonium-comparison

# Use environment variable for database selection
NEO4J_TARGET_DATABASE=daemonium-experimental python scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py
```

### Technical Improvements
- **Docker Compose Updates** - Modified Neo4j service to use Enterprise Edition with proper license acceptance
- **Configuration Schema** - Enhanced `config/default.yaml` with database definitions and script mappings
- **Error Handling** - Robust error handling for database creation and connection failures
- **Database Naming Compliance** - Ensured all database names comply with Neo4j naming restrictions (hyphens instead of underscores)

### Benefits for Comparison Workflows
- **True Data Isolation** - Complete separation between different knowledge graph versions
- **Easy A/B Testing** - Compare different data processing approaches across databases
- **Experimental Safety** - Test new features in isolated experimental database
- **Version Control** - Maintain multiple versions of knowledge graphs simultaneously

---
## Version 0.2.3 (July 29, 2025)

### New Features

#### Bibliography Data Management
- **Bibliography Uploader Script** - Added `upload_bibliography_to_mongodb.py` for uploading author bibliography data to MongoDB
- **Flexible JSON Structure Support** - Script handles various root keys (e.g., `nietzsche_bibliography`, `plato_bibliography`, `author_bibliography`) for backward compatibility
- **Enhanced Bibliography Schema** - Added support for new `background` field in bibliography JSON structure
- **Author-Based Document IDs** - Creates unique document identifiers based on author names for consistent data management
- **Comprehensive Field Mapping** - Extracts and maps all bibliography fields including works, chronological periods, themes, and influence data

#### Master Uploader Integration
- **Updated Script Execution Order** - Added bibliography uploader to `run_all_uploaders.py` execution sequence
- **Strategic Positioning** - Bibliography data loads after core philosopher data but before detailed content for optimal dependency management

#### Data Structure Enhancements
- **Template Updates** - Enhanced bibliography template with new background field for richer author context
- **Modern Adaptation Support** - Added support for modern philosophical adaptations with new JSON structure
- **Philosopher Bio Template Refinements** - Streamlined template structure for better usability

### Technical Improvements
- **Robust Error Handling** - Enhanced error messages for missing or malformed bibliography keys
- **Backward Compatibility** - Maintains support for existing JSON files with different naming conventions
- **Metadata Preservation** - Stores original JSON key names for reference and debugging
- **Clean Document IDs** - Improved ID generation with better character handling (spaces, hyphens, periods)

### Configuration and Integration
- **MongoDB Collection Management** - Uses dedicated `bibliography` collection for author bibliography data
- **YAML Configuration Integration** - Leverages existing configuration system for database connections
- **Logging and Statistics** - Comprehensive logging with detailed upload statistics and error reporting

---
## Version 0.2.2 (July 27, 2025)

### New Features

#### Complete MongoDB Data Upload Suite
- **13 Specialized Uploader Scripts** - Comprehensive collection of MongoDB uploader scripts for all JSON data categories
- **Chat Blueprint Uploader** - Added `upload_chat_blueprints_to_mongodb.py` for chat blueprint templates and response pipelines
- **Conversation Logic Uploader** - Added `upload_conversation_logic_to_mongodb.py` for conversation strategies and tone selection
- **Discussion Hook Uploader** - Added `upload_discussion_hooks_to_mongodb.py` for categorized discussion prompts
- **Idea Summary Uploader** - Added `upload_idea_summaries_to_mongodb.py` for detailed philosophical idea analysis
- **Modern Adaptation Uploader** - Added `upload_modern_adaptations_to_mongodb.py` for contemporary philosophical applications
- **Persona Core Uploader** - Added `upload_persona_cores_to_mongodb.py` for philosopher persona definitions
- **Philosopher Bio Uploader** - Added `upload_philosopher_bios_to_mongodb.py` for biographical information
- **Philosopher Bot Uploader** - Added `upload_philosopher_bots_to_mongodb.py` for bot persona configurations
- **Philosopher Summary Uploader** - Added `upload_philosopher_summaries_to_mongodb.py` for comprehensive philosophical overviews
- **Philosophy Themes Uploader** - Added `upload_philosophy_themes_to_mongodb.py` for core philosophical themes and discussion frameworks
- **Top 10 Ideas Uploader** - Added `upload_top_10_ideas_to_mongodb.py` for ranked philosophical concepts

#### Universal Features Across All Uploaders
- **Template File Filtering** - All scripts automatically skip template files (files starting with 'template')
- **Document Merging** - Intelligent merge functionality that updates existing documents while preserving original upload timestamps
- **Comprehensive Logging** - Detailed logging with separate log files for each uploader script
- **Error Handling** - Robust error handling for connection failures, invalid JSON, and file system issues
- **Statistics Reporting** - Detailed upload statistics including processed, uploaded, updated, skipped, and error counts
- **Unique Document IDs** - Each uploader creates unique document identifiers based on content-specific fields
- **Metadata Tracking** - Rich metadata including content metrics, upload timestamps, and source file information

#### Configuration and Security
- **YAML Configuration Integration** - All scripts use `config/default.yaml` for MongoDB connection settings
- **URL Encoding** - Proper URL encoding of MongoDB credentials to handle special characters
- **Authentication Support** - Support for MongoDB authentication with admin database auth source
- **Modular Architecture** - Each uploader is self-contained with specialized document preparation logic

#### Documentation
- **Comprehensive Uploader Documentation** - Updated `README_uploaders.md` with all 13 uploader scripts, usage instructions, and troubleshooting
- **Dependencies** - Updated requirements with `pymongo>=4.6.0` and `PyYAML>=6.0.1`
- **Collection Mapping** - Clear documentation of which script uploads to which MongoDB collection

---

## Version 0.2.1 (July 27, 2025)

### New Features

#### MongoDB Data Upload Scripts (Initial Implementation)
- **Aphorism Uploader** - Added `upload_aphorisms_to_mongodb.py` script to upload JSON files from `json_bot_docs/aphorisms` to MongoDB `aphorisms` collection
- **Book Summary Uploader** - Added `upload_book_summaries_to_mongodb.py` script to upload JSON files from `json_bot_docs/book_summary` to MongoDB `book_summary` collection
- **Template File Filtering** - Both scripts automatically skip template files (files starting with 'template')
- **Document Merging** - Intelligent merge functionality that updates existing documents while preserving original upload timestamps
- **Comprehensive Logging** - Detailed logging with separate log files for each uploader script
- **Error Handling** - Robust error handling for connection failures, invalid JSON, and file system issues
- **Statistics Reporting** - Detailed upload statistics including processed, uploaded, updated, skipped, and error counts

#### Configuration and Security
- **YAML Configuration Integration** - Both scripts use `config/default.yaml` for MongoDB connection settings
- **URL Encoding** - Proper URL encoding of MongoDB credentials to handle special characters
- **Authentication Support** - Support for MongoDB authentication with admin database auth source

#### Documentation
- **Uploader Documentation** - Added comprehensive `README_uploaders.md` with usage instructions, troubleshooting, and development notes
- **Dependencies** - Updated requirements with `pymongo>=4.6.0` and `PyYAML>=6.0.1`

---

## Version 0.2.0 (May 3, 2025)

### Major Features

#### PDF Processing and Vector Storage
- **MongoDB Tracking System** - Added tracking of processed PDFs in `vector_processed_pdfs` collection to prevent duplicate processing
- **PDF Processing Tracking** - Each processed PDF is tracked with file hash, chunk count, and processing date
- **Category-Based Processing** - Implemented selective vector processing based on configured research categories
- **Papers per Category Limit** - Added configurable limit for papers to process per category

#### GPU Acceleration
- **GPU Support for Vector Operations** - Added GPU acceleration for both Qdrant vector database and embedding generation
- **Multi-GPU Support** - Implemented configurable GPU device selection for optimal performance
- **Automatic Device Detection** - Added graceful fallback to CPU when GPU is unavailable or not properly configured

#### Deployment Improvements
- **Hybrid Deployment Architecture** - Added support for running Qdrant locally with GPU while other services run in Docker
- **Host.Docker.Internal Integration** - Enhanced Docker services to communicate with local Qdrant instance
- **Standalone Qdrant Configuration** - Added documentation for running Qdrant with GPU acceleration
- **Docker Volume Path Handling** - Improved Windows path compatibility for mounted volumes

#### Error Handling
- **Ollama Integration Improvements** - Made Ollama optional with graceful fallback when not available
- **Better Error Recovery** - Added robust error handling for PDF processing failures

### Configuration Enhancements
- **Centralized PDF Directory Config** - Moved PDF directory configuration to central config file
- **Dynamic MongoDB Connection** - Improved connection handling to automatically adjust for local vs Docker environments
- **Ollama Configuration** - Added controls for enabling/disabling Ollama image analysis

### Documentation
- **Deployment Options** - Added documentation for both Docker and standalone deployment options
- **GPU Configuration Guide** - Documented GPU setup and acceleration options
- **Database Installation Guides** - Added detailed instructions for MongoDB, Neo4j, and Qdrant installation
- **Development Notes** - Added developer notes document for tracking ongoing work
- **Release Notes** - Added this release notes document

### Dependencies and Libraries
- **PyTorch with CUDA** - Updated PyTorch requirements to include CUDA support
- **Neo4j JavaScript Driver** - Added documentation for the JS driver required for the web UI

---

## Version 0.1.0 (April 26, 2025)

### Major Features

#### Data Ingestion and Storage
- **ArXiv API Integration** - Implemented paper ingestion from ArXiv Atom XML API
- **MongoDB Storage** - Created document storage for paper metadata with appropriate indexing
- **Neo4j Graph Database** - Established graph representation for papers, authors, and categories
- **PDF Downloading** - Added functionality to download and organize research papers in PDF format
- **Vector Embedding** - Implemented basic text vectorization using Hugging Face models
- **Qdrant Integration** - Set up vector similarity search with Qdrant database

#### Docker Containerization
- **Multi-Container Setup** - Built initial Docker Compose configuration for all services
- **Volume Persistence** - Implemented persistent storage for MongoDB and Neo4j data
- **Network Configuration** - Established internal container communication and port mapping
- **Service Orchestration** - Created coordinated startup/shutdown of all system components

#### Web Interface
- **Neo4j Visualization** - Created basic web interface for exploring the knowledge graph
- **Browsing Interface** - Implemented paper browsing and navigation features
- **Web UI Container** - Dockerized the web interface with appropriate connections to backend services

### Configuration Enhancements
- **YAML Configuration** - Created initial configuration file structure
- **Environment Variables** - Implemented environment variable support for container configuration
- **API Rate Limiting** - Added configurable rate limiting for ArXiv API access

### Documentation
- **Setup Instructions** - Created installation and setup documentation
- **README** - Established initial project documentation with overview and features
- **Configuration Guide** - Documented configuration options and their effects

### Dependencies and Libraries
- **MongoDB Python Driver** - Integrated PyMongo for database access
- **Neo4j Python Driver** - Added Neo4j connectivity for graph operations
- **Hugging Face Transformers** - Integrated for text embedding generation
- **Docker and Docker Compose** - Established containerization foundation
