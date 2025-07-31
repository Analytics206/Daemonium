#!/usr/bin/env python3
"""
MongoDB Philosophers Uploader Script

This script uploads the philosophers.json file to the MongoDB database 'daemonium' 
collection 'philosophers'. It processes the JSON array and creates individual 
documents for each philosopher with proper indexing and metadata.

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


class PhilosopherUploader:
    """Handles uploading philosophers JSON data to MongoDB."""
    
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
                logging.FileHandler('philosopher_upload.log'),
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
            self.collection = self.database['philosophers']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosophers")
            
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
        """Create indexes for the philosophers collection."""
        try:
            indexes = [
                IndexModel([("philosopher", ASCENDING)], unique=True),
                IndexModel([("author", ASCENDING)]),
                IndexModel([("dob", ASCENDING)]),
                IndexModel([("dod", ASCENDING)]),
                IndexModel([("school_id", ASCENDING)]),
                IndexModel([("tag_id", ASCENDING)]),
                IndexModel([("is_active_chat", ASCENDING)]),
                IndexModel([("philosopher", ASCENDING), ("author", ASCENDING)])
            ]
            
            self.collection.create_indexes(indexes)
            self.logger.info("Created indexes for philosophers collection")
            
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            raise
            
    def _load_philosophers_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load and parse the philosophers JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Loaded philosophers file: {file_path.name}")
                
                # Validate that it's a list
                if not isinstance(data, list):
                    raise ValueError("Expected JSON file to contain an array of philosophers")
                    
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON file {file_path.name}: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"Philosophers file not found: {file_path}")
            raise
            
    def _prepare_philosopher_document(self, philosopher_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare philosopher document for MongoDB insertion."""
        # Create a unique identifier based on philosopher name
        philosopher_name = philosopher_data.get('philosopher', 'unknown')
        document_id = philosopher_name.replace(' ', '_').lower()
        
        # Parse dates if they exist
        dob = philosopher_data.get('dob')
        dod = philosopher_data.get('dod')
        
        document = {
            '_id': document_id,
            'philosopher': philosopher_data.get('philosopher', 'Unknown'),
            'author': philosopher_data.get('author', philosopher_data.get('philosopher', 'Unknown')),
            'date_of_birth': dob,
            'date_of_death': dod,
            'summary': philosopher_data.get('summary', ''),
            'content': philosopher_data.get('content', ''),
            'school_id': philosopher_data.get('school_id'),
            'tag_id': philosopher_data.get('tag_id'),
            'is_active_chat': philosopher_data.get('is_active_chat', 0),
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': 'philosophers.json',
                'original_dob': dob,       # Keep original date format
                'original_dod': dod        # Keep original date format
            }
        }
        
        # Add calculated fields
        if dob and dod:
            try:
                # Calculate lifespan if both dates are available
                # Handle BCE dates (negative years)
                birth_year = int(dob.split('-')[0]) if dob.startswith('-') else int(dob.split('-')[0])
                death_year = int(dod.split('-')[0]) if dod.startswith('-') else int(dod.split('-')[0])
                
                # For BCE dates, the calculation is different
                if dob.startswith('-') and dod.startswith('-'):
                    # Both BCE
                    lifespan = abs(birth_year) - abs(death_year)
                elif dob.startswith('-') and not dod.startswith('-'):
                    # Birth BCE, death CE
                    lifespan = abs(birth_year) + death_year
                else:
                    # Both CE
                    lifespan = death_year - birth_year
                    
                document['lifespan_years'] = lifespan
            except (ValueError, IndexError):
                self.logger.warning(f"Could not calculate lifespan for {philosopher_name}")
        
        return document
        
    def _upsert_philosopher(self, document: Dict[str, Any]) -> bool:
        """Insert new philosopher or update existing one."""
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
                    self.logger.info(f"Updated existing philosopher: {document['philosopher']}")
                    return True
                else:
                    self.logger.warning(f"No changes made to philosopher: {document['philosopher']}")
                    return False
            else:
                # Insert new document
                document['metadata']['upload_timestamp'] = current_time
                document['metadata']['last_updated'] = current_time
                
                self.collection.insert_one(document)
                self.logger.info(f"Inserted new philosopher: {document['philosopher']}")
                return True
                
        except DuplicateKeyError:
            self.logger.error(f"Duplicate key error for philosopher: {document['philosopher']}")
            return False
        except Exception as e:
            self.logger.error(f"Error upserting philosopher {document['philosopher']}: {e}")
            return False
            
    def process_philosophers_file(self, philosophers_file: str) -> Dict[str, int]:
        """Process the philosophers JSON file."""
        philosophers_path = Path(philosophers_file)
        
        if not philosophers_path.exists():
            self.logger.error(f"Philosophers file not found: {philosophers_path}")
            raise FileNotFoundError(f"Philosophers file not found: {philosophers_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'errors': 0
        }
        
        # Load the philosophers data
        philosophers_data = self._load_philosophers_file(philosophers_path)
        
        if not philosophers_data:
            self.logger.warning(f"No philosopher data found in {philosophers_path}")
            return stats
            
        self.logger.info(f"Found {len(philosophers_data)} philosophers to process")
        
        # Create indexes
        self._create_indexes()
        
        for philosopher_data in philosophers_data:
            try:
                stats['processed'] += 1
                
                # Validate required fields
                if not philosopher_data.get('philosopher'):
                    self.logger.warning(f"Skipping philosopher with missing name: {philosopher_data}")
                    stats['errors'] += 1
                    continue
                
                # Prepare and upload the document
                document = self._prepare_philosopher_document(philosopher_data)
                
                # Check if this is an update or new upload
                existing_doc = self.collection.find_one({'_id': document['_id']})
                
                # Upload/update the document
                if self._upsert_philosopher(document):
                    if existing_doc:
                        stats['updated'] += 1
                    else:
                        stats['uploaded'] += 1
                        
            except Exception as e:
                self.logger.error(f"Error processing philosopher {philosopher_data.get('philosopher', 'unknown')}: {e}")
                stats['errors'] += 1
                continue
                
        return stats
        
    def run(self, philosophers_file: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosophers upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process the philosophers file
            stats = self.process_philosophers_file(philosophers_file)
            
            # Log summary
            self.logger.info("Upload process completed")
            self.logger.info(f"Philosophers processed: {stats['processed']}")
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
    philosophers_file = project_root / 'json_bot_docs' / 'philosophers' / 'philosophers.json'
    
    try:
        # Create and run the uploader
        uploader = PhilosopherUploader(str(config_path))
        uploader.run(str(philosophers_file))
        
        print("Philosophers upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosophers upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
