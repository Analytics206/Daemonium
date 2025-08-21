#!/usr/bin/env python3
"""
MongoDB Aphorism Uploader Script

This script loops through the json_bot_docs/aphorisms folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'aphorisms'. It skips template files
and merges existing documents while uploading new ones.

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
from pymongo import MongoClient
from pymongo import ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from urllib.parse import quote_plus


class AphorismUploader:
    """Handles uploading aphorism JSON files to MongoDB."""
    
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
                logging.FileHandler('aphorism_upload.log'),
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
            self.collection = self.database['aphorisms']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: aphorisms")
            
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
            
    def _slugify(self, value: str) -> str:
        """Create a safe, lowercase slug from a string for use in document IDs."""
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "unknown"

    def _unique(self, items: List[str]) -> List[str]:
        """Return list of unique strings preserving order."""
        seen = set()
        result = []
        for it in items:
            if it not in seen:
                seen.add(it)
                result.append(it)
        return result

    def _ensure_indexes(self) -> None:
        """Create required indexes for efficient querying and text search."""
        try:
            # Regular indexes
            self.collection.create_index([('author', ASCENDING)], name='idx_author')
            self.collection.create_index([('filename', ASCENDING)], name='idx_filename')
            self.collection.create_index([('category', ASCENDING)], name='idx_category')
            # Nested fields inside the subject array
            self.collection.create_index([('subject.theme', ASCENDING)], name='idx_subject_theme')
            self.collection.create_index([('subject.keywords', ASCENDING)], name='idx_subject_keywords')
            self.collection.create_index([('subject.aphorisms', ASCENDING)], name='idx_subject_aphorisms')

            # Drop any existing text index to ensure a single, consistent text index
            try:
                for idx in self.collection.list_indexes():
                    if 'weights' in idx:  # indicative of a text index
                        if idx.get('name') != 'aphorisms_text_index':
                            self.collection.drop_index(idx['name'])
            except Exception as e:
                self.logger.warning(f"Could not inspect/drop existing text indexes: {e}")

            # Text index across relevant fields
            try:
                self.collection.create_index(
                    [
                        ('author', TEXT),
                        ('category', TEXT),
                        ('subject.theme', TEXT),
                        ('subject.keywords', TEXT),
                        ('subject.aphorisms', TEXT)
                    ],
                    name='aphorisms_text_index',
                    default_language='english'
                )
            except Exception as e:
                self.logger.warning(f"Could not create text index on aphorisms collection: {e}")

            self.logger.info("Indexes ensured for aphorisms collection")
        except Exception as e:
            self.logger.warning(f"Index creation failed: {e}")

    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion from nested subject structure."""
        author = json_data.get('author') or 'Unknown'
        category = json_data.get('category') or 'Aphorisms'

        subjects = json_data.get('subject', []) or []
        # Preserve structure: list of subject dicts with theme/keywords/aphorisms
        normalized_subjects: List[Dict[str, Any]] = []
        for subj in subjects:
            if not isinstance(subj, dict):
                continue
            theme = subj.get('theme')
            keywords_list = [kw.strip() for kw in (subj.get('keywords') or []) if isinstance(kw, str) and kw.strip()]
            aph_list = [a.strip() for a in (subj.get('aphorisms') or []) if isinstance(a, str) and a.strip()]
            # Shallow copy to retain any additional fields while normalizing lists
            new_subj = dict(subj)
            if theme is not None:
                new_subj['theme'] = theme
            new_subj['keywords'] = keywords_list
            new_subj['aphorisms'] = aph_list
            # Include subject entries that have at least one meaningful field
            if theme or keywords_list or aph_list:
                normalized_subjects.append(new_subj)

        # Counts derived from nested subject structure
        theme_count = len([s for s in normalized_subjects if s.get('theme')])
        keyword_count = sum(len(s.get('keywords', [])) for s in normalized_subjects)
        aphorism_count = sum(len(s.get('aphorisms', [])) for s in normalized_subjects)

        # Create a stable _id from author and category
        doc_id = f"{self._slugify(author)}_{self._slugify(category)}"

        document: Dict[str, Any] = {
            '_id': doc_id,
            'filename': filename,
            'author': author,
            'category': category,
            # Preserve source JSON structure
            'subject': normalized_subjects,
            'metadata': {
                'upload_timestamp': None,  # Set during upsert
                'last_updated': None,      # Set during upsert
                'source_file': filename,
                'theme_count': theme_count,
                'keyword_count': keyword_count,
                'aphorism_count': aphorism_count
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
            
    def process_aphorisms_folder(self, aphorisms_folder: str) -> Dict[str, int]:
        """Process all JSON files in the aphorisms folder."""
        aphorisms_path = Path(aphorisms_folder)
        
        if not aphorisms_path.exists():
            self.logger.error(f"Aphorisms folder not found: {aphorisms_path}")
            raise FileNotFoundError(f"Aphorisms folder not found: {aphorisms_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(aphorisms_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {aphorisms_path}")
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
        
    def run(self, aphorisms_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting aphorism upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            # Ensure indexes exist before processing
            self._ensure_indexes()
            
            # Process all files in the aphorisms folder
            stats = self.process_aphorisms_folder(aphorisms_folder)
            
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
    aphorisms_folder = project_root / 'json_bot_docs' / 'aphorisms'
    
    try:
        # Create and run the uploader
        uploader = AphorismUploader(str(config_path))
        uploader.run(str(aphorisms_folder))
        
        print("Aphorism upload completed successfully!")
        
    except Exception as e:
        print(f"Error during aphorism upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
