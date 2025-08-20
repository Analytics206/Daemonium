#!/usr/bin/env python3
"""
MongoDB Philosophy Keywords Uploader Script

This script uploads the philosophy_keywords.json file to the MongoDB database 'daemonium'
collection 'philosophy_keywords'. It processes a JSON array of entries, each with:
- theme: string
- definition: string
- keywords: string[]

One MongoDB document is stored per theme (_id = slugified theme). Legacy formats are no longer supported.

Author: Daemonium System
Version: 2.0.0
"""

import os
import json
import yaml
import logging
import re
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
            
    def _load_json_file(self, file_path: Path) -> Any:
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
            # Drop any existing text indexes to comply with Mongo's single text index rule
            existing_indexes = self.collection.index_information()
            for name, info in existing_indexes.items():
                # info.get('key') is a list of tuples: (field, direction)
                key_spec = info.get('key', [])
                if any(isinstance(direction, str) and direction.lower() == 'text' for _, direction in key_spec):
                    self.logger.info(f"Dropping existing text index: {name}")
                    self.collection.drop_index(name)

            indexes = [
                IndexModel([("theme", ASCENDING)], name="idx_theme"),
                IndexModel([("filename", ASCENDING)], name="idx_filename"),
                IndexModel([("keywords", ASCENDING)], name="idx_keywords"),
                IndexModel([("theme", "text"), ("definition", "text"), ("keywords", "text")], name="philosophy_keywords_text_v2")
            ]
            
            self.collection.create_indexes(indexes)
            self.logger.info("Created indexes for philosophy_keywords collection")
            
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            raise

    def _slugify(self, text: str) -> str:
        """Create a slug from theme text for stable document IDs."""
        text = text.strip().lower()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s-]+", "-", text)
        return text

    def _prepare_entry_document(self, entry: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare a single theme document for MongoDB insertion."""
        current_time = datetime.utcnow()

        theme = entry.get('theme')
        definition = entry.get('definition', '')
        keywords = entry.get('keywords', []) or []

        # Normalize keywords and remove duplicates while preserving order
        seen = set()
        normalized_keywords: List[str] = []
        for kw in keywords:
            if isinstance(kw, str):
                k = kw.strip()
                if k and k.lower() not in seen:
                    seen.add(k.lower())
                    normalized_keywords.append(k)

        theme_slug = self._slugify(theme) if isinstance(theme, str) else None

        document = {
            '_id': theme_slug or None,
            'category': 'Philosophy Keywords',
            'filename': filename,
            'theme': theme,
            'definition': definition,
            'keywords': normalized_keywords,
            'metadata': {
                'keyword_count': len(normalized_keywords),
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
            if not isinstance(json_data, list):
                raise ValueError("philosophy_keywords.json must be a JSON array of {theme, definition, keywords}")
            
            # Create indexes
            self._create_indexes()
            
            # Process entries individually
            for entry in json_data:
                if not isinstance(entry, dict):
                    self.logger.warning(f"Skipping non-dict entry: {entry}")
                    stats['errors'] += 1
                    continue

                # Basic validation
                if 'theme' not in entry or 'keywords' not in entry:
                    self.logger.warning(f"Skipping invalid entry missing required fields: {entry}")
                    stats['errors'] += 1
                    continue

                document = self._prepare_entry_document(entry, keywords_path.name)

                # Validate _id (requires valid theme)
                if not document.get('_id'):
                    self.logger.warning(f"Skipping entry with invalid theme for _id: {entry}")
                    stats['errors'] += 1
                    continue

                stats['processed'] += 1

                # Determine if existing before upsert to set stats
                existing_doc = self.collection.find_one({'_id': document['_id']})

                if self._upsert_document(document):
                    if existing_doc:
                        stats['updated'] += 1
                    else:
                        stats['uploaded'] += 1
                    
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
