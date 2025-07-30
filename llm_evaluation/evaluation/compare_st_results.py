import json
import numpy as np
from datetime import datetime

def compare_sentence_transformer_results(result_paths, output_path="eval_results/st_comparison_results.txt"):
    """
    Compare results from multiple sentence transformer evaluations.
    
    Args:
        result_paths (list): List of paths to result JSON files
        output_path (str): Path to save comparison report
    """
    # Load all results
    results = []
    for path in result_paths:
        try:
            with open(path, "r") as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Error loading {path}: {e}")
    
    if len(results) < 2:
        print("Need at least 2 results to compare")
        return
    
    # Generate comparison report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("SENTENCE TRANSFORMER MODEL COMPARISON REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Models Compared: {len(results)}\n\n")
        
        # Model overview
        f.write("MODEL OVERVIEW\n")
        f.write("-" * 30 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            embedding_dim = result.get("embedding_dimension", "Unknown")
            device = result.get("device", "Unknown")
            f.write(f"{i}. {model_name}\n")
            f.write(f"   Embedding Dimension: {embedding_dim}\n")
            f.write(f"   Device: {device}\n\n")
        
        # Overall scores comparison
        f.write("OVERALL SCORES COMPARISON\n")
        f.write("-" * 40 + "\n")
        
        score_categories = [
            "semantic_similarity_score",
            "clustering_score", 
            "entity_recognition_score",
            "knowledge_graph_score",
            "embedding_quality_score",
            "composite_score"
        ]
        
        # Create comparison table
        f.write(f"{'Metric':<25}")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")[:15]
            f.write(f"{model_name:>15}")
        f.write("\n" + "-" * (25 + 15 * len(results)) + "\n")
        
        for score_category in score_categories:
            f.write(f"{score_category:<25}")
            scores = []
            for result in results:
                score = result.get("overall_scores", {}).get(score_category, 0)
                scores.append(score)
                f.write(f"{score:>15.3f}")
            f.write("\n")
            
            # Highlight best score
            if scores:
                best_idx = np.argmax(scores)
                f.write(f"{'Best:':<25}")
                for i, score in enumerate(scores):
                    marker = " *" if i == best_idx else "  "
                    f.write(f"{marker:>15}")
                f.write("\n\n")
        
        # Detailed task performance
        f.write("DETAILED TASK PERFORMANCE\n")
        f.write("-" * 40 + "\n\n")
        
        # Semantic Similarity Analysis
        f.write("1. SEMANTIC SIMILARITY\n")
        f.write("   " + "-" * 20 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            sem_sim = result.get("evaluations", {}).get("semantic_similarity", {})
            f.write(f"   {model_name}:\n")
            f.write(f"     Accuracy: {sem_sim.get('accuracy', 0):.3f}\n")
            f.write(f"     Correlation: {sem_sim.get('correlation', 0):.3f}\n")
            f.write(f"     MAE: {sem_sim.get('mae', 0):.3f}\n\n")
        
        # Clustering Analysis
        f.write("2. CLUSTERING QUALITY\n")
        f.write("   " + "-" * 18 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            clustering = result.get("evaluations", {}).get("clustering", {})
            f.write(f"   {model_name}:\n")
            f.write(f"     Silhouette Score: {clustering.get('silhouette_score', 0):.3f}\n")
            f.write(f"     Cluster Coherence: {clustering.get('cluster_coherence', 0):.3f}\n")
            f.write(f"     Cluster Separation: {clustering.get('cluster_separation', 0):.3f}\n\n")
        
        # Entity Recognition Analysis
        f.write("3. ENTITY RECOGNITION\n")
        f.write("   " + "-" * 18 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            entity = result.get("evaluations", {}).get("entity_recognition", {})
            entity_clustering = entity.get("entity_clustering", {})
            f.write(f"   {model_name}:\n")
            f.write(f"     Entity Clustering Silhouette: {entity_clustering.get('silhouette_score', 0):.3f}\n")
            f.write(f"     Avg Entity-Text Similarity: {entity.get('avg_entity_text_similarity', 0):.3f}\n")
            f.write(f"     Unique Entity Types: {entity.get('unique_entity_types', 0)}\n\n")
        
        # Knowledge Graph Analysis
        f.write("4. KNOWLEDGE GRAPH CONSTRUCTION\n")
        f.write("   " + "-" * 30 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            kg = result.get("evaluations", {}).get("relation_extraction", {})
            f.write(f"   {model_name}:\n")
            f.write(f"     Relation Coherence: {kg.get('relation_coherence', 0):.3f}\n")
            f.write(f"     Graph Density: {kg.get('graph_density', 0):.3f}\n")
            f.write(f"     Clustering Coefficient: {kg.get('clustering_coefficient', 0):.3f}\n")
            f.write(f"     Nodes: {kg.get('num_nodes', 0)}, Edges: {kg.get('num_edges', 0)}\n\n")
        
        # Embedding Quality Analysis
        f.write("5. EMBEDDING QUALITY\n")
        f.write("   " + "-" * 17 + "\n")
        for i, result in enumerate(results, 1):
            model_name = result.get("model_name", f"Model {i}")
            emb_qual = result.get("evaluations", {}).get("embedding_quality", {})
            f.write(f"   {model_name}:\n")
            f.write(f"     Avg Pairwise Similarity: {emb_qual.get('avg_pairwise_similarity', 0):.3f}\n")
            f.write(f"     Embedding Variance: {emb_qual.get('embedding_variance', 0):.3f}\n")
            f.write(f"     Norm Mean: {emb_qual.get('norm_mean', 0):.3f}\n")
            f.write(f"     Norm Std: {emb_qual.get('norm_std', 0):.3f}\n\n")
        
        # Recommendations
        f.write("RECOMMENDATIONS\n")
        f.write("-" * 20 + "\n")
        
        # Find best model for each task
        best_models = find_best_models(results)
        
        for task, (model_idx, score) in best_models.items():
            model_name = results[model_idx].get("model_name", f"Model {model_idx + 1}")
            f.write(f"Best for {task}: {model_name} (Score: {score:.3f})\n")
        
        # Overall recommendation
        overall_scores = []
        for result in results:
            score = result.get("overall_scores", {}).get("composite_score", 0)
            overall_scores.append(score)
        
        best_overall_idx = np.argmax(overall_scores)
        best_overall_model = results[best_overall_idx].get("model_name", f"Model {best_overall_idx + 1}")
        best_overall_score = overall_scores[best_overall_idx]
        
        f.write(f"\nOVERALL BEST MODEL: {best_overall_model} (Composite Score: {best_overall_score:.3f})\n")
        
        # Usage recommendations
        f.write(f"\nUSAGE RECOMMENDATIONS:\n")
        f.write(f"- For general knowledge graph tasks: {best_overall_model}\n")
        
        # Find specialized recommendations
        if best_models.get("semantic_similarity_score"):
            sem_model_idx = best_models["semantic_similarity_score"][0]
            sem_model = results[sem_model_idx].get("model_name", f"Model {sem_model_idx + 1}")
            f.write(f"- For semantic similarity tasks: {sem_model}\n")
        
        if best_models.get("clustering_score"):
            cluster_model_idx = best_models["clustering_score"][0]
            cluster_model = results[cluster_model_idx].get("model_name", f"Model {cluster_model_idx + 1}")
            f.write(f"- For concept clustering: {cluster_model}\n")
        
        f.write(f"\nReport generated successfully!")

def find_best_models(results):
    """Find the best model for each evaluation task."""
    score_categories = [
        "semantic_similarity_score",
        "clustering_score", 
        "entity_recognition_score",
        "knowledge_graph_score",
        "embedding_quality_score"
    ]
    
    best_models = {}
    
    for category in score_categories:
        scores = []
        for result in results:
            score = result.get("overall_scores", {}).get(category, 0)
            scores.append(score)
        
        if scores:
            best_idx = np.argmax(scores)
            best_models[category] = (best_idx, scores[best_idx])
    
    return best_models

if __name__ == "__main__":
    # Test with dummy data
    print("Testing comparison functionality...")
    
    # This would normally be called by the main evaluation script
    # compare_sentence_transformer_results([
    #     "results/st_model_1_results.json",
    #     "results/st_model_2_results.json"
    # ])
    
    print("Comparison script ready!")
