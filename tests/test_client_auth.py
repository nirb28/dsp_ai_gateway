import pytest
import os
import json
import hashlib
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.clients.auth import ClientManager, CLIENT_SECRETS
from app.schemas.base import ClientConfig

# Test client data
TEST_CLIENT_ID = "test_auth_client"
TEST_CLIENT_SECRET = "test_secret"
TEST_CLIENT_HASHED_SECRET = hashlib.sha256(TEST_CLIENT_SECRET.encode()).hexdigest()

# Test client configuration
TEST_CLIENT_CONFIG = {
    "client_id": TEST_CLIENT_ID,
    "name": "Test Auth Client",
    "allowed_providers": ["openai", "groq"],
    "default_provider": "groq",
    "default_model": "mixtral-8x7b-32768",
    "max_tokens_limit": 2000,
    "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_day": 100000
    },
    "allowed_endpoints": ["generate", "clients/reload"],
    "created_at": "2025-03-16T20:30:00-04:00",
    "updated_at": "2025-03-16T20:30:00-04:00"
}

@pytest.fixture
def client_manager():
    """Create a client manager for testing."""
    # Create a temporary client config directory
    os.makedirs("temp_configs", exist_ok=True)
    
    # Create a test client config file
    with open(os.path.join("temp_configs", f"{TEST_CLIENT_ID}.json"), "w") as f:
        json.dump(TEST_CLIENT_CONFIG, f)
    
    # Add test client to secrets
    CLIENT_SECRETS[TEST_CLIENT_ID] = TEST_CLIENT_HASHED_SECRET
    
    # Create client manager with test config directory
    with patch("app.core.config.settings.CLIENT_CONFIG_DIR", "temp_configs"):
        manager = ClientManager()
        yield manager
    
    # Clean up
    os.remove(os.path.join("temp_configs", f"{TEST_CLIENT_ID}.json"))
    os.rmdir("temp_configs")
    
    # Remove test client from secrets
    if TEST_CLIENT_ID in CLIENT_SECRETS:
        del CLIENT_SECRETS[TEST_CLIENT_ID]

class TestClientAuth:
    def test_load_clients(self, client_manager):
        """Test loading client configurations."""
        # Verify client was loaded
        assert TEST_CLIENT_ID in client_manager.clients
        
        # Verify client config
        client_config = client_manager.clients[TEST_CLIENT_ID]
        assert client_config.client_id == TEST_CLIENT_ID
        assert client_config.name == "Test Auth Client"
        assert client_config.allowed_providers == ["openai", "groq"]
        assert client_config.default_provider == "groq"
        assert client_config.default_model == "mixtral-8x7b-32768"
        assert client_config.max_tokens_limit == 2000
        assert client_config.rate_limit.requests_per_minute == 60
        assert client_config.rate_limit.tokens_per_day == 100000
        assert client_config.allowed_endpoints == ["generate", "clients/reload"]
    
    def test_authenticate_client_success(self, client_manager):
        """Test successful client authentication."""
        # Authenticate client
        client_config = client_manager.authenticate_client(TEST_CLIENT_ID, TEST_CLIENT_SECRET)
        
        # Verify client config
        assert client_config.client_id == TEST_CLIENT_ID
    
    def test_authenticate_client_invalid_id(self, client_manager):
        """Test authentication with invalid client ID."""
        # Attempt to authenticate with invalid client ID
        with pytest.raises(HTTPException) as exc_info:
            client_manager.authenticate_client("invalid_client_id", TEST_CLIENT_SECRET)
        
        # Verify exception
        assert exc_info.value.status_code == 401
        assert "Invalid client credentials" in exc_info.value.detail
    
    def test_authenticate_client_invalid_secret(self, client_manager):
        """Test authentication with invalid client secret."""
        # Attempt to authenticate with invalid client secret
        with pytest.raises(HTTPException) as exc_info:
            client_manager.authenticate_client(TEST_CLIENT_ID, "invalid_secret")
        
        # Verify exception
        assert exc_info.value.status_code == 401
        assert "Invalid client credentials" in exc_info.value.detail
    
    def test_check_endpoint_permission(self, client_manager):
        """Test checking endpoint permission."""
        # Get client config
        client_config = client_manager.clients[TEST_CLIENT_ID]
        
        # Check allowed endpoint
        assert client_manager.check_endpoint_permission(client_config, "generate") is True
        
        # Check disallowed endpoint
        assert client_manager.check_endpoint_permission(client_config, "unauthorized_endpoint") is False
    
    def test_check_provider_permission(self, client_manager):
        """Test checking provider permission."""
        # Get client config
        client_config = client_manager.clients[TEST_CLIENT_ID]
        
        # Check allowed provider
        assert client_manager.check_provider_permission(client_config, "openai") is True
        assert client_manager.check_provider_permission(client_config, "groq") is True
        
        # Check disallowed provider
        assert client_manager.check_provider_permission(client_config, "unauthorized_provider") is False
    
    def test_reload_clients(self, client_manager):
        """Test reloading client configurations."""
        # Initial state
        assert TEST_CLIENT_ID in client_manager.clients
        
        # Create a new client config
        new_client_id = "new_test_client"
        new_client_config = TEST_CLIENT_CONFIG.copy()
        new_client_config["client_id"] = new_client_id
        
        # Write new client config to file
        with open(os.path.join("temp_configs", f"{new_client_id}.json"), "w") as f:
            json.dump(new_client_config, f)
        
        # Reload clients
        count = client_manager.reload_clients()
        
        # Verify both clients are loaded
        assert count == 2
        assert TEST_CLIENT_ID in client_manager.clients
        assert new_client_id in client_manager.clients
        
        # Clean up
        os.remove(os.path.join("temp_configs", f"{new_client_id}.json"))
