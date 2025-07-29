# 🎙️ Windsurf IDE Text-to-Speech Setup Guide

This guide helps you set up text-to-speech functionality in Windsurf IDE using the MCP-TTS server for any project.

## 📋 Overview

The MCP-TTS server enables text-to-speech functionality in Windsurf IDE chat conversations with AI models. Once installed, it works across **all projects** - you don't need to reinstall for each project or Python environment.

## 🆓 **COMPLETELY FREE OPTION (Recommended)**

**Windows Built-in TTS** - No API keys, no usage limits, works offline!

### Quick Setup for Free Windows TTS:

1. **Use the custom Python MCP server** (already created in your Daemonium project)
2. **Configure Windsurf IDE** with this simple setup:

```json
{
  "mcpServers": {
    "windows-tts": {
      "command": "python",
      "args": ["c:\\Users\\mad_p\\OneDrive\\Desktop\\Py Projects\\daemonium\\scripts\\mcp_tts_windows.py"]
    }
  }
}
```

3. **Restart Windsurf IDE** and you're done!

**Available Tools:**
- `windows_tts` - Speak any text using Windows voices
- `list_voices` - See all available Windows TTS voices

**Usage Examples:**
```
Use windows_tts to read this code explanation aloud
List all available Windows TTS voices
Use windows_tts with a slower rate to explain this function
```

---

## 🛠️ One-Time System Setup

### Prerequisites
- Windows 10/11
- Windsurf IDE
- Internet connection for API access

### Step 1: Install Go Programming Language

```powershell
# Install Go using Windows Package Manager
winget install GoLang.Go

# After installation, restart your terminal or run:
refreshenv
```

**Alternative**: Download from [https://golang.org/dl/](https://golang.org/dl/) and run the installer.

### Step 2: Install MCP-TTS Server

```powershell
# Install the MCP-TTS server globally
go install github.com/blacktop/mcp-tts@latest
```

### Step 3: Verify Installation

```powershell
# Check Go version
go version

# Check if mcp-tts is installed (should show help)
mcp-tts --help
```

## 🔧 Windsurf IDE Configuration

### Step 4: Get Google AI API Key (Free Option)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" 
4. Create a new API key
5. Copy the API key (starts with `AIza...`)

### Step 5: Configure Windsurf IDE MCP Settings

1. Open Windsurf IDE
2. Go to **Settings** → **MCP Servers** (or similar - exact location may vary)
3. Add a new MCP server configuration:

```json
{
  "mcpServers": {
    "tts": {
      "command": "mcp-tts",
      "env": {
        "GOOGLE_AI_API_KEY": "YOUR_API_KEY_HERE",
        "MCP_TTS_SUPPRESS_SPEAKING_OUTPUT": "true"
      }
    }
  }
}
```

**Replace `YOUR_API_KEY_HERE` with your actual Google AI API key.**

### Step 6: Restart Windsurf IDE

Close and reopen Windsurf IDE to load the new MCP server configuration.

## 🎯 Available TTS Tools

Once configured, you can use these tools in Windsurf chat:

### Google TTS (Free - Recommended)
```
Use google_tts to read this text aloud
```

**Available Voices:**
- **Zephyr** (Bright)
- **Puck** (Upbeat) 
- **Charon** (Informative)
- **Kore** (Firm)
- **Fenrir** (Excitable)
- **Leda** (Youthful)
- **Orus** (Firm)
- **Aoede** (Breezy)
- **Callirhoe** (Easy-going)
- **Autonoe** (Bright)
- **Enceladus** (Breathy)
- **Iapetus** (Clear)
- And 18 more voices

### Other TTS Options (Require API Keys)

#### OpenAI TTS (Paid)
```json
"OPENAI_API_KEY": "your_openai_key_here"
```

#### ElevenLabs TTS (Paid)
```json
"ELEVENLABS_API_KEY": "your_elevenlabs_key_here"
```

## 💡 Usage Examples

### Basic Usage
```
Please read this code explanation aloud using Google TTS
```

### With Voice Selection
```
Use google_tts with the Puck voice to read this documentation
```

### For Code Reviews
```
Read this function description aloud so I can listen while coding
```

## 🔧 Troubleshooting

### Common Issues

#### "mcp-tts command not found"
- Restart your terminal after installing Go
- Verify Go is in your PATH: `go version`
- Reinstall: `go install github.com/blacktop/mcp-tts@latest`

#### "API key invalid"
- Verify your Google AI API key is correct
- Check that the API key has proper permissions
- Ensure you're using `GOOGLE_AI_API_KEY` or `GEMINI_API_KEY`

#### No audio output
- Check your system audio settings
- Verify speakers/headphones are working
- Try different TTS voices

#### MCP server not loading in Windsurf
- Verify JSON configuration syntax
- Restart Windsurf IDE completely
- Check Windsurf logs for MCP server errors

### Testing the Installation

You can test the MCP-TTS server directly from command line:

```powershell
# Test Google TTS (requires API key in environment)
$env:GOOGLE_AI_API_KEY="your_key_here"
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_tts","arguments":{"text":"Hello, this is a test"}}}' | mcp-tts
```

## 🌟 Advanced Configuration

### Custom Voice Instructions
```json
{
  "mcpServers": {
    "tts": {
      "command": "mcp-tts",
      "env": {
        "GOOGLE_AI_API_KEY": "your_key_here",
        "MCP_TTS_SUPPRESS_SPEAKING_OUTPUT": "false",
        "OPENAI_TTS_INSTRUCTIONS": "Speak in a cheerful and enthusiastic tone"
      }
    }
  }
}
```

### Multiple TTS Services
```json
{
  "mcpServers": {
    "tts": {
      "command": "mcp-tts",
      "env": {
        "GOOGLE_AI_API_KEY": "your_google_key",
        "OPENAI_API_KEY": "your_openai_key",
        "ELEVENLABS_API_KEY": "your_elevenlabs_key"
      }
    }
  }
}
```

## 📝 Notes

- **Global Installation**: The MCP-TTS server is installed system-wide, not per-project
- **Works Across Projects**: Once configured, works in any Windsurf project
- **Free Option**: Google TTS provides high-quality voices at no cost
- **Privacy**: Audio is generated via API calls to the selected service
- **Performance**: Audio generation may take 1-3 seconds depending on text length

## 🔗 Useful Links

- [MCP-TTS GitHub Repository](https://github.com/blacktop/mcp-tts)
- [Google AI Studio](https://aistudio.google.com/)
- [Windsurf IDE Documentation](https://windsurf.com/)
- [Go Programming Language](https://golang.org/)

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Test the MCP server from command line
4. Check Windsurf IDE logs for error messages
5. Consult the [MCP-TTS GitHub issues](https://github.com/blacktop/mcp-tts/issues)

---

**Last Updated**: July 29, 2025  
**Version**: 1.0  
**Tested With**: Windsurf IDE, Windows 11, Go 1.24.5
