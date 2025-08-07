# Ollama Configuration System Documentation

This document provides comprehensive documentation for the Daemonium Ollama configuration system, including the YAML configuration file (`ollama_models.yaml`) and the Python configuration loader (`ollama_config.py`).

## Overview

The Ollama configuration system provides centralized management of AI models, timeouts, retry logic, and performance settings across all Daemonium scripts. It eliminates timeout issues, provides intelligent model loading, and enables easy model switching without code changes.

## 📁 Configuration Files

### `ollama_models.yaml` - Central Configuration File

The main YAML configuration file that defines all Ollama-related settings for the Daemonium system.

#### 🎯 Model Assignments

```yaml
models:
  # General Knowledge Graph Tasks
  general_kg:
    default: "deepseek-r1:latest"
    alternatives:
      - "llama3.1:latest"
      - "mistral:latest"
      - "qwen3-coder:latest"
    description: "Large reasoning models for complex philosophical analysis"
  
  # Semantic Similarity Tasks  
  semantic_similarity:
    default: "granite-embedding:278m"
    alternatives:
      - "snowflake-arctic-embed2:latest"
      - "mxbai-embed-large:latest"
      - "nomic-embed-text:latest"
    description: "Specialized embedding models for semantic similarity"
  
  # Concept Clustering Tasks
  concept_clustering:
    default: "llama3.2:latest"
    alternatives:
      - "llama3.1:latest"
      - "gemma3:12b"
      - "mistral:latest"
    description: "Models optimized for concept extraction and clustering"
```

#### ⏱️ Timeout Configuration

```yaml
timeouts:
  # Model-specific timeouts (seconds)
  model_specific:
    "deepseek-r1:latest": 120    # Large reasoning models
    "llama3.2:latest": 60        # Medium models
    "granite-embedding:278m": 60 # Embedding models
  
  # Task-type defaults (used if model-specific not found)
  task_defaults:
    general_kg: 90
    semantic_similarity: 45
    concept_clustering: 60
    embedding_generation: 60
  
  # Retry settings
  retry:
    max_attempts: 3
    base_delay: 2
    backoff_multiplier: 2
  
  # Model loading settings
  model_loading:
    max_wait: 90
    test_timeout: 5
    warmup_timeout: 120
```

#### 🌐 Server Configuration

```yaml
server:
  url: "http://localhost:11434"
  endpoints:
    generate: "/api/generate"
    embeddings: "/api/embeddings"
    tags: "/api/tags"
  connection_timeout: 10
  read_timeout: 300
```

#### 🔄 Fallback Models

```yaml
fallbacks:
  general_kg_fallbacks:
    - "llama3.1:latest"
    - "mistral:latest"
  
  embedding_fallbacks:
    - "all-minilm:latest"
    - "nomic-embed-text:latest"
  
  clustering_fallbacks:
    - "llama3.1:latest"
    - "mistral:latest"
```

#### 🌍 Environment Overrides

```yaml
environment_overrides:
  enabled: true
  prefix: "OLLAMA_MODEL_"
  # Supports: OLLAMA_MODEL_GENERAL_KG, OLLAMA_MODEL_SEMANTIC_SIMILARITY, etc.
```

#### ⚡ Performance Settings

```yaml
performance:
  # Cache settings
  enable_embedding_cache: true
  max_cache_size: 10000
  clear_cache_threshold: 8000
  
  # Batch processing
  max_batch_size: 10
  batch_delay: 1
  
  # Model warmup
  warmup_on_startup: true
  warmup_all_models: false
```

### `ollama_config.py` - Python Configuration Loader

The Python module that loads and manages the YAML configuration, providing a programmatic interface for all Daemonium scripts.

#### 🏗️ Core Classes

##### `OllamaConfigLoader`

The main configuration loader class that provides centralized access to all Ollama settings.

```python
from config.ollama_config import get_ollama_config

# Get the global configuration instance
config = get_ollama_config()

# Or specify a custom config file
config = get_ollama_config('/path/to/custom_config.yaml')
```

##### Key Methods

**Model Management:**
```python
# Get model for specific task type
model = config.get_model_for_task('general_kg')
model = config.get_model_for_task('semantic_similarity', override='custom-model')

# Get timeout for specific model
timeout = config.get_timeout_for_model('deepseek-r1:latest')
timeout = config.get_timeout_for_model('custom-model', task_type='general_kg')

# Get fallback models
fallbacks = config.get_fallback_models('general_kg')
```

**Server Configuration:**
```python
# Get server URL and endpoints
server_url = config.get_server_url()
generate_url = config.get_endpoint_url('generate')
embeddings_url = config.get_endpoint_url('embeddings')
```

