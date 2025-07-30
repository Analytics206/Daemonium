import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score, silhouette_score
from sklearn.cluster import KMeans
import networkx as nx
from collections import defaultdict
import warnings

warnings.filterwarnings("ignore")

def calculate_semantic_similarity_accuracy(embeddings1, embeddings2, expected_similarities, threshold=0.1):
    """
    Calculate how well the model captures expected semantic similarities.
    
    Args:
        embeddings1: Embeddings for first set of concepts
        embeddings2: Embeddings for second set of concepts  
        expected_similarities: Expected similarity scores (0-1)
        threshold: Acceptable deviation from expected similarity
        
    Returns:
        dict: Accuracy metrics
    """
    computed_similarities = []
    for emb1, emb2 in zip(embeddings1, embeddings2):
        sim = cosine_similarity([emb1], [emb2])[0][0]
        computed_similarities.append(sim)
    
    computed_similarities = np.array(computed_similarities)
    expected_similarities = np.array(expected_similarities)
    
    # Calculate accuracy within threshold
    differences = np.abs(computed_similarities - expected_similarities)
    accurate_predictions = np.sum(differences <= threshold)
    accuracy = accurate_predictions / len(expected_similarities)
    
    # Calculate correlation
    correlation = np.corrcoef(computed_similarities, expected_similarities)[0, 1]
    
    # Calculate mean absolute error
    mae = np.mean(differences)
    
    return {
        "accuracy": accuracy,
        "correlation": correlation,
        "mae": mae,
        "computed_similarities": computed_similarities.tolist(),
        "expected_similarities": expected_similarities.tolist()
    }

def calculate_clustering_quality(embeddings, true_labels):
    """
    Evaluate clustering quality using silhouette score and other metrics.
    
    Args:
        embeddings: Array of embeddings
        true_labels: True cluster labels
        
    Returns:
        dict: Clustering quality metrics
    """
    n_clusters = len(set(true_labels))
    
    # Perform K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    predicted_labels = kmeans.fit_predict(embeddings)
    
    # Calculate silhouette score
    silhouette_avg = silhouette_score(embeddings, predicted_labels)
    
    # Calculate cluster coherence (average intra-cluster similarity)
    cluster_coherence = calculate_cluster_coherence(embeddings, predicted_labels)
    
    # Calculate cluster separation (average inter-cluster distance)
    cluster_separation = calculate_cluster_separation(embeddings, predicted_labels)
    
    return {
        "silhouette_score": silhouette_avg,
        "cluster_coherence": cluster_coherence,
        "cluster_separation": cluster_separation,
        "n_clusters": n_clusters,
        "predicted_labels": predicted_labels.tolist(),
        "true_labels": true_labels
    }

def calculate_cluster_coherence(embeddings, labels):
    """Calculate average intra-cluster cosine similarity."""
    coherence_scores = []
    unique_labels = set(labels)
    
    for label in unique_labels:
        cluster_embeddings = embeddings[np.array(labels) == label]
        if len(cluster_embeddings) > 1:
            similarities = cosine_similarity(cluster_embeddings)
            # Get upper triangle (excluding diagonal)
            upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
            coherence_scores.append(np.mean(upper_triangle))
    
    return np.mean(coherence_scores) if coherence_scores else 0.0

def calculate_cluster_separation(embeddings, labels):
    """Calculate average inter-cluster distance."""
    unique_labels = set(labels)
    separation_scores = []
    
    for i, label1 in enumerate(unique_labels):
        for j, label2 in enumerate(unique_labels):
            if i < j:  # Avoid duplicate pairs
                cluster1_embeddings = embeddings[np.array(labels) == label1]
                cluster2_embeddings = embeddings[np.array(labels) == label2]
                
                # Calculate average distance between clusters
                distances = []
                for emb1 in cluster1_embeddings:
                    for emb2 in cluster2_embeddings:
                        dist = 1 - cosine_similarity([emb1], [emb2])[0][0]
                        distances.append(dist)
                
                separation_scores.append(np.mean(distances))
    
    return np.mean(separation_scores) if separation_scores else 0.0

