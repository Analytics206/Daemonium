# 📄 Windsurf IDE Document Reader Setup Guide

This guide helps you set up document reading functionality in Windsurf IDE using the Document Reader MCP server for any project.

## 📋 Overview

The Document Reader MCP server enables reading and analyzing markdown and text files directly within Windsurf IDE chat conversations. Once configured, it works across **all projects** - you don't need to reconfigure for each project or Python environment.

## 🆓 **COMPLETELY FREE - NO API KEYS REQUIRED**

**Local File Reading** - No external services, no usage limits, works completely offline!

### Quick Setup:

1. **Use the custom Python MCP server** (already created in your Daemonium project)
2. **Configure Windsurf IDE** with this simple setup:

```json
{
  "mcpServers": {
    "document-reader": {
      "command": "python",
      "args": ["c:\\Users\\mad_p\\OneDrive\\Desktop\\Py Projects\\daemonium\\scripts\\mcp_document_reader.py"]
    }
  }
}
```

3. **Restart Windsurf IDE** and you're done!

**Available Tools:**
- `read_document` - Read complete file content with metadata
- `list_documents` - List all supported documents in a directory
- `get_document_info` - Get file metadata without reading content
- `get_supported_extensions` - List supported file types

**Quick Test Commands:**
```
Please read the contents of README.md
List all markdown files in this project
What file types does the document reader support?
```

---

## 🛠️ One-Time System Setup

### Prerequisites
- Python 3.7+ (no additional dependencies required)
- Windsurf IDE with MCP support
- Access to your project files

### Step 1: Verify Python Installation

```powershell
# Check Python version (should be 3.7 or higher)
python --version

# Alternative check
python3 --version
```

