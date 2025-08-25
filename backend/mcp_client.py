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
import sys
import shlex
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _server_params_candidates(server: str = "ollama") -> List[Tuple[str, List[str]]]:
    """Build a list of (command, args) candidates to launch the MCP server.

    Order of preference:
    1) Explicit env MCP_SERVER_CMD (+ optional MCP_SERVER_ARGS)
    2) Python from current venv (sys.executable) running absolute script path overrides
    3) Python from current venv running project-root absolute script path
    4) Python from current venv running CWD absolute script path
    5) As a last resort, a relative path under "mcp-service/"

    The ``server`` arg selects which script to prefer: "ollama" or "openai".
    """
    cmd_env = os.getenv("MCP_SERVER_CMD")
    args_env = os.getenv("MCP_SERVER_ARGS")
    if cmd_env:
        # Allow command to include its own args and optionally append extra args from MCP_SERVER_ARGS
        try:
            cmd_parts = shlex.split(cmd_env)
        except Exception:
            cmd_parts = cmd_env.split()
        cmd = cmd_parts[0]
        base_args = cmd_parts[1:]
        try:
            extra_args = shlex.split(args_env) if args_env else []
        except Exception:
            extra_args = args_env.split() if args_env else []
        return [(cmd, base_args + extra_args)]

    python_bin = os.getenv("PYTHON_BIN") or sys.executable or "python"

    # Map server type to script filenames
    script_name = {
        "ollama": "mcp_server.py",
        "openai": "mcp_server_openai.py",
    }.get(server, "mcp_server.py")

    # Project root (parent of backend/) and CWD
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cwd_dir = os.getcwd()

    # Optional explicit override per server
    override_env = os.getenv("MCP_OLLAMA_SERVER_PATH") if server == "ollama" else os.getenv("MCP_OPENAI_SERVER_PATH")

    candidates: List[Tuple[str, List[str]]] = []

    def add_if_exists(target_list: List[Tuple[str, List[str]]], path: str):
        if path and os.path.isabs(path) and os.path.exists(path):
            target_list.append((python_bin, ["-u", path]))

    # 1) explicit override path
    if override_env:
        add_if_exists(candidates, override_env)

    # 2) common absolute container path (only include if it exists)
    container_path = os.path.join("/app", "mcp-service", script_name)
    add_if_exists(candidates, container_path)

    # 3) absolute path from repo root
    add_if_exists(candidates, os.path.join(root_dir, "mcp-service", script_name))

    # 4) absolute path from current working directory
    add_if_exists(candidates, os.path.join(cwd_dir, "mcp-service", script_name))

    # 5) As a last resort, try relative path (may fail if CWD is unexpected)
    if not candidates:
        candidates.append((python_bin, ["-u", os.path.join("mcp-service", script_name)]))

    # Also consider the alternative script as a fallback
    alt_name = "mcp_server_openai.py" if server == "ollama" else "mcp_server.py"
    alt_candidates: List[Tuple[str, List[str]]] = []

    add_if_exists(alt_candidates, os.path.join(root_dir, "mcp-service", alt_name))
    add_if_exists(alt_candidates, os.path.join(cwd_dir, "mcp-service", alt_name))

    # If still nothing was found for alt, append a relative alt as a weak fallback
    if not alt_candidates:
        alt_candidates.append((python_bin, ["-u", os.path.join("mcp-service", alt_name)]))

    candidates.extend(alt_candidates)

    # Debug: show candidates when verbose logging is enabled
    if logger.isEnabledFor(logging.DEBUG):
        try:
            logger.debug(
                "MCP server launch candidates",
                extra={
                    "server": server,
                    "candidates": [(c, a) for c, a in candidates],
                },
            )
        except Exception:
            pass

    return candidates


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
    # Separate init timeout to avoid indefinite hangs during MCP handshake
    try:
        init_timeout = int(os.getenv("MCP_INIT_TIMEOUT", "10"))
    except Exception:
        init_timeout = 10

    try:
        # Lazy import so importing this module doesn't require mcp unless used
        from mcp.client.stdio import StdioServerParameters, stdio_client  # type: ignore
        from mcp.client.session import ClientSession  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error(f"MCP client package is not installed: {e}")
        return None

    # Compute overall timeout to protect against hangs before/around initialize
    try:
        overall_env = int(os.getenv("MCP_OVERALL_TIMEOUT", "0"))
    except Exception:
        overall_env = 0
    # Default overall timeout = init + call + 5s buffer (or at least 15s)
    overall_timeout = overall_env if overall_env > 0 else max(15, init_timeout + (int(timeout) if timeout else 0) + 5)

    async def _do_call() -> Optional[str]:
        params = StdioServerParameters(command=cmd, args=args)
        logger.debug(
            "Starting MCP stdio server", extra={
                "cmd": cmd,
                "cmd_args": args,
                "tool": tool,
                "init_timeout": init_timeout,
                "call_timeout": timeout,
                "overall_timeout": overall_timeout,
            }
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                # Ensure initialization does not hang indefinitely
                await asyncio.wait_for(session.initialize(), timeout=init_timeout)
                call = session.call_tool(tool, arguments)
                res = await asyncio.wait_for(call, timeout=timeout) if timeout and timeout > 0 else await call

                # Expect a list of text content objects, but support multiple shapes
                text_parts: List[str] = []

                def _extract_from_content_list(content_list: List[Any]) -> None:
                    for item in content_list:
                        try:
                            if isinstance(item, dict):
                                item_type = item.get("type")
                                if (item_type is None or item_type == "text") and "text" in item:
                                    text_parts.append(str(item["text"]))
                            else:
                                item_type = getattr(item, "type", None)
                                item_text = getattr(item, "text", None)
                                if item_text and (item_type is None or item_type == "text"):
                                    text_parts.append(str(item_text))
                        except Exception:
                            continue

                if isinstance(res, list):
                    # Direct list of content
                    _extract_from_content_list(res)
                else:
                    # Common MCP shape: CallToolResult(meta=?, content=[...])
                    content_attr = getattr(res, "content", None)
                    if isinstance(content_attr, list) and content_attr:
                        _extract_from_content_list(content_attr)
                    elif isinstance(res, dict):
                        if isinstance(res.get("content"), list):
                            _extract_from_content_list(res["content"])  # type: ignore[index]
                        elif "text" in res:
                            text_parts.append(str(res["text"]))
                    else:
                        # Last resort: simple object with .text
                        text_attr = getattr(res, "text", None)
                        if text_attr:
                            text_parts.append(str(text_attr))

                if text_parts:
                    result_text = "".join(text_parts).strip()
                    logger.debug(
                        "MCP stdio call succeeded", extra={
                            "cmd": cmd,
                            "tool": tool,
                            "result_length": len(result_text),
                        }
                    )
                    return result_text

                # Fallback: stringify the whole result
                try:
                    result_text = str(res)
                    logger.debug(
                        "MCP stdio call returned non-text content; stringified", extra={
                            "cmd": cmd,
                            "tool": tool,
                            "result_length": len(result_text),
                        }
                    )
                    return result_text
                except Exception:
                    return None

    try:
        return await asyncio.wait_for(_do_call(), timeout=overall_timeout)
    except asyncio.TimeoutError:
        logger.warning(f"MCP stdio overall timeout exceeded (cmd={cmd} args={args}, overall={overall_timeout}s)")
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
    for cmd, arg_list in _server_params_candidates(server="ollama"):
        result = await _try_call_with(cmd, arg_list, "ollama.chat", args, timeout)
        if result is not None and result.strip():
            return result
        last_error = f"Failed with {cmd} {' '.join(arg_list)}"

    raise RuntimeError(last_error or "MCP ollama.chat call failed or returned empty response")


async def call_openai_chat(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 512,
    timeout: Optional[int] = None,
) -> str:
    """Call the MCP server's `openai.chat` tool and return assistant text.

    Args:
        messages: List of {role, content} messages (at least one user message)
        system_prompt: Optional system prompt to prepend
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
    if model:
        args["model"] = model
    if timeout:
        # The OpenAI MCP server supports a 'timeout' argument
        args["timeout"] = int(timeout)

    last_error: Optional[str] = None
    for cmd, arg_list in _server_params_candidates(server="openai"):
        result = await _try_call_with(cmd, arg_list, "openai.chat", args, timeout)
        if result is not None and result.strip():
            return result
        last_error = f"Failed with {cmd} {' '.join(arg_list)}"

    raise RuntimeError(last_error or "MCP openai.chat call failed or returned empty response")
