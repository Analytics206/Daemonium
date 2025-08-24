#!/usr/bin/env python3
"""
Daemonium MCP Server - OpenAI LLM Tools

- Provides two MCP tools:
  1) openai.chat   -> chat completions via OpenAI Chat Completions API
  2) openai.health -> API key and connectivity check + list available models

- Honors OPENAI_API_KEY, OPENAI_MODEL, and OPENAI_MODEL_GENERAL_KG environment variables
- Designed for stdio transport; launched by backend mcp_client or external tooling
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", os.getenv("OPENAI_MODEL_GENERAL_KG", "gpt-4o-mini"))
DEFAULT_OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))


@dataclass
class AppContext:
    api_key: Optional[str]
    model_default: str
    timeout_default: int


def build_app_context() -> AppContext:
    api_key = os.getenv("OPENAI_API_KEY")
    model_default = DEFAULT_OPENAI_MODEL
    timeout_default = DEFAULT_OPENAI_TIMEOUT
    return AppContext(api_key=api_key, model_default=model_default, timeout_default=timeout_default)


app_ctx = build_app_context()


@asynccontextmanager
async def lifespan(server: Server):
    yield app_ctx


server = Server("daemonium-openai-mcp", lifespan=lifespan)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="openai.chat",
            description="Chat with an LLM served by OpenAI. Supports messages with roles and optional streaming.",
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
                    "model": {"type": "string", "description": "OpenAI model name"},
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": 512},
                    "stream": {"type": "boolean", "default": False},
                    "system_prompt": {"type": "string", "description": "If provided, prepended as a system message"},
                },
                "required": ["messages"],
            },
        ),
        types.Tool(
            name="openai.health",
            description="Check OpenAI API key presence and list available models.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def _health_payload(ctx: AppContext) -> str:
    if AsyncOpenAI is None:
        return json.dumps({"ok": False, "error": "openai Python package not installed"}, indent=2)

    if not ctx.api_key:
        return json.dumps({"ok": False, "error": "OPENAI_API_KEY not set"}, indent=2)

    try:
        client = AsyncOpenAI(api_key=ctx.api_key)
        models = await client.models.list()
        model_ids = []
        try:
            for m in models.data:
                mid = getattr(m, "id", None)
                if mid:
                    model_ids.append(mid)
        except Exception:
            model_ids = []
        return json.dumps({
            "ok": True,
            "models": model_ids,
            "default_model": ctx.model_default,
        }, indent=2)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, indent=2)


async def _chat_with_openai(ctx: AppContext, arguments: Dict[str, Any]) -> str:
    if AsyncOpenAI is None:
        return "OpenAI SDK is not installed"

    messages: List[Dict[str, str]] = arguments.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty array of {role, content}")

    # Optional system prompt injection
    sys_prompt = arguments.get("system_prompt")
    if isinstance(sys_prompt, str) and sys_prompt.strip():
        messages = [{"role": "system", "content": sys_prompt.strip()}] + messages

    model = arguments.get("model") or ctx.model_default
    temperature = float(arguments.get("temperature", 0.7))
    max_tokens = int(arguments.get("max_tokens", 512))
    stream = bool(arguments.get("stream", False))

    # Timeout
    timeout_seconds = int(arguments.get("timeout", ctx.timeout_default))

    try:
        client = AsyncOpenAI(api_key=ctx.api_key)
        if stream:
            text_parts: List[str] = []
            # stream=True returns an async iterator of chunks
            async with client.chat.completions.stream(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_seconds,
            ) as stream_resp:
                async for event in stream_resp:
                    try:
                        if event.type == "content.delta":
                            delta = event.delta
                            if delta and getattr(delta, "content", None):
                                text_parts.append(str(delta.content))
                    except Exception:
                        continue
            return "".join(text_parts).strip()
        else:
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_seconds,
            )
            try:
                choice = resp.choices[0]
                content = choice.message.content if getattr(choice, "message", None) else None
                if content:
                    return str(content)
            except Exception:
                pass
            return json.dumps(resp.model_dump() if hasattr(resp, "model_dump") else resp)
    except Exception as e:
        return f"OpenAI request failed: {e}"


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    ctx: AppContext = server.request_context.lifespan_context  # type: ignore

    if name == "openai.health":
        result = await _health_payload(ctx)
        return [types.TextContent(type="text", text=result)]

    if name == "openai.chat":
        text = await _chat_with_openai(ctx, arguments or {})
        return [types.TextContent(type="text", text=text)]

    raise ValueError(f"Unknown tool: {name}")


async def run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="daemonium-openai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())
