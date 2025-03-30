"""
Runner script for testing client authentication.
This script can be used to test the authentication system with different clients.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

# Import the required modules
from app.clients.auth import ClientManager
from tests.test_client_auth_utils import generate_client_secret_hash, print_client_secrets_table

# Output file for test results
DEFAULT_OUTPUT_FILE = os.path.join(project_root, "test_results", "client_auth_test_results.txt")

def setup_output_directory():
    """Set up the output directory for test results."""
    output_dir = os.path.join(project_root, "test_results")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def write_to_file(content, output_file):
    """Write content to the output file."""
    with open(output_file, "a") as f:
        f.write(content + "\n")

def write_separator(title, output_file):
    """Write a separator with a title to the file."""
    separator = "=" * 80
    write_to_file("\n" + separator, output_file)
    write_to_file(f" {title} ".center(80, "="), output_file)
    write_to_file(separator, output_file)

def test_authentication(client_id, client_secret, should_succeed, output_file):
    """Test authentication with the given credentials."""
    write_to_file(f"\nTesting authentication for client_id: '{client_id}' with secret: '{client_secret}'", output_file)
    write_to_file(f"Expected result: {'Success' if should_succeed else 'Failure'}", output_file)
    
    try:
        # Get the client configuration
        client_config = client_manager.authenticate_client(client_id, client_secret)
        
        # Authentication succeeded
        write_to_file("Authentication SUCCEEDED", output_file)
        write_to_file(f"  Client name: {client_config.name}", output_file)
        write_to_file(f"  Allowed providers: {client_config.allowed_providers}", output_file)
        
        # Check if this was expected
        if not should_succeed:
            write_to_file("UNEXPECTED SUCCESS - Test FAILED", output_file)
            return False
        
        write_to_file("Test PASSED", output_file)
        return True
    
    except Exception as e:
        # Authentication failed
        write_to_file("Authentication FAILED", output_file)
        write_to_file(f"  Error: {str(e)}", output_file)
        
        # Check if this was expected
        if should_succeed:
            write_to_file("UNEXPECTED FAILURE - Test FAILED", output_file)
            return False
        
        write_to_file("Test PASSED", output_file)
        return True

def run_tests(output_file=DEFAULT_OUTPUT_FILE, clients_to_test=None):
    """Run authentication tests for the specified clients."""
    # Initialize the output file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"Client Authentication Test Results - {datetime.now()}\n")
    
    # Create a client manager
    global client_manager
    client_manager = ClientManager()
    
    write_separator("LOADED CLIENTS", output_file)
    
    # Write the loaded clients
    for client_id, client in client_manager.clients.items():
        write_to_file(f"Client ID: {client_id}", output_file)
        write_to_file(f"  Name: {client.name}", output_file)
        write_to_file(f"  Has secret hash: {'Yes' if client.client_secret_hash else 'No'}", output_file)
        write_to_file(f"  Secret hash: {client.client_secret_hash}", output_file)
        write_to_file(f"  Allowed providers: {client.allowed_providers}", output_file)
        write_to_file("", output_file)
    
    # If no clients specified, test all loaded clients
    if clients_to_test is None:
        clients_to_test = {
            "test_client": "password",
            "groq_only_client": "groq_password",
            "openai_only_client": "openai_password"
        }
    
    write_separator("AUTHENTICATION TESTS", output_file)
    
    # Test cases
    test_cases = []
    
    # Add test cases for valid credentials
    for client_id, client_secret in clients_to_test.items():
        if client_id in client_manager.clients:
            test_cases.append({
                "name": f"Valid credentials ({client_id})",
                "client_id": client_id,
                "client_secret": client_secret,
                "should_succeed": True
            })
            
            # Also add a test case for invalid credentials
            test_cases.append({
                "name": f"Invalid credentials ({client_id})",
                "client_id": client_id,
                "client_secret": f"wrong_{client_secret}",
                "should_succeed": False
            })
    
    # Add test case for non-existent client
    test_cases.append({
        "name": "Non-existent client",
        "client_id": "non_existent_client",
        "client_secret": "password",
        "should_succeed": False
    })
    
    # Run the test cases
    all_passed = True
    for i, test in enumerate(test_cases):
        write_separator(f"TEST {i+1}: {test['name']}", output_file)
        result = test_authentication(
            test["client_id"], 
            test["client_secret"], 
            test["should_succeed"],
            output_file
        )
        all_passed = all_passed and result
    
    write_separator("TEST RESULTS", output_file)
    write_to_file(f"\nOverall result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}", output_file)
    write_to_file("\nAuthentication testing complete.", output_file)
    
    logger.info(f"Authentication test results have been written to {output_file}")
    return all_passed

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test client authentication")
    parser.add_argument(
        "--output-file", 
        default=DEFAULT_OUTPUT_FILE,
        help="Output file for test results"
    )
    parser.add_argument(
        "--client", 
        action="append", 
        help="Client to test in the format client_id:secret"
    )
    parser.add_argument(
        "--show-secrets-table", 
        action="store_true",
        help="Show a table of client IDs and their corresponding secret hashes"
    )
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Show secrets table if requested
    if args.show_secrets_table:
        clients = {
            "test_client": "password",
            "groq_only_client": "groq_password",
            "openai_only_client": "openai_password"
        }
        print_client_secrets_table(clients)
    
    # Parse client arguments
    clients_to_test = None
    if args.client:
        clients_to_test = {}
        for client_arg in args.client:
            try:
                client_id, client_secret = client_arg.split(":", 1)
                clients_to_test[client_id] = client_secret
            except ValueError:
                logger.error(f"Invalid client argument: {client_arg}")
                logger.error("Client arguments should be in the format client_id:secret")
                sys.exit(1)
    
    # Run the tests
    success = run_tests(args.output_file, clients_to_test)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
