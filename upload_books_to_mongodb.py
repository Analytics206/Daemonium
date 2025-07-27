#!/usr/bin/env python3
"""
MongoDB Books Collection Uploader

This script processes JSON files from the books_json directory and uploads them 
to a MongoDB 'books' collection with merge functionality.

Author: Daemonium Project
Date: 2025-07-26
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import yaml
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('books_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BooksUploader:
    """Handles uploading book JSON files to MongoDB with merge functionality."""
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """Initialize the uploader with configuration."""
        self.config = self._load_config(config_path)
        self.client = None
        self.db = None
        self.collection = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        default_config = {
            'mongodb': {
                'host': 'localhost',
                'port': 27017,
                'database': 'daemonium',
                'username': None,
                'password': None
            }
        }
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                if config is None or not isinstance(config, dict):
                    logger.warning(f"Config file {config_path} is empty or invalid. Using default MongoDB settings.")
                    return default_config
                return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using default MongoDB settings.")
            return default_config
        except Exception as e:
            logger.warning(f"Error loading config file {config_path}: {e}. Using default MongoDB settings.")
            return default_config
    
    def _repair_json_content(self, content: str) -> str:
        """Attempt to repair malformed JSON content."""
        # Note: This method is primarily for legacy support of old JSON formats
        # The new EPUB converter should produce valid JSON with content as arrays
        
        # Fix unquoted content after "content": (for old string-based content)
        pattern = r'"content":\s*([^"\{\[].*?)(?="[^:]*":|"}"|"\]|$)'
        
        def quote_content(match):
            content_text = match.group(1).strip()
            # Remove trailing comma or bracket if present
            content_text = re.sub(r'[,\}\]]+$', '', content_text)
            # Escape quotes within the content
            content_text = content_text.replace('"', '\\"')
            return f'"content": "{content_text}"'
        
        repaired = re.sub(pattern, quote_content, content, flags=re.DOTALL)
        return repaired
    
    def connect_to_mongodb(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            mongo_config = self.config.get('mongodb', {})
            host = mongo_config.get('host', 'localhost')
            port = mongo_config.get('port', 27018)
            database = mongo_config.get('database', 'daemonium')
            username = mongo_config.get('username')
            password = mongo_config.get('password')
            
            # Build connection string
            if username and password:
                # URL-encode username and password to handle special characters
                encoded_username = quote_plus(username)
                encoded_password = quote_plus(password)
                # For root users, authenticate against admin database
                connection_string = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{database}?authSource=admin"
            else:
                connection_string = f"mongodb://{host}:{port}/"
            
            logger.info(f"Connecting to MongoDB at {host}:{port}")
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[database]
            self.collection = self.db['books']
            
            logger.info(f"Successfully connected to MongoDB database: {database}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    def _validate_book_data(self, book_data: Dict[str, Any]) -> bool:
        """Validate book data structure for both old and new formats."""
        required_fields = ['metadata']
        
        for field in required_fields:
            if field not in book_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        metadata = book_data.get('metadata', {})
        if not isinstance(metadata, dict):
            logger.warning("Metadata field must be a dictionary")
            return False
        
        # Check for essential metadata fields
        essential_fields = ['title', 'author']
        for field in essential_fields:
            if field not in metadata:
                logger.warning(f"Missing essential metadata field: {field}")
                return False
        
        # Validate chapter structure (support both old and new formats)
        chapters = book_data.get('chapters', [])
        if chapters and isinstance(chapters, list):
            for i, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    logger.warning(f"Chapter {i} is not a dictionary")
                    return False
                
                # Check if it's the new sectioned format or old content format
                has_sections = 'sections' in chapter
                has_content = 'content' in chapter
                
                if not has_sections and not has_content:
                    logger.warning(f"Chapter {i} has neither 'sections' nor 'content' field")
                    return False
                
                # Validate sections if present
                if has_sections:
                    sections = chapter.get('sections', [])
                    if not isinstance(sections, list):
                        logger.warning(f"Chapter {i} sections must be a list")
                        return False
                    
                    for j, section in enumerate(sections):
                        if not isinstance(section, dict):
                            logger.warning(f"Chapter {i}, section {j} is not a dictionary")
                            return False
                        if 'title' not in section or 'content' not in section:
                            logger.warning(f"Chapter {i}, section {j} missing title or content")
                            return False
                        
                        # Validate content type - support both string (old format) and list (new format)
                        content = section.get('content')
                        if not isinstance(content, (str, list)):
                            logger.warning(f"Chapter {i}, section {j} content must be string or list")
                            return False
                        
                        # If content is a list, validate that all items are strings
                        if isinstance(content, list):
                            for k, paragraph in enumerate(content):
                                if not isinstance(paragraph, str):
                                    logger.warning(f"Chapter {i}, section {j}, paragraph {k} must be a string")
                                    return False
        
        return True
    
    def _create_book_id(self, book_data: Dict[str, Any]) -> str:
        """Create a unique identifier for the book."""
        metadata = book_data.get('metadata', {})
        title = metadata.get('title', '').strip()
        author = metadata.get('author', '').strip()
        
        # Create a simple ID based on title and author
        book_id = f"{author} - {title}".replace(' ', '_').replace('/', '_')
        return book_id
    
    def upload_book(self, book_data: Dict[str, Any], filename: str) -> bool:
        """Upload a single book to MongoDB with merge functionality."""
        try:
            if not self._validate_book_data(book_data):
                logger.error(f"Invalid book data in file: {filename}")
                return False
            
            # Create unique identifier
            book_id = self._create_book_id(book_data)
            book_data['_id'] = book_id
            book_data['source_file'] = filename
            from datetime import datetime
            book_data['upload_timestamp'] = datetime.utcnow().isoformat()
            
            # Try to find existing book
            existing_book = self.collection.find_one({'_id': book_id})
            
            if existing_book:
                logger.info(f"Book already exists: {book_id}. Performing merge update.")
                
                # Merge strategy: update metadata and chapters
                update_data = {
                    '$set': {
                        'metadata': book_data['metadata'],
                        'source_file': filename,
                        'upload_timestamp': book_data['upload_timestamp']
                    }
                }
                
                # If new chapters exist, update them
                if 'chapters' in book_data:
                    update_data['$set']['chapters'] = book_data['chapters']
                
                result = self.collection.update_one(
                    {'_id': book_id},
                    update_data
                )
                
                if result.modified_count > 0:
                    logger.info(f"Successfully updated book: {book_id}")
                    return True
                else:
                    logger.info(f"No changes needed for book: {book_id}")
                    return True
            else:
                # Insert new book
                result = self.collection.insert_one(book_data)
                logger.info(f"Successfully inserted new book: {book_id}")
                return True
                
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error for book: {filename}")
            return False
        except Exception as e:
            logger.error(f"Error uploading book {filename}: {e}")
            return False
    
    def process_books_directory(self, books_dir: str = "books_json") -> Dict[str, int]:
        """Process all JSON files in the books directory."""
        books_path = Path(books_dir)
        
        if not books_path.exists():
            logger.error(f"Books directory not found: {books_dir}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        stats = {'processed': 0, 'successful': 0, 'failed': 0}
        
        # Find all JSON files
        json_files = list(books_path.glob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in directory: {books_dir}")
            return stats
        
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            stats['processed'] += 1
            logger.info(f"Processing file: {json_file.name}")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Try to parse JSON directly first
                try:
                    book_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Malformed JSON in {json_file.name}, attempting repair: {e}")
                    # Attempt to repair the JSON
                    repaired_content = self._repair_json_content(content)
                    try:
                        book_data = json.loads(repaired_content)
                        logger.info(f"Successfully repaired JSON in {json_file.name}")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Could not repair JSON in {json_file.name}: {e2}")
                        stats['failed'] += 1
                        continue
                
                if self.upload_book(book_data, json_file.name):
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {json_file.name}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def create_indexes(self):
        """Create useful indexes for the books collection."""
        try:
            # Create indexes for common query patterns
            self.collection.create_index("metadata.title")
            self.collection.create_index("metadata.author")
            self.collection.create_index("metadata.language")
            self.collection.create_index("upload_timestamp")
            
            logger.info("Successfully created indexes for books collection")
        except Exception as e:
            logger.warning(f"Could not create indexes (may require authentication): {e}")
            logger.info("Continuing without creating indexes...")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the books collection."""
        try:
            total_books = self.collection.count_documents({})
            
            # Get some sample metadata
            pipeline = [
                {"$group": {
                    "_id": "$metadata.language",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            languages = list(self.collection.aggregate(pipeline))
            
            return {
                'total_books': total_books,
                'languages': languages
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def close_connection(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def main():
    """Main function to run the books uploader."""
    logger.info("Starting MongoDB Books Uploader")
    
    uploader = BooksUploader()
    
    try:
        # Connect to MongoDB
        if not uploader.connect_to_mongodb():
            logger.error("Failed to connect to MongoDB. Exiting.")
            return
        
        # Create indexes
        uploader.create_indexes()
        
        # Process books directory
        stats = uploader.process_books_directory()
        
        # Print results
        logger.info("=" * 50)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Files processed: {stats['processed']}")
        logger.info(f"Successful uploads: {stats['successful']}")
        logger.info(f"Failed uploads: {stats['failed']}")
        
        # Get collection statistics
        collection_stats = uploader.get_collection_stats()
        if collection_stats:
            logger.info(f"Total books in collection: {collection_stats['total_books']}")
            
            if collection_stats.get('languages'):
                logger.info("Books by language:")
                for lang_stat in collection_stats['languages'][:5]:  # Top 5 languages
                    language = lang_stat['_id'] or 'Unknown'
                    count = lang_stat['count']
                    logger.info(f"  {language}: {count} books")
        
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("Upload process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        uploader.close_connection()


if __name__ == "__main__":
    main()
