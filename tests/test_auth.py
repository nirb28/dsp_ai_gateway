"""
Tests for client authentication logic.
"""
import os
import sys
import hashlib
import pytest
from fastapi import HTTPException

# Import the required modules
from app.clients.auth import ClientManager

class TestClientAuthentication:
    """Test cases for client authentication."""

    def setup_method(self):
        """Set up the test environment."""
        self.client_manager = ClientManager()
    
    def test_loaded_clients(self):
        """Test that clients are loaded correctly."""
        # Check that we have at least one client
        assert len(self.client_manager.clients) > 0
        
        # Check that test_client is loaded
        assert "test_client" in self.client_manager.clients
        
        # Check that test_client has a secret hash
        assert self.client_manager.clients["test_client"].client_secret_hash is not None
    
    def test_valid_authentication(self):
        """Test authentication with valid credentials."""
        # Authenticate with valid credentials
        client_config = self.client_manager.authenticate_client("test_client", "password")
        
        # Check that authentication succeeded
        assert client_config is not None
        assert client_config.client_id == "test_client"
        assert client_config.name == "Test Client"
    
    def test_invalid_secret(self):
        """Test authentication with invalid secret."""
        # Authenticate with invalid secret
        with pytest.raises(HTTPException) as excinfo:
            self.client_manager.authenticate_client("test_client", "wrong_password")
        
        # Check that authentication failed with the correct error
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid client credentials"
    
    def test_nonexistent_client(self):
        """Test authentication with nonexistent client."""
        # Authenticate with nonexistent client
        with pytest.raises(HTTPException) as excinfo:
            self.client_manager.authenticate_client("nonexistent_client", "password")
        
        # Check that authentication failed with the correct error
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid client credentials"
    
    def test_missing_secret_hash(self):
        """Test authentication for a client with missing secret hash."""
        # Create a test client without a secret hash
        original_client = None
        if "groq_only_client" in self.client_manager.clients:
            # Save the original client config
            original_client = self.client_manager.clients["groq_only_client"]
            
            # Temporarily remove the secret hash
            original_hash = original_client.client_secret_hash
            original_client.client_secret_hash = None
            
            # Authenticate with the client
            with pytest.raises(HTTPException) as excinfo:
                self.client_manager.authenticate_client("groq_only_client", "any_password")
            
            # Check that authentication failed with the correct error
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Invalid client credentials"
            
            # Restore the original secret hash
            original_client.client_secret_hash = original_hash
