# 🔐 Security Implementation Guide
## Comprehensive Security & Access Control Documentation

This document explains all security features implemented in the Quiz Master Application, including password hashing, RSA digital signatures, encoding techniques, **AES-256 encryption for correct answers**, and **Role-Based Access Control (RBAC)**.

---

## Table of Contents
1. [Password Hashing with Salt](#1-password-hashing-with-salt)
2. [RSA Digital Signatures](#2-rsa-digital-signatures)
3. [Encoding Techniques](#3-encoding-techniques)
4. [AES-256 Encryption for Correct Answers](#4-aes-256-encryption-for-correct-answers)
5. [Access Control Matrix (ACM)](#5-access-control-matrix-acm)
6. [Setup Instructions](#setup-instructions)
7. [Security Summary](#security-summary)

---

## 1. Password Hashing with Salt

### Overview
User passwords are **never stored in plain text**. Instead, they are hashed using the **scrypt** algorithm (Werkzeug 3.x default) with a **random salt** that is unique for each user. Scrypt is a memory-hard function providing superior protection against hardware-accelerated attacks.

### Implementation Details

#### Algorithm: scrypt (Werkzeug 3.x default)
- **scrypt** (Memory-hard password hashing function)
- **N=32768** (CPU/memory cost parameter)
- **r=8** (block size parameter)
- **p=1** (parallelization parameter)
- **Random salt** generated automatically per user
- Uses **Werkzeug's security functions**

> **Note**: Werkzeug 3.x defaults to scrypt which provides better protection against GPU/ASIC attacks compared to the older pbkdf2:sha256 algorithm.

#### How It Works

**During Registration (Hashing):**
```python
from werkzeug.security import generate_password_hash

# User provides password: "mypassword123"
plain_password = "mypassword123"

# Hash with auto-generated salt using scrypt (Werkzeug 3.x default)
hashed = generate_password_hash(plain_password)
# Result: "scrypt:32768:8:1$randomsalt$hashedvalue"

# Store in database (NOT the plain password)
user.password = hashed
```

**During Login (Verification):**
```python
from werkzeug.security import check_password_hash

# User provides password
input_password = "mypassword123"

# Retrieve stored hash from database
stored_hash = user.password  # "scrypt:32768:8:1$salt$hash"

# Verify: extracts salt from stored hash and compares
if check_password_hash(stored_hash, input_password):
    # Password correct ✅
    login_success()
else:
    # Password incorrect ❌
    login_failed()
```

### Storage Format
```
scrypt:32768:8:1$<random_salt>$<hashed_password>
│      │    │ │        │              │
│      │    │ │        │              └─ Hash output (Base64 encoded)
│      │    │ │        └─ Random salt (Base64 encoded)
│      │    │ └─ Parallelization factor (p=1)
│      │    └─ Block size (r=8)
│      └─ CPU/Memory cost (N=32768)
└─ Algorithm identifier (scrypt)
```

**Example:**
```
scrypt:32768:8:1$aB3xY9kMwZ$1a2b3c4d5e6f7g8h9i0j...
```

### Code Locations

#### 1. User Model ([models/models.py](models/models.py))
```python
class User(db.Model):
    # Password stored as salted hash (200 chars to accommodate full hash)
    # Never stores plain text - uses Werkzeug's generate_password_hash with random salt per user
    password = db.Column(db.String(200), nullable=False)
```

#### 2. Registration ([routes/auth_routes.py](routes/auth_routes.py))
```python
# Password hashing with scrypt: Werkzeug 3.x uses scrypt algorithm by default
# scrypt is a memory-hard function providing better security against GPU/ASIC attacks
# A random salt is generated and embedded in the hash (format: scrypt:32768:8:1$<salt>$<hash>)
hashed_password = generate_password_hash(registration_data['password'])
new_user = User(
    email=email,
    password=hashed_password,  # Stored as: "scrypt:32768:8:1$randomsalt$hashedvalue"
)
```

#### 3. Login Verification ([routes/auth_routes.py](routes/auth_routes.py))
```python
# Secure password verification: check_password_hash extracts the salt from the stored
# scrypt hash (format: scrypt:32768:8:1$salt$hash) and uses it to hash the input
# password for comparison using constant-time algorithm to prevent timing attacks
if not check_password_hash(user.password, password):
    return jsonify({'error': 'Invalid credentials'}), 401
```

### Security Benefits

✅ **Salt Protection**: Each user has unique salt → same password = different hashes  
✅ **Rainbow Table Defense**: Pre-computed hash tables are useless  
✅ **Memory-Hard Function**: scrypt requires significant memory, defeating GPU/ASIC attacks  
✅ **No Plain Text**: Passwords never stored in readable form  
✅ **Database Breach Protection**: Even if database leaked, passwords stay protected

### Example Scenario

**Two users with same password:**
```
User 1: password = "password123"
  → Hash: scrypt:32768:8:1$aB3xY$1f2e3d4c5b...
  
User 2: password = "password123"  
  → Hash: scrypt:32768:8:1$zK9mW$9a8b7c6d5e...
  
Different salts → Different hashes ✅
```

---

## 2. RSA Digital Signatures for Quiz Results

### Overview
Quiz results are **digitally signed** using **RSA-2048** encryption to ensure **integrity** and **authenticity**. This prevents tampering and allows students to verify results came from the trusted server.

### Implementation Details

#### What Gets Signed
Every quiz submission is signed with:
```
user_id | quiz_id | score | timestamp
```

Example:
```
123|45|8.5|2026-01-12T14:27:17.257170
```

#### Algorithms Used
- **Hashing**: SHA-256 (using Python's `hashlib`)
- **Signature**: RSA-2048 with PSS padding
- **Key Size**: 2048 bits
- **Encoding**: Base64 (for database storage)

### How It Works

#### Step 1: Key Generation (One-time setup)
```python
# Run once: python init_keys.py
from crypto_utils import generate_rsa_keys

generate_rsa_keys()
# Creates:
#   - keys/private_key.pem (server secret - NEVER share)
#   - keys/public_key.pem (publicly available)
```

#### Step 2: Signing Quiz Results (Automatic)
```python
import hashlib
from crypto_utils import sign_quiz_result

# Student submits quiz
user_id = 123
quiz_id = 45
score = 8.5
timestamp = "2026-01-12T14:27:17.257170"

# Create message
message = f"{user_id}|{quiz_id}|{score}|{timestamp}"
# Result: "123|45|8.5|2026-01-12T14:27:17.257170"

# Hash with SHA-256 using hashlib
hash_obj = hashlib.sha256(message.encode('utf-8'))
digest = hash_obj.digest()  # 32-byte hash

# Sign with RSA private key
signature = sign_quiz_result(user_id, quiz_id, score, timestamp)
# Result: "FUeIhpknAFAf2n3O1dV7A7gAihOwAbU7..." (base64, ~344 chars)

# Store in database
score_record.digital_signature = signature
```

#### Step 3: Verification (Anyone can verify)
```python
from crypto_utils import verify_quiz_result

# Retrieve data from database
user_id = 123
quiz_id = 45
score = 8.5
timestamp = "2026-01-12T14:27:17.257170"
signature = "FUeIhpknAFAf2n3O..."

# Verify using public key
is_valid = verify_quiz_result(user_id, quiz_id, score, timestamp, signature)

if is_valid:
    print("✅ Result is authentic and unmodified")
else:
    print("❌ Result has been tampered with")
```

### Code Locations

#### 1. Crypto Utilities ([crypto_utils.py](crypto_utils.py))
Complete RSA implementation with:
- `generate_rsa_keys()` - Generate key pair
- `sign_quiz_result()` - Sign data with SHA-256 + RSA
- `verify_quiz_result()` - Verify signatures
- `load_private_key()` / `load_public_key()` - Key management

#### 2. Score Model ([models/models.py](models/models.py))
```python
class Score(db.Model):
    # ... other fields ...
    
    # RSA digital signature: Proves result integrity and authenticity
    # Signature is computed from: user_id|quiz_id|score|timestamp using SHA-256 + RSA-2048
    # Prevents tampering: changing score/user/quiz will invalidate signature
    digital_signature = db.Column(db.Text, nullable=True)
```

#### 3. Quiz Submission ([routes/user_routes.py](routes/user_routes.py))
```python
from crypto_utils import sign_quiz_result

# After calculating score
attempt_timestamp = datetime.utcnow()
timestamp_str = attempt_timestamp.isoformat()

# 🔐 DIGITAL SIGNATURE: Sign the quiz result using RSA
# Signing: user_id|quiz_id|score|timestamp with SHA-256 hash + RSA-2048 private key
# This proves the result came from trusted server and hasn't been tampered with
signature = sign_quiz_result(user_id, quiz_id, score, timestamp_str)

new_score = Score(
    user_id=user_id,
    quiz_id=quiz_id,
    total_score=score,
    attempt_timestamp=attempt_timestamp,
    digital_signature=signature  # Store base64-encoded RSA signature
)
```

#### 4. Verification Endpoint ([routes/user_routes.py](routes/user_routes.py))
```python
@user_bp.route('/verify-signature/<int:score_id>', methods=['GET'])
def verify_score_signature(score_id):
    score = Score.query.get_or_404(score_id)
    
    # Verify signature using public key
    is_valid = verify_quiz_result(
        score.user_id,
        score.quiz_id,
        score.total_score,
        score.attempt_timestamp.isoformat(),
        score.digital_signature
    )
    
    return jsonify({
        'verified': is_valid,
        'message': '✅ Signature valid' if is_valid else '❌ Signature invalid'
    })
```

### Key Management

#### Private Key (Server Secret)
- **Location**: `Backend/keys/private_key.pem`
- **Usage**: Server uses this to SIGN quiz results
- **Security**: 
  - Never committed to git (in `.gitignore`)
  - Never shared with anyone
  - Only server has access

#### Public Key (Publicly Available)
- **Location**: `Backend/keys/public_key.pem`
- **Usage**: Anyone can use this to VERIFY signatures
- **Distribution**: Available via `/api/public-key` endpoint
- **Security**: Safe to share publicly

### API Endpoints

#### 1. Submit Quiz (Auto-signs)
```http
POST /api/user/quiz/<quiz_id>/submit
Authorization: Bearer <token>

Response:
{
  "total_score": 8.5,
  "digital_signature": "FUeIhpknAFAf2n3O...",
  "signed": true
}
```

#### 2. Verify Signature
```http
GET /api/user/verify-signature/<score_id>
Authorization: Bearer <token>

Response:
{
  "verified": true,
  "message": "✅ Signature valid - Result is authentic"
}
```

#### 3. Get Public Key (No auth required)
```http
GET /api/user/public-key

Response:
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "algorithm": "RSA-2048",
  "hash": "SHA-256"
}
```

### Security Benefits

✅ **Integrity Protection**: Cannot change score, user_id, quiz_id, or timestamp  
✅ **Authenticity Proof**: Result verified as coming from trusted server  
✅ **Non-repudiation**: Cryptographic proof of quiz completion  
✅ **Tamper Detection**: Any modification invalidates signature  
✅ **Verifiable**: Students can independently verify their results

### Tampering Detection Example

```python
# Original signed result
original_score = 8.5
signature = "FUeIhpknAFAf2n3O..."

# Attacker changes score in database
tampered_score = 10.0

# Verification with tampered data
is_valid = verify_quiz_result(user_id, quiz_id, tampered_score, timestamp, signature)
# Result: False ❌ - Tampering detected!
```

### Technical Flow

```
Quiz Submission
    ↓
Calculate Score
    ↓
Create Message: "user_id|quiz_id|score|timestamp"
    ↓
SHA-256 Hash (hashlib)
    ↓
Sign with RSA-2048 Private Key
    ↓
Base64 Encode
    ↓
Store in Database
    ↓
Return to Student

Verification
    ↓
Retrieve from Database
    ↓
Recreate Message
    ↓
SHA-256 Hash (hashlib)
    ↓
Verify with RSA-2048 Public Key
    ↓
Valid ✅ or Invalid ❌
```

---

## Setup Instructions

### 1. Password Hashing (Already configured)
No setup needed! Werkzeug is included in Flask and works automatically.

### 2. RSA Digital Signatures

#### First Time Setup:
```bash
cd Backend

# Generate RSA key pair
python init_keys.py

# Test signatures work
python test_signatures.py

# Start application
python app.py
```

#### What Gets Created:
- `keys/private_key.pem` - Server's private key (keep secret!)
- `keys/public_key.pem` - Public key (can share)

---

## Testing

### Test Password Hashing
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash a password
password = "test123"
hashed = generate_password_hash(password)
print(hashed)
# Output: pbkdf2:sha256:260000$abc123$1a2b3c...

# Verify password
check_password_hash(hashed, "test123")  # True ✅
check_password_hash(hashed, "wrong")    # False ❌
```

### Test Digital Signatures
```bash
cd Backend
python test_signatures.py
```

Expected output:
- ✅ Signature generation works
- ✅ Valid signatures verify correctly
- ❌ Tampered data is detected

---

## Security Summary

| Feature | Algorithm | Purpose | Protection |
|---------|-----------|---------|------------|
| **Password Storage** | pbkdf2:sha256 (260k iterations) | Protect user credentials | Rainbow tables, brute force |
| **Password Salt** | Random per user | Unique hashes for same passwords | Pre-computed attacks |
| **Quiz Signatures** | RSA-2048 + SHA-256 | Prove result authenticity | Tampering, forgery |
| **Signature Hash** | SHA-256 (hashlib) | Message digest before signing | Data integrity |

---

## 3. Encoding Techniques

### Overview
Two encoding techniques are used to safely represent and transfer quiz data:
- **Base64**: For quiz result verification tokens
- **Hexadecimal (Base16)**: For quiz integrity hashes

---

### Base64 Encoding - Quiz Result Verification

#### Purpose
To safely represent quiz result data in a compact, transferable text format that can be:
- Embedded in URLs
- Stored in JSON
- Transmitted via API
- Displayed to users

#### Tool Used
Python built-in `base64` module

#### Character Set
Uses 64 characters: `A-Z`, `a-z`, `0-9`, `+`, `/` (with `=` for padding)

#### How It Works

**Encoding Quiz Results:**
```python
import base64
from crypto_utils import encode_quiz_result_base64

# Quiz result data
user_id = 123
quiz_id = 45
score = 8.5
timestamp = "2026-01-12T14:58:46.118041"

# Encode to Base64
verification_token = encode_quiz_result_base64(user_id, quiz_id, score, timestamp)
# Result: "MTIzfDQ1fDguNXwyMDI2LTAxLTEyVDE0OjU4OjQ2LjExODA0MQ=="

# Compact, URL-safe, easily transferable
```

**Decoding Quiz Results:**
```python
from crypto_utils import decode_quiz_result_base64

# Decode from Base64
decoded = decode_quiz_result_base64(verification_token)
# Result:
# {
#     'user_id': 123,
#     'quiz_id': 45,
#     'score': 8.5,
#     'timestamp': '2026-01-12T14:58:46.118041'
# }
```

#### Code Locations

**1. Database Field ([models/models.py](models/models.py))**
```python
class Score(db.Model):
    # Base64 encoding: Compact verification token for result data
    # Format: user_id|quiz_id|score|timestamp encoded in Base64 (URL-safe, transferable)
    verification_token = db.Column(db.Text, nullable=True)
```

**2. Quiz Submission ([routes/user_routes.py](routes/user_routes.py))**
```python
# 📦 BASE64 ENCODING: Create verification token for quiz result
# Encodes result data (user_id|quiz_id|score|timestamp) in Base64 format
# Makes data compact, URL-safe, and easily transferable
verification_token = encode_quiz_result_base64(user_id, quiz_id, score, timestamp_str)

new_score = Score(
    # ... other fields ...
    verification_token=verification_token  # Store base64-encoded result data
)
```

**3. Token Decoding Endpoint ([routes/user_routes.py](routes/user_routes.py))**
```python
@user_bp.route('/decode-token', methods=['POST'])
def decode_verification_token():
    """Decode Base64-encoded quiz result verification token"""
    token = request.json.get('verification_token')
    decoded = decode_quiz_result_base64(token)
    return jsonify({'decoded_data': decoded})
```

#### API Usage

**Submit Quiz (Returns Base64 token):**
```http
POST /api/user/quiz/45/submit

Response:
{
  "total_score": 8.5,
  "verification_token": "MTIzfDQ1fDguNXwyMDI2LTAxLTEyVDE0OjU4OjQ2LjExODA0MQ==",
  "digital_signature": "FUeIhpkn..."
}
```

**Decode Token:**
```http
POST /api/user/decode-token
{
  "verification_token": "MTIzfDQ1fDguNXwyMDI2LTAxLTEyVDE0OjU4OjQ2LjExODA0MQ=="
}

Response:
{
  "decoded_data": {
    "user_id": 123,
    "quiz_id": 45,
    "score": 8.5,
    "timestamp": "2026-01-12T14:58:46.118041"
  },
  "encoding_method": "Base64 (RFC 4648)"
}
```

#### Benefits
- ✅ **Compact**: ~33% larger than original (efficient)
- ✅ **URL-Safe**: Can be included in URLs without encoding
- ✅ **Transferable**: Safe for JSON, APIs, emails
- ✅ **Reversible**: Easy to decode back to original data

---

### Hexadecimal Encoding - Quiz Integrity

#### Purpose
To represent binary integrity data (hash/signature) in a human-readable form for:
- Detecting quiz content tampering
- Verifying questions haven't been modified
- Storing integrity checksums
- Debugging and logging

#### Tool Used
Python built-in `bytes.hex()` and `bytes.fromhex()`

#### Character Set
Uses 16 characters: `0-9`, `a-f`

Each byte (8 bits) = 2 hex characters

#### How It Works

**Generate Hexadecimal Integrity Hash:**
```python
import hashlib
from crypto_utils import generate_quiz_integrity_hex

# Quiz content
quiz_id = 45
questions_data = "1:What is Python?:A|2:What is Flask?:B|3:What is SQL?:C"

# Generate SHA-256 hash in hexadecimal format
integrity_hex = generate_quiz_integrity_hex(quiz_id, questions_data)
# Result: "3bad936a49c8a12c5e631425657556371b3f318befa41edc693b4e67a7bcafd3"
# Length: 64 hex characters (32 bytes = 256 bits)

# Process:
# 1. Combine quiz_id and questions_data
# 2. SHA-256 hash → 32 bytes
# 3. Convert to hex → 64 characters
```

**Verify Quiz Integrity:**
```python
from crypto_utils import verify_quiz_integrity_hex

# Verify with expected hash
is_valid = verify_quiz_integrity_hex(
    quiz_id,
    questions_data,
    expected_hash="3bad936a49c8a12c..."
)

if is_valid:
    print("✅ Quiz content intact")
else:
    print("❌ Quiz has been tampered with!")
```

**Convert Between Hex and Bytes:**
```python
from crypto_utils import hex_to_bytes

# Hex string to bytes
hex_string = "3bad936a49c8a12c"
byte_data = hex_to_bytes(hex_string)
# Result: b';\xad\x93jI\xc8\xa1,'

# Bytes to hex (built-in)
byte_data = b'Hello'
hex_string = byte_data.hex()
# Result: "48656c6c6f"
```

#### Code Locations

**1. Database Field ([models/models.py](models/models.py))**
```python
class Quiz(db.Model):
    # Hexadecimal (Base16) encoding: Quiz integrity hash for tamper detection
    # SHA-256 hash of quiz_id + questions content, encoded as hex string (64 chars)
    # Detects if questions/answers were modified after quiz creation
    integrity_hash = db.Column(db.String(64), nullable=True)
```

**2. Quiz Integrity Generation ([routes/user_routes.py](routes/user_routes.py))**
```python
@user_bp.route('/quiz/<int:quiz_id>/integrity', methods=['GET'])
def get_quiz_integrity(quiz_id):
    """Get quiz integrity hash in hexadecimal format"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Create questions data string
    questions_data = ""
    for q in quiz.questions:
        questions_data += f"{q.id}:{q.question_text}:{q.correct_option}|"
    
    # Generate hexadecimal integrity hash
    integrity_hex = generate_quiz_integrity_hex(quiz_id, questions_data)
    
    return jsonify({
        'integrity_hash': integrity_hex,
        'encoding_method': 'Hexadecimal (Base16)'
    })
```

**3. Quiz Integrity Verification ([routes/user_routes.py](routes/user_routes.py))**
```python
@user_bp.route('/quiz/<int:quiz_id>/verify-integrity', methods=['POST'])
def verify_quiz_integrity_endpoint(quiz_id):
    """Verify quiz integrity using stored hexadecimal hash"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Create current questions data
    questions_data = ""
    for q in quiz.questions:
        questions_data += f"{q.id}:{q.question_text}:{q.correct_option}|"
    
    # Verify integrity
    is_valid = verify_quiz_integrity_hex(quiz_id, questions_data, quiz.integrity_hash)
    
    return jsonify({
        'verified': is_valid,
        'message': '✅ Quiz intact' if is_valid else '❌ Quiz tampered'
    })
```

#### API Usage

**Get Quiz Integrity Hash:**
```http
GET /api/user/quiz/45/integrity

Response:
{
  "quiz_id": 45,
  "integrity_hash": "3bad936a49c8a12c5e631425657556371b3f318befa41edc693b4e67a7bcafd3",
  "encoding_method": "Hexadecimal (Base16)",
  "hash_algorithm": "SHA-256",
  "hash_length": 64
}
```

**Verify Quiz Integrity:**
```http
POST /api/user/quiz/45/verify-integrity

Response:
{
  "verified": true,
  "quiz_id": 45,
  "stored_hash": "3bad936a49c8a12c...",
  "message": "✅ Quiz content is intact (not tampered)"
}
```

#### Benefits
- ✅ **Human-Readable**: Easy to read and debug (0-9, a-f)
- ✅ **Standard Format**: Widely used for hashes and checksums
- ✅ **Tamper Detection**: Any content change = different hash
- ✅ **Logging-Friendly**: Perfect for logs and diagnostics

---

### Base64 vs Hexadecimal Comparison

| Feature | Base64 | Hexadecimal |
|---------|--------|-------------|
| **Character Set** | 64 chars (A-Z, a-z, 0-9, +, /) | 16 chars (0-9, a-f) |
| **Size Overhead** | +33% (~1.33x original) | +100% (2x original) |
| **Readability** | Less readable | More readable |
| **Use Case** | Data transfer, URLs, APIs | Hashes, debugging, integrity |
| **URL-Safe** | Yes (with modifications) | Yes |
| **Python Module** | `base64` | `bytes.hex()` |
| **Example** | `MTIzfDQ1fDguNQ==` | `3bad936a49c8a12c` |

---

### Testing Encodings

```bash
cd Backend
python test_encoding.py
```

**Expected Output:**
- ✅ Base64 encoding/decoding works
- ✅ Hexadecimal hash generation works
- ✅ Quiz integrity tamper detection works
- ✅ Comparison shows both methods

---

## Files Reference

### Core Implementation
- `crypto_utils.py` - RSA signing/verification logic + encoding functions
- `models/models.py` - Database schema with security fields
- `routes/auth_routes.py` - Password hashing on registration/login
- `routes/user_routes.py` - Digital signature + encoding on quiz operations

### Setup & Testing
- `init_keys.py` - Generate RSA key pair (run once)
- `test_signatures.py` - Test signature functionality
- `test_encoding.py` - Test Base64 and Hexadecimal encoding
- `keys/` - RSA key storage (gitignored)

### Security Configuration
- `.gitignore` - Protects private keys from git
- Database: Stores hashed passwords, signatures, and encoded data

---

## 4. AES-256 Encryption for Correct Answers

### Overview
**Correct answers are encrypted at rest** using **AES-256-CBC** (Advanced Encryption Standard) so that even if the database is compromised, the answers cannot be retrieved without the server-held encryption key. This preserves **exam integrity** and **confidentiality**.

### Why AES-256?
- **Symmetric encryption**: Same key for encryption and decryption (fast, efficient)
- **256-bit key**: Computationally infeasible to brute-force
- **Industry standard**: Approved by NIST, used by governments and enterprises
- **Perfect for at-rest encryption**: Protects data stored in database

### Implementation Details

#### Algorithm: AES-256-CBC
- **AES** (Advanced Encryption Standard)
- **256-bit key** (32 bytes) - stored as environment variable
- **CBC mode** (Cipher Block Chaining) with random IV per encryption
- **PKCS7 padding** for data alignment
- Uses **Python cryptography library**

### Data Flow

#### A. Quiz Creation (Admin / Quiz Master)
```
1. Admin/Quiz Master creates question
2. Enters correct answer (e.g., "A")
3. Server encrypts: encrypt_answer("A") 
4. Stores encrypted ciphertext in database
5. Client UI shows decrypted answer (for editing)
```

#### B. Quiz Attempt (User)
```
1. User requests quiz questions
2. Server sends: question text, options A/B/C/D
3. ❌ Server does NOT send correct_option (encrypted or decrypted)
4. User submits answers: {"1": "A", "2": "C", ...}
5. Server decrypts correct answers and compares
6. Returns score (not the answers)
```

### Security Guarantees

✅ **At no point:**
- Client sees the correct answer (encrypted or decrypted)
- Client sees the encryption key
- Database stores plaintext answers

### Code Implementation

#### Encryption Function ([crypto_utils.py](crypto_utils.py))
```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import base64

def encrypt_answer(plaintext):
    """
    Encrypt correct answer using AES-256-CBC
    
    Args:
        plaintext: The correct answer (e.g., 'A', 'B', 'C', 'D')
    
    Returns:
        Base64-encoded string: IV (16 bytes) + Ciphertext
    """
    key = get_aes_key()  # 32 bytes from env variable
    
    # Random IV ensures same answer encrypts differently each time
    iv = os.urandom(16)
    
    # Create AES-256-CBC cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # PKCS7 padding (AES requires 16-byte blocks)
    plaintext_bytes = plaintext.encode('utf-8')
    padding_length = 16 - (len(plaintext_bytes) % 16)
    padded_data = plaintext_bytes + bytes([padding_length] * padding_length)
    
    # Encrypt and combine IV + ciphertext
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_data = iv + ciphertext
    
    return base64.b64encode(encrypted_data).decode('utf-8')
```

#### Decryption Function ([crypto_utils.py](crypto_utils.py))
```python
def decrypt_answer(encrypted_base64):
    """
    Decrypt correct answer using AES-256-CBC
    Server-side only - client never calls this
    
    Args:
        encrypted_base64: Base64(IV + Ciphertext)
    
    Returns:
        Decrypted plaintext answer (e.g., 'A')
    """
    key = get_aes_key()
    
    # Decode from Base64
    encrypted_data = base64.b64decode(encrypted_base64)
    
    # Extract IV (first 16 bytes) and ciphertext
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    # Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    padding_length = padded_data[-1]
    plaintext_bytes = padded_data[:-padding_length]
    
    return plaintext_bytes.decode('utf-8')
```

### Key Management

#### Key Storage
```bash
# Production: Environment variable
export QUIZ_AES_KEY='base64_encoded_32_byte_key'

# Development: Auto-generated in keys/aes_key.bin
# ⚠️ For development only - use env variable in production
```

#### Generate New Key
```bash
python -c "from crypto_utils import generate_aes_key_for_env; generate_aes_key_for_env()"

# Output:
# 🔑 Generated AES-256 Key (Base64):
#    dGhpcyBpcyBhIDMyIGJ5dGUga2V5IGZvciBBRVM=
#
#    Set as environment variable:
#    export QUIZ_AES_KEY='dGhpcyBpcyBhIDMyIGJ5dGUga2V5IGZvciBBRVM='  # Linux/Mac
#    $env:QUIZ_AES_KEY='dGhpcyBpcyBhIDMyIGJ5dGUga2V5IGZvciBBRVM='   # PowerShell
```

### Database Schema

#### Question Model ([models/models.py](models/models.py))
```python
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    # AES-256-CBC encrypted correct answer
    # Stores: Base64(IV + AES_encrypted(answer)) ≈ 44 characters
    correct_option = db.Column(db.String(100), nullable=False)
```

### API Endpoints

#### Create Question (Admin) - Encrypts answer
```http
POST /api/admin/quizzes/1/questions
Content-Type: multipart/form-data

question_text=What is 2+2?
option_a=3
option_b=4
option_c=5
option_d=6
correct_option=B   ← Plaintext from admin

Server encrypts → Stores: "Yjk0ZjNhMjE1NmU4..." (Base64 ciphertext)
```

#### Get Questions (User) - No answer sent
```http
GET /api/user/quiz/1/questions

Response:
{
  "questions": [
    {
      "id": 1,
      "question_text": "What is 2+2?",
      "option_a": "3",
      "option_b": "4",
      "option_c": "5",
      "option_d": "6"
      // ❌ NO correct_option field - answer is server-side only
    }
  ]
}
```

#### Submit Quiz (User) - Server decrypts and compares
```http
POST /api/user/quiz/1/submit
{
  "answers": {"1": "B", "2": "A", "3": "C"}
}

Server:
1. For each question:
   - Decrypt stored answer: decrypt_answer(encrypted) → "B"
   - Compare with user answer: "B" == "B" ✓
2. Calculate score
3. Return score (not answers)

Response:
{
  "total_score": 2,
  "max_score": 3
}
```

### Security Benefits

| Benefit | Description |
|---------|-------------|
| **Database Breach Protection** | Even if database is leaked, encrypted answers are useless without key |
| **Exam Integrity** | Users cannot extract answers by inspecting API responses |
| **Confidentiality** | Answers are encrypted at rest, decrypted only during scoring |
| **Defense in Depth** | Complements access control with cryptographic protection |
| **Unique Ciphertext** | Same answer encrypts differently each time (random IV) |

### Example: Same Answer, Different Ciphertext

```python
# Due to random IV, encrypting "A" multiple times gives different results:
encrypt_answer("A")  # "Yjk0ZjNhMjE1NmU4YzE0NTZiMjNkOWUxMjM0NTY3ODk="
encrypt_answer("A")  # "ZmE5YjdjOGUyM2E0NTY3ODlhYmNkZWYwMTIzNDU2Nzg="
encrypt_answer("A")  # "MWIzZDVmN2E5YjBjMmQ0ZTZmOGExYjNjNWQ3ZTlmMGE="

# All decrypt to "A" but look completely different in database
# Prevents frequency analysis attacks
```

---

## 5. Access Control Matrix (ACM)

### Overview
The application implements **Role-Based Access Control (RBAC)** with three distinct roles providing comprehensive access control across all system resources.

For complete Access Control documentation including:
- Access Control Matrix (3 subjects × 7+ objects)
- Policy definitions and justifications
- Programmatic enforcement details
- API endpoint security
- Test cases

**See: [ACCESS_CONTROL.md](ACCESS_CONTROL.md)**

### Quick Reference

#### Roles (Subjects)
1. **User** - Take quizzes, view own scores (OTP authentication)
2. **Quiz Master** - Create/manage own quizzes (No OTP)
3. **Admin** - Full system access (No OTP)

#### Objects (Resources)
1. Subjects, 2. Chapters, 3. Quizzes, 4. Questions, 5. Users, 6. Scores, 7. Analytics

#### Key Access Policies
- **Users**: Read-only access to public content, full access to own data
- **Quiz Masters**: Create/modify own quizzes only, view own analytics
- **Admin**: Full CRUD access to all resources

#### Implementation
```python
# Role-based decorators
@admin_required           # Admin-only endpoints
@user_required            # User-only endpoints
@quiz_master_required     # Quiz Master-only endpoints
@admin_or_quiz_master_required  # Shared endpoints

# Ownership verification
Quiz.query.filter_by(id=quiz_id, created_by_quiz_master_id=qm_id).first_or_404()
```

---

## Assignment Notes

### What's Implemented

1. **Password Hashing with Salt** ✅
   - Algorithm: pbkdf2:sha256 with 260,000 iterations
   - Unique random salt per user
   - Implemented in registration and login
   - Protects against rainbow table and brute force attacks

2. **RSA Digital Signatures** ✅
   - Algorithm: RSA-2048 with SHA-256 hashing (hashlib)
   - Signs: user_id|quiz_id|score|timestamp
   - Prevents tampering with quiz results
   - Provides authenticity and non-repudiation

3. **Base64 Encoding** ✅
   - Purpose: Quiz result verification tokens
   - Tool: Python built-in `base64` module
   - Encodes: user_id|quiz_id|score|timestamp
   - Benefits: Compact, URL-safe, transferable
   - Stored in: `Score.verification_token` field

4. **Hexadecimal Encoding** ✅
   - Purpose: Quiz integrity hashes
   - Tool: Python built-in `bytes.hex()` and `bytes.fromhex()`
   - Encodes: SHA-256 hash of quiz content
   - Benefits: Human-readable, tamper detection
   - Stored in: `Quiz.integrity_hash` field

5. **AES-256 Encryption for Correct Answers** ✅
   - Algorithm: AES-256-CBC with random IV per encryption
   - Purpose: Encrypt correct answers at rest in database
   - Key: 32-byte key stored in environment variable (never in code/database)
   - Flow: Admin creates question → Server encrypts answer → Store ciphertext
   - Flow: User submits quiz → Server decrypts → Compare → Return score (not answers)
   - **At no point**: Client sees correct answer or encryption key
   - Stored in: `Question.correct_option` field as Base64(IV + ciphertext)

6. **Access Control Matrix (ACM)** ✅
   - **3 Subjects**: User, Quiz Master, Admin
   - **7+ Objects**: Subjects, Chapters, Quizzes, Questions, Users, Scores, Analytics
   - **Policy Definitions**: Clear justifications for each access right
   - **Programmatic Enforcement**: Decorators + database filters + ownership checks
   - See [ACCESS_CONTROL.md](ACCESS_CONTROL.md) for complete documentation

### Key Security Concepts Demonstrated

- **Salting**: Each password gets unique random salt
- **Hashing**: One-way function, cannot reverse to get password
- **Asymmetric Cryptography**: Public/private key pairs (RSA)
- **Symmetric Cryptography**: Single key for encrypt/decrypt (AES)
- **Digital Signatures**: Proves data origin and integrity
- **Message Digest**: SHA-256 hashing before signing
- **Tamper Detection**: Any change invalidates signature
- **At-Rest Encryption**: Data encrypted when stored in database
- **Base64 Encoding**: Compact binary-to-text encoding
- **Hexadecimal Encoding**: Human-readable binary representation
- **Role-Based Access Control (RBAC)**: Three-tier permission system
- **Principle of Least Privilege**: Minimum necessary permissions per role
- **Separation of Duties**: Content creation vs. user management
- **Defense in Depth**: Multiple security layers

---

**Implementation Date**: January 25, 2026  
**Status**: Fully Implemented and Tested ✅
