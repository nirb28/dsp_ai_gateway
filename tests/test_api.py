import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import hashlib

from app.main import app
from app.clients.auth import CLIENT_SECRETS

# Create a test client
client = TestClient(app)

# Test client credentials
TEST_CLIENT_ID = "test_client"
TEST_CLIENT_SECRET = "password"  # In a real scenario, use a more secure password

class TestAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Add test client secret (password hashed with sha256)
        CLIENT_SECRETS[TEST_CLIENT_ID] = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        yield
        # Clean up
        if TEST_CLIENT_ID in CLIENT_SECRETS:
            del CLIENT_SECRETS[TEST_CLIENT_ID]
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "docs_url" in response.json()
        assert "redoc_url" in response.json()
    
    @patch("app.models.llm.get_model")
    def test_generate_text(self, mock_get_model):
        """Test generate text endpoint."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.generate.return_value = {
            "text": "This is a test response",
            "model": "mixtral-8x7b-32768",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }
        mock_get_model.return_value = mock_model
        
        # Make request
        response = client.post(
            "/api/v1/generate",
            headers={
                "client_id": TEST_CLIENT_ID,
                "client_secret": TEST_CLIENT_SECRET
            },
            json={
                "prompt": "Test prompt",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["text"] == "This is a test response"
        assert response.json()["model"] == "mixtral-8x7b-32768"
        assert response.json()["usage"] == {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        # Verify model was called with correct parameters
        mock_get_model.assert_called_once()
        mock_model.generate.assert_called_once_with(
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=100
        )
    
    def test_generate_text_invalid_auth(self):
        """Test generate text endpoint with invalid authentication."""
        # Make request with invalid client secret
        response = client.post(
            "/api/v1/generate",
            headers={
                "client_id": TEST_CLIENT_ID,
                "client_secret": "wrong_password"
            },
            json={
                "prompt": "Test prompt",
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        
        # Verify response
        assert response.status_code == 401
        assert "Invalid client credentials" in response.json()["detail"]
    
    def test_generate_text_max_tokens_exceeded(self):
        """Test generate text endpoint with max tokens exceeded."""
        # Make request with max tokens exceeding limit
        response = client.post(
            "/api/v1/generate",
            headers={
                "client_id": TEST_CLIENT_ID,
                "client_secret": TEST_CLIENT_SECRET
            },
            json={
                "prompt": "Test prompt",
                "temperature": 0.7,
                "max_tokens": 3000  # Exceeds the 2000 limit
            }
        )
        
        # Verify response
        assert response.status_code == 400
        assert "Max tokens limit exceeded" in response.json()["detail"]
    
    @patch("app.clients.auth.ClientManager.reload_clients")
    def test_reload_clients(self, mock_reload_clients):
        """Test reload clients endpoint."""
        # Mock reload_clients to return 3
        mock_reload_clients.return_value = 3
        
        # Make request
        response = client.get(
            "/api/v1/clients/reload",
            headers={
                "client_id": TEST_CLIENT_ID,
                "client_secret": TEST_CLIENT_SECRET
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully reloaded 3 client configurations"
        assert response.json()["count"] == 3
        
        # Verify reload_clients was called
        mock_reload_clients.assert_called_once()
