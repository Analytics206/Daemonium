#!/usr/bin/env python3
"""
Script to convert special characters to HTML entities in HTML files.
"""
import os
import shutil
from html import escape
import re

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.bak"
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"Created backup at: {backup_path}")
    return backup_path

def convert_special_chars(html_content):
    """Convert special characters to HTML entities"""
    # Common special characters and their HTML entities
    char_map = {
        '—': '&mdash;',
        '–': '&ndash;',
        '“': '&ldquo;',
        '”': '&rdquo;',
        '‘': '&lsquo;',
        '’': '&rsquo;',
        '…': '&hellip;',
        '«': '&laquo;',
        '»': '&raquo;',
        '‹': '&lsaquo;',
        '›': '&rsaquo;',
        '„': '&bdquo;',
        '“': '&ldquo;',
        '”': '&rdquo;',
        '•': '&bull;',
        '·': '&middot;',
        '©': '&copy;',
        '®': '&reg;',
        '™': '&trade;',
        '€': '&euro;',
        '£': '&pound;',
        '¥': '&yen;',
        '¢': '&cent;',
        '§': '&sect;',
        '¶': '&para;',
        '°': '&deg;',
        '±': '&plusmn;',
        '×': '&times;',
        '÷': '&divide;',
        '¼': '&frac14;',
        '½': '&frac12;',
        '¾': '&frac34;',
        '≠': '&ne;',
        '≤': '&le;',
        '≥': '&ge;',
        '≈': '&asymp;',
        '∞': '&infin;',
        '√': '&radic;',
        '∫': '&int;',
        '∑': '&sum;',
        '∂': '&part;',
        '∏': '&prod;',
        'π': '&pi;',
        'µ': '&micro;',
        '…': '&hellip;',
        '–': '&ndash;',
        '—': '&mdash;',
        '‘': '&lsquo;',
        '’': '&rsquo;',
        '“': '&ldquo;',
        '”': '&rdquo;',
        '•': '&bull;',
        '…': '&hellip;',
        '℗': '&copysr;',
        '™': '&trade;',
        '©': '&copy;',
        '®': '&reg;',
        '°': '&deg;',
        '±': '&plusmn;',
        '×': '&times;',
        '÷': '&divide;',
        '¼': '&frac14;',
        '½': '&frac12;',
        '¾': '&frac34;',
        '≠': '&ne;',
        '≤': '&le;',
        '≥': '&ge;',
        '≈': '&asymp;',
        '∞': '&infin;',
        '√': '&radic;',
        '∫': '&int;',
        '∑': '&sum;',
        '∂': '&part;',
        '∏': '&prod;',
        'π': '&pi;',
        'µ': '&micro;',
        '…': '&hellip;',
    }
    
    # Replace special characters with their HTML entities
    for char, entity in char_map.items():
        html_content = html_content.replace(char, entity)
    
    # Handle any remaining non-ASCII characters
    html_content = ''.join(
        char if ord(char) < 128 else f'&#{ord(char)};' 
        for char in html_content
    )
    
    return html_content

def main():
    # Path to the HTML file
    file_path = r"c:\Users\mad_p\OneDrive\Desktop\Py Projects\Daemonium\books\Plato\Plato - The Republic\Plato - The Republic.html"
    
    try:
        # Create backup
        backup_path = backup_file(file_path)
        
        # Read the original content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Convert special characters
        new_content = convert_special_chars(content)
        
        # Write the new content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("Successfully converted special characters to HTML entities.")
        print(f"Original file backed up to: {backup_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if 'backup_path' in locals() and os.path.exists(backup_path):
            print("Restoring from backup...")
            shutil.copy2(backup_path, file_path)
            print("Original file restored from backup.")

if __name__ == "__main__":
    main()