**Performance Settings:**
```python
# Check warmup settings
should_warmup = config.should_warmup_on_startup()
warmup_all = config.should_warmup_all_models()

# Get cache configuration
cache_config = config.get_cache_config()
# Returns: {'enabled': True, 'max_size': 10000, 'clear_threshold': 8000}

# Get batch processing configuration
batch_config = config.get_batch_config()
# Returns: {'max_size': 10, 'delay': 1}
```

**Retry and Loading Configuration:**
```python
# Get retry configuration
retry_config = config.get_retry_config()
# Returns: {'max_attempts': 3, 'base_delay': 2, 'backoff_multiplier': 2}

# Get model loading configuration
loading_config = config.get_model_loading_config()
# Returns: {'max_wait': 90, 'test_timeout': 5, 'warmup_timeout': 120}
```

#### 📊 Data Classes

**`ModelConfig`** - Configuration for a specific model type:
```python
@dataclass
class ModelConfig:
    default: str
    alternatives: List[str]
    description: str
```

**`TimeoutConfig`** - Timeout configuration for models and operations:
```python
@dataclass
class TimeoutConfig:
    model_specific: Dict[str, int]
    task_defaults: Dict[str, int]
    retry: Dict[str, Any]
    model_loading: Dict[str, int]
```

**`ServerConfig`** - Ollama server configuration:
```python
@dataclass
class ServerConfig:
    url: str
    endpoints: Dict[str, str]
    connection_timeout: int
    read_timeout: int
```

## 🚀 Usage Examples

### Basic Usage in Scripts

```python
from config.ollama_config import get_ollama_config

class MyScript:
    def __init__(self):
        # Load centralized configuration
        self.config = get_ollama_config()
        
        # Get models for different tasks
        self.general_model = self.config.get_model_for_task('general_kg')
        self.embedding_model = self.config.get_model_for_task('semantic_similarity')
        self.clustering_model = self.config.get_model_for_task('concept_clustering')
        
        # Get server configuration
        self.server_url = self.config.get_server_url()
        
    def query_model(self, prompt, task_type='general_kg'):
        # Get appropriate timeout for the model
        model = self.config.get_model_for_task(task_type)
        timeout = self.config.get_timeout_for_model(model, task_type)
        
        # Get retry configuration
        retry_config = self.config.get_retry_config()
        
        # Use configuration in your API calls
        # ... implementation details
```

### Custom Configuration Files

```python
# Use custom configuration file
config = get_ollama_config('/path/to/custom_ollama_config.yaml')

# Override models via environment variables
import os
os.environ['OLLAMA_MODEL_GENERAL_KG'] = 'custom-reasoning-model'
config = get_ollama_config()  # Will use environment override
```

### Integration with CLI Arguments

```python
import argparse
from config.ollama_config import get_ollama_config

parser = argparse.ArgumentParser()
parser.add_argument('--ollama-config', help='Path to Ollama config file')
parser.add_argument('--general-kg-model', help='Override general KG model')
args = parser.parse_args()

# Load configuration with optional custom path
config = get_ollama_config(args.ollama_config)

# Get model with CLI override support
general_model = args.general_kg_model or config.get_model_for_task('general_kg')
```

## 🔧 Configuration Hierarchy

The configuration system follows a clear hierarchy (highest priority first):

1. **CLI Arguments** - Direct command line parameters
2. **Environment Variables** - `OLLAMA_MODEL_*` environment variables
3. **Configuration File** - Settings in `ollama_models.yaml`
4. **Built-in Defaults** - Hardcoded fallback values

### Environment Variable Format

```bash
# Set environment overrides
export OLLAMA_MODEL_GENERAL_KG="custom-reasoning-model"
export OLLAMA_MODEL_SEMANTIC_SIMILARITY="custom-embedding-model"
export OLLAMA_MODEL_CONCEPT_CLUSTERING="custom-clustering-model"

# Run script - will use environment overrides
python your_script.py
```

## ⚡ Performance Features

### Model Warmup

The configuration system supports intelligent model warmup to eliminate loading delays:

```python
# Check if warmup is enabled
if config.should_warmup_on_startup():
    # Warmup assigned models or all models
    models_to_warmup = get_models_for_warmup()
    warmup_models(models_to_warmup)
```

### Intelligent Timeouts

Models have different timeout requirements based on their characteristics:

- **DeepSeek-R1**: 120 seconds (large reasoning models)
- **Llama3.2**: 60 seconds (medium models)
- **Embedding models**: 60 seconds (embedding generation)
- **Default**: 45 seconds (fallback)

### Retry Logic

Configurable retry logic with exponential backoff:

```python
retry_config = config.get_retry_config()
max_attempts = retry_config['max_attempts']  # 3
base_delay = retry_config['base_delay']      # 2 seconds
multiplier = retry_config['backoff_multiplier']  # 2

# Retry delays: 2s, 4s, 8s
```

