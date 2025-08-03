# Ollama embedding models to compare for knowledge graph tasks
# Note: These models need to be pulled in Ollama first using: ollama pull <model_name>
MODELS_TO_COMPARE = [
    "nomic-embed-text",                 # Nomic's embedding model (excellent for text)
    # "mxbai-embed-large",                # MixedBread AI large embedding model
    # "snowflake-arctic-embed2:latest",    # Snowflake's Arctic embedding model
    "granite-embedding:278m",           # 
    "llama3.1:latest",                  # Llama 3.1 (can generate embeddings)
    "llama3.2:latest"                   # Llama 3.2 (can generate embeddings)    
]

# Alternative top-tier models for future testing:
# "bge-m3", "e5-mistral-7b-instruct", "stella-en-400m-v5"

# Score archive:
# "llama3.1:latest"
# "overall_scores":
# "overall_scores": 
#   "semantic_similarity_score": 0.1714596547952384,
#   "clustering_score": 0.36334743848348,
#   "entity_recognition_score": 0.3365780621556119,
#   "knowledge_graph_score": 0.32226901420345405,
#   "embedding_quality_score": 0.4286228115112348,
#   "composite_score": 0.32445539622980385

# Retired models: 
# "all-minilm"
# "all-minilm:l6-v2"
# "gte-large"

# "mxbai-embed-large" 
# "overall_scores": 
#   "semantic_similarity_score": 0.050430334788967746,
#   "clustering_score": 0.3341354427207051,
#   "entity_recognition_score": 0.38781078465512436,
#   "knowledge_graph_score": 0.29805217534644696,
#   "embedding_quality_score": 0.24176345606266103,
#   "composite_score": 0.26243843871478106

# "snowflake-arctic-embed:latest"
# "overall_scores":
#   "semantic_similarity_score": 0.04537094818904683,
#   "clustering_score": 0.33381195729868923,
#   "entity_recognition_score": 0.4313101095885627,
#   "knowledge_graph_score": 0.3768216893375676,
#   "embedding_quality_score": 0.13865745888157352,
#   "composite_score": 0.26519443265908793

# "snowflake-arctic-embed2:latest"
# "overall_scores":
#     "semantic_similarity_score": 0.19527566759035891,
#     "clustering_score": 0.32165767879344975,
#     "entity_recognition_score": 0.3009503044266065,
#     "knowledge_graph_score": 0.22832794853534,
#     "embedding_quality_score": 0.3044946879390685,
#     "composite_score": 0.2701412574569647