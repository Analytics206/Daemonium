import json
import numpy as np
import os
import time
from pathlib import Path
from models.load_sentence_transformer import load_sentence_transformer, get_embeddings
from evaluation.kg_metrics import (
    calculate_semantic_similarity_accuracy,
    calculate_clustering_quality,
    evaluate_entity_recognition_embeddings,
    calculate_knowledge_graph_metrics,
    calculate_embedding_quality_metrics
)

delaytime = 10

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).parent.parent  # Go up to llm_evaluation directory
DATA_DIR = SCRIPT_DIR / "data"

def evaluate_semantic_similarity(model, test_data_path=None):
    """Evaluate model on semantic similarity tasks."""
    if test_data_path is None:
        test_data_path = DATA_DIR / "semantic_similarity_test.json"
    with open(test_data_path, "r") as f:
        test_data = json.load(f)
    
    concepts_1 = [item["concept_1"] for item in test_data]
    concepts_2 = [item["concept_2"] for item in test_data]
    expected_similarities = [item["expected_similarity"] for item in test_data]
    
    # Generate embeddings
    embeddings_1 = get_embeddings(model, concepts_1)
    embeddings_2 = get_embeddings(model, concepts_2)
    
    # Calculate metrics
    metrics = calculate_semantic_similarity_accuracy(
        embeddings_1, embeddings_2, expected_similarities
    )
    
    return metrics

def evaluate_clustering(model, test_data_path=None):
    """Evaluate model on clustering tasks."""
    if test_data_path is None:
        test_data_path = DATA_DIR / "clustering_test.json"
    with open(test_data_path, "r") as f:
        test_data = json.load(f)
    
    all_concepts = []
    true_labels = []
    
    for cluster_data in test_data:
        concepts = cluster_data["concepts"]
        cluster_id = cluster_data["cluster_id"]
        
        all_concepts.extend(concepts)
        true_labels.extend([cluster_id] * len(concepts))
    
    # Generate embeddings
    embeddings = get_embeddings(model, all_concepts)
    
    # Calculate clustering metrics
    metrics = calculate_clustering_quality(embeddings, true_labels)
    
    return metrics

def evaluate_entity_recognition(model, test_data_path=None):
    """Evaluate model on entity recognition tasks."""
    if test_data_path is None:
        test_data_path = DATA_DIR / "entity_recognition_test.json"
    with open(test_data_path, "r") as f:
        test_data = json.load(f)
    
    texts = []
    entities = []
    entity_labels = []
    
    for item in test_data:
        text = item["text"]
        for entity in item["entities"]:
            texts.append(text)
            entities.append(entity["text"])
            entity_labels.append(entity["label"])
    
    # Generate embeddings
    text_embeddings = get_embeddings(model, texts)
    entity_embeddings = get_embeddings(model, entities)
    
    # Calculate metrics
    metrics = evaluate_entity_recognition_embeddings(
        text_embeddings, entity_embeddings, entity_labels
    )
    
    return metrics

def evaluate_relation_extraction(model, test_data_path=None):
    """Evaluate model on relation extraction tasks."""
    if test_data_path is None:
        test_data_path = DATA_DIR / "relation_extraction_test.json"
    with open(test_data_path, "r") as f:
        test_data = json.load(f)
    
    all_entities = set()
    relations = []
    
    for item in test_data:
        for relation in item["relations"]:
            subject = relation["subject"]
            predicate = relation["predicate"]
            obj = relation["object"]
            
            all_entities.add(subject)
            all_entities.add(obj)
            relations.append((subject, predicate, obj))
    
    # Generate embeddings for all entities
    entity_list = list(all_entities)
    entity_embeddings = get_embeddings(model, entity_list)
    embeddings_dict = dict(zip(entity_list, entity_embeddings))
    
    # Calculate knowledge graph metrics
    metrics = calculate_knowledge_graph_metrics(relations, embeddings_dict)
    
    return metrics

