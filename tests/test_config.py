import pytest
from unittest.mock import patch, MagicMock
import os

from app.core.config import Settings

class TestConfig:
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_openai_key",
        "GROQ_API_KEY": "test_groq_key",
        "DEFAULT_PROVIDER": "openai",
        "DEFAULT_MODEL": "gpt-4"
    })
    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        # Create settings instance
        settings = Settings()
        
        # Verify settings
        assert settings.OPENAI_API_KEY == "test_openai_key"
        assert settings.GROQ_API_KEY == "test_groq_key"
        assert settings.DEFAULT_PROVIDER == "openai"
        assert settings.DEFAULT_MODEL == "gpt-4"
    
    @patch.dict(os.environ, {})
    def test_settings_defaults(self):
        """Test default settings when environment variables are not set."""
        # Create settings instance
        settings = Settings()
        
        # Verify default settings
        assert settings.OPENAI_API_KEY == ""
        assert settings.GROQ_API_KEY == ""
        assert settings.DEFAULT_PROVIDER == "groq"
        assert settings.DEFAULT_MODEL == "mixtral-8x7b-32768"
    
    @patch.dict(os.environ, {
        "DEFAULT_PROVIDER": "invalid_provider"
    })
    def test_settings_validation(self):
        """Test validation of settings."""
        # Attempt to create settings with invalid provider
        with pytest.raises(ValueError):
            settings = Settings()
    
    @patch("builtins.open")
    @patch("app.core.config.logger")
    def test_settings_logging(self, mock_logger, mock_open):
        """Test that settings are properly logged."""
        # Mock open to avoid reading actual .env file
        mock_open.side_effect = FileNotFoundError
        
        # Create settings
        settings = Settings()
        
        # Verify logging calls
        mock_logger.info.assert_any_call(f"Loaded settings with provider: {settings.DEFAULT_PROVIDER}")
        mock_logger.info.assert_any_call(f"OpenAI API key present: {bool(settings.OPENAI_API_KEY)}")
        mock_logger.info.assert_any_call(f"Groq API key present: {bool(settings.GROQ_API_KEY)}")
        mock_logger.info.assert_any_call(f"Default model: {settings.DEFAULT_MODEL}")
