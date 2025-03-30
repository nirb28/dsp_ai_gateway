"""
Utility functions for client authentication testing.
"""
import hashlib
import json
import os
from typing import Dict, Any, Optional

def generate_client_secret_hash(secret: str) -> str:
    """
    Generate a SHA-256 hash for a client secret.
    
    Args:
        secret: The plain text secret to hash
        
    Returns:
        str: The SHA-256 hash of the secret
    """
    return hashlib.sha256(secret.encode()).hexdigest()

def create_test_client_config(
    client_id: str,
    name: str,
    secret: str,
    allowed_providers: list,
    output_dir: str,
    default_provider: str = "groq",
    default_model: str = "mixtral-8x7b-32768",
    max_tokens_limit: int = 2000,
    requests_per_minute: int = 60,
    tokens_per_day: int = 100000,
    allowed_endpoints: Optional[list] = None
) -> Dict[str, Any]:
    """
    Create a test client configuration and save it to a JSON file.
    
    Args:
        client_id: Client ID
        name: Client name
        secret: Client secret (will be hashed)
        allowed_providers: List of allowed providers
        output_dir: Directory to save the client configuration
        default_provider: Default provider
        default_model: Default model
        max_tokens_limit: Maximum tokens limit
        requests_per_minute: Maximum requests per minute
        tokens_per_day: Maximum tokens per day
        allowed_endpoints: List of allowed endpoints
        
    Returns:
        Dict[str, Any]: The client configuration
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set default allowed endpoints if not provided
    if allowed_endpoints is None:
        allowed_endpoints = ["generate", "clients/reload"]
    
    # Create the client configuration
    client_config = {
        "client_id": client_id,
        "name": name,
        "client_secret_hash": generate_client_secret_hash(secret),
        "allowed_providers": allowed_providers,
        "default_provider": default_provider,
        "default_model": default_model,
        "max_tokens_limit": max_tokens_limit,
        "rate_limit": {
            "requests_per_minute": requests_per_minute,
            "tokens_per_day": tokens_per_day
        },
        "allowed_endpoints": allowed_endpoints,
        "created_at": "2025-03-30T18:00:00-04:00",
        "updated_at": "2025-03-30T18:00:00-04:00"
    }
    
    # Save the client configuration to a JSON file
    output_file = os.path.join(output_dir, f"{client_id}.json")
    with open(output_file, "w") as f:
        json.dump(client_config, f, indent=4)
    
    return client_config

def print_client_secrets_table(clients_with_secrets: Dict[str, str]) -> None:
    """
    Print a table of client IDs and their corresponding secret hashes.
    
    Args:
        clients_with_secrets: Dictionary mapping client IDs to secrets
    """
    print("\nClient Secrets Table:")
    print("-" * 100)
    print(f"{'Client ID':<20} | {'Secret':<20} | {'Secret Hash':<60}")
    print("-" * 100)
    
    for client_id, secret in clients_with_secrets.items():
        secret_hash = generate_client_secret_hash(secret)
        print(f"{client_id:<20} | {secret:<20} | {secret_hash}")
    
    print("-" * 100)

if __name__ == "__main__":
    # Example usage
    clients = {
        "test_client": "password",
        "groq_only_client": "groq_password",
        "openai_only_client": "openai_password"
    }
    
    print_client_secrets_table(clients)
