# Ollama Embedding Model Evaluation for Knowledge Graphs

This project evaluates **Ollama embedding models** for **Knowledge Graph construction tasks** using philosophical content. It leverages your local Ollama installation to generate embeddings and includes comprehensive metrics for semantic similarity, clustering quality, entity recognition, relation extraction, and overall embedding quality specifically designed for philosophical knowledge graph applications.

---

## Table of Contents
0. [Quick Start-0](#quick-start-0)
1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Evaluation Metrics](#evaluation-metrics)
6. [Example Output](#example-output)
7. [Limitations](#limitations)
8. [Useful Resources](#useful-resources)

#### 🔍 Embedding Model Evaluation
Daimonion includes a comprehensive evaluation system for selecting the best embedding models for knowledge graph construction. Based on our evaluation results, **`llama3.1:latest` is now the default embedding model** for both knowledge graph builder scripts.

**Quick Start-0:**
```bash
# Setup required Ollama models
python llm_evaluation/setup_ollama_models.py

# Evaluate all embedding models
python llm_evaluation/main_sentence_transformers.py

# View evaluation results
cat llm_evaluation/eval_results/st_comparison_results.txt
## Project Overview
The goal of this project is to:
- Connect to your local Ollama installation to use embedding models (e.g., `nomic-embed-text`, `mxbai-embed-large`).
- Generate embeddings for philosophical concepts, entities, and relations using Ollama's API.
- Evaluate model performance on knowledge graph construction tasks:
  - **Semantic Similarity**: How well models capture relationships between philosophical concepts
  - **Clustering Quality**: Ability to group related philosophical ideas
  - **Entity Recognition**: Quality of identifying philosophers, concepts, and works
  - **Relation Extraction**: Accuracy in detecting relationships between entities
  - **Embedding Quality**: Overall quality of vector representations
- Compare multiple models to find the best fit for philosophical knowledge graph applications.

## Folder Structure
llm_evaluation/
│
├── data/
│ ├── semantic_similarity_test.json # Philosophical concept similarity pairs
│ ├── entity_recognition_test.json # Labeled philosophical entities
│ ├── relation_extraction_test.json # Philosophical relation triplets
│ └── clustering_test.json # Grouped philosophical concepts
│
├── models/
│ ├── load_sentence_transformer.py # Ollama embedding model loader
│ └── models_to_compare.py # List of Ollama models to evaluate
│
├── evaluation/
│ ├── evaluate_sentence_transformers.py # Main evaluation script
│ ├── kg_metrics.py # Knowledge graph specific metrics
│ └── compare_st_results.py # Model comparison functionality
│
├── results/
│ └── st_model_*_results.json # Individual model evaluation results
│ └── st_comparison_results.txt # Comparative analysis report
│
├── main_sentence_transformers.py # Main script for ST evaluation
│
└── requirements.txt # Dependencies (Ollama-based, no HuggingFace)

## Installation

### Prerequisites
1. **Install Ollama**: Download and install Ollama from [https://ollama.ai](https://ollama.ai)
2. **Pull required embedding models**:
   ```bash
   ollama pull nomic-embed-text
   ollama pull mxbai-embed-large
   ollama pull all-minilm
   ollama pull snowflake-arctic-embed
   ollama pull llama3.1:latest
   ollama pull all-MiniLM-L6-v2
   ```

### Python Environment Setup
1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download NLTK data**:
   ```bash
   python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
   ```

3. **Verify Ollama connection**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Usage

### Quick Start
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Ollama Embedding Model Evaluation:**
   ```bash
   python main_sentence_transformers.py
   ```

3. **Check Results:**
   - Individual model results: `results/st_model_*_results.json`
   - Comparison report: `results/st_comparison_results.txt`

### Advanced Usage

**Evaluate a Single Model:**
```python
from evaluation.evaluate_sentence_transformers import evaluate_sentence_transformer_model

results = evaluate_sentence_transformer_model(
    "nomic-embed-text", 
    output_path="results/single_model_results.json"
)
```

**Add Custom Models:**
Edit `models/models_to_compare.py` to include additional Ollama embedding models:
```python
MODELS_TO_COMPARE = [
    "nomic-embed-text",
    "your-custom-ollama-model"
]
```

**Setup Models Automatically:**
```bash
python setup_ollama_models.py
```

## Evaluation Metrics
This project uses specialized metrics for evaluating Ollama embedding models on knowledge graph tasks:

| Metric Category | Specific Metrics | Description | Score Range |
|----------------|------------------|-------------|-------------|
| **Semantic Similarity** | Accuracy, Correlation, MAE | How well the model captures expected relationships between philosophical concepts | 0 to 1 (higher is better) |
| **Clustering Quality** | Silhouette Score, Coherence, Separation | Ability to group related philosophical concepts together | -1 to 1 (higher is better) |
| **Entity Recognition** | Entity Clustering, Entity-Text Similarity | Quality of identifying and representing philosophical entities | 0 to 1 (higher is better) |
| **Knowledge Graph** | Relation Coherence, Graph Density, Clustering Coefficient | Overall quality of knowledge graph structure | 0 to 1 (higher is better) |
| **Embedding Quality** | Pairwise Similarity, Variance, Norm Distribution | Intrinsic quality of vector representations | Various ranges |
| **Composite Score** | Weighted average of all metrics | Overall model performance for KG tasks | 0 to 1 (higher is better) |

## Limitations

**Ollama Dependency:**
Requires a running Ollama instance with embedding models installed. Performance depends on your local hardware.

**Model Availability:**
Some embedding models may not be available in Ollama or may require manual installation.

**Philosophical Domain:**
Test datasets are focused on Nietzschean philosophy. Results may not generalize to other philosophical domains.

**Ground Truth Quality:**
Evaluation quality depends on the accuracy of expected similarity scores and clustering assignments in test data.

## Useful Resources

**Ollama Documentation:**
- [Ollama Official Website](https://ollama.ai)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)

**Embedding Models:**
- [Nomic Embed Text](https://ollama.ai/library/nomic-embed-text)
- [MixedBread AI Embed Large](https://ollama.ai/library/mxbai-embed-large)
- [Snowflake Arctic Embed](https://ollama.ai/library/snowflake-arctic-embed)

**Evaluation Metrics:**
- [NLTK Documentation](https://www.nltk.org/)
- [Scikit-learn Clustering Metrics](https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation)
- [NetworkX Graph Analysis](https://networkx.org/documentation/stable/)

**Knowledge Graph Resources:**
- [Neo4j Graph Database](https://neo4j.com/docs/)
- [Graph Theory Fundamentals](https://en.wikipedia.org/wiki/Graph_theory)

Contributing
Feel free to contribute to this project by:
Adding new evaluation metrics.
Improving the test dataset.
Fixing bugs or adding new features.