def evaluate_sentence_transformer_model(model_name, output_path="results/st_model_results.json"):
    """
    Comprehensive evaluation of a sentence transformer model for KG tasks.
    
    Args:
        model_name (str): Name of the sentence transformer model
        output_path (str): Path to save results
        
    Returns:
        dict: Comprehensive evaluation results
    """
    print(f"Evaluating sentence transformer: {model_name}")
    
    # Load model
    model, device = load_sentence_transformer(model_name)
    
    # Add delay after loading model to allow Ollama to stabilize
    print("Model loaded, waiting 5 seconds before starting evaluation...")
    time.sleep(delaytime)
    
    results = {
        "model_name": model_name,
        "device": str(device),
        "embedding_dimension": model.get_sentence_embedding_dimension(),
        "evaluations": {}
    }
    
    try:
        # Evaluate semantic similarity
        print("Evaluating semantic similarity...")
        semantic_metrics = evaluate_semantic_similarity(model)
        results["evaluations"]["semantic_similarity"] = semantic_metrics
        
        # Evaluate clustering
        print("Evaluating clustering...")
        clustering_metrics = evaluate_clustering(model)
        results["evaluations"]["clustering"] = clustering_metrics
        
        # Evaluate entity recognition
        print("Evaluating entity recognition...")
        entity_metrics = evaluate_entity_recognition(model)
        results["evaluations"]["entity_recognition"] = entity_metrics
        
        # Evaluate relation extraction
        print("Evaluating relation extraction...")
        relation_metrics = evaluate_relation_extraction(model)
        results["evaluations"]["relation_extraction"] = relation_metrics
        
        # Calculate overall embedding quality
        print("Calculating embedding quality metrics...")
        test_concepts = [
            "will to power", "eternal recurrence", "übermensch", "perspectivism",
            "master morality", "slave morality", "amor fati", "nihilism",
            "dionysian", "apollonian", "ressentiment", "free spirit"
        ]
        test_embeddings = get_embeddings(model, test_concepts)
        embedding_quality = calculate_embedding_quality_metrics(test_embeddings)
        results["evaluations"]["embedding_quality"] = embedding_quality
        
        # Calculate overall scores
        overall_scores = calculate_overall_scores(results["evaluations"])
        results["overall_scores"] = overall_scores
        
        print(f"Evaluation completed for {model_name}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        results["error"] = str(e)
    
    # Save results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def calculate_overall_scores(evaluations):
    """Calculate overall performance scores across all tasks."""
    scores = {}
    
    # Semantic similarity score
    if "semantic_similarity" in evaluations:
        sem_sim = evaluations["semantic_similarity"]
        scores["semantic_similarity_score"] = (
            sem_sim["accuracy"] * 0.4 + 
            sem_sim["correlation"] * 0.4 + 
            (1 - sem_sim["mae"]) * 0.2
        )
    
    # Clustering score
    if "clustering" in evaluations:
        clustering = evaluations["clustering"]
        scores["clustering_score"] = (
            clustering["silhouette_score"] * 0.5 +
            clustering["cluster_coherence"] * 0.3 +
            clustering["cluster_separation"] * 0.2
        )
    
    # Entity recognition score
    if "entity_recognition" in evaluations:
        entity = evaluations["entity_recognition"]
        scores["entity_recognition_score"] = (
            entity["entity_clustering"]["silhouette_score"] * 0.6 +
            entity["avg_entity_text_similarity"] * 0.4
        )
    
    # Knowledge graph score
    if "relation_extraction" in evaluations:
        kg = evaluations["relation_extraction"]
        scores["knowledge_graph_score"] = (
            kg["relation_coherence"] * 0.4 +
            min(kg["graph_density"], 0.5) * 0.3 +  # Cap density at 0.5
            kg["clustering_coefficient"] * 0.3
        )
    
    # Embedding quality score
    if "embedding_quality" in evaluations:
        emb_qual = evaluations["embedding_quality"]
        # Lower similarity = more diverse, which is good
        diversity_score = max(0, 1 - emb_qual["avg_pairwise_similarity"])
        scores["embedding_quality_score"] = (
            diversity_score * 0.4 +
            min(emb_qual["embedding_variance"], 1.0) * 0.3 +
            min(emb_qual["norm_std"] / emb_qual["norm_mean"], 1.0) * 0.3
        )
    
    # Calculate overall composite score
    if scores:
        scores["composite_score"] = np.mean(list(scores.values()))
    
    return scores

if __name__ == "__main__":
    # Test evaluation with a single model
    test_model = "all-MiniLM-L6-v2"
    results = evaluate_sentence_transformer_model(test_model, "results/test_evaluation.json")
    
    print("\nEvaluation Results Summary:")
    if "overall_scores" in results:
        for score_name, score_value in results["overall_scores"].items():
            print(f"{score_name}: {score_value:.3f}")
    else:
        print("Evaluation failed - check error messages above")
