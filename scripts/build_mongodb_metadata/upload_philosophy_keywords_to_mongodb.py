#!/usr/bin/env python3
"""
MongoDB Philosophy Keywords Uploader Script

This script uploads the philosophy_keywords.json file to the MongoDB database 'daemonium' 
collection 'philosophy_keywords'. It processes the comprehensive philosophy keywords structure
including philosophical branches, fundamental concepts, and major questions.

Author: Daemonium System
Version: 1.0.0
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from pymongo import MongoClient, IndexModel, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from urllib.parse import quote_plus
from datetime import datetime


class PhilosophyKeywordsUploader:
    """Handles uploading philosophy keywords JSON file to MongoDB."""
    
    def __init__(self, config_path: str):
        """Initialize the uploader with configuration."""
        self.config_path = Path(config_path)
        self.client = None
        self.database = None
        self.collection = None
        self._setup_logging()
        self.config = self._load_config()
        
    def _setup_logging(self) -> None:
        """Configure logging for the uploader."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('philosophy_keywords_upload.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML configuration: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            raise
            
    def connect_to_mongodb(self) -> None:
        """Establish connection to MongoDB."""
        try:
            mongo_config = self.config['mongodb']
            host = mongo_config.get('host', 'localhost')
            port = mongo_config.get('port', 27018)
            database = mongo_config.get('database', 'daemonium')
            username = mongo_config.get('username')
            password = mongo_config.get('password')
            
            # Build connection string with proper URL encoding
            if username and password:
                # URL-encode username and password to handle special characters
                encoded_username = quote_plus(username)
                encoded_password = quote_plus(password)
                # For root users, authenticate against admin database
                connection_string = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{database}?authSource=admin"
            else:
                connection_string = f"mongodb://{host}:{port}/{database}"
            
            self.client = MongoClient(connection_string)
            # Test the connection
            self.client.admin.command('ping')
            
            self.database = self.client[database]
            self.collection = self.database['philosophy_keywords']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosophy_keywords")
            
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Missing MongoDB configuration key: {e}")
            raise
            
    def disconnect_from_mongodb(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
            
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Successfully loaded JSON file: {file_path}")
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading file {file_path}: {e}")
            raise

    def _create_indexes(self) -> None:
        """Create indexes for the philosophy_keywords collection."""
        try:
            indexes = [
                IndexModel([("category", ASCENDING)]),
                IndexModel([("filename", ASCENDING)]),
                IndexModel([("keywords", ASCENDING)]),
                IndexModel([("philosophy_keywords", "text"), ("fundamental_concepts", "text"), ("major_philosophical_questions", "text"), ("keywords", "text")], name="text_search_index")
            ]
            
            self.collection.create_indexes(indexes)
            self.logger.info("Created indexes for philosophy_keywords collection")
            
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            raise

    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare the complete philosophy keywords document for MongoDB insertion."""
        current_time = datetime.utcnow()
        
        # Extract all keywords for search indexing
        all_keywords = []
        
        # Collect keywords from philosophical branches
        philosophy_keywords = json_data.get('philosophy_keywords', {})
        for branch_data in philosophy_keywords.values():
            all_keywords.extend(branch_data.get('key_concepts', []))
        
        # Add fundamental concepts
        all_keywords.extend(json_data.get('fundamental_concepts', []))
        
        # Add questions as keywords (first few words of each question)
        questions = json_data.get('major_philosophical_questions', [])
        for question in questions:
            # Extract first 3-4 words from each question for keyword indexing
            question_words = question.lower().replace('?', '').split()[:4]
            all_keywords.extend(question_words)
        
        # Calculate statistics
        total_branches = len(philosophy_keywords)
        total_concepts = len(json_data.get('fundamental_concepts', []))
        total_questions = len(questions)
        total_branch_concepts = sum(len(branch.get('key_concepts', [])) for branch in philosophy_keywords.values())
        
        document = {
            '_id': 'philosophy_keywords_complete',
            'category': 'Philosophy Keywords',
            'filename': filename,
            'philosophy_keywords': philosophy_keywords,
            'fundamental_concepts': json_data.get('fundamental_concepts', []),
            'major_philosophical_questions': questions,
            'keywords': list(set(all_keywords)),  # Remove duplicates for search indexing
            'metadata': {
                'total_branches': total_branches,
                'total_fundamental_concepts': total_concepts,
                'total_questions': total_questions,
                'total_branch_concepts': total_branch_concepts,
                'total_unique_keywords': len(set(all_keywords)),
                'upload_timestamp': current_time,
                'last_updated': current_time,
                'source_file': filename
            }
        }
        
        return document
            
    def _upsert_document(self, document: Dict[str, Any]) -> bool:
        """Insert new document or update existing one."""
        try:
            # Check if document already exists
            existing_doc = self.collection.find_one({'_id': document['_id']})
            
            if existing_doc:
                # Update existing document, preserving original upload timestamp
                document['metadata']['upload_timestamp'] = existing_doc['metadata'].get('upload_timestamp', document['metadata']['upload_timestamp'])
                document['metadata']['last_updated'] = datetime.utcnow()
                
                result = self.collection.replace_one(
                    {'_id': document['_id']}, 
                    document
                )
                
                if result.modified_count > 0:
                    self.logger.info(f"Updated document: {document['_id']}")
                    return True
                else:
                    self.logger.warning(f"No changes made to document: {document['_id']}")
                    return True
            else:
                # Insert new document
                result = self.collection.insert_one(document)
                self.logger.info(f"Inserted new document: {document['_id']}")
                return True
                
        except DuplicateKeyError:
            self.logger.warning(f"Document with ID {document['_id']} already exists")
            return False
        except Exception as e:
            self.logger.error(f"Error upserting document {document['_id']}: {e}")
            return False

    def process_philosophy_keywords_file(self, keywords_file: str) -> Dict[str, int]:
        """Process the philosophy keywords JSON file."""
        keywords_path = Path(keywords_file)
        
        if not keywords_path.exists():
            self.logger.error(f"Philosophy keywords file not found: {keywords_path}")
            raise FileNotFoundError(f"Philosophy keywords file not found: {keywords_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'errors': 0
        }
        
        try:
            # Load the JSON file
            json_data = self._load_json_file(keywords_path)
            
            # Create indexes
            self._create_indexes()
            
            # Process the entire file as one document
            stats['processed'] = 1
            
            document = self._prepare_document(json_data, keywords_path.name)
            
            # Check if this is an update or new upload
            existing_doc = self.collection.find_one({'_id': document['_id']})
            
            # Upload/update the document
            if self._upsert_document(document):
                if existing_doc:
                    stats['updated'] = 1
                else:
                    stats['uploaded'] = 1
                    
        except Exception as e:
            self.logger.error(f"Error processing philosophy keywords file: {e}")
            stats['errors'] = 1
            
        return stats
        
    def run(self, keywords_file: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosophy keywords upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process the philosophy keywords file
            stats = self.process_philosophy_keywords_file(keywords_file)
            
            # Log summary
            self.logger.info("Upload process completed")
            self.logger.info(f"Items processed: {stats['processed']}")
            self.logger.info(f"New uploads: {stats['uploaded']}")
            self.logger.info(f"Updates: {stats['updated']}")
            self.logger.info(f"Errors: {stats['errors']}")
            
        except Exception as e:
            self.logger.error(f"Fatal error during upload process: {e}")
            raise
        finally:
            # Always disconnect from MongoDB
            self.disconnect_from_mongodb()


def main():
    """Main entry point for the script."""
    # Define paths relative to the script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    config_path = project_root / 'config' / 'default.yaml'
    keywords_file = project_root / 'json_bot_docs' / 'philosophy_keywords' / 'philosophy_keywords.json'
    
    try:
        # Create and run the uploader
        uploader = PhilosophyKeywordsUploader(str(config_path))
        uploader.run(str(keywords_file))
        
        print("Philosophy keywords upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosophy keywords upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
