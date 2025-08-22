#!/usr/bin/env python3
"""
Daemonium MCP Server - Ollama LLM Tools Only

- Provides two MCP tools:
  1) ollama.chat   -> chat completions via Ollama /api/chat
  2) ollama.health -> connectivity + available models via /api/tags

- Uses centralized configuration from config/ollama_config.py when available
- Honors OLLAMA_BASE_URL and OLLAMA_MODEL environment variables
- Designed for stdio transport; launched via docker exec by the client config

Notes:
- We keep the server minimal and focused on Ollama only as requested.
- Other model providers (OpenAI/Anthropic) are not wired due to missing keys.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Centralized Ollama config (optional but preferred)
try:
    from config.ollama_config import get_ollama_config
except Exception:  # pragma: no cover - fallback if config module not available
    get_ollama_config = None  # type: ignore


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")


@dataclass
class AppContext:
    base_url: str
    fallback_urls: List[str]
    model_default: str
    config: Any  # OllamaConfigLoader or None


def _dedupe(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in seq:
        if s and s not in seen:
            out.append(s)
            seen.add(s)
    return out


def resolve_ollama_urls() -> List[str]:
    env_url = os.getenv("OLLAMA_BASE_URL")
    cfg_url = None
    if get_ollama_config is not None:
        try:
            cfg = get_ollama_config()
            cfg_url = getattr(cfg, "server", None).url if getattr(cfg, "server", None) else None
        except Exception:
            cfg_url = None

    # Preferred order: ENV -> Config -> docker compose service -> host fallback
    candidates = [
        env_url,
        cfg_url,
        "http://ollama:11434",
        "http://host.docker.internal:11434",
        "http://localhost:11434",
    ]
    return _dedupe([c for c in candidates if c])


def build_app_context() -> AppContext:
    urls = resolve_ollama_urls()
    cfg = None
    if get_ollama_config is not None:
        try:
            cfg = get_ollama_config()
        except Exception:
            cfg = None

    model_default = DEFAULT_MODEL
    # Allow centralized config to provide a default for general tasks
    if cfg is not None:
        try:
            model_default = cfg.get_model_for_task("general_kg") or model_default
        except Exception:
            pass

    base_url = urls[0] if urls else "http://host.docker.internal:11434"
    return AppContext(base_url=base_url, fallback_urls=urls, model_default=model_default, config=cfg)


app_ctx = build_app_context()

# Create MCP server
server = Server("daemonium-ollama-mcp", lifespan=app_ctx)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="ollama.chat",
            description="Chat with an LLM served by Ollama. Supports messages with roles and optional streaming.",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Array of chat messages {role, content}",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                                "content": {"type": "string"},
                            },
                            "required": ["role", "content"],
                        },
                    },
                    "model": {"type": "string", "description": "Ollama model name"},
                    "task_type": {"type": "string", "description": "Optional task type to select model via centralized config (e.g., general_kg)"},
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": 512},
                    "stream": {"type": "boolean", "default": False},
                    "system_prompt": {"type": "string", "description": "If provided, prepended as a system message"},
                },
                "required": ["messages"],
            },
        ),
        types.Tool(
            name="ollama.health",
            description="Check connectivity to Ollama and list available models.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def _pick_first_healthy_url(urls: List[str], timeout: int = 5) -> Optional[str]:
    for url in urls:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(f"{url}/api/tags") as resp:
                    if resp.status == 200:
                        return url
        except Exception:
            continue
    return None


async def _health_payload(ctx: AppContext) -> str:
    urls = ctx.fallback_urls or [ctx.base_url]
    healthy_url = await _pick_first_healthy_url(urls)
    if not healthy_url:
        return json.dumps({
            "ok": False,
            "error": "No reachable Ollama endpoint",
            "tried": urls,
        }, indent=2)

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{healthy_url}/api/tags") as resp:
                data = await resp.json()
                return json.dumps({
                    "ok": True,
                    "base_url": healthy_url,
                    "models": data.get("models", []),
                }, indent=2)
    except Exception as e:
        return json.dumps({
            "ok": False,
            "base_url": healthy_url,
            "error": str(e),
        }, indent=2)


async def _chat_with_ollama(ctx: AppContext, arguments: Dict[str, Any]) -> str:
    messages: List[Dict[str, str]] = arguments.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty array of {role, content}")

    # Optional system prompt injection
    sys_prompt = arguments.get("system_prompt")
    if isinstance(sys_prompt, str) and sys_prompt.strip():
        messages = [{"role": "system", "content": sys_prompt.strip()}] + messages

    task_type = arguments.get("task_type")
    model = arguments.get("model")

    # Resolve model via config, env, or default
    if not model:
        model = os.getenv("OLLAMA_MODEL") or ctx.model_default
        if ctx.config is not None and task_type:
            try:
                model = ctx.config.get_model_for_task(task_type, override=model)
            except Exception:
                pass

    temperature = float(arguments.get("temperature", 0.7))
    max_tokens = int(arguments.get("max_tokens", 512))
    stream = bool(arguments.get("stream", False))

    # Resolve timeout via config
    timeout_seconds = 60
    if ctx.config is not None:
        try:
            timeout_seconds = int(ctx.config.get_timeout_for_model(model, task_type=task_type))
        except Exception:
            pass

    # Find a healthy base URL
    healthy_url = await _pick_first_healthy_url(ctx.fallback_urls or [ctx.base_url], timeout=5)
    base_url = healthy_url or ctx.base_url

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"{base_url}/api/chat"
            if stream:
                # Aggregate streamed chunks
                text_parts: List[str] = []
                async with session.post(url, json=payload) as resp:
                    resp.raise_for_status()
                    async for raw_line in resp.content:
                        try:
                            line = raw_line.decode("utf-8").strip()
                            if not line:
                                continue
                            chunk = json.loads(line)
                            # Ollama stream format: {"message": {"role": "assistant", "content": "..."}, "done": false}
                            msg = chunk.get("message", {})
                            if isinstance(msg, dict):
                                c = msg.get("content")
                                if c:
                                    text_parts.append(c)
                        except Exception:
                            continue
                return "".join(text_parts).strip()
            else:
                async with session.post(url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    # Non-stream format: {"message": {"role":"assistant","content":"..."}, ...}
                    msg = data.get("message", {}) if isinstance(data, dict) else {}
                    if isinstance(msg, dict) and msg.get("content"):
                        return str(msg.get("content"))
                    # Fallback if using /api/generate-like response
                    if isinstance(data, dict) and data.get("response"):
                        return str(data.get("response"))
                    return json.dumps(data)
    except aiohttp.ClientResponseError as cre:
        return f"Error from Ollama ({cre.status}): {cre.message}"
    except Exception as e:
        return f"Ollama request failed: {e}"


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    ctx: AppContext = server.request_context.lifespan_context  # type: ignore

    if name == "ollama.health":
        result = await _health_payload(ctx)
        return [types.TextContent(type="text", text=result)]

    if name == "ollama.chat":
        text = await _chat_with_ollama(ctx, arguments or {})
        return [types.TextContent(type="text", text=text)]

    raise ValueError(f"Unknown tool: {name}")


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="daemonium-ollama-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
