from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import os

# Path to store RSA keys (in production, use secure key management service)
KEY_DIR = os.path.join(os.path.dirname(__file__), 'keys')
PRIVATE_KEY_PATH = os.path.join(KEY_DIR, 'private_key.pem')
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, 'public_key.pem')


def get_aes_key():
    """
    Get AES-256 encryption key from environment variable
    Key must be exactly 32 bytes (256 bits) for AES-256
    
    Security: Key is stored as environment variable, never in code or database
    """
    key = os.environ.get('QUIZ_AES_KEY')
    if not key:
        # For development: generate and store a key if not exists
        key_file = os.path.join(KEY_DIR, 'aes_key.bin')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key for development
            os.makedirs(KEY_DIR, exist_ok=True)
            new_key = os.urandom(32)  # 256 bits
            with open(key_file, 'wb') as f:
                f.write(new_key)
            print(f"⚠️  Development AES key generated: {key_file}")
            print("   For production, set QUIZ_AES_KEY environment variable")
            return new_key
    
    # Decode from base64 if provided as env variable
    return base64.b64decode(key)

def encrypt_answer(plaintext):
    """
    Encrypt correct answer using AES-256-CBC
    
    Args:
        plaintext: The correct answer (e.g., 'A', 'B', 'C', 'D')
    
    Returns:
        Base64-encoded string containing: IV (16 bytes) + Ciphertext
    
    Security:
        - AES-256-CBC mode with random IV per encryption
        - Each encryption produces unique ciphertext (even for same answer)
        - IV is prepended to ciphertext and stored together
    """
    if not plaintext:
        return None
    
    key = get_aes_key()
    
    # Generate random 16-byte IV (Initialization Vector) for each encryption
    # IV ensures same plaintext produces different ciphertext each time
    iv = os.urandom(16)
    
    # Create AES-256-CBC cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # PKCS7 padding: AES requires data to be multiple of 16 bytes
    # For single character answers (A, B, C, D), we pad to 16 bytes
    plaintext_bytes = plaintext.encode('utf-8')
    padding_length = 16 - (len(plaintext_bytes) % 16)
    padded_data = plaintext_bytes + bytes([padding_length] * padding_length)
    
    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Combine IV + Ciphertext and encode as Base64 for storage
    encrypted_data = iv + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_answer(encrypted_base64):
    """
    Decrypt correct answer using AES-256-CBC
    
    Args:
        encrypted_base64: Base64-encoded string containing IV + Ciphertext
    
    Returns:
        Decrypted plaintext answer (e.g., 'A', 'B', 'C', 'D')
    
    Security:
        - Only server can decrypt (key is server-side only)
        - Client never sees decrypted answer or key
    """
    if not encrypted_base64:
        return None
    
    key = get_aes_key()
    
    # Decode from Base64
    encrypted_data = base64.b64decode(encrypted_base64)
    
    # Extract IV (first 16 bytes) and Ciphertext (rest)
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    # Create AES-256-CBC cipher for decryption
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    # Decrypt
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    padding_length = padded_data[-1]
    plaintext_bytes = padded_data[:-padding_length]
    
    return plaintext_bytes.decode('utf-8')

def generate_aes_key_for_env():
    """
    Generate a new AES-256 key and print it as Base64 for environment variable
    Run this once to generate key: python -c "from crypto_utils import generate_aes_key_for_env; generate_aes_key_for_env()"
    """
    key = os.urandom(32)
    key_b64 = base64.b64encode(key).decode('utf-8')
    print(f"\n🔑 Generated AES-256 Key (Base64):")
    print(f"   {key_b64}")
    print(f"\n   Set as environment variable:")
    print(f"   export QUIZ_AES_KEY='{key_b64}'  # Linux/Mac")
    print(f"   $env:QUIZ_AES_KEY='{key_b64}'   # PowerShell")
    return key_b64


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
    
    print("RSA key pair generated successfully!")
    print(f"Private key: {PRIVATE_KEY_PATH}")
    print(f"Public key: {PUBLIC_KEY_PATH}")

def load_private_key():
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
        print(f"Signature verification failed: {e}")
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


