import debug_imports  # Import the debug helper to fix import issues

import pytest
from unittest.mock import patch, MagicMock
import asyncio
import os

from app.models.llm import BaseModel, OpenAIModel, GroqModel, get_model
from app.core.config import settings

class TestModels:
    def test_base_model(self):
        """Test BaseModel class."""
        # Create base model
        model = BaseModel("test_model")
        
        # Verify model name
        assert model.model_name == "test_model"
        
        # Verify generate method raises NotImplementedError
        with pytest.raises(NotImplementedError):
            asyncio.run(model.generate("Test prompt"))
    
    @patch("app.core.config.settings.OPENAI_API_KEY", "sk-test-key-for-openai")
    @patch("openai.OpenAI")
    def test_openai_model(self, mock_openai_client):
        """Test OpenAIModel class."""
        # Print debug information
        print("\nDEBUG: Starting OpenAI model test")
        print(f"DEBUG: OPENAI_API_KEY in settings: {settings.OPENAI_API_KEY}")
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_client.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        # Set up mock client to return mock response
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create OpenAI model
        model = OpenAIModel("gpt-4")
        
        # Generate text
        response = asyncio.run(model.generate("Test prompt", temperature=0.5, max_tokens=200))
        
        # Verify response
        assert response["text"] == "OpenAI response"
        assert response["model"] == "gpt-4"
        assert response["usage"] == {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        # Verify client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.5,
            max_tokens=200
        )
    
    @patch("app.core.config.settings.GROQ_API_KEY", "gsk-test-key-for-groq")
    @patch("groq.Groq")
    def test_groq_model(self, mock_groq_client):
        """Test GroqModel class."""
        # Print debug information
        print("\nDEBUG: Starting Groq model test")
        print(f"DEBUG: GROQ_API_KEY in settings: {settings.GROQ_API_KEY}")
        
        # Mock Groq client
        mock_client = MagicMock()
        mock_groq_client.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Groq response"
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 40
        
        # Set up mock client to return mock response
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create Groq model
        model = GroqModel("mixtral-8x7b-32768")
        
        # Generate text
        response = asyncio.run(model.generate("Test prompt", temperature=0.8, max_tokens=150))
        
        # Verify response
        assert response["text"] == "Groq response"
        assert response["model"] == "mixtral-8x7b-32768"
        assert response["usage"] == {"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40}
        
        # Verify client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.8,
            max_tokens=150
        )
    
    @patch("app.models.llm.OpenAIModel")
    @patch("app.models.llm.GroqModel")
    def test_get_model_openai(self, mock_groq_model, mock_openai_model):
        """Test get_model function with OpenAI provider."""
        # Create model
        model = get_model("openai", "gpt-4")
        
        # Verify OpenAIModel was created with correct model name
        mock_openai_model.assert_called_once_with("gpt-4")
        
        # Verify GroqModel was not created
        mock_groq_model.assert_not_called()
    
    @patch("app.models.llm.OpenAIModel")
    @patch("app.models.llm.GroqModel")
    def test_get_model_groq(self, mock_groq_model, mock_openai_model):
        """Test get_model function with Groq provider."""
        # Create model
        model = get_model("groq", "mixtral-8x7b-32768")
        
        # Verify GroqModel was created with correct model name
        mock_groq_model.assert_called_once_with("mixtral-8x7b-32768")
        
        # Verify OpenAIModel was not created
        mock_openai_model.assert_not_called()
    
    @patch("app.models.llm.OpenAIModel")
    @patch("app.models.llm.GroqModel")
    def test_get_model_default(self, mock_groq_model, mock_openai_model):
        """Test get_model function with default provider and model."""
        # Create model with default provider and model
        model = get_model()
        
        # Verify correct model was created based on default provider
        if settings.DEFAULT_PROVIDER == "openai":
            mock_openai_model.assert_called_once_with(settings.DEFAULT_MODEL)
            mock_groq_model.assert_not_called()
        else:  # groq
            mock_groq_model.assert_called_once_with(settings.DEFAULT_MODEL)
            mock_openai_model.assert_not_called()
    
    def test_get_model_invalid_provider(self):
        """Test get_model function with invalid provider."""
        # Attempt to create model with invalid provider
        with pytest.raises(ValueError) as exc_info:
            get_model("invalid_provider")
        
        # Verify exception message
        assert "Invalid provider: invalid_provider" in str(exc_info.value)
