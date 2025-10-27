"""Run context wrapper for LangGraph tools.

Provides an object similar to RunContextWrapper used by OpenAI tools so tool
functions can access contextual metadata (thread_id, stores, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class RunLanggraphContextWrapper(Generic[T]):
    """A lightweight RunContextWrapper for LangGraph.

    Currently wraps minimal data (thread_id and metadata). Can be extended later
    to carry request/response helpers or stores.
    """

    thread_id: str
    metadata: dict[str, Any] = None

    @classmethod
    def from_thread_id(cls, thread_id: str) -> "RunLanggraphContextWrapper":
        return cls(thread_id=thread_id, metadata={})