def encode_quiz_result_base64(user_id, quiz_id, score, timestamp):
    """
    Base64 Encoding - Quiz Result Verification
    
    Purpose: Safely represent quiz result data in a compact, transferable text format  
    Base64 converts binary data into ASCII string using 64-character set:

    Args:
        user_id: User who took the quiz
        quiz_id: Quiz identifier
        score: Quiz score achieved
        timestamp: When quiz was submitted
    
    Returns:
        Base64-encoded string representing the quiz result
    """
    # Create result data string
    result_data = f"{user_id}|{quiz_id}|{score}|{timestamp}"
    
    # Convert string to bytes
    data_bytes = result_data.encode('utf-8')
    
    # Base64 encode - converts binary data to ASCII text
    # Uses 64 characters: A-Z, a-z, 0-9, +, /
    encoded = base64.b64encode(data_bytes)
    
    # Return as string (decode bytes to str)
    return encoded.decode('utf-8')

def decode_quiz_result_base64(encoded_data):
    """
    Decode Base64-encoded quiz result back to original data
    
    Args:
        encoded_data: Base64-encoded string
    
    Returns:
        Dictionary with decoded quiz result data
    """
    try:
        # Decode from base64 to bytes
        decoded_bytes = base64.b64decode(encoded_data)
        
        # Convert bytes to string
        result_string = decoded_bytes.decode('utf-8')
        
        # Parse the data
        parts = result_string.split('|')
        if len(parts) == 4:
            return {
                'user_id': int(parts[0]),
                'quiz_id': int(parts[1]),
                'score': float(parts[2]),
                'timestamp': parts[3]
            }
        return None
    except Exception as e:
        print(f"Error decoding base64 data: {e}")
        return None

def generate_quiz_integrity_hex(quiz_id, questions_data):
    """
    Hexadecimal (Base16) Encoding - Quiz Integrity Data
    
    Purpose: Represent binary integrity data (hash) in human-readable form
    Tool: Python built-in bytes.hex() and bytes.fromhex()
    
    Hexadecimal uses 16 characters: 0-9, a-f
    Each byte (8 bits) = 2 hex characters
    
    Use Case: Creating quiz fingerprint to detect if:
    - Questions were modified
    - Options were changed
    - Correct answers were altered
    - Quiz content was tampered with
    
    Args:
        quiz_id: Quiz identifier
        questions_data: String containing all quiz questions and answers
    
    Returns:
        Hexadecimal string representing quiz integrity hash
    """
    # Combine quiz ID and questions data
    quiz_content = f"{quiz_id}:{questions_data}"
    
    # Create SHA-256 hash of the content
    hash_obj = hashlib.sha256(quiz_content.encode('utf-8'))
    hash_bytes = hash_obj.digest()  # 32-byte binary hash
    
    # Convert bytes to hexadecimal string
    # bytes.hex() converts each byte to 2 hex characters (0-9, a-f)
    hex_string = hash_bytes.hex()
    
    return hex_string

def verify_quiz_integrity_hex(quiz_id, questions_data, expected_hex):
    """
    Verify quiz integrity by comparing current hash with expected hash
    Case-insensitive comparison (hex can be uppercase or lowercase)
    """
    try:
        # Generate current hash
        current_hex = generate_quiz_integrity_hex(quiz_id, questions_data)
        
        # Compare with expected hash (case-insensitive)
        return current_hex.lower() == expected_hex.lower()
    except Exception as e:
        print(f"Error verifying quiz integrity: {e}")
        return False

def hex_to_bytes(hex_string):
    return bytes.fromhex(hex_string)

def create_quiz_verification_token(user_id, quiz_id, score, timestamp, signature):
    """
    Combined encoding example: Create comprehensive verification token
    
    Combines:
    - Base64 encoding for quiz result data
    - Hexadecimal encoding for signature bytes
    
    Returns:
        Dictionary with both encoded formats
    """
    # Base64 encode the result data
    result_token = encode_quiz_result_base64(user_id, quiz_id, score, timestamp)
    
    # If signature is already base64 string, convert to hex for demonstration
    # Decode base64 signature to bytes, then encode as hex
    sig_bytes = base64.b64decode(signature)
    sig_hex = sig_bytes.hex()
    
    return {
        'result_token_base64': result_token,  # Compact, URL-safe
        'signature_hex': sig_hex[:64] + '...',  # Human-readable (truncated for display)
        'encoding_methods': {
            'result_data': 'Base64 (RFC 4648)',
            'integrity_hash': 'Hexadecimal (Base16)'
        }
    }

# Initialize keys on module import (only if running directly)
if __name__ == "__main__":
    print("Generating RSA keys for quiz result signing...")
    generate_rsa_keys()
