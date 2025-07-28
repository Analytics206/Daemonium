# MongoDB Uploader Scripts

This directory contains scripts for uploading JSON documents from various folders to MongoDB collections in the Daemonium database.

## Available Scripts

### 1. Aphorism Uploader (`upload_aphorisms_to_mongodb.py`)

Uploads JSON files from `json_bot_docs/aphorisms` to the `aphorisms` collection.

**Features:**
- Skips template files (files starting with 'template')
- Merges existing documents and uploads new ones
- Creates unique document IDs based on author and category
- Comprehensive logging with timestamps
- Error handling and connection management

**Usage:**
```bash
python build_metadata/upload_aphorisms_to_mongodb.py
```

**Collection:** `aphorisms`
**Document Structure:**
- `_id`: Unique identifier (author_category)
- `filename`: Source JSON filename
- `author`: Author name
- `category`: Document category
- `aphorisms`: Object containing categorized aphorisms
- `metadata`: Upload timestamps and source information

### 2. Book Summary Uploader (`upload_book_summaries_to_mongodb.py`)

Uploads JSON files from `json_bot_docs/book_summary` to the `book_summary` collection.

**Features:**
- Skips template files (files starting with 'template')
- Merges existing documents and uploads new ones
- Creates unique document IDs based on author, title, and category
- Handles book summary structure with sections
- Comprehensive logging with timestamps
- Error handling and connection management

**Usage:**
```bash
python build_metadata/upload_book_summaries_to_mongodb.py
```

**Collection:** `book_summary`
**Document Structure:**
- `_id`: Unique identifier (author_title_category)
- `filename`: Source JSON filename
- `author`: Author name
- `category`: Document category
- `title`: Book title
- `publication_year`: Year of publication
- `summary`: Array of section objects with content
- `key_themes`: Array of key themes (if present)
- `notable_quotes`: Array of notable quotes (if present)
- `philosophical_significance`: Significance description (if present)
- `metadata`: Upload timestamps, source information, and section count

## Configuration

Both scripts use the configuration from `config/default.yaml`:

```yaml
mongodb:
  host: localhost
  port: 27018
  database: daemonium
  username: admin
  password: ch@ng3m300
```

## Dependencies

Required Python packages (install with `pip install -r requirements.txt`):
- `pymongo>=4.6.0`
- `PyYAML>=6.0.1`

## Logging

Each script creates its own log file:
- `aphorism_upload.log` - For aphorism uploads
- `book_summary_upload.log` - For book summary uploads

Logs include:
- Configuration loading status
- MongoDB connection details
- File processing progress
- Upload/update statistics
- Error messages and warnings

## Error Handling

The scripts handle various error conditions:
- Missing configuration files
- MongoDB connection failures
- Invalid JSON files
- Duplicate key errors
- File system errors

## Template File Handling

Both scripts automatically skip files that start with 'template' (case-insensitive):
- `Template - Aphorisms.json` ✓ Skipped
- `template_example.json` ✓ Skipped
- `Friedrich Wilhelm Nietzsche - Aphorisms.json` ✓ Processed

## Document Merging

When a document with the same `_id` already exists:
1. The existing `upload_timestamp` is preserved
2. The `last_updated` timestamp is set to current time
3. All other fields are updated with new data
4. The operation is logged as an "update"

When a document is new:
1. Both `upload_timestamp` and `last_updated` are set to current time
2. The operation is logged as a "new upload"

## Statistics

After processing, each script reports:
- Files processed: Total number of JSON files found
- New uploads: Documents inserted for the first time
- Updates: Existing documents that were updated
- Skipped (templates): Template files that were ignored
- Errors: Files that failed to process

## Security

- MongoDB credentials are URL-encoded to handle special characters
- Authentication uses the admin database as the auth source
- Connection strings are not logged for security

## Troubleshooting

### Common Issues

1. **Connection Error**: Check MongoDB is running on the configured port
2. **Authentication Error**: Verify username/password in config file
3. **JSON Parse Error**: Check JSON file format and syntax
4. **Permission Error**: Ensure write access to log files and database

### Debug Steps

1. Check MongoDB service status
2. Verify configuration file exists and is readable
3. Test MongoDB connection manually
4. Check log files for detailed error messages
5. Ensure JSON files are valid format

## Development Notes

- Scripts follow PEP8 style guidelines
- Use type hints for better code documentation
- Comprehensive error handling and logging
- Modular design with separate methods for each operation
- Configuration-driven approach for flexibility
