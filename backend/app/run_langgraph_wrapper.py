"""Run context wrapper for LangGraph tools.

Provides an object similar to RunContextWrapper used by OpenAI tools so tool
functions can accept contextual metadata (thread_id, stores, etc.) injected
by the LangGraph framework.

This mirrors the ChatKit/OpenAI pattern where context is injected as a parameter
but may not be used directly by the tool logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class RunLanggraphContextWrapper(Generic[T]):
    """A lightweight RunContextWrapper for LangGraph.

    Mirrors the shape of the OpenAI `RunContextWrapper[T]` used in the
    ChatKit-based tools so that tool implementations can accept a similarly
    typed `ctx: RunLanggraphContextWrapper[AgentContext]` parameter.

    Fields:
    - thread_id: the LangGraph thread id for this execution
    - agent_context: an optional backend-specific agent context (kept generic)
    - metadata: arbitrary metadata dictionary
    """

    thread_id: str
    agent_context: T | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_thread_id(
        cls, thread_id: str, agent_context: T | None = None, metadata: dict | None = None
    ) -> "RunLanggraphContextWrapper":
        """Create a RunLanggraphContextWrapper from a thread id.

        The signature mirrors the typical factory shape used by RunContextWrapper
        so tests and type checkers can treat them similarly.
        """
        return cls(thread_id=thread_id, agent_context=agent_context, metadata=metadata or {})

    @classmethod
    def from_thread_id(
        cls, thread_id: str, metadata: dict[str, Any] | None = None
    ) -> RunLanggraphContextWrapper:
        """Create a context from a thread ID and optional metadata."""
        return cls(thread_id=thread_id, metadata=metadata or {})
