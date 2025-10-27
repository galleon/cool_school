"""LangGraph context wrapper for managing thread metadata.

Similar to OpenAI's RunContextWrapper, this provides a unified context object
for LangGraph tool functions to access thread information and other metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LangGraphContext:
    """Context wrapper for LangGraph tool execution.

    Holds thread metadata and other contextual information needed by tools,
    similar to how OpenAI's RunContextWrapper works.
    """

    thread_id: str
    """The LangGraph thread ID for this execution."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata associated with this thread."""

    @classmethod
    def from_thread_id(cls, thread_id: str) -> LangGraphContext:
        """Create a context from a thread ID."""
        return cls(thread_id=thread_id)
