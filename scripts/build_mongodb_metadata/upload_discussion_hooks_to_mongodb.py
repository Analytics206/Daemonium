#!/usr/bin/env python3
"""
MongoDB Discussion Hook Uploader Script

This script loops through the json_bot_docs/discussion_hook folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'discussion_hook'. It skips template files
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
from pymongo import MongoClient, IndexModel, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from urllib.parse import quote_plus


class DiscussionHookUploader:
    """Handles uploading discussion hook JSON files to MongoDB."""
    
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
                logging.FileHandler('discussion_hook_upload.log'),
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
            self.collection = self.database['discussion_hook']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: discussion_hook")
            
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
        """Create indexes for the discussion_hook collection."""
        try:
            # Drop any existing text indexes to comply with Mongo's single text index rule
            existing_indexes = self.collection.index_information()
            for name, info in existing_indexes.items():
                key_spec = info.get('key', [])
                if any(isinstance(direction, str) and direction.lower() == 'text' for _, direction in key_spec):
                    self.logger.info(f"Dropping existing text index: {name}")
                    self.collection.drop_index(name)

            indexes = [
                IndexModel([("author", ASCENDING)], name="idx_author"),
                IndexModel([("category", ASCENDING)], name="idx_category"),
                IndexModel([("filename", ASCENDING)], name="idx_filename"),
                IndexModel([("themes", ASCENDING)], name="idx_themes"),
                IndexModel([("keywords", ASCENDING)], name="idx_keywords"),
                IndexModel([("discussion_hooks.theme", ASCENDING)], name="idx_discussion_hooks_theme"),
                IndexModel([("discussion_hooks.keywords", ASCENDING)], name="idx_discussion_hooks_keywords"),
                IndexModel([
                    ("discussion_hooks.theme", "text"),
                    ("discussion_hooks.hooks", "text"),
                    ("discussion_hooks.keywords", "text")
                ], name="discussion_hooks_text_v2")
            ]

            self.collection.create_indexes(indexes)
            self.logger.info("Created indexes for discussion_hook collection")
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            raise
            
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
        """Prepare document for MongoDB insertion with support for keywords per theme.

        Backward compatible with legacy dict-based structure where discussion_hooks
        was a mapping of theme -> [hooks].
        """
        # Create a unique identifier based on author and category
        author_slug = json_data.get('author', 'unknown').replace(' ', '_').lower()
        category_slug = json_data.get('category', 'unknown').replace(' ', '_').lower()

        raw_hooks = json_data.get('discussion_hooks', [])

        normalized_hooks: List[Dict[str, Any]] = []
        themes: List[str] = []
        keywords_set_lower = set()
        all_keywords: List[str] = []
        total_hooks = 0

        if isinstance(raw_hooks, dict):
            # Legacy format: { "Theme": ["Q1", "Q2", ...], ... }
            for theme, hooks in raw_hooks.items():
                hooks_list = hooks if isinstance(hooks, list) else []
                normalized_hooks.append({
                    "theme": theme,
                    "keywords": [],
                    "hooks": hooks_list
                })
                if isinstance(theme, str):
                    themes.append(theme)
                total_hooks += len(hooks_list)
        elif isinstance(raw_hooks, list):
            # New format: [ { theme, keywords: [], hooks: [] }, ... ]
            for item in raw_hooks:
                if not isinstance(item, dict):
                    continue
                theme = item.get("theme")
                hooks_list = item.get("hooks", []) or []
                raw_keywords = item.get("keywords", []) or []

                # Normalize keywords: trim, dedupe (case-insensitive) while preserving order
                seen_local = set()
                norm_keywords: List[str] = []
                for kw in raw_keywords:
                    if isinstance(kw, str):
                        k = kw.strip()
                        if k and k.lower() not in seen_local:
                            seen_local.add(k.lower())
                            norm_keywords.append(k)
                            if k.lower() not in keywords_set_lower:
                                keywords_set_lower.add(k.lower())
                                all_keywords.append(k)

                normalized_hooks.append({
                    "theme": theme,
                    "keywords": norm_keywords,
                    "hooks": hooks_list
                })
                if isinstance(theme, str):
                    themes.append(theme)
                total_hooks += len(hooks_list)
        else:
            # Unknown structure; store as-is to avoid data loss
            self.logger.warning("Unrecognized discussion_hooks structure; storing as-is")
            normalized_hooks = raw_hooks  # type: ignore

        document = {
            '_id': f"{author_slug}_{category_slug}",
            'filename': filename,
            'author': json_data.get('author', 'Unknown'),
            'category': json_data.get('category', 'Unknown'),
            'discussion_hooks': normalized_hooks,
            # Aggregates for easier querying/search
            'themes': themes,
            'keywords': all_keywords,
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'total_hooks': total_hooks,
                'hook_categories': themes,           # Back-compat naming
                'categories_count': len(themes),
                'unique_keywords_count': len(all_keywords)
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
            
    def process_discussion_hooks_folder(self, discussion_hooks_folder: str) -> Dict[str, int]:
        """Process all JSON files in the discussion hooks folder."""
        discussion_hooks_path = Path(discussion_hooks_folder)
        
        if not discussion_hooks_path.exists():
            self.logger.error(f"Discussion hooks folder not found: {discussion_hooks_path}")
            raise FileNotFoundError(f"Discussion hooks folder not found: {discussion_hooks_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(discussion_hooks_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {discussion_hooks_path}")
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
        
    def run(self, discussion_hooks_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting discussion hook upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            # Ensure indexes exist
            self._create_indexes()
            
            # Process all files in the discussion hooks folder
            stats = self.process_discussion_hooks_folder(discussion_hooks_folder)
            
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
    discussion_hooks_folder = project_root / 'json_bot_docs' / 'discussion_hook'
    
    try:
        # Create and run the uploader
        uploader = DiscussionHookUploader(str(config_path))
        uploader.run(str(discussion_hooks_folder))
        
        print("Discussion hook upload completed successfully!")
        
    except Exception as e:
        print(f"Error during discussion hook upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
