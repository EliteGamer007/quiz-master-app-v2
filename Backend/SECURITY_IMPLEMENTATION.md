# 🔐 Security Implementation Guide
## Password Hashing with Salt & RSA Digital Signatures

This document explains the two key security features implemented in this Quiz Master application.

---

## 1. Password Hashing with Salt

### Overview
User passwords are **never stored in plain text**. Instead, they are hashed using **pbkdf2:sha256** algorithm with a **random salt** that is unique for each user.

### Implementation Details

#### Algorithm: pbkdf2:sha256
- **PBKDF2** (Password-Based Key Derivation Function 2)
- **260,000 iterations** (computational cost to slow down brute-force attacks)
- **Random salt** generated automatically per user
- Uses **Werkzeug's security functions**

#### How It Works

**During Registration (Hashing):**
```python
from werkzeug.security import generate_password_hash

# User provides password: "mypassword123"
plain_password = "mypassword123"

# Hash with auto-generated salt
hashed = generate_password_hash(plain_password)
# Result: "pbkdf2:sha256:260000$randomsalt$hashedvalue"

# Store in database (NOT the plain password)
user.password = hashed
```

**During Login (Verification):**
```python
from werkzeug.security import check_password_hash

# User provides password
input_password = "mypassword123"

# Retrieve stored hash from database
stored_hash = user.password  # "pbkdf2:sha256:260000$salt$hash"

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
pbkdf2:sha256:260000$<random_salt>$<hashed_password>
│     │        │              │             │
│     │        │              │             └─ Hash output (64 chars)
│     │        │              └─ Random salt (16 chars)
│     │        └─ Iteration count (260,000)
│     └─ Hash algorithm (SHA-256)
└─ Key derivation function (PBKDF2)
```

**Example:**
```
pbkdf2:sha256:260000$abc123XYZ$1a2b3c4d5e6f7g8h9i0j...
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
# Password hashing with salt: generate_password_hash uses pbkdf2:sha256 with 260,000 iterations
# A random salt is generated and embedded in the hash (format: pbkdf2:sha256:260000$<salt>$<hash>)
# This protects against rainbow table attacks and ensures unique hashes for identical passwords
hashed_password = generate_password_hash(registration_data['password'])
new_user = User(
    email=email,
    password=hashed_password,  # Stored as: "pbkdf2:sha256:260000$randomsalt$hashedvalue"
)
```

#### 3. Login Verification ([routes/auth_routes.py](routes/auth_routes.py))
```python
# Secure password verification: check_password_hash extracts the salt from the stored
# hash (format: method$salt$hash) and uses it to hash the input password for comparison
if not check_password_hash(user.password, password):
    return jsonify({'error': 'Invalid credentials'}), 401
```

### Security Benefits

✅ **Salt Protection**: Each user has unique salt → same password = different hashes  
✅ **Rainbow Table Defense**: Pre-computed hash tables are useless  
✅ **Brute Force Resistance**: 260,000 iterations slow down attacks  
✅ **No Plain Text**: Passwords never stored in readable form  
✅ **Database Breach Protection**: Even if database leaked, passwords stay protected

### Example Scenario

**Two users with same password:**
```
User 1: password = "password123"
  → Hash: pbkdf2:sha256:260000$aB3xY$1f2e3d4c5b...
  
User 2: password = "password123"  
  → Hash: pbkdf2:sha256:260000$zK9mW$9a8b7c6d5e...
  
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

## Files Reference

### Core Implementation
- `crypto_utils.py` - RSA signing/verification logic
- `models/models.py` - Database schema with security fields
- `routes/auth_routes.py` - Password hashing on registration/login
- `routes/user_routes.py` - Digital signature on quiz submission

### Setup & Testing
- `init_keys.py` - Generate RSA key pair (run once)
- `test_signatures.py` - Test signature functionality
- `keys/` - RSA key storage (gitignored)

### Security Configuration
- `.gitignore` - Protects private keys from git
- Database: Stores hashed passwords and signatures

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

### Key Security Concepts Demonstrated

- **Salting**: Each password gets unique random salt
- **Hashing**: One-way function, cannot reverse to get password
- **Asymmetric Cryptography**: Public/private key pairs
- **Digital Signatures**: Proves data origin and integrity
- **Message Digest**: SHA-256 hashing before signing
- **Tamper Detection**: Any change invalidates signature

---

**Implementation Date**: January 12, 2026  
**Status**: Fully Implemented and Tested ✅
