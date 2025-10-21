"""
Configuration file to switch between OpenAI Agents and LangGraph implementations.
"""

import os

# Set this to switch between implementations
# Can be overridden by AGENT_BACKEND environment variable
AGENT_BACKEND = os.getenv("AGENT_BACKEND", "langgraph")  # Options: "openai" or "langgraph"


def get_llm_config():
    """Get LLM configuration from environment variables."""
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_api_base": os.getenv("OPENAI_API_BASE"),
    }


def get_app():
    """Lazy import of the app to avoid circular dependencies."""
    if AGENT_BACKEND == "langgraph":
        from .langgraph_server import app

        return app
    elif AGENT_BACKEND == "openai":
        from .openai_server import app

        return app
    else:
        raise ValueError(f"Unknown agent backend: {AGENT_BACKEND}")


# Export functions
__all__ = ["get_llm_config", "get_app", "AGENT_BACKEND"]
