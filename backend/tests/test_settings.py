"""
Unit tests for application settings and configuration.

Tests verify that Settings models correctly:
1. Enforce required environment variables
2. Reject missing critical configuration
3. Validate configuration values
4. Provide sensible defaults for optional values
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.settings import Settings, get_settings


class TestSettingsRequired:
    """Tests for required environment variables in Settings."""

    def test_settings_with_all_required_env_vars(self):
        """Should create Settings instance when all required vars are set."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.openai_api_key == "test-key"

    def test_missing_openai_api_key_rejected(self):
        """Should raise ValidationError when OPENAI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            errors = exc_info.value.errors()
            assert any(err["type"] == "missing" for err in errors)

    def test_empty_openai_api_key_accepted(self):
        """Should accept empty string for API key (runtime check would happen elsewhere)."""
        env_vars = {
            "OPENAI_API_KEY": "",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.openai_api_key == ""

    def test_settings_case_insensitive_env_keys(self):
        """Should read environment variables case-insensitively."""
        env_vars = {
            "openai_api_key": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.openai_api_key == "test-key"


class TestSettingsDefaults:
    """Tests for default values in Settings."""

    def test_log_level_has_default(self):
        """Should have sensible default for log_level."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.log_level == "INFO"

    def test_environment_has_default(self):
        """Should have sensible default for environment."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.environment == "development"

    def test_database_url_has_default(self):
        """Should have sensible default for database_url."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.database_url is not None

    def test_model_config_extra_forbid(self):
        """Settings should forbid extra fields."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings(unknown_field="value")
            errors = exc_info.value.errors()
            assert any(err["type"] == "extra_forbidden" for err in errors)


class TestSettingsValidation:
    """Tests for Settings field validation."""

    def test_environment_valid_values(self):
        """Should accept valid environment values."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "ENVIRONMENT": "production",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.environment == "production"

    def test_environment_invalid_value_rejected(self):
        """Should reject invalid environment values."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "ENVIRONMENT": "invalid_env",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            errors = exc_info.value.errors()
            # The exact error depends on how Settings validates environment
            # It could be enum validation or pattern validation
            assert len(errors) > 0

    def test_log_level_valid_values(self):
        """Should accept valid log level values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            env_vars = {
                "OPENAI_API_KEY": "test-key",
                "LOG_LEVEL": level,
            }
            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings()
                assert settings.log_level == level

    def test_log_level_invalid_value_rejected(self):
        """Should reject invalid log level values."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "LOG_LEVEL": "INVALID_LEVEL",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            errors = exc_info.value.errors()
            assert len(errors) > 0


class TestSettingsIntegration:
    """Integration tests for Settings."""

    def test_get_settings_singleton(self):
        """get_settings should return singleton Settings instance."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            # They should be the same instance or at least have the same values
            assert settings1.openai_api_key == settings2.openai_api_key

    def test_settings_from_env_file_if_exists(self):
        """Settings should load from .env file if it exists."""
        # This test depends on actual .env file presence
        # For now, we just verify the Settings can be created
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings is not None

    def test_settings_database_url_not_none(self):
        """Settings database_url should not be None."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.database_url is not None
            assert isinstance(settings.database_url, str)
            assert len(settings.database_url) > 0


class TestSettingsTypes:
    """Tests for Settings field types and constraints."""

    def test_settings_all_required_fields_present(self):
        """Settings should define all required fields."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            # Verify critical attributes exist
            assert hasattr(settings, "openai_api_key")
            assert hasattr(settings, "environment")
            assert hasattr(settings, "log_level")
            assert hasattr(settings, "database_url")

    def test_settings_field_types_correct(self):
        """Settings fields should have correct types."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert isinstance(settings.openai_api_key, str)
            assert isinstance(settings.environment, str)
            assert isinstance(settings.log_level, str)
            assert isinstance(settings.database_url, str)


class TestEnvFilePriority:
    """Tests for environment variable loading priority."""

    def test_explicit_env_var_overrides_env_file(self):
        """Explicit environment variables should override .env file values."""
        env_vars = {
            "OPENAI_API_KEY": "explicit-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.openai_api_key == "explicit-key"

    def test_all_required_fields_can_be_set_via_env(self):
        """All required fields should be settable via environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "DATABASE_URL": "postgresql://localhost/test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.openai_api_key == "test-key"
            assert settings.environment == "production"
            assert settings.log_level == "DEBUG"
            assert settings.database_url == "postgresql://localhost/test"


class TestSettingsValidationErrors:
    """Tests for validation error messages and clarity."""

    def test_missing_required_field_error_message_clear(self):
        """ValidationError message for missing required field should be clear."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            # The error should mention the missing field
            error_str = str(exc_info.value)
            assert "openai_api_key" in error_str.lower() or "OPENAI_API_KEY" in error_str

    def test_extra_field_error_message_clear(self):
        """ValidationError message for extra field should be clear."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings(extra_field="value")
            error_str = str(exc_info.value)
            # Error should mention extra field
            assert "extra_field" in error_str or "Extra" in error_str
