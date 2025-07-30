#!/usr/bin/env python3
"""
Setup script to pull required Ollama embedding models for knowledge graph evaluation.
"""

import subprocess
import sys
import requests
import time
from models.models_to_compare import MODELS_TO_COMPARE

def check_ollama_running():
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def pull_ollama_model(model_name):
    """Pull an Ollama model."""
    print(f"Pulling Ollama model: {model_name}")
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully pulled {model_name}")
            return True
        else:
            print(f"✗ Failed to pull {model_name}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout pulling {model_name} (5 minutes)")
        return False
    except FileNotFoundError:
        print("✗ Ollama command not found. Please install Ollama first.")
        return False
    except Exception as e:
        print(f"✗ Error pulling {model_name}: {e}")
        return False

def list_available_models():
    """List currently available Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("Currently available Ollama models:")
            print(result.stdout)
            return result.stdout
        else:
            print(f"Error listing models: {result.stderr}")
            return ""
            
    except Exception as e:
        print(f"Error listing models: {e}")
        return ""

def main():
    """Main setup function."""
    print("Ollama Embedding Models Setup for Knowledge Graph Evaluation")
    print("=" * 65)
    
    # Check if Ollama is running
    print("1. Checking Ollama status...")
    if not check_ollama_running():
        print("✗ Ollama is not running or not accessible at http://localhost:11434")
        print("  Please start Ollama first:")
        print("  - On Windows: Start Ollama from the Start menu")
        print("  - On macOS/Linux: Run 'ollama serve' in a terminal")
        sys.exit(1)
    else:
        print("✓ Ollama is running and accessible")
    
    # List current models
    print("\n2. Current Ollama models:")
    current_models = list_available_models()
    
    # Pull required models
    print(f"\n3. Pulling required embedding models...")
    print(f"   Models to install: {len(MODELS_TO_COMPARE)}")
    
    successful_pulls = []
    failed_pulls = []
    
    for i, model_name in enumerate(MODELS_TO_COMPARE, 1):
        print(f"\n   [{i}/{len(MODELS_TO_COMPARE)}] {model_name}")
        
        # Check if model is already available
        if model_name in current_models:
            print(f"   ✓ {model_name} already available")
            successful_pulls.append(model_name)
            continue
        
        # Pull the model
        if pull_ollama_model(model_name):
            successful_pulls.append(model_name)
        else:
            failed_pulls.append(model_name)
        
        # Small delay between pulls
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 65)
    print("SETUP SUMMARY")
    print("=" * 65)
    
    print(f"✓ Successfully available: {len(successful_pulls)} models")
    for model in successful_pulls:
        print(f"  - {model}")
    
    if failed_pulls:
        print(f"\n✗ Failed to pull: {len(failed_pulls)} models")
        for model in failed_pulls:
            print(f"  - {model}")
        print("\nYou can try pulling failed models manually:")
        for model in failed_pulls:
            print(f"  ollama pull {model}")
    
    print(f"\nSetup complete! You can now run the evaluation:")
    print(f"  python main_sentence_transformers.py")
    
    if failed_pulls:
        print(f"\nNote: Evaluation will continue with available models only.")

if __name__ == "__main__":
    main()
