#!/usr/bin/env python3
"""
MongoDB Philosophy Schools Uploader Script

This script uploads the philosophy_school.json file to the MongoDB database 'daemonium' 
collection 'philosophy_schools'. It processes the JSON array and creates individual 
documents for each philosophical school with proper indexing and metadata.

Author: Daemonium System
Version: 2.0.0
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


class PhilosophySchoolUploader:
    """Handles uploading philosophy schools JSON data to MongoDB."""
    
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
                logging.FileHandler('philosophy_school_upload.log'),
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
            self.collection = self.database['philosophy_schools']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosophy_schools")
            
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
            
    def _create_indexes(self) -> None:
        """Create indexes for the philosophy_schools collection."""
        try:
            # Drop any existing text indexes to comply with MongoDB's single text index rule
            existing_indexes = self.collection.index_information()
            for name, info in existing_indexes.items():
                key_spec = info.get('key', [])
                if any(isinstance(direction, str) and direction.lower() == 'text' for _, direction in key_spec):
                    self.logger.info(f"Dropping existing text index: {name}")
                    self.collection.drop_index(name)

            indexes = [
                IndexModel([("school_id", ASCENDING)], name="idx_school_id_unique", unique=True),
                IndexModel([("school", ASCENDING)], name="idx_school"),
                IndexModel([("category", ASCENDING)], name="idx_category"),
                IndexModel([("school", ASCENDING), ("category", ASCENDING)], name="idx_school_category"),
                IndexModel([("keywords", ASCENDING)], name="idx_keywords"),
                IndexModel([( "school", "text" ), ( "summary", "text" ), ( "core_principles", "text" ), ( "keywords", "text" )], name="philosophy_schools_text_v2"),
            ]

            self.collection.create_indexes(indexes)
            self.logger.info("Created indexes for philosophy_schools collection")
            
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            raise
            
    def _load_philosophy_schools_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load and parse the philosophy schools JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Loaded philosophy schools file: {file_path.name}")
                
                # Validate that it's a list
                if not isinstance(data, list):
                    raise ValueError("Expected JSON file to contain an array of philosophy schools")
                    
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON file {file_path.name}: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"Philosophy schools file not found: {file_path}")
            raise
            
    def _prepare_school_document(self, school_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare philosophy school document for MongoDB insertion."""
        # Use schoolID as the primary identifier
        school_id = school_data.get('schoolID')
        school_name = school_data.get('school', 'Unknown')
        
        # Validate that schoolID is not None or empty
        if school_id is None or school_id == '':
            raise ValueError(f"School '{school_name}' has invalid or missing schoolID: {school_id}")
        
        # Create a unique identifier based on schoolID
        document_id = f"school_{school_id}"
        
        document = {
            '_id': document_id,
            'school_id': school_id,
            'school': school_name,
            'category': school_data.get('category', 'Unknown'),
            'summary': school_data.get('summary', ''),
            'core_principles': school_data.get('corePrinciples', ''),
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': 'philosophy_school.json'
            }
        }
        
        # Add derived fields for better searchability
        document['school_normalized'] = school_name.lower().replace(' ', '_')
        document['category_normalized'] = school_data.get('category', 'Unknown').lower().replace(' ', '_').replace('&', 'and')
        
        # Use provided keywords from JSON (v2 format). Do NOT derive legacy keywords.
        raw_keywords = school_data.get('keywords', []) or []
        if not isinstance(raw_keywords, list):
            raw_keywords = []
        seen = set()
        normalized_keywords: List[str] = []
        for kw in raw_keywords:
            if isinstance(kw, str):
                k = kw.strip()
                if k and k.lower() not in seen:
                    seen.add(k.lower())
                    normalized_keywords.append(k)
        document['keywords'] = normalized_keywords
        
        return document
        
    def _upsert_school(self, document: Dict[str, Any]) -> bool:
        """Insert new philosophy school or update existing one."""
        try:
            # Set timestamps
            current_time = datetime.utcnow()
            
            # First try to find by _id which is our primary key
            document_id = document.get('_id')
            existing_doc = self.collection.find_one({'_id': document_id}) if document_id else None
            
            if existing_doc:
                # Update existing document
                update_data = {
                    'school': document['school'],
                    'category': document['category'],
                    'summary': document['summary'],
                    'core_principles': document['core_principles'],
                    'school_normalized': document.get('school_normalized', ''),
                    'category_normalized': document.get('category_normalized', ''),
                    'keywords': document.get('keywords', []),
                    'metadata': {
                        'upload_timestamp': existing_doc['metadata'].get('upload_timestamp', current_time),
                        'last_updated': current_time,
                        'source_file': document['metadata']['source_file']
                    }
                }
                
                # Use update_one with upsert=False to prevent creating new documents
                result = self.collection.update_one(
                    {'_id': document_id},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0 or result.matched_count > 0:
                    self.logger.info(f"Updated existing school: {document.get('school', 'Unknown')} (ID: {document['school_id']})")
                    return True
                else:
                    self.logger.warning(f"No changes made to school: {document.get('school', 'Unknown')} (ID: {document['school_id']})")
                    return True  # Still return True as this isn't an error
            else:
                # For new document, first check if a document with the same school_id exists
                existing_by_id = self.collection.find_one({'school_id': document['school_id']})
                if existing_by_id:
                    # If a document with the same school_id exists, update it
                    self.logger.warning(f"School with ID {document['school_id']} already exists, updating it.")
                    
                    update_data = {
                        'school': document['school'],
                        'category': document['category'],
                        'summary': document['summary'],
                        'core_principles': document['core_principles'],
                        'school_normalized': document.get('school_normalized', ''),
                        'category_normalized': document.get('category_normalized', ''),
                        'keywords': document.get('keywords', []),
                        'metadata': {
                            'upload_timestamp': existing_by_id['metadata'].get('upload_timestamp', current_time),
                            'last_updated': current_time,
                            'source_file': document['metadata']['source_file']
                        }
                    }
                    
                    result = self.collection.update_one(
                        {'_id': existing_by_id['_id']},
                        {'$set': update_data}
                    )
                    
                    if result.modified_count > 0 or result.matched_count > 0:
                        self.logger.info(f"Updated existing school by ID: {document.get('school', 'Unknown')} (ID: {document['school_id']})")
                        return True
                    else:
                        self.logger.warning(f"No changes made to school by ID: {document.get('school', 'Unknown')}")
                        return True
                
                # If no existing document found, insert new one
                document['metadata']['upload_timestamp'] = current_time
                document['metadata']['last_updated'] = current_time
                
                # Ensure we have all required fields
                if '_id' not in document:
                    document['_id'] = f"school_{document['school_id']}"
                
                try:
                    self.collection.insert_one(document)
                    self.logger.info(f"Inserted new school: {document.get('school', 'Unknown')} (ID: {document['school_id']})")
                    return True
                except DuplicateKeyError as e:
                    # If we get a duplicate key error, try to find the existing document by _id
                    existing = self.collection.find_one({'_id': document['_id']})
                    if existing:
                        self.logger.warning(f"Document with _id {document['_id']} already exists, updating instead")
                        return self._upsert_school(document)  # Recursively try to update
                    
                    # If we get here, it's an unexpected duplicate key error
                    self.logger.error(f"Unexpected duplicate key error for school: {document.get('school', 'Unknown')}. Error: {str(e)}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error upserting school {document.get('school', 'Unknown')}: {e}")
            return False
            
    def process_philosophy_schools_file(self, schools_file: str) -> Dict[str, int]:
        """Process the philosophy schools JSON file."""
        schools_path = Path(schools_file)
        
        if not schools_path.exists():
            self.logger.error(f"Philosophy schools file not found: {schools_path}")
            raise FileNotFoundError(f"Philosophy schools file not found: {schools_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'errors': 0
        }
        
        # Load the schools data
        schools_data = self._load_philosophy_schools_file(schools_path)
        
        if not schools_data:
            self.logger.warning(f"No philosophy school data found in {schools_path}")
            return stats
            
        self.logger.info(f"Found {len(schools_data)} philosophy schools to process")
        
        # Debug: Show first 3 schools
        self.logger.info("DEBUG: First 3 schools:")
        for i, school in enumerate(schools_data[:3]):
            self.logger.info(f"  School {i+1}: ID={school.get('schoolID')}, Name={school.get('school')}")
        
        # Create indexes
        self._create_indexes()
        
        for school_data in schools_data:
            try:
                stats['processed'] += 1
                
                # Validate required fields
                if not school_data.get('schoolID'):
                    self.logger.warning(f"Skipping school with missing schoolID: {school_data}")
                    stats['errors'] += 1
                    continue
                    
                if not school_data.get('school'):
                    self.logger.warning(f"Skipping school with missing school: {school_data}")
                    stats['errors'] += 1
                    continue
                
                # Prepare and upload the document
                document = self._prepare_school_document(school_data)
                
                # Check if this is an update or new upload
                existing_doc = self.collection.find_one({'_id': document['_id']})
                
                # Upload/update the document
                if self._upsert_school(document):
                    if existing_doc:
                        stats['updated'] += 1
                    else:
                        stats['uploaded'] += 1
                        
            except Exception as e:
                self.logger.error(f"Error processing school {school_data.get('school', 'unknown')}: {e}")
                stats['errors'] += 1
                continue
                
        return stats
        
    def run(self, schools_file: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosophy schools upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process the schools file
            stats = self.process_philosophy_schools_file(schools_file)
            
            # Log summary
            self.logger.info("Upload process completed")
            self.logger.info(f"Schools processed: {stats['processed']}")
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
    schools_file = project_root / 'json_bot_docs' / 'philosophy_school' / 'philosophy_school.json'
    
    # Debug: Print the actual file path being used
    print(f"DEBUG: Using schools file: {schools_file}")
    print(f"DEBUG: File exists: {schools_file.exists()}")
    
    try:
        # Create and run the uploader
        uploader = PhilosophySchoolUploader(str(config_path))
        uploader.run(str(schools_file))
        
        print("Philosophy schools upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosophy schools upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
