"""
Application configuration using Pydantic BaseSettings.

This module provides type-safe, validated configuration management
with support for environment variables, default values, and validation.
"""

import os
from typing import Literal

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application configuration with environment variable support."""

    # Core Application Settings
    agent_backend: Literal["openai", "langgraph"] = Field(
        default="openai", description="Which AI agent backend to use", env="AGENT_BACKEND"
    )

    debug: bool = Field(default=False, description="Enable debug mode", env="DEBUG")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level", env="LOG_LEVEL"
    )

    # API Configuration
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key for GPT models", env="OPENAI_API_KEY"
    )

    openai_model: str = Field(
        default="gpt-4", description="OpenAI model to use", env="OPENAI_MODEL"
    )

    # LangChain/LangGraph Configuration
    langchain_api_key: str | None = Field(
        default=None, description="LangChain API key for tracing", env="LANGCHAIN_API_KEY"
    )

    langchain_project: str = Field(
        default="cool_school_assistant",
        description="LangChain project name for tracing",
        env="LANGCHAIN_PROJECT",
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host address", env="HOST")

    port: int = Field(default=8000, ge=1, le=65535, description="Server port number", env="PORT")

    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins (comma-separated or '*' for all)",
        env="CORS_ORIGINS",
    )

    # Data Configuration
    schedule_data_path: str = Field(
        default="data/university_schedule.json",
        description="Path to schedule data file",
        env="SCHEDULE_DATA_PATH",
    )

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, v: str) -> str:
        """Validate OpenAI model name."""
        valid_models = {
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
        }
        if v not in valid_models:
            # Allow any model that starts with gpt- for future compatibility
            if not v.startswith("gpt-"):
                raise ValueError(
                    f'Invalid OpenAI model: {v}. Must be one of {valid_models} or start with "gpt-"'
                )
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v) -> list[str]:
        """Parse and validate CORS origins."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("schedule_data_path")
    @classmethod
    def validate_schedule_data_path(cls, v: str) -> str:
        """Validate schedule data path exists."""
        if not os.path.exists(v):
            # Don't raise error - just warn, as file might be created later
            print(f"Warning: Schedule data file not found at {v}")
        return v

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )


class LLMConfig(BaseSettings):
    """Configuration specific to Language Model settings."""

    # Model Parameters
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for model responses",
        env="LLM_TEMPERATURE",
    )

    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=32000,
        description="Maximum tokens in model response",
        env="LLM_MAX_TOKENS",
    )

    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter", env="LLM_TOP_P"
    )

    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty for reducing repetition",
        env="LLM_FREQUENCY_PENALTY",
    )

    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty for encouraging diversity",
        env="LLM_PRESENCE_PENALTY",
    )

    # Streaming Configuration
    stream: bool = Field(default=True, description="Enable streaming responses", env="LLM_STREAM")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )


# Global settings instances
app_settings = AppSettings()
llm_config = LLMConfig()

# Backward compatibility alias
Settings = AppSettings


def get_app_settings() -> AppSettings:
    """Get the global application settings."""
    return app_settings


def get_settings() -> AppSettings:
    """Alias for get_app_settings for backward compatibility."""
    return get_app_settings()


def get_llm_config() -> LLMConfig:
    """Get the global LLM configuration."""
    return llm_config


def reload_settings() -> None:
    """Reload settings from environment variables."""
    global app_settings, llm_config
    app_settings = AppSettings()
    llm_config = LLMConfig()


# Backward compatibility functions for existing code
def get_llm_config_dict() -> dict:
    """
    Get LLM configuration as a dictionary for backward compatibility.

    Returns:
        Dictionary with LLM configuration parameters.
    """
    config = get_llm_config()
    result = {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "frequency_penalty": config.frequency_penalty,
        "presence_penalty": config.presence_penalty,
        "stream": config.stream,
    }

    if config.max_tokens is not None:
        result["max_tokens"] = config.max_tokens

    return result


def get_app():
    """
    Get the FastAPI application instance based on configured backend.

    Returns:
        FastAPI application instance for the selected backend.
    """
    settings = get_app_settings()

    if settings.agent_backend == "openai":
        from .openai_server import app

        return app
    elif settings.agent_backend == "langgraph":
        from .langgraph_server import app

        return app
    else:
        raise ValueError(f"Unknown agent backend: {settings.agent_backend}")


def get_app_module() -> str:
    """
    Get the application module name based on configured backend.

    Returns:
        Module name string for the selected backend (for uvicorn command line).
    """
    settings = get_app_settings()

    if settings.agent_backend == "openai":
        return "app.openai_server:app"
    elif settings.agent_backend == "langgraph":
        return "app.langgraph_server:app"
    else:
        raise ValueError(f"Unknown agent backend: {settings.agent_backend}")


# Example usage and validation
if __name__ == "__main__":
    print("Application Settings:")
    settings = get_app_settings()
    print(f"  Backend: {settings.agent_backend}")
    print(f"  Debug: {settings.debug}")
    print(f"  Host: {settings.host}:{settings.port}")
    print(f"  CORS Origins: {settings.cors_origins}")

    print("\nLLM Configuration:")
    llm = get_llm_config()
    print(f"  Temperature: {llm.temperature}")
    print(f"  Stream: {llm.stream}")
    print(f"  Max Tokens: {llm.max_tokens}")

    print(f"\nSelected App Module: {get_app()}")
    print(f"LLM Config Dict: {get_llm_config_dict()}")
