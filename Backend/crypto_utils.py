"""
RSA Digital Signature Implementation for Quiz Results
Ensures integrity and authenticity of quiz scores

Security Features:
- 2048-bit RSA key pair (private key kept on server, public key for verification)
- SHA-256 hashing for message digest before signing
- Digital signature prevents tampering with: user_id, quiz_id, score, timestamp
"""

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import os

# Path to store RSA keys (in production, use secure key management service)
KEY_DIR = os.path.join(os.path.dirname(__file__), 'keys')
PRIVATE_KEY_PATH = os.path.join(KEY_DIR, 'private_key.pem')
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, 'public_key.pem')

def generate_rsa_keys():
    """
    Generate RSA 2048-bit key pair for digital signatures
    Called once during initial setup - keys are persistent
    Private key: Used by server to sign quiz results
    Public key: Used to verify signatures (can be shared)
    """
    # Create keys directory if it doesn't exist
    os.makedirs(KEY_DIR, exist_ok=True)
    
    # Generate private key with 2048-bit strength
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Extract public key from private key
    public_key = private_key.public_key()
    
    # Serialize and save private key (PEM format, no encryption for simplicity)
    # In production: encrypt with password using BestAvailableEncryption
    with open(PRIVATE_KEY_PATH, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Serialize and save public key (PEM format)
    with open(PUBLIC_KEY_PATH, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    print("✅ RSA key pair generated successfully!")
    print(f"Private key: {PRIVATE_KEY_PATH}")
    print(f"Public key: {PUBLIC_KEY_PATH}")

def load_private_key():
    """Load the server's private key for signing"""
    # Generate keys if they don't exist
    if not os.path.exists(PRIVATE_KEY_PATH):
        generate_rsa_keys()
    
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def load_public_key():
    """Load the public key for verification"""
    if not os.path.exists(PUBLIC_KEY_PATH):
        generate_rsa_keys()
    
    with open(PUBLIC_KEY_PATH, 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    return public_key

def create_message_digest(user_id, quiz_id, score, timestamp):
    """
    Create SHA-256 hash of quiz result data
    Format: "user_id|quiz_id|score|timestamp"
    This message digest is what gets signed by RSA
    """
    # Concatenate data with pipe delimiter
    message = f"{user_id}|{quiz_id}|{score}|{timestamp}"
    
    # SHA-256 hashing using hashlib (produces 256-bit/32-byte digest)
    hash_object = hashlib.sha256(message.encode('utf-8'))
    message_digest = hash_object.digest()  # Binary digest
    
    return message_digest, message

def sign_quiz_result(user_id, quiz_id, score, timestamp):
    """
    Digitally sign a quiz result using RSA private key
    
    Process:
    1. Create message from: user_id + quiz_id + score + timestamp
    2. Hash message with SHA-256 (using hashlib)
    3. Sign the hash with RSA private key
    4. Return base64-encoded signature
    
    Args:
        user_id: User who took the quiz
        quiz_id: Quiz identifier
        score: Quiz score achieved
        timestamp: When quiz was submitted (ISO format string)
    
    Returns:
        Base64-encoded signature string
    """
    # Create SHA-256 digest of the data
    message_digest, original_message = create_message_digest(user_id, quiz_id, score, timestamp)
    
    # Load server's private key
    private_key = load_private_key()
    
    # Sign the digest using RSA with PSS padding (more secure than PKCS1v15)
    # PSS = Probabilistic Signature Scheme
    signature = private_key.sign(
        message_digest,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Encode signature to base64 for storage in database
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    return signature_b64

def verify_quiz_result(user_id, quiz_id, score, timestamp, signature_b64):
    """
    Verify the digital signature of a quiz result
    
    Process:
    1. Recreate message from provided data
    2. Hash message with SHA-256
    3. Decode base64 signature
    4. Verify signature using RSA public key
    
    Args:
        user_id: User ID from the score record
        quiz_id: Quiz ID from the score record
        score: Score value from the record
        timestamp: Timestamp from the record (ISO format string)
        signature_b64: Base64-encoded signature from database
    
    Returns:
        True if signature is valid (data not tampered), False otherwise
    """
    try:
        # Recreate the message digest
        message_digest, original_message = create_message_digest(user_id, quiz_id, score, timestamp)
        
        # Decode signature from base64
        signature = base64.b64decode(signature_b64)
        
        # Load public key
        public_key = load_public_key()
        
        # Verify signature - raises exception if invalid
        public_key.verify(
            signature,
            message_digest,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True  # Signature valid - data not tampered
    
    except Exception as e:
        print(f"❌ Signature verification failed: {e}")
        return False  # Signature invalid - data may be tampered

def get_public_key_pem():
    """
    Get public key in PEM format for distribution
    Students can use this to verify their results independently
    """
    public_key = load_public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

# Initialize keys on module import (only if running directly)
if __name__ == "__main__":
    print("Generating RSA keys for quiz result signing...")
    generate_rsa_keys()
