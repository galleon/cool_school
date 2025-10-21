"""
Main entry point that dynamically loads the correct agent backend.
To switch between OpenAI Agents and LangGraph, modify AGENT_BACKEND in config.py
"""

from .config import get_app

# Load the appropriate app based on configuration
app = get_app()

# Export app for uvicorn to find
__all__ = ["app"]
