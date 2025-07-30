from models.models_to_compare import MODELS_TO_COMPARE
from evaluation.evaluate_sentence_transformers import evaluate_sentence_transformer_model
from evaluation.compare_st_results import compare_sentence_transformer_results
import os
import time

def main():
    """Main function to evaluate multiple sentence transformer models and compare results."""
    print("Starting Sentence Transformer Evaluation for Knowledge Graph Tasks")
    print("=" * 70)
    
    # Ensure eval_results directory exists
    os.makedirs("eval_results", exist_ok=True)
    
    # Evaluate each model
    model_results = []
    for i, model_name in enumerate(MODELS_TO_COMPARE):
        print(f"\nEvaluating Model {i+1}/{len(MODELS_TO_COMPARE)}: {model_name}")
        print("-" * 50)
        
        output_path = f"eval_results/st_model_{i+1}_results.json"
        try:
            results = evaluate_sentence_transformer_model(model_name, output_path=output_path)
            model_results.append((model_name, output_path, results))
            print(f"✓ Successfully evaluated {model_name}")
            
            # Print quick summary
            if "overall_scores" in results:
                composite_score = results["overall_scores"].get("composite_score", 0)
                print(f"  Composite Score: {composite_score:.3f}")
            
        except Exception as e:
            print(f"✗ Failed to evaluate {model_name}: {e}")
            model_results.append((model_name, None, None))
        
        # Add 5-second delay between model evaluations (except after the last model)
        if i < len(MODELS_TO_COMPARE) - 1:
            print(f"  Waiting 5 seconds before next model evaluation...")
            time.sleep(5)
    
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    
    # Display summary of all models
    successful_evaluations = []
    for model_name, output_path, results in model_results:
        if results and "overall_scores" in results:
            composite_score = results["overall_scores"].get("composite_score", 0)
            successful_evaluations.append((model_name, composite_score, output_path))
            print(f"{model_name:<50} Score: {composite_score:.3f}")
        else:
            print(f"{model_name:<50} FAILED")
    
    # Compare results if we have multiple successful evaluations
    if len(successful_evaluations) >= 2:
        print(f"\nGenerating comparison report...")
        
        # Sort by score (descending)
        successful_evaluations.sort(key=lambda x: x[1], reverse=True)
        
        # Compare top models
        compare_sentence_transformer_results(
            [path for _, _, path in successful_evaluations],
            output_path="eval_results/st_comparison_results.txt"
        )
        
        print("✓ Comparison report saved to eval_results/st_comparison_results.txt")
        
        # Print ranking
        print(f"\nMODEL RANKING:")
        for i, (model_name, score, _) in enumerate(successful_evaluations, 1):
            print(f"{i}. {model_name} (Score: {score:.3f})")
    
    print(f"\nEvaluation completed! Check the eval_results/ directory for detailed reports.")

if __name__ == "__main__":
    main()
