#!/usr/bin/env python3
"""
Simple test to check Qdrant connection
"""

from qdrant_client import QdrantClient

try:
    print("Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=6333)
    
    print("Getting collections...")
    collections = client.get_collections()
    
    print(f"✅ Success! Found {len(collections.collections)} collections")
    for collection in collections.collections:
        print(f"  - {collection.name}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
