#!/usr/bin/env python3
"""
MongoDB Top 10 Ideas Uploader Script

This script loops through the json_bot_docs/top_10_ideas folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'top_10_ideas'. It skips template files
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


class Top10IdeasUploader:
    """Handles uploading top 10 ideas JSON files to MongoDB."""
    
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
                logging.FileHandler('top_10_ideas_upload.log'),
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
            self.collection = self.database['top_10_ideas']
            
            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: top_10_ideas")
            
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
            
    def _count_ideas_metrics(self, top_ideas: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count various metrics from top ideas data."""
        metrics = {
            'total_ideas': len(top_ideas) if isinstance(top_ideas, list) else 0,
            'ideas_with_descriptions': 0,
            'ideas_with_key_books': 0,
            'total_key_books': 0,
            'total_description_length': 0,
            'ideas_with_quotes': 0,
            'ideas_with_examples': 0,
            'ideas_with_modern_relevance': 0
        }
        
        if isinstance(top_ideas, list):
            for idea in top_ideas:
                if isinstance(idea, dict):
                    # Count descriptions
                    description = idea.get('description', '')
                    if description and description.strip():
                        metrics['ideas_with_descriptions'] += 1
                        metrics['total_description_length'] += len(description)
                    
                    # Count key books
                    key_books = idea.get('key_books', [])
                    if isinstance(key_books, list) and len(key_books) > 0:
                        metrics['ideas_with_key_books'] += 1
                        metrics['total_key_books'] += len(key_books)
                    
                    # Count additional fields
                    if idea.get('quotes'):
                        metrics['ideas_with_quotes'] += 1
                    if idea.get('examples'):
                        metrics['ideas_with_examples'] += 1
                    if idea.get('modern_relevance'):
                        metrics['ideas_with_modern_relevance'] += 1
        
        return metrics
            
    def _prepare_document(self, json_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion."""
        # Create a unique identifier based on author and category
        author = json_data.get('author', 'unknown').replace(' ', '_').lower()
        category = json_data.get('category', 'unknown').replace(' ', '_').lower()
        
        # Extract top ideas data
        top_ideas = json_data.get('top_ideas', [])
        ideas_metrics = self._count_ideas_metrics(top_ideas)
        
        # Process each idea with enhanced structure
        processed_ideas = []
        for i, idea in enumerate(top_ideas):
            if isinstance(idea, dict):
                processed_idea = {
                    'rank': i + 1,
                    'idea': idea.get('idea', ''),
                    'description': idea.get('description', ''),
                    'key_books': idea.get('key_books', []),
                    'related_concepts': idea.get('related_concepts', []),
                    'quotes': idea.get('quotes', []),
                    'examples': idea.get('examples', []),
                    'modern_relevance': idea.get('modern_relevance', ''),
                    'criticism': idea.get('criticism', ''),
                    'further_reading': idea.get('further_reading', []),
                    'cross_references': idea.get('cross_references', [])
                }
                processed_ideas.append(processed_idea)
        
        document = {
            '_id': f"{author}_{category}",
            'filename': filename,
            'author': json_data.get('author', 'Unknown'),
            'category': json_data.get('category', 'Unknown'),
            'top_ideas': processed_ideas,
            'summary': {
                'overview': json_data.get('overview', ''),
                'methodology': json_data.get('methodology', ''),
                'selection_criteria': json_data.get('selection_criteria', ''),
                'historical_context': json_data.get('historical_context', ''),
                'philosophical_significance': json_data.get('philosophical_significance', '')
            },
            'additional_info': {
                'honorable_mentions': json_data.get('honorable_mentions', []),
                'related_philosophers': json_data.get('related_philosophers', []),
                'recommended_reading_order': json_data.get('recommended_reading_order', []),
                'study_guide': json_data.get('study_guide', {}),
                'discussion_questions': json_data.get('discussion_questions', [])
            },
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
                'ideas_metrics': ideas_metrics,
                'has_summary': bool(json_data.get('overview', '') or json_data.get('methodology', '')),
                'has_additional_info': bool(json_data.get('honorable_mentions', []) or json_data.get('related_philosophers', [])),
                'has_study_materials': bool(json_data.get('study_guide', {}) or json_data.get('discussion_questions', [])),
                'has_reading_recommendations': bool(json_data.get('recommended_reading_order', [])),
                'average_books_per_idea': round(ideas_metrics['total_key_books'] / max(ideas_metrics['total_ideas'], 1), 2)
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
            
    def process_top_10_ideas_folder(self, top_10_ideas_folder: str) -> Dict[str, int]:
        """Process all JSON files in the top 10 ideas folder."""
        top_10_ideas_path = Path(top_10_ideas_folder)
        
        if not top_10_ideas_path.exists():
            self.logger.error(f"Top 10 ideas folder not found: {top_10_ideas_path}")
            raise FileNotFoundError(f"Top 10 ideas folder not found: {top_10_ideas_path}")
            
        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all JSON files in the folder
        json_files = list(top_10_ideas_path.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {top_10_ideas_path}")
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
        
    def run(self, top_10_ideas_folder: str) -> None:
        """Main execution method."""
        try:
            self.logger.info("Starting top 10 ideas upload process")
            
            # Connect to MongoDB
            self.connect_to_mongodb()
            
            # Process all files in the top 10 ideas folder
            stats = self.process_top_10_ideas_folder(top_10_ideas_folder)
            
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
    top_10_ideas_folder = project_root / 'json_bot_docs' / 'top_10_ideas'
    
    try:
        # Create and run the uploader
        uploader = Top10IdeasUploader(str(config_path))
        uploader.run(str(top_10_ideas_folder))
        
        print("Top 10 ideas upload completed successfully!")
        
    except Exception as e:
        print(f"Error during top 10 ideas upload: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit(main())
