#!/usr/bin/env python3
"""
Async MCP client helper for Daemonium backend

- Spawns the local MCP server over stdio transport
- Calls the `ollama.chat` tool and returns assistant text
- Uses centralized config indirectly via the MCP server

This module avoids framework coupling and can be reused in routers or services.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _server_params_candidates() -> List[Tuple[str, List[str]]]:
    """Build a list of (command, args) candidates to launch the MCP server.

    Order of preference:
    1) Explicit env MCP_SERVER_CMD (+ optional MCP_SERVER_ARGS)
    2) Python running server from container path: /app/mcp-service/mcp_server.py
    3) Python running server from repo-relative path: mcp-service/mcp_server.py
    """
    cmd_env = os.getenv("MCP_SERVER_CMD")
    args_env = os.getenv("MCP_SERVER_ARGS")
    if cmd_env:
        args_list = args_env.split() if args_env else []
        return [(cmd_env, args_list)]

    python_bin = os.getenv("PYTHON_BIN", "python")
    return [
        (python_bin, ["-u", "/app/mcp-service/mcp_server.py"]),
        (python_bin, ["-u", "mcp-service/mcp_server.py"]),
    ]


async def _try_call_with(
    cmd: str,
    args: List[str],
    tool: str,
    arguments: Dict[str, Any],
    timeout: Optional[int],
) -> Optional[str]:
    """Try to run a single stdio MCP server process and call a tool.

    Returns assistant text if successful, else None.
    """
    try:
        # Lazy import so importing this module doesn't require mcp unless used
        from mcp.client.stdio import StdioServerParameters, stdio_client  # type: ignore
        from mcp.client.session import ClientSession  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error(f"MCP client package is not installed: {e}")
        return None

    try:
        params = StdioServerParameters(command=cmd, args=args)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                call = session.call_tool(tool, arguments)
                res = await asyncio.wait_for(call, timeout=timeout) if timeout and timeout > 0 else await call

                # Expect a list of text content objects, but support multiple shapes
                text_parts: List[str] = []
                if isinstance(res, list):
                    for item in res:
                        try:
                            if isinstance(item, dict):
                                if item.get("type") == "text" and "text" in item:
                                    text_parts.append(str(item["text"]))
                            else:
                                text_attr = getattr(item, "text", None)
                                if text_attr:
                                    text_parts.append(str(text_attr))
                        except Exception:
                            continue
                else:
                    text_attr = getattr(res, "text", None)
                    if text_attr:
                        text_parts.append(str(text_attr))

                if text_parts:
                    return "".join(text_parts).strip()

                # Fallback: stringify the whole result
                try:
                    return str(res)
                except Exception:
                    return None
    except Exception as e:
        logger.warning(f"MCP stdio call failed (cmd={cmd} args={args}): {e}")
        return None


async def call_ollama_chat(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    task_type: Optional[str] = "general_kg",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 512,
    timeout: Optional[int] = None,
) -> str:
    """Call the MCP server's `ollama.chat` tool and return assistant text.

    Args:
        messages: List of {role, content} messages (at least one user message)
        system_prompt: Optional system prompt to prepend
        task_type: Optional task type for centralized config model selection
        model: Optional explicit model override
        temperature: Sampling temperature
        max_tokens: Limit generated tokens
        timeout: Overall timeout (seconds) for the tool call

    Returns:
        Assistant response text

    Raises:
        RuntimeError if all attempts fail or response is empty.
    """
    if not messages:
        raise ValueError("messages must be non-empty")

    args: Dict[str, Any] = {
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": False,
    }
    if system_prompt:
        args["system_prompt"] = system_prompt
    if task_type:
        args["task_type"] = task_type
    if model:
        args["model"] = model

    # Try server launch candidates in order
    last_error: Optional[str] = None
    for cmd, arg_list in _server_params_candidates():
        result = await _try_call_with(cmd, arg_list, "ollama.chat", args, timeout)
        if result is not None and result.strip():
            return result
        last_error = f"Failed with {cmd} {' '.join(arg_list)}"

    raise RuntimeError(last_error or "MCP ollama.chat call failed or returned empty response")
