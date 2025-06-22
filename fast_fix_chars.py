#!/usr/bin/env python3
"""
Optimized script to convert special characters to HTML entities in large HTML files.
"""
import os
import shutil
import re
from tqdm import tqdm

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.bak"
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"Created backup at: {backup_path}")
    return backup_path

def get_file_size(file_path):
    """Get file size in a human-readable format"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def process_file(input_path, output_path=None, chunk_size=1024*1024):
    """Process the file in chunks to replace special characters"""
    if output_path is None:
        output_path = input_path + ".tmp"
    
    # Common special characters and their HTML entities
    char_map = {
        '—': '&mdash;', '–': '&ndash;', '“': '&ldquo;', '”': '&rdquo;',
        '‘': '&lsquo;', '’': '&rsquo;', '…': '&hellip;', '«': '&laquo;',
        '»': '&raquo;', '‹': '&lsaquo;', '›': '&rsaquo;', '„': '&bdquo;',
        '•': '&bull;', '·': '&middot;', '©': '&copy;', '®': '&reg;',
        '™': '&trade;', '€': '&euro;', '£': '&pound;', '¥': '&yen;',
        '¢': '&cent;', '§': '&sect;', '¶': '&para;', '°': '&deg;',
        '±': '&plusmn;', '×': '&times;', '÷': '&divide;', '¼': '&frac14;',
        '½': '&frac12;', '¾': '&frac34;', '≠': '&ne;', '≤': '&le;',
        '≥': '&ge;', '≈': '&asymp;', '∞': '&infin;', '√': '&radic;',
        '∫': '&int;', '∑': '&sum;', '∂': '&part;', '∏': '&prod;',
        'π': '&pi;', 'µ': '&micro;', '℗': '&copysr;',
    }
    
    # Create a compiled regex pattern for all special characters
    pattern = re.compile('|'.join(re.escape(char) for char in char_map.keys()))
    
    # Get total file size for progress bar
    total_size = os.path.getsize(input_path)
    
    print(f"Processing file: {os.path.basename(input_path)} ({get_file_size(input_path)})")
    print("Replacing special characters...")
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        # Process the file in chunks
        with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                
                # Replace special characters in this chunk
                def replace_match(match):
                    return char_map[match.group(0)]
                
                processed_chunk = pattern.sub(replace_match, chunk)
                
                # Handle any remaining non-ASCII characters
                processed_chunk = ''.join(
                    c if ord(c) < 128 else f'&#{ord(c)};' 
                    for c in processed_chunk
                )
                
                outfile.write(processed_chunk)
                pbar.update(len(chunk.encode('utf-8')))
    
    # If output is a temp file, replace the original
    if output_path != input_path:
        shutil.move(output_path, input_path)
    
    print("\nProcessing complete!")
    print(f"Original file backed up to: {input_path}.bak")

def main():
    # Path to the HTML file
    file_path = r"c:\Users\mad_p\OneDrive\Desktop\Py Projects\Daemonium\books\Plato\Plato - The Republic\Plato - The Republic.html"
    
    try:
        # Create backup
        backup_path = backup_file(file_path)
        
        # Process the file
        process_file(file_path)
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        if 'backup_path' in locals() and os.path.exists(backup_path):
            print("Restoring from backup...")
            shutil.copy2(backup_path, file_path)
            print("Original file restored from backup.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
