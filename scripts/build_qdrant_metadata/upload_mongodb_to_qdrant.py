#!/usr/bin/env python3
"""
Qdrant Vector Database Uploader for Daemonium Project
Reads from MongoDB collections and uploads embeddings to Qdrant
"""

import os
import sys
import yaml
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

import pymongo
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np

class QdrantUploader:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Qdrant uploader with configuration"""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Get script directory and project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        
        # Load configuration
        if config_path is None:
            config_path = project_root / "config" / "default.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize connections
        self._init_mongodb()
        self._init_qdrant()
        self._init_sentence_transformer()
        
        # Collection mapping for processing
        self.collections_config = {
            'book_summary': {
                'text_fields': ['content', 'summary', 'text'],
                'metadata_fields': ['title', 'author', 'chapter', 'section', 'filename']
            },
            'aphorisms': {
                'text_fields': ['aphorisms', 'content', 'text'],
                'metadata_fields': ['filename', 'source_file', 'metadata']
            },
            'idea_summary': {
                'text_fields': ['content', 'summary', 'description', 'text'],
                'metadata_fields': ['title', 'philosopher', 'category', 'theme', 'filename']
            },
            'philosopher_summary': {
                'text_fields': ['content', 'biography', 'key_ideas', 'influence', 'summary', 'text'],
                'metadata_fields': ['name', 'birth_year', 'death_year', 'nationality', 'school', 'filename']
            },
            'top_10_ideas': {
                'text_fields': ['content', 'description', 'explanation', 'text'],
                'metadata_fields': ['title', 'rank', 'philosopher', 'category', 'filename']
            },
            'books': {
                'text_fields': ['content', 'text', 'chapters'],
                'metadata_fields': ['title', 'author', 'language', 'filename']
            }
        }
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            mongo_config = self.config['mongodb']
            username = quote_plus(mongo_config['username'])
            password = quote_plus(mongo_config['password'])
            host = mongo_config['host']
            port = mongo_config['port']
            database = mongo_config['database']
            
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            
            self.mongo_client = pymongo.MongoClient(connection_string)
            self.mongo_db = self.mongo_client[database]
            
            # Test connection
            self.mongo_client.admin.command('ping')
            self.logger.info(f"Connected to MongoDB: {host}:{port}/{database}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _init_qdrant(self):
        """Initialize Qdrant connection"""
        try:
            qdrant_config = self.config['qdrant']
            host = qdrant_config['host']
            port = qdrant_config['port']
            
            self.qdrant_client = QdrantClient(host=host, port=port)
            
            # Test connection
            collections = self.qdrant_client.get_collections()
            self.logger.info(f"Connected to Qdrant: {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def _init_sentence_transformer(self):
        """Initialize sentence transformer model"""
        try:
            # Use the best performing model from your evaluation
            model_name = "all-mpnet-base-v2"  # High quality, good balance
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.logger.info(f"Loaded sentence transformer: {model_name} (dim: {self.embedding_dim})")
            
        except Exception as e:
            self.logger.error(f"Failed to load sentence transformer: {e}")
            raise
    
    def create_collection(self, collection_name: str, recreate: bool = False):
        """Create or recreate a Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)
            
            if collection_exists:
                if recreate:
                    self.logger.info(f"Deleting existing collection: {collection_name}")
                    self.qdrant_client.delete_collection(collection_name)
                else:
                    self.logger.info(f"Collection already exists: {collection_name}")
                    return
            
            # Create collection
            self.logger.info(f"Creating collection: {collection_name}")
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            self.logger.info(f"Created collection: {collection_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def generate_text_for_embedding(self, document: Dict[str, Any], config: Dict[str, List[str]]) -> str:
        """Generate combined text for embedding from document fields"""
        text_parts = []
        
        def extract_text_recursive(obj):
            """Recursively extract text from nested structures"""
            if isinstance(obj, str):
                return [obj]
            elif isinstance(obj, list):
                texts = []
                for item in obj:
                    texts.extend(extract_text_recursive(item))
                return texts
            elif isinstance(obj, dict):
                texts = []
                for value in obj.values():
                    texts.extend(extract_text_recursive(value))
                return texts
            else:
                return [str(obj)] if obj is not None else []
        
        # Extract text from specified fields
        for field in config['text_fields']:
            if field in document and document[field]:
                extracted_texts = extract_text_recursive(document[field])
                text_parts.extend([text for text in extracted_texts if text and text.strip()])
        
        # Combine all text parts
        combined_text = " ".join(text_parts)
        
        # Clean and truncate if necessary (sentence transformers have token limits)
        combined_text = combined_text.replace('\n', ' ').replace('\t', ' ')
        combined_text = ' '.join(combined_text.split())  # Normalize whitespace
        
        # Truncate to reasonable length (approx 512 tokens = ~2000 characters)
        if len(combined_text) > 2000:
            combined_text = combined_text[:2000] + "..."
        
        return combined_text
    
    def extract_metadata(self, document: Dict[str, Any], config: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract metadata from document"""
        metadata = {}
        
        # Extract specified metadata fields
        for field in config['metadata_fields']:
            if field in document and document[field] is not None:
                metadata[field] = str(document[field])
        
        # Add common metadata
        metadata['source_collection'] = document.get('_collection', 'unknown')
        metadata['document_id'] = str(document.get('_id', ''))
        metadata['upload_timestamp'] = datetime.now().isoformat()
        
        return metadata
    
    def generate_point_id(self, document: Dict[str, Any], collection_name: str) -> str:
        """Generate a unique point ID for the document"""
        # Use document ID and collection name to create unique hash
        doc_id = str(document.get('_id', ''))
        unique_string = f"{collection_name}_{doc_id}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def process_collection(self, collection_name: str, batch_size: int = 50) -> int:
        """Process a MongoDB collection and upload to Qdrant"""
        if collection_name not in self.collections_config:
            self.logger.warning(f"No configuration found for collection: {collection_name}")
            return 0
        
        config = self.collections_config[collection_name]
        
        try:
            # Get MongoDB collection
            mongo_collection = self.mongo_db[collection_name]
            total_docs = mongo_collection.count_documents({})
            
            if total_docs == 0:
                self.logger.info(f"No documents found in {collection_name}")
                return 0
            
            self.logger.info(f"Processing {total_docs} documents from {collection_name}")
            
            # Create Qdrant collection name (prefix with 'daemonium_')
            qdrant_collection_name = f"daemonium_{collection_name}"
            self.create_collection(qdrant_collection_name)
            
            # Process documents in batches
            processed_count = 0
            points_batch = []
            
            for document in mongo_collection.find({}):
                try:
                    # Generate text for embedding
                    text = self.generate_text_for_embedding(document, config)
                    if not text.strip():
                        self.logger.warning(f"Empty text for document {document.get('_id')}")
                        continue
                    
                    # Generate embedding
                    embedding = self.model.encode(text, convert_to_tensor=False)
                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()
                    
                    # Extract metadata
                    metadata = self.extract_metadata(document, config)
                    metadata['original_text'] = text[:500] + "..." if len(text) > 500 else text
                    
                    # Create point
                    point_id = self.generate_point_id(document, collection_name)
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=metadata
                    )
                    
                    points_batch.append(point)
                    processed_count += 1
                    
                    # Upload batch when full
                    if len(points_batch) >= batch_size:
                        self.qdrant_client.upsert(
                            collection_name=qdrant_collection_name,
                            points=points_batch
                        )
                        self.logger.info(f"Uploaded batch of {len(points_batch)} points to {qdrant_collection_name}")
                        points_batch = []
                    
                except Exception as e:
                    self.logger.error(f"Error processing document {document.get('_id')}: {e}")
                    continue
            
            # Upload remaining points
            if points_batch:
                self.qdrant_client.upsert(
                    collection_name=qdrant_collection_name,
                    points=points_batch
                )
                self.logger.info(f"Uploaded final batch of {len(points_batch)} points to {qdrant_collection_name}")
            
            self.logger.info(f"Successfully processed {processed_count} documents from {collection_name}")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"Failed to process collection {collection_name}: {e}")
            raise
    
    def upload_all_collections(self, recreate_collections: bool = False):
        """Upload all configured MongoDB collections to Qdrant"""
        total_processed = 0
        
        self.logger.info("Starting upload of all MongoDB collections to Qdrant")
        start_time = datetime.now()
        
        for collection_name in self.collections_config.keys():
            try:
                self.logger.info(f"\n{'='*50}")
                self.logger.info(f"Processing collection: {collection_name}")
                self.logger.info(f"{'='*50}")
                
                processed = self.process_collection(collection_name)
                total_processed += processed
                
            except Exception as e:
                self.logger.error(f"Failed to process collection {collection_name}: {e}")
                continue
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"UPLOAD COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total documents processed: {total_processed}")
        self.logger.info(f"Total duration: {duration}")
        self.logger.info(f"Average processing rate: {total_processed / duration.total_seconds():.2f} docs/second")
    
    def get_qdrant_statistics(self):
        """Get statistics about Qdrant collections"""
        try:
            collections = self.qdrant_client.get_collections().collections
            
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"QDRANT STATISTICS")
            self.logger.info(f"{'='*50}")
            
            total_points = 0
            for collection in collections:
                if collection.name.startswith('daemonium_'):
                    info = self.qdrant_client.get_collection(collection.name)
                    points_count = info.points_count
                    total_points += points_count
                    
                    self.logger.info(f"{collection.name}: {points_count:,} points")
            
            self.logger.info(f"Total points across all collections: {total_points:,}")
            
        except Exception as e:
            self.logger.error(f"Failed to get Qdrant statistics: {e}")
    
    def close_connections(self):
        """Close database connections"""
        try:
            if hasattr(self, 'mongo_client'):
                self.mongo_client.close()
            self.logger.info("Closed database connections")
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")

def main():
    """Main execution function"""
    uploader = None
    try:
        # Initialize uploader
        uploader = QdrantUploader()
        
        # Upload all collections
        uploader.upload_all_collections(recreate_collections=True)
        
        # Show statistics
        uploader.get_qdrant_statistics()
        
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        sys.exit(1)
    
    finally:
        if uploader:
            uploader.close_connections()

if __name__ == "__main__":
    main()
