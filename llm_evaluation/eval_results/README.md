# Sentence Transformer Evaluation Metrics

This document provides a comprehensive explanation of the evaluation metrics used to assess sentence transformer models for knowledge graph construction tasks in the Daemonium philosophical chatbot project.

## Overview

The evaluation system assesses five key aspects of sentence transformer performance:

1. **Semantic Similarity Score** - How well the model captures expected semantic relationships
2. **Clustering Score** - Quality of concept grouping and thematic organization
3. **Entity Recognition Score** - Ability to distinguish between different philosophical entity types
4. **Knowledge Graph Score** - Performance in relation extraction and graph structure quality
5. **Embedding Quality Score** - Intrinsic quality of the generated embeddings

---

## 1. Semantic Similarity Score

### What it Measures
This metric evaluates how accurately a model captures the expected semantic relationships between philosophical concepts. It measures whether concepts that should be semantically similar (like "will to power" and "übermensch") produce embeddings with high cosine similarity.

### Why it's Important
- **Philosophical Accuracy**: Ensures the chatbot understands conceptual relationships correctly
- **Coherent Responses**: Models with good semantic similarity create more coherent philosophical discussions
- **Knowledge Retrieval**: Critical for finding related concepts during conversation

### Method and Algorithm
The evaluation uses a curated test dataset of philosophical concept pairs with expert-annotated expected similarity scores (0-1 scale).

**Algorithm Steps:**
1. Generate embeddings for concept pairs using the sentence transformer
2. Calculate cosine similarity between each pair: `cosine_similarity(embedding1, embedding2)`
3. Compare computed similarities with expected similarities
4. Calculate three sub-metrics:
   - **Accuracy**: Percentage of predictions within acceptable threshold (±0.1)
   - **Correlation**: Pearson correlation between computed and expected similarities
   - **Mean Absolute Error (MAE)**: Average absolute difference between computed and expected

**Final Score Calculation:**
```
semantic_similarity_score = (accuracy × 0.4) + (correlation × 0.4) + ((1 - mae) × 0.2)
```

**Test Data Example:**
```json
{
  "concept_1": "will to power",
  "concept_2": "übermensch", 
  "expected_similarity": 0.85
}
```

---

## 2. Clustering Score

### What it Measures
This metric evaluates how well the model groups related philosophical concepts into coherent clusters. It tests whether concepts from the same philosophical theme (e.g., Nietzschean ethics, existentialism) cluster together in the embedding space.

### Why it's Important
- **Thematic Organization**: Enables the chatbot to organize knowledge by philosophical schools and themes
- **Context Switching**: Helps maintain thematic coherence during conversations
- **Knowledge Discovery**: Facilitates finding related concepts within philosophical domains

### Method and Algorithm
Uses predefined clusters of philosophical concepts and evaluates clustering quality through multiple metrics.

**Algorithm Steps:**
1. Generate embeddings for all concepts in the test dataset
2. Apply K-means clustering with the true number of clusters
3. Calculate three clustering quality metrics:

**Sub-metrics:**
- **Silhouette Score**: Measures how well-separated clusters are (-1 to 1, higher is better)
- **Cluster Coherence**: Average intra-cluster cosine similarity (how similar concepts within clusters are)
- **Cluster Separation**: Average inter-cluster distance (how different concepts between clusters are)

**Final Score Calculation:**
```
clustering_score = (silhouette_score × 0.5) + (cluster_coherence × 0.3) + (cluster_separation × 0.2)
```

**Test Data Example:**
```json
{
  "cluster_id": 0,
  "theme": "Nietzschean_Ethics",
  "concepts": ["will to power", "master morality", "übermensch", "amor fati"]
}
```

---

## 3. Entity Recognition Score

### What it Measures
This metric evaluates how well the model can distinguish between different types of philosophical entities (PHILOSOPHER, CONCEPT, WORK) based on their embeddings. It tests whether the model creates distinct embedding spaces for different entity types.

### Why it's Important
- **Entity Disambiguation**: Helps the chatbot distinguish between philosophers, their concepts, and their works
- **Accurate Attribution**: Ensures proper attribution of ideas to philosophers
- **Structured Knowledge**: Maintains clear ontological distinctions in the knowledge graph

### Method and Algorithm
Uses annotated philosophical texts with labeled entities of different types.

**Algorithm Steps:**
1. Extract entities and their types from annotated texts
2. Generate embeddings for both full texts and extracted entities
3. Evaluate clustering quality of entities by type
4. Calculate similarity between entities and their source texts

**Sub-metrics:**
- **Entity Clustering**: Silhouette score of entities clustered by type
- **Entity-Text Similarity**: Average cosine similarity between entities and their source texts

**Final Score Calculation:**
```
entity_recognition_score = (entity_clustering_silhouette × 0.6) + (avg_entity_text_similarity × 0.4)
```

