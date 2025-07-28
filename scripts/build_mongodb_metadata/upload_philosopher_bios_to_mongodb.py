#!/usr/bin/env python3
"""
MongoDB Philosopher Bio Uploader Script

This script loops through the json_bot_docs/philosopher_bio folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'philosopher_bio'. It skips template files
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


class PhilosopherBioUploader:
    """Handles uploading philosopher bio JSON files to MongoDB."""
    
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
                logging.FileHandler('philosopher_bio_upload.log'),
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
            self.collection = self.database['philosopher_bio']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosopher_bio")
            
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
        # Create a unique identifier based on philosopher name and category
        philosopher = json_data.get('philosopher', 'unknown').replace(' ', '_').lower()
        category = json_data.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract sections data
        sections = json_data.get('sections', {})
        
        # Count various elements
        sections_count = len(sections.keys()) if isinstance(sections, dict) else 0
        
        # Count key events across all sections
        total_key_events = 0
        for section_data in sections.values():
            if isinstance(section_data, dict) and 'key_events' in section_data:
                key_events = section_data.get('key_events', [])
                if isinstance(key_events, list):
                    total_key_events += len(key_events)
        
        document = {
            '_id': f"{philosopher}_{category}",
            'filename': filename,
            'philosopher': json_data.get('philosopher', 'Unknown'),
            'category': json_data.get('category', 'Unknown'),
            'birth_year': json_data.get('birth_year', None),
            'death_year': json_data.get('death_year', None),
            'nationality': json_data.get('nationality', 'Unknown'),
            'description': json_data.get('description', ''),
            'sections': sections,
            'major_works': json_data.get('major_works', []),
            'philosophical_schools': json_data.get('philosophical_schools', []),
            'influences': json_data.get('influences', []),
            'influenced': json_data.get('influenced', []),
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'sections_count': sections_count,
                'total_key_events': total_key_events,
                'has_birth_year': json_data.get('birth_year') is not None,
                'has_death_year': json_data.get('death_year') is not None,
                'has_description': bool(json_data.get('description', '')),
                'major_works_count': len(json_data.get('major_works', [])) if isinstance(json_data.get('major_works'), list) else 0,
                'philosophical_schools_count': len(json_data.get('philosophical_schools', [])) if isinstance(json_data.get('philosophical_schools'), list) else 0,
                'influences_count': len(json_data.get('influences', [])) if isinstance(json_data.get('influences'), list) else 0,
                'influenced_count': len(json_data.get('influenced', [])) if isinstance(json_data.get('influenced'), list) else 0
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
            
    def process_philosopher_bios_folder(self, philosopher_bios_folder: str) -> Dict[str, int]:
        """Process all JSON files in the philosopher bios folder."""
        philosopher_bios_path = Path(philosopher_bios_folder)
        
        if not philosopher_bios_path.exists():
            self.logger.error(f"Philosopher bios folder not found: {philosopher_bios_path}")
            raise FileNotFoundError(f"Philosopher bios folder not found: {philosopher_bios_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(philosopher_bios_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {philosopher_bios_path}")
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
        
    def run(self, philosopher_bios_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosopher bio upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the philosopher bios folder
            stats = self.process_philosopher_bios_folder(philosopher_bios_folder)
            
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
    philosopher_bios_folder = project_root / 'json_bot_docs' / 'philosopher_bio'
    
    try:
        # Create and run the uploader
        uploader = PhilosopherBioUploader(str(config_path))
        uploader.run(str(philosopher_bios_folder))
        
        print("Philosopher bio upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosopher bio upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