**If Python is not installed**: Download from [https://python.org/downloads/](https://python.org/downloads/) and install.

### Step 2: Verify Document Reader Script

The Document Reader MCP script should be located at:
```
c:\Users\mad_p\OneDrive\Desktop\Py Projects\daemonium\scripts\mcp_document_reader.py
```

### Step 3: Test the Script (Optional)

```powershell
# Test the MCP server directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python "c:\Users\mad_p\OneDrive\Desktop\Py Projects\daemonium\scripts\mcp_document_reader.py"
```

## 🔧 Windsurf IDE Configuration

### Step 4: Configure Windsurf IDE MCP Settings

1. Open Windsurf IDE
2. Go to **Settings** → **MCP Servers** (or access via settings menu)
3. Add the Document Reader MCP server configuration:

```json
{
  "mcpServers": {
    "document-reader": {
      "command": "python",
      "args": ["c:\\Users\\mad_p\\OneDrive\\Desktop\\Py Projects\\daemonium\\scripts\\mcp_document_reader.py"]
    }
  }
}
```

**Important**: Update the path to match your actual project location.

### Step 5: Restart Windsurf IDE

Close and reopen Windsurf IDE to load the new MCP server configuration.

## 🎯 Available Document Tools

Once configured, you can use these tools in Windsurf chat:

### 1. Read Document Content
```
Please read the contents of README.md
Read the configuration file config/default.yaml
Show me the contents of docs/installation.txt
```

**Features:**
- Supports multiple encodings (UTF-8, Latin-1, CP1252)
- File size protection (default 1MB limit)
- Line count and metadata included
- Error handling for missing or corrupted files

### 2. List Documents in Directory
```
List all markdown files in this project
Show me all text files in the docs directory
Find all supported documents in the current folder
```

**Features:**
- Recursive directory search (optional)
- File size and modification date information
- Relative path display
- Automatic filtering by supported extensions

### 3. Get Document Information
```
Show me information about the README file
Get details about config/settings.txt without reading it
What's the size and modification date of the documentation?
```

**Features:**
- File metadata without content reading
- Size, modification time, and path information
- Supported file type verification
- No file size limits for info queries

### 4. List Supported File Types
```
What file types does the document reader support?
Show me all supported extensions
Which document formats can you read?
```

## 📁 Supported File Types

The Document Reader MCP supports the following file extensions:

- **`.md`** - Markdown files
- **`.txt`** - Plain text files  
- **`.markdown`** - Markdown variant files
- **`.text`** - Text variant files

## 💡 Usage Examples

### Basic File Reading
```
Please read the contents of README.md
```

### Project Documentation Analysis
```
List all markdown files in this project and then read the main README
```

### Configuration File Review
```
Show me information about config/default.yaml and then read its contents
```

### Documentation Discovery
```
Find all text files in the docs directory and show me their sizes
```

### Content Analysis
```
Read the installation guide and summarize the key steps
```

## 🔧 Advanced Features

### File Size Management
- **Default limit**: 1MB per file
- **Configurable**: Can be adjusted per request
- **Protection**: Prevents reading extremely large files
- **Encoding detection**: Automatic encoding detection and conversion

### Directory Search Options
- **Recursive search**: Search subdirectories automatically
- **Pattern matching**: Filter by file extensions
- **Metadata collection**: Size, modification date, relative paths
- **Sorting**: Alphabetical sorting by filename

### Error Handling
- **Missing files**: Clear error messages for non-existent files
- **Encoding issues**: Multiple encoding attempts with fallback
- **Permission errors**: Graceful handling of access restrictions
- **Large files**: Size limit protection with informative messages

## 🔧 Troubleshooting

### Common Issues

#### "Python command not found"
- Verify Python is installed: `python --version`
- Try `python3` instead of `python`
- Add Python to your system PATH
- Restart terminal after Python installation

#### "File not found" errors
- Verify the script path in your MCP configuration
- Check that the file exists at the specified location
- Ensure proper escaping of backslashes in Windows paths
- Use forward slashes or double backslashes in JSON

#### MCP server not loading in Windsurf
- Verify JSON configuration syntax (no trailing commas)
- Restart Windsurf IDE completely
- Check Windsurf logs for MCP server errors
- Ensure Python path is correct and accessible

#### "Encoding error" when reading files
- The script automatically tries multiple encodings
- Most common text encodings are supported
- Binary files are not supported (images, executables, etc.)
- Check if the file is actually a text-based document

### Testing the Installation

#### Command Line Testing
```powershell
# Test tools list
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python scripts/mcp_document_reader.py

# Test reading a file
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_document","arguments":{"file_path":"README.md"}}}' | python scripts/mcp_document_reader.py
```

#### Windsurf IDE Testing
After restarting Windsurf IDE, test with these commands:
- `"Please read the contents of README.md"`
- `"List all markdown files in this project"`
- `"What file types does the document reader support?"`

## 🌟 Advanced Configuration

### Custom File Size Limits
You can specify custom file size limits when reading documents:

```
Read the large documentation file with a 5MB size limit
```

The MCP will automatically handle the size parameter based on your request.

### Multiple Project Support
The Document Reader works across all your projects. Simply:

1. Configure once in Windsurf IDE
2. Use in any project directory
3. Specify relative or absolute paths as needed

### Integration with Other Tools
Combine Document Reader with other MCP servers:

```
Read the README.md file and then use TTS to speak the installation instructions
```

## 📝 Technical Details

### Architecture
- **Language**: Python 3.7+
- **Dependencies**: None (uses only standard library)
- **Protocol**: JSON-RPC 2.0 (MCP standard)
- **Platform**: Cross-platform (Windows, Linux, macOS)

### Performance
- **File reading**: Instant for files under 1MB
- **Directory scanning**: Fast recursive search
- **Memory usage**: Minimal (files read on-demand)
- **Encoding detection**: Automatic with fallback options

### Security
- **Local only**: No external API calls or network access
- **File system access**: Limited to readable text files
- **Size protection**: Prevents reading extremely large files
- **Error isolation**: Graceful error handling without crashes

## 📝 Notes

- **No Dependencies**: Uses only Python standard library
- **Works Offline**: Completely local file operations
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Project Agnostic**: Works in any directory or project
- **Privacy**: No external services or data transmission
- **Performance**: Fast file operations with intelligent caching

## 🔗 Useful Links

- [Daemonium Project Repository](https://github.com/your-repo/daemonium)
- [Windsurf IDE Documentation](https://windsurf.com/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Python Documentation](https://docs.python.org/)

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify Python installation and version
3. Test the MCP server from command line
4. Check Windsurf IDE logs for error messages
5. Ensure file paths are correct and accessible
6. Verify JSON configuration syntax

## 🚀 Quick Start Checklist

- [ ] Python 3.7+ installed and accessible
- [ ] Document Reader script exists at correct path
- [ ] MCP configuration added to Windsurf IDE
- [ ] Windsurf IDE restarted
- [ ] Test commands executed successfully

---

**Last Updated**: July 31, 2025  
**Version**: 1.0  
**Tested With**: Windsurf IDE, Windows 11, Python 3.11+  
**Dependencies**: None (Python standard library only)
