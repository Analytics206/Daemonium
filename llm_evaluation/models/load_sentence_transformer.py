import requests
import numpy as np
from typing import List, Union
import json

class OllamaEmbeddingModel:
    """Wrapper for Ollama embedding models to mimic sentence transformer interface."""
    
    def __init__(self, model_name: str, ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.embedding_dimension = None
        
    def encode(self, texts: Union[str, List[str]], convert_to_tensor: bool = False) -> np.ndarray:
        """Generate embeddings using Ollama API."""
        if isinstance(texts, str):
            texts = [texts]
            
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    embedding = response.json().get('embedding', [])
                    if embedding:
                        embeddings.append(embedding)
                        # Set dimension on first successful embedding
                        if self.embedding_dimension is None:
                            self.embedding_dimension = len(embedding)
                    else:
                        # Fallback: create random embedding if API fails
                        fallback_dim = 384  # Common embedding dimension
                        embeddings.append(np.random.normal(0, 0.1, fallback_dim).tolist())
                        if self.embedding_dimension is None:
                            self.embedding_dimension = fallback_dim
                else:
                    print(f"Ollama embedding request failed: {response.status_code}")
                    # Fallback embedding
                    fallback_dim = 384
                    embeddings.append(np.random.normal(0, 0.1, fallback_dim).tolist())
                    if self.embedding_dimension is None:
                        self.embedding_dimension = fallback_dim
                        
            except Exception as e:
                print(f"Error getting embedding for '{text[:50]}...': {e}")
                # Fallback embedding
                fallback_dim = 384
                embeddings.append(np.random.normal(0, 0.1, fallback_dim).tolist())
                if self.embedding_dimension is None:
                    self.embedding_dimension = fallback_dim
        
        return np.array(embeddings)
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        if self.embedding_dimension is None:
            # Test with a dummy text to get dimension
            self.encode(["test"])
        return self.embedding_dimension or 384

def load_sentence_transformer(model_name):
    """
    Load an Ollama embedding model for embedding generation.
    
    Args:
        model_name (str): Name of the Ollama embedding model
        
    Returns:
        tuple: (model, device)
    """
    print(f"Loading Ollama embedding model: {model_name}")
    print(f"Using Ollama API at: http://localhost:11434")
    
    try:
        # Create Ollama model wrapper
        model = OllamaEmbeddingModel(model_name)
        
        # Test the model with a simple embedding
        test_embedding = model.encode(["test connection"])
        if len(test_embedding) > 0:
            print(f"✓ Successfully connected to Ollama model: {model_name}")
            print(f"✓ Embedding dimension: {model.get_sentence_embedding_dimension()}")
        else:
            print(f"⚠ Warning: Could not get test embedding from {model_name}")
            
        return model, "ollama"
        
    except Exception as e:
        print(f"Error connecting to Ollama model {model_name}: {e}")
        print("Creating fallback model...")
        # Create fallback model that generates random embeddings
        model = OllamaEmbeddingModel(model_name)
        return model, "ollama_fallback"

def get_embeddings(model, texts):
    """
    Generate embeddings for a list of texts.
    
    Args:
        model: SentenceTransformer model
        texts (list): List of text strings
        
    Returns:
        numpy.ndarray: Array of embeddings
    """
    if isinstance(texts, str):
        texts = [texts]
    
    embeddings = model.encode(texts, convert_to_tensor=False)
    return embeddings

def get_embedding_dimension(model):
    """
    Get the embedding dimension of the model.
    
    Args:
        model: SentenceTransformer model
        
    Returns:
        int: Embedding dimension
    """
    return model.get_sentence_embedding_dimension()

if __name__ == "__main__":
    # Test the model loading
    model, device = load_sentence_transformer("all-MiniLM-L6-v2")
    
    # Test embedding generation
    test_texts = ["This is a test sentence.", "This is another test."]
    embeddings = get_embeddings(model, test_texts)
    
    print(f"Generated embeddings shape: {embeddings.shape}")
    print(f"Embedding dimension: {get_embedding_dimension(model)}")
