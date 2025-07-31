#!/usr/bin/env python3
"""
Test script to verify Qdrant connection and basic functionality
"""

import sys
import yaml
from pathlib import Path
from qdrant_client import QdrantClient

def test_qdrant_connection():
    """Test basic Qdrant connection"""
    try:
        # Get project root and load config
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        config_path = project_root / "config" / "default.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Connect to Qdrant
        qdrant_config = config['qdrant']
        host = qdrant_config['host']
        port = qdrant_config['port']
        
        print(f"Connecting to Qdrant at {host}:{port}...")
        client = QdrantClient(host=host, port=port)
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Successfully connected to Qdrant!")
        print(f"Found {len(collections.collections)} existing collections:")
        
        for collection in collections.collections:
            info = client.get_collection(collection.name)
            print(f"  - {collection.name}: {info.points_count:,} points")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return False

def test_sentence_transformers():
    """Test sentence transformers loading"""
    try:
        print("\nTesting sentence transformers...")
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer("all-mpnet-base-v2")
        embedding_dim = model.get_sentence_embedding_dimension()
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        embedding = model.encode(test_text)
        
        print(f"✅ Successfully loaded sentence transformer!")
        print(f"Model: all-mpnet-base-v2")
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Test embedding shape: {embedding.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load sentence transformers: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Qdrant uploader dependencies...\n")
    
    qdrant_ok = test_qdrant_connection()
    transformers_ok = test_sentence_transformers()
    
    print(f"\n{'='*50}")
    print("TEST RESULTS:")
    print(f"Qdrant Connection: {'✅ PASS' if qdrant_ok else '❌ FAIL'}")
    print(f"Sentence Transformers: {'✅ PASS' if transformers_ok else '❌ FAIL'}")
    
    if qdrant_ok and transformers_ok:
        print("\n🎉 All tests passed! Ready to run the uploader.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check dependencies and configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
