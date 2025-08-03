# Ollama embedding models to compare for knowledge graph tasks
# Note: These models need to be pulled in Ollama first using: ollama pull <model_name>
MODELS_TO_COMPARE = [
    "nomic-embed-text",           # Nomic's embedding model (excellent for text)
    "mxbai-embed-large",          # MixedBread AI large embedding model
    "snowflake-arctic-embed",     # Snowflake's Arctic embedding model
    "llama3.1:latest",            # Llama 3.1 (can generate embeddings)
    "llama3.2:latest",            # Llama 3.2 (can generate embeddings)
    "granite3-embedding"          # 
]

# Alternative top-tier models for future testing:
# "bge-m3", "gte-large", "e5-mistral-7b-instruct", "stella-en-400m-v5","granite3-embedding"
# Retired models: "all-minilm", "all-minilm:l6-v2"