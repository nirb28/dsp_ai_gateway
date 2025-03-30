import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import os
import hashlib

from app.main import app
from app.clients.auth import CLIENT_SECRETS, client_manager

# Create a test client
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Set up the test environment with test clients and configs."""
    # Create test client configs directory if it doesn't exist
    os.makedirs("temp_integration_configs", exist_ok=True)
    
    # Add test clients to secrets
    test_secrets = {
        "integration_client": hashlib.sha256("integration_password".encode()).hexdigest()
    }
    
    # Create test client config
    integration_client_config = {
        "client_id": "integration_client",
        "name": "Integration Test Client",
        "allowed_providers": ["openai", "groq"],
        "default_provider": "groq",
        "default_model": "mixtral-8x7b-32768",
        "max_tokens_limit": 2000,
        "rate_limit": {
            "requests_per_minute": 60,
            "tokens_per_day": 100000
        },
        "allowed_endpoints": ["generate", "clients/reload"],
        "created_at": "2025-03-16T19:40:00-04:00",
        "updated_at": "2025-03-16T19:40:00-04:00"
    }
    
    # Write config to file
    with open(os.path.join("temp_integration_configs", "integration_client.json"), "w") as f:
        json.dump(integration_client_config, f)
    
    # Add test client to secrets
    for client_id, secret in test_secrets.items():
        CLIENT_SECRETS[client_id] = secret
    
    # Patch the client config directory
    with patch("app.core.config.settings.CLIENT_CONFIG_DIR", "temp_integration_configs"):
        # Reload client configurations
        client_manager.reload_clients()
        
        yield
    
    # Clean up test secrets
    for client_id in test_secrets:
        if client_id in CLIENT_SECRETS:
            del CLIENT_SECRETS[client_id]
    
    # Remove test config file
    if os.path.exists(os.path.join("temp_integration_configs", "integration_client.json")):
        os.remove(os.path.join("temp_integration_configs", "integration_client.json"))
    
    # Remove test config directory
    if os.path.exists("temp_integration_configs"):
        os.rmdir("temp_integration_configs")

class TestIntegration:
    @patch("app.models.llm.get_model")
    def test_complete_flow(self, mock_get_model):
        """Test the complete flow from authentication to response generation."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.generate.return_value = {
            "text": "This is an integration test response",
            "model": "mixtral-8x7b-32768",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }
        mock_get_model.return_value = mock_model
        
        # Make request with valid authentication
        response = client.post(
            "/api/v1/generate", 
            headers={
                "client_id": "integration_client",
                "client_secret": "integration_password"
            },
            json={
                "prompt": "Integration test prompt",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["text"] == "This is an integration test response"
        assert response.json()["model"] == "mixtral-8x7b-32768"
        assert response.json()["usage"] == {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        # Verify model was called with correct parameters
        mock_get_model.assert_called_once()
        mock_model.generate.assert_called_once_with(
            prompt="Integration test prompt",
            temperature=0.7,
            max_tokens=100
        )
    
    def test_invalid_auth_flow(self):
        """Test the flow with invalid authentication."""
        # Make request with invalid authentication
        response = client.post(
            "/api/v1/generate", 
            headers={
                "client_id": "integration_client",
                "client_secret": "wrong_password"
            },
            json={
                "prompt": "Integration test prompt",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        # Verify response
        assert response.status_code == 401
        assert "Invalid client credentials" in response.json()["detail"]
    
    def test_unauthorized_endpoint_flow(self):
        """Test the flow with unauthorized endpoint."""
        # Create a mock endpoint that doesn't exist in allowed_endpoints
        response = client.post(
            "/api/v1/unauthorized_endpoint", 
            headers={
                "client_id": "integration_client",
                "client_secret": "integration_password"
            },
            json={}
        )
        
        # Verify response
        assert response.status_code == 404  # FastAPI returns 404 for undefined routes
    
    @patch("app.models.llm.get_model")
    def test_max_tokens_limit_flow(self, mock_get_model):
        """Test the flow with max tokens limit exceeded."""
        # Make request with max tokens exceeding limit
        response = client.post(
            "/api/v1/generate", 
            headers={
                "client_id": "integration_client",
                "client_secret": "integration_password"
            },
            json={
                "prompt": "Integration test prompt",
                "temperature": 0.7,
                "max_tokens": 3000  # Exceeds the 2000 limit
            }
        )
        
        # Verify response
        assert response.status_code == 400
        assert "Max tokens limit exceeded" in response.json()["detail"]
        
        # Verify model was not called
        mock_get_model.assert_not_called()
    
    @patch("app.clients.auth.ClientManager.reload_clients")
    def test_reload_clients_flow(self, mock_reload_clients):
        """Test the flow for reloading client configurations."""
        # Mock reload_clients to return 1
        mock_reload_clients.return_value = 1
        
        # Make request
        response = client.get(
            "/api/v1/clients/reload", 
            headers={
                "client_id": "integration_client",
                "client_secret": "integration_password"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully reloaded 1 client configurations"
        assert response.json()["count"] == 1
        
        # Verify reload_clients was called
        mock_reload_clients.assert_called_once()
