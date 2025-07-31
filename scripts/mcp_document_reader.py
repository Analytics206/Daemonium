#!/usr/bin/env python3
"""
Document Reader MCP Server for Windsurf IDE
Reads .md and .txt files from specified directories
"""

import json
import sys
import os
import glob
from pathlib import Path
from typing import Dict, Any, List
import mimetypes

def log_message(message: str, level: str = "INFO"):
    """Log messages to stderr for debugging"""
    print(f"[{level}] {message}", file=sys.stderr)

def get_supported_extensions() -> List[str]:
    """Get list of supported file extensions"""
    return ['.md', '.txt', '.markdown', '.text']

def find_documents(directory: str = None, recursive: bool = True) -> List[Dict[str, Any]]:
    """Find all supported documents in a directory"""
    try:
        if directory is None:
            directory = os.getcwd()
        
        if not os.path.exists(directory):
            return []
        
        documents = []
        supported_extensions = get_supported_extensions()
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for ext in supported_extensions:
            search_pattern = os.path.join(directory, pattern + ext)
            for file_path in glob.glob(search_pattern, recursive=recursive):
                if os.path.isfile(file_path):
                    try:
                        stat = os.stat(file_path)
                        documents.append({
                            "path": os.path.abspath(file_path),
                            "name": os.path.basename(file_path),
                            "extension": os.path.splitext(file_path)[1],
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "relative_path": os.path.relpath(file_path, directory)
                        })
                    except OSError:
                        continue
        
        # Sort by name
        documents.sort(key=lambda x: x['name'].lower())
        return documents
        
    except Exception as e:
        log_message(f"Error finding documents: {e}", "ERROR")
        return []

def read_document(file_path: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
    """Read content from a document file"""
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {file_path}"
            }
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return {
                "success": False,
                "error": "File too large",
                "message": f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)"
            }
        
        # Check if it's a supported file type
        supported_extensions = get_supported_extensions()
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in supported_extensions:
            return {
                "success": False,
                "error": "Unsupported file type",
                "message": f"File extension '{file_ext}' is not supported. Supported: {', '.join(supported_extensions)}"
            }
        
        # Try to read the file with different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        encoding_used = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    encoding_used = encoding
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return {
                "success": False,
                "error": "Encoding error",
                "message": "Could not decode file with any supported encoding"
            }
        
        return {
            "success": True,
            "content": content,
            "file_path": os.path.abspath(file_path),
            "file_name": os.path.basename(file_path),
            "file_size": file_size,
            "encoding": encoding_used,
            "lines": len(content.splitlines()),
            "message": f"Successfully read {os.path.basename(file_path)} ({file_size} bytes, {len(content.splitlines())} lines)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error reading file: {str(e)}"
        }

def get_document_info(file_path: str) -> Dict[str, Any]:
    """Get information about a document without reading its content"""
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found",
                "message": f"File does not exist: {file_path}"
            }
        
        stat = os.stat(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        return {
            "success": True,
            "path": os.path.abspath(file_path),
            "name": os.path.basename(file_path),
            "extension": file_ext,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_supported": file_ext in get_supported_extensions(),
            "message": f"File info for {os.path.basename(file_path)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error getting file info: {str(e)}"
        }

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP protocol requests"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "document-reader",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "read_document",
                            "description": "Read content from a .md or .txt file",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Path to the document file to read"
                                    },
                                    "max_size": {
                                        "type": "integer",
                                        "description": "Maximum file size in bytes (default: 1MB)",
                                        "default": 1048576
                                    }
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "list_documents",
                            "description": "List all .md and .txt files in a directory",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "directory": {
                                        "type": "string",
                                        "description": "Directory to search (default: current directory)"
                                    },
                                    "recursive": {
                                        "type": "boolean",
                                        "description": "Search subdirectories recursively (default: true)",
                                        "default": True
                                    }
                                },
                                "required": []
                            }
                        },
                        {
                            "name": "get_document_info",
                            "description": "Get information about a document file without reading its content",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Path to the document file"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "get_supported_extensions",
                            "description": "Get list of supported file extensions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "read_document":
                file_path = arguments.get("file_path", "")
                max_size = arguments.get("max_size", 1024 * 1024)
                
                if not file_path:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "file_path parameter is required"
                        }
                    }
                
                result = read_document(file_path, max_size)
                
                if result["success"]:
                    content_text = f"File: {result['file_name']}\n"
                    content_text += f"Path: {result['file_path']}\n"
                    content_text += f"Size: {result['file_size']} bytes\n"
                    content_text += f"Lines: {result['lines']}\n"
                    content_text += f"Encoding: {result['encoding']}\n"
                    content_text += f"\n--- Content ---\n{result['content']}"
                else:
                    content_text = f"Error: {result['message']}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": content_text
                            }
                        ]
                    }
                }
            
            elif tool_name == "list_documents":
                directory = arguments.get("directory")
                recursive = arguments.get("recursive", True)
                
                documents = find_documents(directory, recursive)
                
                if documents:
                    doc_list = f"Found {len(documents)} documents:\n\n"
                    for doc in documents:
                        doc_list += f"• {doc['name']} ({doc['extension']})\n"
                        doc_list += f"  Path: {doc['relative_path']}\n"
                        doc_list += f"  Size: {doc['size']} bytes\n\n"
                else:
                    search_dir = directory or os.getcwd()
                    doc_list = f"No supported documents found in: {search_dir}\n"
                    doc_list += f"Supported extensions: {', '.join(get_supported_extensions())}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": doc_list
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_document_info":
                file_path = arguments.get("file_path", "")
                
                if not file_path:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "file_path parameter is required"
                        }
                    }
                
                result = get_document_info(file_path)
                
                if result["success"]:
                    info_text = f"File Information:\n"
                    info_text += f"Name: {result['name']}\n"
                    info_text += f"Path: {result['path']}\n"
                    info_text += f"Extension: {result['extension']}\n"
                    info_text += f"Size: {result['size']} bytes\n"
                    info_text += f"Modified: {result['modified']}\n"
                    info_text += f"Supported: {'Yes' if result['is_supported'] else 'No'}"
                else:
                    info_text = f"Error: {result['message']}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": info_text
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_supported_extensions":
                extensions = get_supported_extensions()
                ext_text = f"Supported file extensions:\n"
                ext_text += "\n".join([f"• {ext}" for ext in extensions])
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": ext_text
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }
    
    except Exception as e:
        log_message(f"Error handling request: {e}", "ERROR")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

def main():
    """Main MCP server loop"""
    log_message("Starting Document Reader MCP Server", "INFO")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = handle_mcp_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                log_message(f"Invalid JSON: {e}", "ERROR")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        log_message("Server stopped by user", "INFO")
    except Exception as e:
        log_message(f"Server error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
