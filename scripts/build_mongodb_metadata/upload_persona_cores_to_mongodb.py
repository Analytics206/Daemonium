#!/usr/bin/env python3
"""
MongoDB Persona Core Uploader Script

This script loops through the json_bot_docs/persona_core folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'persona_core'. It skips template files
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


class PersonaCoreUploader:
    """Handles uploading persona core JSON files to MongoDB."""
    
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
                logging.FileHandler('persona_core_upload.log'),
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
            self.collection = self.database['persona_core']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: persona_core")
            
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
        
        # Create a unique identifier based on author and category
        author = persona.get('author', 'unknown').replace(' ', '_').lower()
        category = persona.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract identity and biography data
        identity = persona.get('identity', {})
        biography = persona.get('biography', {})
        voice = persona.get('voice', {})
        
        document = {
            '_id': f"{author}_{category}",
            'filename': filename,
            'persona': {
                'author': persona.get('author', 'Unknown'),
                'category': persona.get('category', 'Unknown'),
                'language': persona.get('language', 'English'),
                'identity': {
                    'full_name': identity.get('full_name', ''),
                    'birth_date': identity.get('birth_date', ''),
                    'death_date': identity.get('death_date', ''),
                    'nationality': identity.get('nationality', ''),
                    'roles': identity.get('roles', [])
                },
                'biography': {
                    'overview': biography.get('overview', ''),
                    'historical_context': biography.get('historical_context', ''),
                    'key_events': biography.get('key_events', []),
                    'personality_traits': biography.get('personality_traits', []),
                    'philosophical_evolution': biography.get('philosophical_evolution', [])
                },
                'voice': {
                    'tone': voice.get('tone', ''),
                    'style': voice.get('style', ''),
                    'speech_patterns': voice.get('speech_patterns', []),
                    'vocabulary_preferences': voice.get('vocabulary_preferences', []),
                    'rhetorical_devices': voice.get('rhetorical_devices', [])
                },
                'interaction_guidelines': persona.get('interaction_guidelines', {}),
                'response_patterns': persona.get('response_patterns', {}),
                'philosophical_stance': persona.get('philosophical_stance', {})
            },
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'roles_count': len(identity.get('roles', [])),
                'key_events_count': len(biography.get('key_events', [])),
                'personality_traits_count': len(biography.get('personality_traits', [])),
                'speech_patterns_count': len(voice.get('speech_patterns', [])),
                'has_birth_date': bool(identity.get('birth_date', '')),
                'has_death_date': bool(identity.get('death_date', ''))
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
            
    def process_persona_cores_folder(self, persona_cores_folder: str) -> Dict[str, int]:
        """Process all JSON files in the persona cores folder."""
        persona_cores_path = Path(persona_cores_folder)
        
        if not persona_cores_path.exists():
            self.logger.error(f"Persona cores folder not found: {persona_cores_path}")
            raise FileNotFoundError(f"Persona cores folder not found: {persona_cores_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(persona_cores_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {persona_cores_path}")
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
        
    def run(self, persona_cores_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting persona core upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the persona cores folder
            stats = self.process_persona_cores_folder(persona_cores_folder)
            
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
    persona_cores_folder = project_root / 'json_bot_docs' / 'persona_core'
    
    try:
        # Create and run the uploader
        uploader = PersonaCoreUploader(str(config_path))
        uploader.run(str(persona_cores_folder))
        
        print("Persona core upload completed successfully!")
        
    except Exception as e:
        print(f"Error during persona core upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
