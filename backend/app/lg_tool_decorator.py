"""Decorator for registering LangGraph tools.

Provides a decorator pattern similar to @function_tool for OpenAI tools,
allowing tools to be registered and discoverable.
"""

from __future__ import annotations

import functools
from typing import Callable, Optional


_TOOL_REGISTRY: dict[str, dict] = {}


def lg_tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator for registering LangGraph tools.

    Similar to the @function_tool decorator used in OpenAI backend, this allows
    tools to be registered centrally and automatically discovered.

    Args:
        name: Optional override for the tool name (defaults to function name)
        description: Optional override for the tool description
    """

    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        tool_description = description or (fn.__doc__ or "").strip()

        _TOOL_REGISTRY[tool_name] = {
            "fn": fn,
            "name": tool_name,
            "description": tool_description,
        }

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        # Attach registry info to the wrapper
        wrapper._is_lg_tool = True
        wrapper._tool_name = tool_name
        wrapper._tool_description = tool_description

        return wrapper

    return decorator


def get_registered_tools() -> dict[str, dict]:
    """Get all registered LangGraph tools."""
    return _TOOL_REGISTRY.copy()


def get_tool(name: str) -> Callable:
    """Get a registered tool by name."""
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Tool {name} not registered")
    return _TOOL_REGISTRY[name]["fn"]
