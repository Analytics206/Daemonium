#!/usr/bin/env python3
"""
MongoDB Modern Adaptation Uploader Script

This script loops through the json_bot_docs/modern_adaptation folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'modern_adaptation'. It skips template files
and merges existing documents while uploading new ones.

Author: Daemonium System
Version: 1.0.0
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from urllib.parse import quote_plus


class ModernAdaptationUploader:
    """Handles uploading modern adaptation JSON files to MongoDB."""
    
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
                logging.FileHandler('modern_adaptation_upload.log'),
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
            self.collection = self.database['modern_adaptation']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: modern_adaptation")
            
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
            
    def _is_template_file(self, filename: str) -> bool:
        """Check if the file is a template file that should be skipped."""
        return filename.lower().startswith('template')
        
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Loaded JSON file: {file_path.name}")
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON file {file_path.name}: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"JSON file not found: {file_path}")
            raise
            
    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion."""
        # Create a unique identifier based on author and category
        author = json_data.get('author', 'unknown').replace(' ', '_').lower()
        category = json_data.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract modern adaptation data
        modern_adaptation = json_data.get('modern_adaptation', {})
        
        # Count modern topics
        modern_topics = modern_adaptation.get('modern_topics', [])
        topics_count = len(modern_topics) if isinstance(modern_topics, list) else 0
        
        # Extract context awareness data
        context_awareness = modern_adaptation.get('context_awareness', {})
        historical_refs_count = len(context_awareness.get('historical_self_reference', []))
        era_contrast_rules_count = len(context_awareness.get('era_contrast_rules', []))
        
        # Extract adaptive templates
        adaptive_templates = modern_adaptation.get('adaptive_templates', [])
        adaptive_templates_count = len(adaptive_templates) if isinstance(adaptive_templates, list) else 0
        
        # Extract tone instructions (dynamic section)
        tone_instructions = modern_adaptation.get('tone_instructions', {})
        tone_instructions_count = len(tone_instructions) if isinstance(tone_instructions, dict) else 0
        
        document = {
            '_id': f"{author}_{category}",
            'filename': filename,
            'author': json_data.get('author', 'Unknown'),
            'category': json_data.get('category', 'Unknown'),
            'modern_adaptation': {
                'purpose': modern_adaptation.get('purpose', ''),
                'context_awareness': context_awareness,
                'modern_topics': modern_topics,
                'adaptive_templates': adaptive_templates,
                'tone_instructions': tone_instructions
            },
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'modern_topics_count': topics_count,
                'historical_references_count': historical_refs_count,
                'era_contrast_rules_count': era_contrast_rules_count,
                'adaptive_templates_count': adaptive_templates_count,
                'tone_instructions_count': tone_instructions_count,
                'has_purpose': bool(modern_adaptation.get('purpose', '')),
                'has_context_awareness': bool(context_awareness),
                'has_adaptive_templates': bool(adaptive_templates),
                'has_tone_instructions': bool(tone_instructions)
            }
        }
        return document
        
    def _upsert_document(self, document: Dict[str, Any]) -> bool:
        """Insert new document or update existing one."""
        from datetime import datetime
        
        try:
            # Set timestamps
            current_time = datetime.utcnow()
            
            # Check if document exists
            existing_doc = self.collection.find_one({'_id': document['_id']})
            
            if existing_doc:
                # Update existing document
                document['metadata']['upload_timestamp'] = existing_doc['metadata'].get('upload_timestamp', current_time)
                document['metadata']['last_updated'] = current_time
                
                result = self.collection.replace_one(
                    {'_id': document['_id']},
                    document
                )
                
                if result.modified_count > 0:
                    self.logger.info(f"Updated existing document: {document['_id']}")
                    return True
                else:
                    self.logger.warning(f"No changes made to document: {document['_id']}")
                    return False
            else:
                # Insert new document
                document['metadata']['upload_timestamp'] = current_time
                document['metadata']['last_updated'] = current_time
                
                self.collection.insert_one(document)
                self.logger.info(f"Inserted new document: {document['_id']}")
                return True
                
        except DuplicateKeyError:
            self.logger.error(f"Duplicate key error for document: {document['_id']}")
            return False
        except Exception as e:
            self.logger.error(f"Error upserting document {document['_id']}: {e}")
            return False
            
    def process_modern_adaptations_folder(self, modern_adaptations_folder: str) -> Dict[str, int]:
        """Process all JSON files in the modern adaptations folder."""
        modern_adaptations_path = Path(modern_adaptations_folder)
        
        if not modern_adaptations_path.exists():
            self.logger.error(f"Modern adaptations folder not found: {modern_adaptations_path}")
            raise FileNotFoundError(f"Modern adaptations folder not found: {modern_adaptations_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(modern_adaptations_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {modern_adaptations_path}")
            return stats
            
        self.logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            try:
                stats['processed'] += 1
                
                # Skip template files
                if self._is_template_file(json_file.name):
                    self.logger.info(f"Skipping template file: {json_file.name}")
                    stats['skipped'] += 1
                    continue
                    
                # Load and process the JSON file
                json_data = self._load_json_file(json_file)
                document = self._prepare_document(json_data, json_file.name)
                
                # Check if this is an update or new upload
                existing_doc = self.collection.find_one({'_id': document['_id']})
                
                # Upload/update the document
                if self._upsert_document(document):
                    if existing_doc:
                        stats['updated'] += 1
                    else:
                        stats['uploaded'] += 1
                        
            except Exception as e:
                self.logger.error(f"Error processing file {json_file.name}: {e}")
                stats['errors'] += 1
                continue
                
        return stats
        
    def run(self, modern_adaptations_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting modern adaptation upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the modern adaptations folder
            stats = self.process_modern_adaptations_folder(modern_adaptations_folder)
            
            # Log summary
            self.logger.info("Upload process completed")
            self.logger.info(f"Files processed: {stats['processed']}")
            self.logger.info(f"New uploads: {stats['uploaded']}")
            self.logger.info(f"Updates: {stats['updated']}")
            self.logger.info(f"Skipped (templates): {stats['skipped']}")
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
    modern_adaptations_folder = project_root / 'json_bot_docs' / 'modern_adaptation'
    
    try:
        # Create and run the uploader
        uploader = ModernAdaptationUploader(str(config_path))
        uploader.run(str(modern_adaptations_folder))
        
        print("Modern adaptation upload completed successfully!")
        
    except Exception as e:
        print(f"Error during modern adaptation upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
