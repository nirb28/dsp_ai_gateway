"""
Generate SHA-256 hashes for client secrets and write them to a file.
"""
import hashlib

def generate_hash(secret):
    """Generate a SHA-256 hash for a secret."""
    return hashlib.sha256(secret.encode()).hexdigest()

# Client secrets
clients = {
    "test_client": "password",
    "groq_only_client": "groq_password",
    "openai_only_client": "openai_password"
}

# Write the hashes to a file
with open("client_secret_hashes.txt", "w") as f:
    f.write("Client Secret Hashes:\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'Client ID':<20} | {'Secret':<20} | {'Secret Hash'}\n")
    f.write("-" * 80 + "\n")
    
    for client_id, secret in clients.items():
        hash_value = generate_hash(secret)
        f.write(f"{client_id:<20} | {secret:<20} | {hash_value}\n")
    
    f.write("-" * 80 + "\n")

print("Client secret hashes have been written to client_secret_hashes.txt")
