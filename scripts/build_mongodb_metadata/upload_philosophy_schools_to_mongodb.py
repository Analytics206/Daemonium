#!/usr/bin/env python3
"""
MongoDB Philosophy Schools Uploader Script

This script uploads the philosophy_school.json file to the MongoDB database 'daemonium' 
collection 'philosophy_schools'. It processes the JSON array and creates individual 
documents for each philosophical school with proper indexing and metadata.

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
            indexes = [
                IndexModel([("schoolID", ASCENDING)], unique=True),
                IndexModel([("school", ASCENDING)], unique=True),
                IndexModel([("category", ASCENDING)]),
                IndexModel([("school", ASCENDING), ("category", ASCENDING)])
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
        
        # Extract keywords from summary and principles for enhanced search
        summary_text = school_data.get('summary', '') + ' ' + school_data.get('corePrinciples', '')
        keywords = []
        
        # Simple keyword extraction (could be enhanced with NLP)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'that', 'this', 'these', 'those'}
        
        words = summary_text.lower().replace(',', ' ').replace('.', ' ').replace(';', ' ').split()
        keywords = [word.strip() for word in words if len(word) > 3 and word not in common_words]
        
        document['keywords'] = list(set(keywords))  # Remove duplicates
        
        return document
        
    def _upsert_school(self, document: Dict[str, Any]) -> bool:
        """Insert new philosophy school or update existing one."""
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
                    self.logger.info(f"Updated existing school: {document['school']}")
                    return True
                else:
                    self.logger.warning(f"No changes made to school: {document['school']}")
                    return False
            else:
                # Insert new document
                document['metadata']['upload_timestamp'] = current_time
                document['metadata']['last_updated'] = current_time
                
                self.collection.insert_one(document)
                self.logger.info(f"Inserted new school: {document['school']}")
                return True
                
        except DuplicateKeyError:
            self.logger.error(f"Duplicate key error for school: {document['school']}")
            return False
        except Exception as e:
            self.logger.error(f"Error upserting school {document['school']}: {e}")
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
