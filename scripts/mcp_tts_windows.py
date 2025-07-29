#!/usr/bin/env python3
"""
Free Windows TTS MCP Server for Windsurf IDE
Uses Windows built-in SAPI text-to-speech (completely free, no API keys needed)
"""

import json
import sys
import subprocess
import platform
from typing import Dict, Any, List

def log_message(message: str, level: str = "INFO"):
    """Log messages to stderr for debugging"""
    print(f"[{level}] {message}", file=sys.stderr)

def get_windows_voices() -> List[Dict[str, str]]:
    """Get available Windows TTS voices"""
    try:
        # PowerShell command to get available voices
        cmd = [
            "powershell", "-Command",
            "Add-Type -AssemblyName System.Speech; "
            "(New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | "
            "ForEach-Object { $_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture + '|' + $_.VoiceInfo.Gender }"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        voices = []
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        voices.append({
                            "name": parts[0].strip(),
                            "culture": parts[1].strip(),
                            "gender": parts[2].strip()
                        })
        
        # Fallback to default if no voices found
        if not voices:
            voices = [{"name": "Default", "culture": "en-US", "gender": "NotSet"}]
            
        return voices
    except Exception as e:
        log_message(f"Error getting voices: {e}", "ERROR")
        return [{"name": "Default", "culture": "en-US", "gender": "NotSet"}]

def speak_text_windows(text: str, voice: str = None, rate: int = 3) -> Dict[str, Any]:
    """Use Windows SAPI to speak text"""
    try:
        # Escape text for PowerShell
        escaped_text = text.replace("'", "''").replace('"', '""')
        
        # Build PowerShell command
        ps_command = [
            "Add-Type -AssemblyName System.Speech;",
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        ]
        
        # Set voice if specified, default to female voice
        if voice and voice != "Default":
            ps_command.append(f"$synth.SelectVoice('{voice}');")
        else:
            # Default to Microsoft Zira Desktop (female voice)
            ps_command.append("$synth.SelectVoice('Microsoft Zira Desktop');")
        
        # Set rate if specified (-10 to 10, where 0 is normal)
        if rate != 0:
            ps_command.append(f"$synth.Rate = {max(-10, min(10, rate))};")
        
        # Speak the text
        ps_command.append(f"$synth.Speak('{escaped_text}');")
        
        # Execute PowerShell command
        cmd = ["powershell", "-Command", " ".join(ps_command)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Speaking: {text[:50]}{'...' if len(text) > 50 else ''}",
                "voice": voice or "Microsoft Zira Desktop",
                "rate": rate
            }
        else:
            return {
                "success": False,
                "error": f"TTS failed: {result.stderr}",
                "message": "Failed to speak text"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "TTS timeout",
            "message": "Speech synthesis timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "TTS error occurred"
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
                        "name": "windows-tts",
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
                            "name": "windows_tts",
                            "description": "Convert text to speech using Windows built-in TTS (completely free)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "description": "Text to convert to speech"
                                    },
                                    "voice": {
                                        "type": "string",
                                        "description": "Voice name (optional, use list_voices to see available)",
                                        "default": "Default"
                                    },
                                    "rate": {
                                        "type": "integer",
                                        "description": "Speech rate (-10 to 10, 0 = normal speed)",
                                        "default": 0,
                                        "minimum": -10,
                                        "maximum": 10
                                    }
                                },
                                "required": ["text"]
                            }
                        },
                        {
                            "name": "list_voices",
                            "description": "List available Windows TTS voices",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "windows_tts":
                text = arguments.get("text", "")
                voice = arguments.get("voice")
                rate = arguments.get("rate", 0)
                
                if not text:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Text parameter is required"
                        }
                    }
                
                result = speak_text_windows(text, voice, rate)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result["message"]
                            }
                        ]
                    }
                }
            
            elif tool_name == "list_voices":
                voices = get_windows_voices()
                voice_list = "\n".join([
                    f"• {voice['name']} ({voice['culture']}, {voice['gender']})"
                    for voice in voices
                ])
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Available Windows TTS Voices:\n{voice_list}"
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
    if platform.system() != "Windows":
        log_message("This MCP server only works on Windows", "ERROR")
        sys.exit(1)
    
    log_message("Starting Windows TTS MCP Server", "INFO")
    
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
