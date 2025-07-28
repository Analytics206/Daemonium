#!/usr/bin/env python3
"""
MongoDB Philosopher Bot Uploader Script

This script loops through the json_bot_docs/philosopher_bot folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'philosopher_bot'. It skips template files
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


class PhilosopherBotUploader:
    """Handles uploading philosopher bot JSON files to MongoDB."""
    
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
                logging.FileHandler('philosopher_bot_upload.log'),
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
            self.collection = self.database['philosopher_bot']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosopher_bot")
            
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
        # Extract persona data
        persona = json_data.get('persona', {})
        
        # Create a unique identifier based on name and category
        name = persona.get('name', 'unknown').replace(' ', '_').lower()
        category = persona.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract style and instructions data
        style = persona.get('style', {})
        instructions = json_data.get('instructions', {})
        
        # Count philosophical themes
        philosophical_themes = persona.get('philosophical_themes', [])
        themes_count = len(philosophical_themes) if isinstance(philosophical_themes, list) else 0
        
        # Count behavior instructions
        behavior = instructions.get('behavior', [])
        behavior_count = len(behavior) if isinstance(behavior, list) else 0
        
        document = {
            '_id': f"{name}_{category}",
            'filename': filename,
            'persona': {
                'name': persona.get('name', 'Unknown'),
                'category': persona.get('category', 'Unknown'),
                'language': persona.get('language', 'English'),
                'style': {
                    'tone': style.get('tone', ''),
                    'speaking_style': style.get('speaking_style', ''),
                    'speed': style.get('speed', ''),
                    'thought_process': style.get('thought_process', ''),
                    'vocabulary': style.get('vocabulary', []),
                    'rhetorical_patterns': style.get('rhetorical_patterns', [])
                },
                'philosophical_themes': philosophical_themes,
                'core_concepts': persona.get('core_concepts', []),
                'personality_traits': persona.get('personality_traits', [])
            },
            'instructions': {
                'primary_goal': instructions.get('primary_goal', ''),
                'behavior': behavior,
                'conversation_guidelines': instructions.get('conversation_guidelines', []),
                'response_patterns': instructions.get('response_patterns', {}),
                'engagement_rules': instructions.get('engagement_rules', []),
                'limitations': instructions.get('limitations', [])
            },
            'configuration': json_data.get('configuration', {}),
            'examples': json_data.get('examples', []),
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'philosophical_themes_count': themes_count,
                'behavior_instructions_count': behavior_count,
                'has_primary_goal': bool(instructions.get('primary_goal', '')),
                'has_style_info': bool(style),
                'examples_count': len(json_data.get('examples', [])) if isinstance(json_data.get('examples'), list) else 0,
                'has_configuration': bool(json_data.get('configuration', {}))
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
            
    def process_philosopher_bots_folder(self, philosopher_bots_folder: str) -> Dict[str, int]:
        """Process all JSON files in the philosopher bots folder."""
        philosopher_bots_path = Path(philosopher_bots_folder)
        
        if not philosopher_bots_path.exists():
            self.logger.error(f"Philosopher bots folder not found: {philosopher_bots_path}")
            raise FileNotFoundError(f"Philosopher bots folder not found: {philosopher_bots_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(philosopher_bots_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {philosopher_bots_path}")
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
        
    def run(self, philosopher_bots_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosopher bot upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the philosopher bots folder
            stats = self.process_philosopher_bots_folder(philosopher_bots_folder)
            
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
    project_root = script_dir.parent
    
    config_path = project_root / 'config' / 'default.yaml'
    philosopher_bots_folder = project_root / 'json_bot_docs' / 'philosopher_bot'
    
    try:
        # Create and run the uploader
        uploader = PhilosopherBotUploader(str(config_path))
        uploader.run(str(philosopher_bots_folder))
        
        print("Philosopher bot upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosopher bot upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
