"""
Configuration module using Pydantic BaseSettings.

This module provides a centralized configuration system that reads from environment
variables and .env files, with validation and type safety.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Core API Keys
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key for GPT models")

    LANGCHAIN_API_KEY: str | None = Field(default=None, description="LangChain API key for tracing")

    # Agent Configuration
    AGENT_BACKEND: str = Field(
        default="langgraph", description="Which AI agent backend to use: 'openai' or 'langgraph'"
    )

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host address")
    PORT: int = Field(default=8000, description="Server port number")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Database/Data Configuration
    SCHEDULE_DATA_PATH: str = Field(
        default="data/university_schedule.json", description="Path to schedule data file"
    )

    # Model Configuration
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model to use")

    OPENAI_API_BASE: str | None = Field(default=None, description="OpenAI API base URL")

    LANGCHAIN_PROJECT: str = Field(
        default="cool_school_assistant", description="LangChain project name for tracing"
    )

    # LLM Parameters
    LLM_TEMPERATURE: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Sampling temperature for model responses"
    )

    LLM_MAX_TOKENS: int | None = Field(
        default=None, ge=1, le=32000, description="Maximum tokens in model response"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def get_llm_config():
    """Get LLM configuration from settings (backward compatibility)."""
    return {
        "model": settings.OPENAI_MODEL,
        "openai_api_key": settings.OPENAI_API_KEY,
        "openai_api_base": settings.OPENAI_API_BASE,
    }


def get_app():
    """Lazy import of the app to avoid circular dependencies."""
    if settings.AGENT_BACKEND == "langgraph":
        from .langgraph_server import app

        return app
    elif settings.AGENT_BACKEND == "openai":
        from .openai_server import app

        return app
    else:
        raise ValueError(f"Unknown agent backend: {settings.AGENT_BACKEND}")


def reload_settings() -> Settings:
    """Reload settings from environment variables and return new instance."""
    global settings
    settings = Settings()
    return settings


# Backward compatibility
AGENT_BACKEND = settings.AGENT_BACKEND

# Export functions and settings
__all__ = [
    "settings",
    "get_settings",
    "get_llm_config",
    "get_app",
    "AGENT_BACKEND",
    "reload_settings",
]
