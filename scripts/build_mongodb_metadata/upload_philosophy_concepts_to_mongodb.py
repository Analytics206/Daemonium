#!/usr/bin/env python3
"""
MongoDB Philosophy Concepts Uploader Script

This script loops through the json_bot_docs/philosophy_concepts folder and uploads JSON files
to the MongoDB database 'daemonium' collection 'philosophy_concepts'. It skips template files
and merges existing documents while uploading new ones.

Author: Daemonium System
Version: 1.0.0
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import yaml


class PhilosophyConceptsUploader:
    """Handles uploading philosophy concept JSON files to MongoDB."""

    def __init__(self, config_path: str):
        """Initialize the uploader with configuration."""
        self.config_path = Path(config_path)
        self.client = None
        self.database = None
        self.collection = None
        self.collection_name = 'philosophy_concepts'
        self._setup_logging()
        self.config = self._load_config()

    def _setup_logging(self) -> None:
        """Configure logging for the uploader."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('philosophy_concepts_upload.log'),
                logging.StreamHandler(),
            ],
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
                encoded_username = quote_plus(username)
                encoded_password = quote_plus(password)
                # For root users, authenticate against admin database
                connection_string = (
                    f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{database}?authSource=admin"
                )
            else:
                connection_string = f"mongodb://{host}:{port}/{database}"

            self.client = MongoClient(connection_string)
            # Test the connection
            self.client.admin.command('ping')

            self.database = self.client[database]
            self.collection = self.database[self.collection_name]

            self.logger.info(f"Connected to MongoDB: {host}:{port}")
            self.logger.info(f"Using database: {database}, collection: {self.collection_name}")

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
        # Accept both capitalized and lowercase keys from the template
        # Authors: support array or string while maintaining backward compatibility
        authors_raw = (
            json_data.get('authors')
            or json_data.get('Authors')
            or json_data.get('author')
            or json_data.get('Author')
            or 'Unknown'
        )
        if isinstance(authors_raw, list):
            authors = [str(a).strip() for a in authors_raw if str(a).strip()]
        elif isinstance(authors_raw, str):
            authors = [authors_raw.strip()] if authors_raw.strip() else ['Unknown']
        else:
            authors = ['Unknown']

        author_primary = authors[0] if authors else 'Unknown'

        concept = (json_data.get('concept') or json_data.get('Concept') or 'Unknown').strip()
        category = (json_data.get('category') or json_data.get('Category') or 'Philosophy Concepts').strip()
        antagonist = (json_data.get('antagonist') or json_data.get('Antagonist') or '').strip()

        raw_keywords = json_data.get('keywords') or json_data.get('Keywords') or []
        if isinstance(raw_keywords, str):
            keywords = [k.strip() for k in raw_keywords.split(',') if k.strip()]
        elif isinstance(raw_keywords, list):
            keywords = [str(k).strip() for k in raw_keywords]
        else:
            keywords = []

        content = (json_data.get('content') or json_data.get('Content') or '').strip()

        # Create a unique identifier based on primary author and concept
        doc_id = f"{author_primary}_{concept}".replace(' ', '_').lower()

        document = {
            '_id': doc_id,
            'filename': filename,
            # Normalized keys for project-wide joins
            'author': author_primary,
            'authors': authors,
            'concept': concept,
            'category': category,
            'antagonist': antagonist,
            'keywords': keywords,
            'content': content,
            'metadata': {
                'upload_timestamp': None,  # Will be set during upload
                'last_updated': None,      # Will be set during upload
                'source_file': filename,
            },
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
                document['metadata']['upload_timestamp'] = existing_doc['metadata'].get(
                    'upload_timestamp', current_time
                )
                document['metadata']['last_updated'] = current_time

                result = self.collection.replace_one({'_id': document['_id']}, document)

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

    def process_concepts_folder(self, concepts_folder: str, dry_run: bool = False) -> Dict[str, int]:
        """Process all JSON files in the philosophy concepts folder.

        When dry_run is True, validates and prepares documents without any DB calls.
        """
        concepts_path = Path(concepts_folder)

        if not concepts_path.exists():
            self.logger.error(f"Concepts folder not found: {concepts_path}")
            raise FileNotFoundError(f"Concepts folder not found: {concepts_path}")

        stats = {
            'processed': 0,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'validated': 0,
            'duplicates_in_batch': 0,
        }

        # Get all JSON files in the folder
        json_files = list(concepts_path.glob('*.json'))

        if not json_files:
            self.logger.warning(f"No JSON files found in {concepts_path}")
            return stats

        self.logger.info(f"Found {len(json_files)} JSON files to process")

        # Track in-batch duplicates by _id during dry-run
        seen_ids = set()

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

                if dry_run:
                    # Validate document structure and track duplicates within the batch
                    doc_id = document.get('_id')
                    if doc_id in seen_ids:
                        self.logger.warning(f"Duplicate _id in batch (dry-run): {doc_id} from file {json_file.name}")
                        stats['duplicates_in_batch'] += 1
                    else:
                        seen_ids.add(doc_id)
                    stats['validated'] += 1
                    continue

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

    def run(self, concepts_folder: str, dry_run: bool = False) -> None:
        """Main execution method."""
        try:
            if dry_run:
                self.logger.info("Starting philosophy concepts validation (dry-run) — no DB changes will be made")
            else:
                self.logger.info("Starting philosophy concepts upload process")

            # Connect to MongoDB only if not dry-run
            if not dry_run:
                self.connect_to_mongodb()

            # Process all files in the concepts folder
            stats = self.process_concepts_folder(concepts_folder, dry_run=dry_run)

            # Log summary
            if dry_run:
                self.logger.info("Validation (dry-run) completed")
                self.logger.info(f"Files processed: {stats['processed']}")
                self.logger.info(f"Validated: {stats['validated']}")
                self.logger.info(f"Duplicates in batch: {stats['duplicates_in_batch']}")
                self.logger.info(f"Skipped (templates): {stats['skipped']}")
                self.logger.info(f"Errors: {stats['errors']}")
            else:
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
            # Always disconnect from MongoDB if connected
            if self.client:
                self.disconnect_from_mongodb()


def main():
    """Main entry point for the script."""
    # Define paths relative to the script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    default_config = project_root / 'config' / 'default.yaml'
    default_concepts_folder = project_root / 'json_bot_docs' / 'philosophy_concepts'

    parser = argparse.ArgumentParser(description="Upload or validate philosophy concept JSON files to MongoDB.")
    parser.add_argument('--config', type=str, default=str(default_config), help='Path to YAML config (default: config/default.yaml)')
    parser.add_argument('--concepts-folder', type=str, default=str(default_concepts_folder), help='Folder containing philosophy concept JSON files')
    parser.add_argument('--dry-run', action='store_true', help='Validate JSON files without connecting to MongoDB')

    args = parser.parse_args()

    try:
        # Create and run the uploader
        uploader = PhilosophyConceptsUploader(str(args.config))
        uploader.run(str(args.concepts_folder), dry_run=bool(args.dry_run))

        if args.dry_run:
            print("Philosophy concepts validation (dry-run) completed successfully!")
        else:
            print("Philosophy concepts upload completed successfully!")

    except Exception as e:
        action = 'validation' if args.dry_run else 'upload'
        print(f"Error during philosophy concepts {action}: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
