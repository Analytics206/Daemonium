#!/usr/bin/env python3
"""
MongoDB Bibliography Uploader Script

This script loops through the json_bot_docs/bibliography folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'bibliography'. It skips template files
and merges existing documents while uploading new ones.

v2.0.0: Enforces the new bibliography JSON format and uses book-level 'keywords'.
        Drops legacy/auxiliary fields (e.g., no 'original_key' persisted). Works
        are sanitized to a strict shape: {title, original_title, year, type, summary, keywords[]}.

Author: Daemonium System
Version: 2.0.0
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


class BibliographyUploader:
    """Handles uploading bibliography JSON files to MongoDB."""
    
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
                logging.FileHandler('bibliography_upload.log'),
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
            self.collection = self.database['bibliography']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: bibliography")
            
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
                return json.load(file)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise
            
    def _normalize_works(self, works: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Normalize works to the strict schema and ensure keywords is a list of strings.

        Allowed keys per work:
        - title: str
        - original_title: str
        - year: int | str
        - type: str
        - summary: str
        - keywords: List[str]
        """
        normalized: List[Dict[str, Any]] = []
        if not isinstance(works, list):
            self.logger.warning(f"'works' is not a list in {filename}; coercing to empty list")
            return normalized

        for idx, w in enumerate(works):
            if not isinstance(w, dict):
                self.logger.warning(f"Work item at index {idx} in {filename} is not an object; skipping")
                continue

            # Extract fields strictly
            title = w.get("title")
            original_title = w.get("original_title")
            year = w.get("year")
            wtype = w.get("type")
            summary = w.get("summary")
            keywords = w.get("keywords", [])

            # Coerce keywords to list[str]
            if keywords is None:
                keywords = []
            if isinstance(keywords, str):
                # Comma-separated string support (just in case)
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            elif isinstance(keywords, list):
                coerced: List[str] = []
                for k in keywords:
                    try:
                        coerced.append(str(k).strip())
                    except Exception:
                        pass
                keywords = [k for k in coerced if k]
            else:
                self.logger.warning(f"keywords for work '{title or idx}' in {filename} is not list/str; defaulting to []")
                keywords = []

            sanitized = {
                "title": title or "",
                "original_title": original_title or "",
                "year": year if year is not None else "",
                "type": wtype or "",
                "summary": summary or "",
                "keywords": keywords,
            }

            normalized.append(sanitized)

        return normalized

    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion."""
        # Find the bibliography data - look for any key ending with '_bibliography'
        bibliography_data = None
        bibliography_key = None
        
        for key in json_data.keys():
            if key.endswith('_bibliography'):
                bibliography_data = json_data[key]
                bibliography_key = key
                break
        
        if bibliography_data is None:
            raise ValueError(f"No bibliography key found (expected key ending with '_bibliography') in {filename}")
            
        # Create document ID from author name
        author = bibliography_data.get('author', '')
        if not author:
            raise ValueError(f"Missing 'author' field in {filename}")
            
        # Create a clean ID from the author name
        document_id = author.lower().replace(' ', '_').replace('-', '_').replace('.', '')
        
        # Validate and process chronological periods structure
        chronological_periods = bibliography_data.get('chronological_periods', {})
        if chronological_periods:
            # Validate that the expected period keys are present
            expected_periods = ['early_period', 'middle_period', 'late_period']
            period_keys = list(chronological_periods.keys())
            
            # Log information about the periods structure
            self.logger.info(f"Processing chronological periods for {author}: {period_keys}")
            
            # Validate each period has the expected structure
            for period_key, period_data in chronological_periods.items():
                if not isinstance(period_data, dict):
                    self.logger.warning(f"Invalid period structure for {period_key} in {filename}")
                    continue
                    
                if 'characteristics' not in period_data or 'themes' not in period_data:
                    self.logger.warning(f"Missing characteristics or themes in {period_key} for {filename}")
        
        # Prepare the final document with all expected fields
        # Enforce new structure and sanitize works (including keywords)
        document = {
            '_id': document_id,
            'filename': filename,
            'author': bibliography_data.get('author', ''),
            'category': bibliography_data.get('category', 'Bibliography'),  # Include category field
            'birth_death': bibliography_data.get('birth_death', ''),
            'description': bibliography_data.get('description', ''),
            'background': bibliography_data.get('background', ''),  # Include background field
            'works': self._normalize_works(bibliography_data.get('works', []), filename),
            'chronological_periods': chronological_periods,  # Use validated periods
            'major_themes': bibliography_data.get('major_themes', []),
            'influence': bibliography_data.get('influence', ''),
            'note': bibliography_data.get('note', '')
        }
        
        return document
        
    def _upsert_document(self, document: Dict[str, Any]) -> bool:
        """Insert new document or update existing one."""
        try:
            # Check if document already exists
            existing_doc = self.collection.find_one({'_id': document['_id']})
            
            if existing_doc:
                # Update existing document
                result = self.collection.replace_one(
                    {'_id': document['_id']},
                    document
                )
                
                if result.modified_count > 0:
                    self.logger.info(f"Updated existing bibliography: {document['_id']}")
                    return True
                else:
                    self.logger.info(f"No changes needed for bibliography: {document['_id']}")
                    return True
            else:
                # Insert new document
                self.collection.insert_one(document)
                self.logger.info(f"Inserted new bibliography: {document['_id']}")
                return True
                
        except DuplicateKeyError:
            # This shouldn't happen with upsert, but handle it gracefully
            self.logger.warning(f"Duplicate key for bibliography {document['_id']}, attempting update")
            try:
                result = self.collection.replace_one(
                    {'_id': document['_id']},
                    document
                )
                if result.modified_count > 0:
                    self.logger.info(f"Updated bibliography after duplicate key: {document['_id']}")
                    return True
            except Exception as update_error:
                self.logger.error(f"Failed to update after duplicate key error: {update_error}")
                return False
        except Exception as e:
            self.logger.error(f"Error upserting document {document['_id']}: {e}")
            return False
            
    def process_bibliography_folder(self, bibliography_folder: str) -> Dict[str, int]:
        """Process all JSON files in the bibliography folder."""
        bibliography_path = Path(bibliography_folder)
        
        if not bibliography_path.exists():
            self.logger.error(f"Bibliography folder not found: {bibliography_path}")
            raise FileNotFoundError(f"Bibliography folder not found: {bibliography_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(bibliography_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {bibliography_path}")
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
        
    def run(self, bibliography_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting bibliography upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the bibliography folder
            stats = self.process_bibliography_folder(bibliography_folder)
            
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
    bibliography_folder = project_root / 'json_bot_docs' / 'bibliography'
    
    try:
        # Create and run the uploader
        uploader = BibliographyUploader(str(config_path))
        uploader.run(str(bibliography_folder))
        
        print("Bibliography upload completed successfully!")
        
    except Exception as e:
        print(f"Error during bibliography upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