def evaluate_entity_recognition_embeddings(text_embeddings, entity_embeddings, entity_labels):
    """
    Evaluate how well embeddings can distinguish between different entity types.
    
    Args:
        text_embeddings: Embeddings of full texts
        entity_embeddings: Embeddings of extracted entities
        entity_labels: Labels for entity types
        
    Returns:
        dict: Entity recognition quality metrics
    """
    # Calculate entity type clustering quality
    unique_labels = list(set(entity_labels))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    numeric_labels = [label_to_idx[label] for label in entity_labels]
    
    clustering_metrics = calculate_clustering_quality(entity_embeddings, numeric_labels)
    
    # Calculate entity-text relevance (how well entities relate to their source texts)
    entity_text_similarities = []
    for text_emb, entity_emb in zip(text_embeddings, entity_embeddings):
        sim = cosine_similarity([text_emb], [entity_emb])[0][0]
        entity_text_similarities.append(sim)
    
    return {
        "entity_clustering": clustering_metrics,
        "avg_entity_text_similarity": np.mean(entity_text_similarities),
        "entity_text_similarities": entity_text_similarities,
        "unique_entity_types": len(unique_labels)
    }

def calculate_knowledge_graph_metrics(relations, embeddings_dict):
    """
    Calculate knowledge graph quality metrics based on relation embeddings.
    
    Args:
        relations: List of relation triplets (subject, predicate, object)
        embeddings_dict: Dictionary mapping entities to their embeddings
        
    Returns:
        dict: Knowledge graph quality metrics
    """
    # Build graph
    G = nx.DiGraph()
    for subj, pred, obj in relations:
        G.add_edge(subj, obj, relation=pred)
    
    # Calculate graph structure metrics
    density = nx.density(G)
    
    # Calculate average path length (for connected components)
    try:
        avg_path_length = nx.average_shortest_path_length(G)
    except:
        avg_path_length = 0.0
    
    # Calculate clustering coefficient
    clustering_coeff = nx.average_clustering(G.to_undirected())
    
    # Calculate relation coherence (how semantically similar are related entities)
    relation_coherence = calculate_relation_coherence(relations, embeddings_dict)
    
    return {
        "graph_density": density,
        "avg_path_length": avg_path_length,
        "clustering_coefficient": clustering_coeff,
        "relation_coherence": relation_coherence,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges()
    }

def calculate_relation_coherence(relations, embeddings_dict):
    """Calculate how semantically coherent the relations are."""
    coherence_scores = []
    
    for subj, pred, obj in relations:
        if subj in embeddings_dict and obj in embeddings_dict:
            subj_emb = embeddings_dict[subj]
            obj_emb = embeddings_dict[obj]
            similarity = cosine_similarity([subj_emb], [obj_emb])[0][0]
            coherence_scores.append(similarity)
    
    return np.mean(coherence_scores) if coherence_scores else 0.0

def calculate_embedding_quality_metrics(embeddings):
    """
    Calculate intrinsic embedding quality metrics.
    
    Args:
        embeddings: Array of embeddings
        
    Returns:
        dict: Embedding quality metrics
    """
    # Calculate average cosine similarity (diversity measure)
    similarities = cosine_similarity(embeddings)
    # Get upper triangle excluding diagonal
    upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
    avg_similarity = np.mean(upper_triangle)
    
    # Calculate embedding variance (spread measure)
    embedding_variance = np.var(embeddings, axis=0).mean()
    
    # Calculate embedding norm distribution
    norms = np.linalg.norm(embeddings, axis=1)
    norm_mean = np.mean(norms)
    norm_std = np.std(norms)
    
    return {
        "avg_pairwise_similarity": avg_similarity,
        "embedding_variance": embedding_variance,
        "norm_mean": norm_mean,
        "norm_std": norm_std,
        "embedding_dimension": embeddings.shape[1]
    }

if __name__ == "__main__":
    # Test the metrics with dummy data
    print("Testing KG metrics with dummy data...")
    
    # Test semantic similarity
    emb1 = np.random.rand(5, 384)
    emb2 = np.random.rand(5, 384)
    expected_sim = [0.8, 0.6, 0.9, 0.7, 0.5]
    
    sim_metrics = calculate_semantic_similarity_accuracy(emb1, emb2, expected_sim)
    print(f"Semantic similarity metrics: {sim_metrics}")
    
    # Test clustering
    embeddings = np.random.rand(20, 384)
    labels = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 1, 2, 3, 0, 1, 2, 3]
    
    cluster_metrics = calculate_clustering_quality(embeddings, labels)
    print(f"Clustering metrics: {cluster_metrics}")
    
    print("KG metrics test completed successfully!")
