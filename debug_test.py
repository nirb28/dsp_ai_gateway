"""
Debug script for running a specific test with detailed error output.
"""
import os
import sys
import traceback
from fastapi.testclient import TestClient
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from app.main import app
from app.core.config import settings
from app.clients.auth import client_manager
from tests.test_api_auth import create_test_client_config, TEST_TEMP_DIR, TEST_CLIENT_ID, TEST_CLIENT_SECRET

def setup_test_environment():
    """Set up the test environment."""
    # Create a temporary directory for test client configs
    temp_dir = TEST_TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    
    # Set the client config directory to the temporary directory
    settings.CLIENT_CONFIG_DIR = temp_dir
    
    # Create test client configurations
    create_test_client_config(
        client_id=TEST_CLIENT_ID,
        name="Test API Client",
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
    
    # Reload client configurations
    client_manager.reload_clients()
    
    # Create the FastAPI test client
    client = TestClient(app)
    
    return client

def debug_test_reload_clients_endpoint():
    """Debug the reload clients endpoint test."""
    print("\n=== Testing reload clients endpoint ===")
    client = setup_test_environment()
    
    try:
        # Create auth headers
        headers = {
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET
        }
        
        # Print client manager state
        print(f"Client manager has {len(client_manager.clients)} clients loaded")
        print(f"Client IDs: {list(client_manager.clients.keys())}")
        
        # Check if the test client exists in the client manager
        if TEST_CLIENT_ID in client_manager.clients:
            print(f"Test client {TEST_CLIENT_ID} is in the client manager")
        else:
            print(f"Test client {TEST_CLIENT_ID} is NOT in the client manager")
        
        # Send request
        print("Sending request to /clients/reload...")
        response = client.post(
            "/clients/reload",
            headers=headers
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"Response JSON: {response_json}")
            
            # Check for expected keys
            if "clients_loaded" in response_json:
                print("Found 'clients_loaded' key in response")
            elif "count" in response_json:
                print("Found 'count' key in response")
            elif "message" in response_json:
                print("Found 'message' key in response")
            else:
                print(f"Expected keys not found in response. Available keys: {list(response_json.keys())}")
        
        print("Test completed")
    except Exception as e:
        print(f"Test FAILED with exception: {e}")
        traceback.print_exc()

def debug_test_endpoints():
    """Debug the API endpoints."""
    print("\n=== Checking available endpoints ===")
    client = setup_test_environment()
    
    try:
        # Get the OpenAPI schema to see available endpoints
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            schema = response.json()
            print("Available paths:")
            for path in schema.get("paths", {}):
                print(f"  {path}")
        else:
            print(f"Failed to get OpenAPI schema: {response.status_code}")
    except Exception as e:
        print(f"Failed to check endpoints: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Run the debug tests
    print("Starting debug tests...")
    debug_test_endpoints()
    debug_test_reload_clients_endpoint()
    print("\nDebug tests completed.")
