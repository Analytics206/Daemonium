# Ollama embedding models to compare for knowledge graph tasks
# Note: These models need to be pulled in Ollama first using: ollama pull <model_name>
MODELS_TO_COMPARE = [
    "nomic-embed-text",           # Nomic's embedding model (excellent for text)
    "mxbai-embed-large",          # MixedBread AI large embedding model
    "all-minilm",                 # MiniLM embedding model in Ollama
    "snowflake-arctic-embed",     # Snowflake's Arctic embedding model
    "llama3.1:latest",            # Llama 3.1 (can generate embeddings)
    "all-minilm:l6-v2"             # MiniLM L6-v2 embedding model in Ollama
]

# Alternative top-tier models for future testing:
# "bge-m3", "gte-large", "e5-mistral-7b-instruct", "stella-en-400m-v5"