### Caching

Embedding and response caching for improved performance:

```python
cache_config = config.get_cache_config()
if cache_config['enabled']:
    max_size = cache_config['max_size']  # 10000
    clear_threshold = cache_config['clear_threshold']  # 8000
```

## 🛠️ Customization

### Creating Custom Configuration Files

1. **Copy the default configuration:**
   ```bash
   cp config/ollama_models.yaml config/my_custom_config.yaml
   ```

2. **Modify settings as needed:**
   ```yaml
   models:
     general_kg:
       default: "my-custom-model:latest"
   
   timeouts:
     model_specific:
       "my-custom-model:latest": 180
   ```

3. **Use in your scripts:**
   ```python
   config = get_ollama_config('config/my_custom_config.yaml')
   ```

### Adding New Model Types

To add support for new model types:

1. **Update `ollama_models.yaml`:**
   ```yaml
   models:
     my_new_task:
       default: "specialized-model:latest"
       alternatives: ["fallback-model:latest"]
       description: "Model for my specialized task"
   
   timeouts:
     task_defaults:
       my_new_task: 75
   
   fallbacks:
     my_new_task_fallbacks:
       - "fallback-model:latest"
   ```

2. **Use in your code:**
   ```python
   model = config.get_model_for_task('my_new_task')
   timeout = config.get_timeout_for_model(model, 'my_new_task')
   ```

## 🔍 Troubleshooting

### Common Issues

**1. Configuration File Not Found:**
```python
# Check if config file exists
from pathlib import Path
config_path = Path('config/ollama_models.yaml')
if not config_path.exists():
    print(f"Config file not found: {config_path}")
```

**2. Model Loading Timeouts:**
```yaml
# Increase model loading timeout
timeouts:
  model_loading:
    max_wait: 180  # Increase from default 90s
    warmup_timeout: 240  # Increase from default 120s
```

**3. Environment Variables Not Working:**
```bash
# Check environment variable format
echo $OLLAMA_MODEL_GENERAL_KG

# Ensure underscores match task type names
# general_kg -> OLLAMA_MODEL_GENERAL_KG
# semantic_similarity -> OLLAMA_MODEL_SEMANTIC_SIMILARITY
```

**4. Custom Models Not Recognized:**
```yaml
# Add custom models to configuration
timeouts:
  model_specific:
    "my-custom-model:latest": 120
```

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = get_ollama_config()
# Will show detailed configuration loading information
```

## 📚 Integration Examples

### Enhanced Neo4j Knowledge Graph Builder

The enhanced Neo4j knowledge graph builder uses the configuration system extensively:

```python
# In enhanced_neo4j_kg_build.py
from config.ollama_config import get_ollama_config

class EnhancedKnowledgeGraphBuilder:
    def __init__(self, ollama_config_path=None, **kwargs):
        # Load centralized configuration
        self.ollama_config = get_ollama_config(ollama_config_path)
        
        # Get models with CLI override support
        self.general_kg_model = (
            kwargs.get('ollama_model') or  # Legacy
            kwargs.get('general_kg_model') or  # CLI override
            self.ollama_config.get_model_for_task('general_kg')  # Config
        )
        
        # Get timeouts and retry settings
        self.timeout = self.ollama_config.get_timeout_for_model(
            self.general_kg_model, 'general_kg'
        )
        self.retry_config = self.ollama_config.get_retry_config()
```

### Other Scripts

Any script can easily integrate the configuration system:

```python
from config.ollama_config import get_ollama_config

def my_ai_function():
    config = get_ollama_config()
    
    # Get appropriate model and settings
    model = config.get_model_for_task('semantic_similarity')
    timeout = config.get_timeout_for_model(model)
    server_url = config.get_server_url()
    
    # Use in your AI operations
    # ... implementation
```

## 🎯 Best Practices

1. **Use the global configuration instance** via `get_ollama_config()`
2. **Leverage the configuration hierarchy** - CLI args override config files
3. **Set appropriate timeouts** for different model types
4. **Use environment variables** for deployment-specific overrides
5. **Enable model warmup** to eliminate loading delays
6. **Configure fallback models** for reliability
7. **Monitor cache usage** and adjust thresholds as needed
8. **Test configuration changes** in experimental environments first

## 📖 Related Documentation

- [`README.md`](../README.md) - Main project documentation with usage examples
- [`enhanced_neo4j_kg_build.py`](../scripts/build_neo4j_metadata/enhanced_neo4j_kg_build.py) - Primary integration example
- [`config/default.yaml`](default.yaml) - Main project configuration file

---

This configuration system provides a robust, flexible, and user-friendly way to manage Ollama models and settings across the entire Daemonium project. It eliminates timeout issues, provides intelligent model loading, and enables easy experimentation with different AI models.
