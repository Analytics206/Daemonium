#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EPUB to JSON Converter
Converts EPUB books to JSON format for further processing.
"""

import os
import json
import logging
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import argparse
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setupDirectories(rootDir):
    """
    Set up the necessary directories for processing
    """
    # Ensure the books_json directory exists
    booksJsonDir = os.path.join(rootDir, "books_json")
    if not os.path.exists(booksJsonDir):
        logger.info(f"Creating books_json directory at {booksJsonDir}")
        os.makedirs(booksJsonDir)
    return booksJsonDir

def parseChapterContent(chapterContent):
    """
    Parse the HTML content of an EPUB chapter and extract clean text, chunked by sections
    """
    soup = BeautifulSoup(chapterContent, 'html.parser')
    
    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.extract()
    
    sections = []
    
    # Try to identify sections by headers (h1, h2, h3, etc.)
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    if headers:
        # Process content by sections defined by headers
        current_section = {
            'title': 'Introduction',
            'content': ''
        }
        
        # Get all elements in order
        all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'])
        
        for element in all_elements:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save current section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': element.get_text().strip(),
                    'content': ''
                }
            else:
                # Add content to current section
                # Use get_text(separator=' ') to ensure spaces between elements
                text = element.get_text(separator=' ').strip()
                # Clean escaped quotes and HTML entities immediately after extraction
                text = text.replace('\"', '"').replace('&quot;', '"').replace('&#34;', '"')
                text = text.replace("\\", "").replace('&#39;', "'").replace('&apos;', "'")
                if text:
                    current_section['content'] += text + '\n\n'
        
        # Add the last section
        if current_section['content'].strip():
            sections.append(current_section)
    
    else:
        # No headers found, chunk by paragraphs or length
        full_text = soup.get_text()
        
        # Process text to clean it up
        lines = (line.strip() for line in full_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Split into chunks of approximately 2000 characters
        chunk_size = 2000
        words = clean_text.split()
        
        current_chunk = ''
        chunk_num = 1
        
        for word in words:
            if len(current_chunk) + len(word) + 1 > chunk_size and current_chunk:
                sections.append({
                    'title': f'Section {chunk_num}',
                    'content': current_chunk.strip()
                })
                current_chunk = word
                chunk_num += 1
            else:
                current_chunk += ' ' + word if current_chunk else word
        
        # Add the last chunk
        if current_chunk.strip():
            sections.append({
                'title': f'Section {chunk_num}',
                'content': current_chunk.strip()
            })
    
    return sections

def calculatePageCount(chapters):
    """
    Calculate an estimated page count based on content
    """
    # Standard estimate: 250 words per page for a typical book
    WORDS_PER_PAGE = 250
    
    total_words = 0
    for chapter in chapters:
        sections = chapter.get('sections', [])
        for section in sections:
            content = section.get('content', '')
            # Count words - handle both string and list content
            if isinstance(content, str):
                words = len(content.split())
            elif isinstance(content, list):
                # Content is a list of paragraphs, join them and count words
                text = ' '.join(content)
                words = len(text.split())
            else:
                words = 0
            total_words += words
    
    # Calculate page count and round up to nearest whole page
    page_count = max(1, round(total_words / WORDS_PER_PAGE))
    
    return page_count

def epubToJson(epubPath, outputDir):
    """
    Convert an EPUB book to JSON format
    """
    try:
        # Read the EPUB file
        logger.info(f"Processing: {epubPath}")
        book = epub.read_epub(epubPath)
        
        # Extract metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else os.path.basename(epubPath)
        creator = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
        language = book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else "Unknown"
        identifier = book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else "Unknown"
        
        # Create book structure
        bookData = {
            "metadata": {
                "title": title,
                "author": creator,
                "language": language,
                "identifier": identifier,
                "source_file": os.path.basename(epubPath)
            },
            "chapters": []
        }
        
        # Process items (chapters)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Try to extract chapter title from file name or content
                chapterTitle = ""
                try:
                    # Extract potential chapter title from filename
                    filename = os.path.basename(item.get_name())
                    chapterTitle = filename.replace('.xhtml', '').replace('.html', '')
                    
                    # If it's a typical chapter filename (like chapter01.html), try to get a better title
                    if re.match(r'chapter\d+', chapterTitle, re.IGNORECASE):
                        # Try to get title from content
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        h1 = soup.find('h1')
                        h2 = soup.find('h2')
                        if h1:
                            chapterTitle = h1.get_text().strip()
                        elif h2:
                            chapterTitle = h2.get_text().strip()
                except Exception as e:
                    logger.warning(f"Error extracting chapter title: {e}")
                    chapterTitle = f"Chapter {len(bookData['chapters']) + 1}"
                
                # Extract and clean chapter content, chunked by sections
                try:
                    logger.info(f"Processing chapter: {chapterTitle}")
                    sections = parseChapterContent(item.get_content().decode('utf-8'))
                    logger.info(f"Parsed {len(sections)} sections")
                    
                    # Break content sections into paragraphs
                    for i, section in enumerate(sections):
                        logger.info(f"Processing section {i}: {section.get('title', 'No title')}")
                        logger.info(f"Content type: {type(section.get('content', 'No content'))}")
                        
                        if isinstance(section["content"], str):
                            # Split by double newlines to preserve paragraph structure while maintaining word spacing
                            # First, replace single newlines with spaces to preserve word spacing
                            content_with_spaces = section["content"].replace('\n', ' ')
                            
                            # Clean up escaped quotes and other unwanted characters
                            # Handle various quote escape patterns
                            content_with_spaces = content_with_spaces.replace('\"', '"')
                            content_with_spaces = content_with_spaces.replace('\\"', '"')
                            content_with_spaces = content_with_spaces.replace('&quot;', '"')
                            content_with_spaces = content_with_spaces.replace("\\'", "'")
                            content_with_spaces = content_with_spaces.replace('&#39;', "'")
                            
                            # Clean up other common escaped characters
                            content_with_spaces = content_with_spaces.replace('\\n', ' ')
                            content_with_spaces = content_with_spaces.replace('\\t', ' ')
                            
                            # Normalize multiple spaces to single spaces
                            content_with_spaces = re.sub(r'\s+', ' ', content_with_spaces)

                            # Then split by double newlines (paragraph breaks) and filter out empty paragraphs
                            paragraphs = [p.strip() for p in content_with_spaces.split('\n\n') if p.strip()]
                            section["content"] = paragraphs
                            logger.info(f"Split string content into {len(paragraphs)} paragraphs")
                        elif isinstance(section["content"], list):
                            # Content is already a list, ensure each item is stripped
                            section["content"] = [p.strip() for p in section["content"] if p.strip()]
                            logger.info(f"Processed list content with {len(section['content'])} items")
                        else:
                            logger.warning(f"Unexpected content type: {type(section['content'])}")
                            
                except Exception as e:
                    logger.error(f"Error processing chapter {chapterTitle}: {e}")
                    logger.error(f"Error type: {type(e).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
                
                # Add chapter to book
                bookData["chapters"].append({
                    "title": chapterTitle,
                    "sections": sections,
                    "filename": item.get_name()
                })
        
        # Create a safe filename
        safeTitle = re.sub(r'[^\w\-_\.]', '_', title)
        outputFile = os.path.join(outputDir, f"{safeTitle}.json")
        
        # Calculate page count and add to metadata
        page_count = calculatePageCount(bookData["chapters"])
        bookData["metadata"]["page_count"] = page_count
        logger.info(f"Estimated page count: {page_count}")
        
        # Final cleanup: Remove ALL backslashes from the entire book data
        def clean_backslashes(obj):
            if isinstance(obj, str):
                # Remove all backslashes and normalize spaces
                cleaned = obj.replace('\\', '').replace('\"', '"').replace("\\", '').replace("\'", "'")
                cleaned = cleaned.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                return cleaned
            elif isinstance(obj, list):
                return [clean_backslashes(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: clean_backslashes(value) for key, value in obj.items()}
            else:
                return obj
        
        # Apply final cleaning to all book data
        bookData = clean_backslashes(bookData)
        
        # Write to JSON file with custom encoder to prevent re-escaping
        json_str = json.dumps(bookData, ensure_ascii=False, indent=2, separators=(',', ': '))
        with open(outputFile, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"Successfully converted {epubPath} to {outputFile}")
        return outputFile
    except Exception as e:
        logger.error(f"Error converting {epubPath} to JSON: {e}")
        return None

def main():
    """
    Main function to process all EPUB files in the specified directory
    """
    parser = argparse.ArgumentParser(description='Convert EPUB books to JSON')
    parser.add_argument('--input-dir', type=str, default='epub', 
                        help='Directory containing EPUB files (default: epub)')
    parser.add_argument('--single-file', type=str,
                        help='Process only a specific EPUB file')
    args = parser.parse_args()
    
    # Get root directory (one level up from script location)
    rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Set up directories
    booksJsonDir = setupDirectories(rootDir)
    
    # Determine the input directory (relative to root)
    inputDir = os.path.join(rootDir, args.input_dir) if not os.path.isabs(args.input_dir) else args.input_dir
    
    if args.single_file:
        # Process a single file
        filePath = args.single_file if os.path.isabs(args.single_file) else os.path.join(inputDir, args.single_file)
        if os.path.isfile(filePath) and filePath.lower().endswith('.epub'):
            outputFile = epubToJson(filePath, booksJsonDir)
            if outputFile:
                logger.info(f"Conversion completed: {outputFile}")
            else:
                logger.error(f"Failed to convert {filePath}")
        else:
            logger.error(f"Invalid EPUB file: {filePath}")
    else:
        # Process all EPUB files in the directory
        if os.path.isdir(inputDir):
            epubFiles = [f for f in os.listdir(inputDir) if f.lower().endswith('.epub')]
            logger.info(f"Found {len(epubFiles)} EPUB files to process")
            
            for epubFile in epubFiles:
                filePath = os.path.join(inputDir, epubFile)
                outputFile = epubToJson(filePath, booksJsonDir)
                if not outputFile:
                    logger.error(f"Failed to convert {filePath}")
            
            logger.info("Conversion process completed")
        else:
            logger.error(f"Input directory not found: {inputDir}")

if __name__ == "__main__":
    main()
