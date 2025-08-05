#!/usr/bin/env python3
"""
MongoDB Philosophy and Themes Uploader Script

This script loops through the json_bot_docs/philosophy_and_themes folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'philosophy_themes'. It skips template files
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


class PhilosophyThemesUploader:
    """Handles uploading philosophy and themes JSON files to MongoDB."""
    
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
                logging.FileHandler('philosophy_themes_upload.log'),
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
            self.collection = self.database['philosophy_themes']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: philosophy_themes")
            
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
            
    def _count_theme_metrics(self, philosophy_themes: Dict[str, Any]) -> Dict[str, int]:
        """Count various metrics from philosophy and themes data."""
        metrics = {
            'total_core_ideas': 0,
            'total_discussion_hooks': 0,
            'core_ideas_with_hooks': 0,
            'total_summary_length': 0,
            'total_aphorisms': 0,
            'total_discussion_templates': 0,
            'has_perspectivism_framework': False,
            'has_aphorisms': False,
            'has_discussion_templates': False
        }
        
        # Count core ideas
        core_ideas = philosophy_themes.get('core_ideas', [])
        if isinstance(core_ideas, list):
            metrics['total_core_ideas'] = len(core_ideas)
            
            for idea in core_ideas:
                if isinstance(idea, dict):
                    # Count discussion hooks
                    hooks = idea.get('discussion_hooks', [])
                    if isinstance(hooks, list):
                        metrics['total_discussion_hooks'] += len(hooks)
                        if len(hooks) > 0:
                            metrics['core_ideas_with_hooks'] += 1
                    
                    # Count summary length
                    summary = idea.get('summary', '')
                    if summary:
                        metrics['total_summary_length'] += len(summary)
        
        # Count aphorisms
        aphorisms = philosophy_themes.get('aphorisms', [])
        if isinstance(aphorisms, list):
            metrics['total_aphorisms'] = len(aphorisms)
            metrics['has_aphorisms'] = len(aphorisms) > 0
        
        # Count discussion templates
        discussion_templates = philosophy_themes.get('discussion_templates', [])
        if isinstance(discussion_templates, list):
            metrics['total_discussion_templates'] = len(discussion_templates)
            metrics['has_discussion_templates'] = len(discussion_templates) > 0
        
        # Check for perspectivism framework
        perspectivism_framework = philosophy_themes.get('perspectivism_framework', {})
        metrics['has_perspectivism_framework'] = bool(perspectivism_framework.get('principle', ''))
        
        return metrics
            
    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion."""
        # Create a unique identifier based on author and category
        author = json_data.get('author', 'unknown').replace(' ', '_').lower()
        category = json_data.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract philosophy and themes data
        philosophy_themes = json_data.get('philosophy_and_themes', {})
        theme_metrics = self._count_theme_metrics(philosophy_themes)
        
        # Extract core ideas with their actual structure
        core_ideas = philosophy_themes.get('core_ideas', [])
        processed_core_ideas = []
        
        for idea in core_ideas:
            if isinstance(idea, dict):
                processed_idea = {
                    'name': idea.get('name', ''),
                    'summary': idea.get('summary', ''),
                    'discussion_hooks': idea.get('discussion_hooks', [])
                }
                processed_core_ideas.append(processed_idea)
        
        # Extract perspectivism framework
        perspectivism_framework = philosophy_themes.get('perspectivism_framework', {})
        
        # Extract aphorisms
        aphorisms = philosophy_themes.get('aphorisms', [])
        
        # Extract discussion templates
        discussion_templates = philosophy_themes.get('discussion_templates', [])
        
        document = {
            '_id': f"{author}_{category}",
            'filename': filename,
            'author': json_data.get('author', 'Unknown'),
            'category': json_data.get('category', 'Unknown'),
            'philosophy_and_themes': {
                'core_ideas': processed_core_ideas,
                'perspectivism_framework': {
                    'principle': perspectivism_framework.get('principle', ''),
                    'implications': perspectivism_framework.get('implications', []),
                    'example_prompts': perspectivism_framework.get('example_prompts', [])
                },
                'aphorisms': aphorisms,
                'discussion_templates': discussion_templates
            },
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'theme_metrics': theme_metrics,
                'core_ideas_count': len(processed_core_ideas),
                'aphorisms_count': len(aphorisms),
                'discussion_templates_count': len(discussion_templates),
                'has_perspectivism_framework': bool(perspectivism_framework.get('principle', '')),
                'has_core_ideas': bool(processed_core_ideas),
                'has_aphorisms': bool(aphorisms),
                'has_discussion_templates': bool(discussion_templates)
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
            
    def process_philosophy_themes_folder(self, philosophy_themes_folder: str) -> Dict[str, int]:
        """Process all JSON files in the philosophy and themes folder."""
        philosophy_themes_path = Path(philosophy_themes_folder)
        
        if not philosophy_themes_path.exists():
            self.logger.error(f"Philosophy and themes folder not found: {philosophy_themes_path}")
            raise FileNotFoundError(f"Philosophy and themes folder not found: {philosophy_themes_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(philosophy_themes_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {philosophy_themes_path}")
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
        
    def run(self, philosophy_themes_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting philosophy and themes upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the philosophy and themes folder
            stats = self.process_philosophy_themes_folder(philosophy_themes_folder)
            
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
    philosophy_themes_folder = project_root / 'json_bot_docs' / 'philosophy_and_themes'
    
    try:
        # Create and run the uploader
        uploader = PhilosophyThemesUploader(str(config_path))
        uploader.run(str(philosophy_themes_folder))
        
        print("Philosophy and themes upload completed successfully!")
        
    except Exception as e:
        print(f"Error during philosophy and themes upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
