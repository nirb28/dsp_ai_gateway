"""
Generate SHA-256 hashes for client secrets.
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

# Print the hashes
print("\nClient Secret Hashes:")
print("-" * 80)
print(f"{'Client ID':<20} | {'Secret':<20} | {'Secret Hash'}")
print("-" * 80)

for client_id, secret in clients.items():
    hash_value = generate_hash(secret)
    print(f"{client_id:<20} | {secret:<20} | {hash_value}")

print("-" * 80)