**Test Data Example:**
```json
{
  "text": "Nietzsche's concept of the will to power represents...",
  "entities": [
    {"text": "Nietzsche", "label": "PHILOSOPHER"},
    {"text": "will to power", "label": "CONCEPT"}
  ]
}
```

---

## 4. Knowledge Graph Score

### What it Measures
This metric evaluates how well the model supports knowledge graph construction by assessing the quality of relationships between philosophical entities. It measures graph structure quality and semantic coherence of relations.

### Why it's Important
- **Relationship Quality**: Ensures meaningful connections between philosophical concepts
- **Graph Navigation**: Enables effective traversal of the knowledge graph during conversations
- **Contextual Understanding**: Supports understanding of how concepts relate to each other

### Method and Algorithm
Uses relation triplets (subject, predicate, object) extracted from philosophical texts.

**Algorithm Steps:**
1. Build a directed graph from relation triplets
2. Generate embeddings for all entities in relations
3. Calculate graph structure metrics and semantic coherence

**Sub-metrics:**
- **Relation Coherence**: Average cosine similarity between related entities (0.4 weight)
- **Graph Density**: Ratio of actual edges to possible edges, capped at 0.5 (0.3 weight)
- **Clustering Coefficient**: Measure of local connectivity in the graph (0.3 weight)

**Final Score Calculation:**
```
knowledge_graph_score = (relation_coherence × 0.4) + (min(graph_density, 0.5) × 0.3) + (clustering_coefficient × 0.3)
```

**Test Data Example:**
```json
{
  "relations": [
    {"subject": "Nietzsche", "predicate": "developed", "object": "will to power"},
    {"subject": "will to power", "predicate": "relates_to", "object": "übermensch"}
  ]
}
```

---

## 5. Embedding Quality Score

### What it Measures
This metric evaluates the intrinsic quality of embeddings by measuring their diversity, variance, and distributional properties. High-quality embeddings should be diverse (not all similar) while maintaining consistent norms.

### Why it's Important
- **Representational Capacity**: Ensures embeddings can capture diverse philosophical concepts
- **Numerical Stability**: Prevents embedding collapse or extreme values
- **Downstream Performance**: Better embedding quality typically leads to better task performance

### Method and Algorithm
Analyzes the statistical properties of embeddings generated for a standard set of philosophical concepts.

**Algorithm Steps:**
1. Generate embeddings for a standard set of 12 philosophical concepts
2. Calculate distributional and diversity metrics
3. Assess embedding space quality

**Sub-metrics:**
- **Diversity Score**: `1 - average_pairwise_cosine_similarity` (higher diversity is better)
- **Embedding Variance**: Average variance across embedding dimensions (capped at 1.0)
- **Norm Consistency**: Ratio of standard deviation to mean of embedding norms (capped at 1.0)

**Final Score Calculation:**
```
embedding_quality_score = (diversity_score × 0.4) + (min(embedding_variance, 1.0) × 0.3) + (min(norm_std/norm_mean, 1.0) × 0.3)
```

**Standard Test Concepts:**
```
["will to power", "eternal recurrence", "übermensch", "perspectivism", 
 "master morality", "slave morality", "amor fati", "nihilism",
 "dionysian", "apollonian", "ressentiment", "free spirit"]
```

---

## Composite Score

The overall model performance is calculated as the arithmetic mean of all five individual scores:

```
composite_score = (semantic_similarity_score + clustering_score + entity_recognition_score + knowledge_graph_score + embedding_quality_score) / 5
```

## Score Interpretation

- **0.0 - 0.3**: Poor performance, not suitable for philosophical applications
- **0.3 - 0.5**: Moderate performance, may work for basic tasks
- **0.5 - 0.7**: Good performance, suitable for most philosophical chatbot tasks
- **0.7 - 1.0**: Excellent performance, ideal for sophisticated philosophical reasoning

## Usage in Model Selection

The evaluation results provide recommendations for different use cases:

- **General Knowledge Graph Tasks**: Use the model with the highest composite score
- **Semantic Similarity Tasks**: Use the model with the highest semantic similarity score
- **Concept Clustering**: Use the model with the highest clustering score
- **Entity Recognition**: Use the model with the highest entity recognition score
- **Relation Extraction**: Use the model with the highest knowledge graph score

## Technical Dependencies

The evaluation system uses the following key libraries:
- **scikit-learn**: For clustering algorithms and similarity metrics
- **numpy**: For numerical computations and statistical analysis
- **networkx**: For graph structure analysis
- **sentence-transformers**: For embedding generation
- **cosine_similarity**: For semantic similarity calculations

## Data Sources

All test datasets are derived from philosophical texts and expert annotations, focusing on:
- Nietzschean philosophy concepts and relationships
- Classical philosophical distinctions and categorizations
- Semantic relationships validated by philosophical scholars
- Real-world philosophical text structures and entity types
