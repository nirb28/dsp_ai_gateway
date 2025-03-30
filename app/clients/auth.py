import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, Depends, Header
from app.core.config import settings
from app.schemas.base import ClientConfig

# Configure logging
logger = logging.getLogger(__name__)

class ClientManager:
    """Manager for client authentication and configuration."""
    
    def __init__(self):
        """Initialize the client manager."""
        self.clients: Dict[str, ClientConfig] = {}
        self.load_clients()
    
    def load_clients(self) -> int:
        """Load client configurations from JSON files.
        
        Returns:
            int: Number of clients loaded
        """
        client_count = 0
        
        # Create client config directory if it doesn't exist
        os.makedirs(settings.CLIENT_CONFIG_DIR, exist_ok=True)
        
        # Load client configurations from JSON files
        for filename in os.listdir(settings.CLIENT_CONFIG_DIR):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(settings.CLIENT_CONFIG_DIR, filename)
                    with open(file_path, "r") as f:
                        client_data = json.load(f)
                        client_config = ClientConfig(**client_data)
                        self.clients[client_config.client_id] = client_config
                        client_count += 1
                        logger.info(f"Loaded client configuration: {client_config.client_id}")
                except Exception as e:
                    logger.error(f"Error loading client configuration from {filename}: {e}")
        
        logger.info(f"Loaded {client_count} client configurations")
        return client_count
    
    def reload_clients(self) -> int:
        """Reload client configurations from JSON files.
        
        Returns:
            int: Number of clients reloaded
        """
        self.clients = {}
        return self.load_clients()
    
    def authenticate_client(self, client_id: str, client_secret: str) -> ClientConfig:
        """Authenticate a client using client ID and secret.
        
        Args:
            client_id: Client ID
            client_secret: Client secret
        
        Returns:
            ClientConfig: Client configuration
        
        Raises:
            HTTPException: If authentication fails
        """
        # Step 1: Check if client configuration exists
        if client_id not in self.clients:
            logger.warning(f"Client configuration not found: {client_id}")
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        client_config = self.clients[client_id]
        
        # Step 2: Validate the provided secret
        # Hash the provided secret
        hashed_secret = hashlib.sha256(client_secret.encode()).hexdigest()
        
        # Check if the client has a secret hash and if the hashed secret matches
        if not client_config.client_secret_hash or hashed_secret != client_config.client_secret_hash:
            logger.warning(f"Invalid credentials provided for client: {client_id}")
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        # Authentication successful
        logger.debug(f"Client authenticated successfully: {client_id}")
        return client_config
    
    def check_endpoint_permission(self, client_config: ClientConfig, endpoint: str) -> bool:
        """Check if a client has permission to access an endpoint.
        
        Args:
            client_config: Client configuration
            endpoint: Endpoint path
        
        Returns:
            bool: True if client has permission, False otherwise
        """
        return endpoint in client_config.allowed_endpoints
    
    def check_provider_permission(self, client_config: ClientConfig, provider: str) -> bool:
        """Check if a client has permission to use a provider.
        
        Args:
            client_config: Client configuration
            provider: Provider name
        
        Returns:
            bool: True if client has permission, False otherwise
        """
        return provider in client_config.allowed_providers
    
    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """Get client configuration by client ID.
        
        Args:
            client_id: Client ID
        
        Returns:
            Optional[ClientConfig]: Client configuration or None if not found
        """
        return self.clients.get(client_id)

# Create global client manager
client_manager = ClientManager()

async def get_client_auth(
    client_id: str = Header(...),
    client_secret: str = Header(...),
) -> ClientConfig:
    """Dependency for client authentication.
    
    Args:
        client_id: Client ID from header
        client_secret: Client secret from header
    
    Returns:
        ClientConfig: Client configuration
    
    Raises:
        HTTPException: If authentication fails
    """
    return client_manager.authenticate_client(client_id, client_secret)

async def check_endpoint_access(
    endpoint: str,
    client_config: ClientConfig = Depends(get_client_auth),
) -> None:
    """Dependency for checking endpoint access.
    
    Args:
        endpoint: Endpoint path
        client_config: Client configuration
    
    Raises:
        HTTPException: If client does not have permission to access the endpoint
    """
    if not client_manager.check_endpoint_permission(client_config, endpoint):
        logger.warning(f"Client {client_config.client_id} attempted to access unauthorized endpoint: {endpoint}")
        raise HTTPException(status_code=403, detail=f"Client does not have permission to access endpoint: {endpoint}")

async def check_provider_access(
    provider: str,
    client_config: ClientConfig = Depends(get_client_auth),
) -> None:
    """Dependency for checking provider access.
    
    Args:
        provider: Provider name
        client_config: Client configuration
    
    Raises:
        HTTPException: If client does not have permission to use the provider
    """
    if not client_manager.check_provider_permission(client_config, provider):
        logger.warning(f"Client {client_config.client_id} attempted to use unauthorized provider: {provider}")
        raise HTTPException(status_code=403, detail=f"Client does not have permission to use provider: {provider}")
