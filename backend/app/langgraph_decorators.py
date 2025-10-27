"""Decorators and registry for LangGraph tool functions.

Register functions (the real Python callables) so the LangGraph agent can call
them directly while the same functions stay wrapped with LangChain's @tool
for LangChain/LangGraph integration.
"""
from __future__ import annotations

from typing import Callable, Optional

_LG_TOOL_REGISTRY: dict[str, dict] = {}


def lg_tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to register a function as a LangGraph callable.

    Usage:
        @lg_tool(description="...")
        def my_tool(ctx, ...):
            ...
    """

    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        _LG_TOOL_REGISTRY[tool_name] = {
            "fn": fn,
            "description": description,
        }
        # attach metadata to the function for convenience
        setattr(fn, "_lg_tool_name", tool_name)
        setattr(fn, "_lg_description", description)
        return fn

    return decorator


def get_lg_tool_fn(name: str) -> Optional[Callable]:
    entry = _LG_TOOL_REGISTRY.get(name)
    return entry["fn"] if entry else None


def list_lg_tools() -> dict:
    return {k: {"description": v.get("description")} for k, v in _LG_TOOL_REGISTRY.items()}
