"""
Tests for API authentication endpoints.
"""
import os
import json
import pytest
import hashlib
import shutil
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.core.config import settings
from app.clients.auth import client_manager
from app.schemas.base import ClientConfig

# Test constants
TEST_CLIENT_ID = "test_api_client"
TEST_CLIENT_SECRET = "test_api_password"
TEST_CLIENT_NAME = "Test API Client"
TEST_TEMP_DIR = "temp_configs"

def generate_secret_hash(secret):
    """Generate a SHA-256 hash for a secret."""
    return hashlib.sha256(secret.encode()).hexdigest()

def create_test_client_config(client_id, name, secret, allowed_providers, output_dir):
    """Create a test client configuration file."""
    default_provider = allowed_providers[0] if allowed_providers else None
    default_model = "mixtral-8x7b-32768" if "groq" in allowed_providers else "gpt-3.5-turbo"
    
    client_config = {
        "client_id": client_id,
        "name": name,
        "client_secret_hash": generate_secret_hash(secret),
        "allowed_providers": allowed_providers,
        "default_provider": default_provider,
        "default_model": default_model,
        "max_tokens_limit": 2000,
        "rate_limit": {
            "requests_per_minute": 60,
            "tokens_per_day": 100000
        },
        "allowed_endpoints": ["generate", "clients/reload", "health"],
        "created_at": "2025-03-30T19:00:00-04:00",
        "updated_at": "2025-03-30T19:00:00-04:00"
    }
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the client configuration to a JSON file
    output_file = os.path.join(output_dir, f"{client_id}.json")
    with open(output_file, "w") as f:
        json.dump(client_config, f, indent=4)
    
    return output_file

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app with test client configurations."""
    # Save the original client config directory
    original_config_dir = settings.CLIENT_CONFIG_DIR
    
    # Create a temporary directory for test client configs
    temp_dir = TEST_TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    
    # Set the client config directory to the temporary directory
    settings.CLIENT_CONFIG_DIR = temp_dir
    
    # Create test client configurations
    create_test_client_config(
        client_id=TEST_CLIENT_ID,
        name=TEST_CLIENT_NAME,
        secret=TEST_CLIENT_SECRET,
        allowed_providers=["openai", "groq"],
        output_dir=temp_dir
    )
    
    # Create an OpenAI-only client
    create_test_client_config(
        client_id="openai_only_client",
        name="OpenAI Only Client",
        secret="openai_password",
        allowed_providers=["openai"],
        output_dir=temp_dir
    )
    
    # Create a Groq-only client
    create_test_client_config(
        client_id="groq_only_client",
        name="Groq Only Client",
        secret="groq_password",
        allowed_providers=["groq"],
        output_dir=temp_dir
    )
    
    # Create the FastAPI test client
    client = TestClient(app)
    
    # Reload client configurations to ensure they're loaded
    client_manager.reload_clients()
    
    # Yield the test client for testing
    yield client
    
    # Clean up: restore original config dir and remove temp files
    settings.CLIENT_CONFIG_DIR = original_config_dir
    
    # Clean up the temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def auth_headers():
    """Create authentication headers for different clients."""
    return {
        "test_client": {
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET
        },
        "openai_client": {
            "client_id": "openai_only_client",
            "client_secret": "openai_password"
        },
        "groq_client": {
            "client_id": "groq_only_client",
            "client_secret": "groq_password"
        },
        "invalid": {
            "client_id": TEST_CLIENT_ID,
            "client_secret": "wrong_password"
        },
        "nonexistent": {
            "client_id": "nonexistent_client",
            "client_secret": "password"
        }
    }

class TestAPI:
    """Tests for the API endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Test the health endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_generate_endpoint_with_valid_auth(self, test_client, auth_headers):
        """Test the generate endpoint with valid authentication."""
        # Create a simple generate request
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10
        }
        
        # Send request with valid authentication
        response = test_client.post(
            "/generate",
            json=request_data,
            headers=auth_headers["test_client"]
        )
        
        # Check that the request was authenticated (not checking actual generation)
        assert response.status_code != 401, "Authentication should succeed"
    
    def test_generate_endpoint_with_invalid_auth(self, test_client, auth_headers):
        """Test the generate endpoint with invalid authentication."""
        # Create a simple generate request
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10
        }
        
        # Send request with invalid authentication
        response = test_client.post(
            "/generate",
            json=request_data,
            headers=auth_headers["invalid"]
        )
        
        # Check that authentication failed
        assert response.status_code == 401
        assert "Invalid client credentials" in response.json()["detail"]
    
    def test_generate_endpoint_with_nonexistent_client(self, test_client, auth_headers):
        """Test the generate endpoint with a nonexistent client."""
        # Create a simple generate request
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10
        }
        
        # Send request with nonexistent client
        response = test_client.post(
            "/generate",
            json=request_data,
            headers=auth_headers["nonexistent"]
        )
        
        # Check that authentication failed
        assert response.status_code == 401
        assert "Invalid client credentials" in response.json()["detail"]
    
    def test_generate_endpoint_without_auth(self, test_client):
        """Test the generate endpoint without authentication."""
        # Create a simple generate request
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10
        }
        
        # Send request without authentication
        response = test_client.post(
            "/generate",
            json=request_data
        )
        
        # Check that authentication is required
        assert response.status_code == 422 or response.status_code == 401
    
    def test_openai_provider_with_openai_client(self, test_client, auth_headers):
        """Test using the OpenAI provider with an OpenAI-only client."""
        # Create a generate request with OpenAI provider
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10,
            "provider": "openai"
        }
        
        # Send request with OpenAI client
        response = test_client.post(
            "/generate",
            json=request_data,
            headers=auth_headers["openai_client"]
        )
        
        # Check that the request was authenticated (not checking actual generation)
        assert response.status_code != 401, "Authentication should succeed"
    
    def test_groq_provider_with_openai_client(self, test_client, auth_headers):
        """Test using the Groq provider with an OpenAI-only client."""
        # Create a generate request with Groq provider
        request_data = {
            "prompt": "Hello, world!",
            "max_tokens": 10,
            "provider": "groq"
        }
        
        # Send request with OpenAI client
        response = test_client.post(
            "/generate",
            json=request_data,
            headers=auth_headers["openai_client"]
        )
        
        # Check that the request was rejected due to provider restrictions
        assert response.status_code == 403
        assert "not allowed to use provider" in response.json()["detail"].lower()
    
    def test_reload_clients_endpoint(self, test_client, auth_headers):
        """Test the reload clients endpoint."""
        # Send request to reload clients
        response = test_client.get(
            "/clients/reload",
            headers=auth_headers["test_client"]
        )
        
        # Check that the request was successful
        assert response.status_code == 200
        assert "message" in response.json() or "count" in response.json()
    
    def test_reload_clients_with_invalid_auth(self, test_client, auth_headers):
        """Test the reload clients endpoint with invalid authentication."""
        # Send request with invalid authentication
        response = test_client.get(
            "/clients/reload",
            headers=auth_headers["invalid"]
        )
        
        # Check that authentication failed
        assert response.status_code == 401
        assert "Invalid client credentials" in response.json()["detail"]
    
    def test_unauthorized_endpoint(self, test_client, auth_headers):
        """Test accessing an endpoint that the client is not authorized to use."""
        # Create a client with limited endpoint permissions
        limited_client_id = "limited_client"
        create_test_client_config(
            client_id=limited_client_id,
            name="Limited Client",
            secret="limited_password",
            allowed_providers=["openai", "groq"],
            output_dir=TEST_TEMP_DIR
        )
        
        # Modify the allowed_endpoints to exclude the reload endpoint
        config_file = os.path.join(TEST_TEMP_DIR, f"{limited_client_id}.json")
        with open(config_file, "r") as f:
            config = json.load(f)
        
        config["allowed_endpoints"] = ["generate"]  # Only allow generate endpoint
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        
        # Reload client configurations
        client_manager.reload_clients()
        
        # Create limited client auth headers
        limited_client_auth = {
            "client_id": limited_client_id,
            "client_secret": "limited_password"
        }
        
        # Send request to reload clients with limited client
        response = test_client.get(
            "/clients/reload",
            headers=limited_client_auth
        )
        
        # Check that the request was rejected due to endpoint restrictions
        assert response.status_code == 403
        assert "not authorized to access endpoint" in response.json()["detail"].lower() or "not have permission to access endpoint" in response.json()["detail"].lower()
