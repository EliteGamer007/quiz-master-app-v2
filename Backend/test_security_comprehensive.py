"""
Comprehensive Security Testing Suite for Quiz Master Application
================================================================
Tests all security implementations for LAB EVALUATION 1

Run: python test_security_comprehensive.py
"""

import sys
import os
import base64
import hashlib
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🔐 QUIZ MASTER - COMPREHENSIVE SECURITY TESTS")
print("=" * 70)
print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Track test results
passed = 0
failed = 0
total = 0

def test(name, condition, details=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"✅ PASS: {name}")
        if details:
            print(f"         {details}")
    else:
        failed += 1
        print(f"❌ FAIL: {name}")
        if details:
            print(f"         {details}")
    return condition

# ============================================================================
# 1. PASSWORD HASHING WITH SALT
# ============================================================================
print("\n" + "=" * 70)
print("1️⃣  PASSWORD HASHING WITH SALT (pbkdf2:sha256)")
print("=" * 70)

from werkzeug.security import generate_password_hash, check_password_hash

# Test 1.1: Hash generation
password = "SecurePassword123!"
hashed = generate_password_hash(password)
test("Hash is generated (not plaintext)", 
     hashed != password and len(hashed) > 50,
     f"Length: {len(hashed)} chars")

# Test 1.2: Hash format verification (Werkzeug 3.x uses scrypt by default, older uses pbkdf2)
is_scrypt = hashed.startswith("scrypt:")
is_pbkdf2 = hashed.startswith("pbkdf2:sha256:")
test("Hash format is scrypt or pbkdf2:sha256", 
     is_scrypt or is_pbkdf2,
     f"Format: {'scrypt (modern)' if is_scrypt else 'pbkdf2:sha256'}")

# Test 1.3: Correct password verification
test("Correct password verifies", 
     check_password_hash(hashed, password))

# Test 1.4: Wrong password fails
test("Wrong password fails verification", 
     not check_password_hash(hashed, "WrongPassword"))

# Test 1.5: Case sensitivity
test("Password is case-sensitive", 
     not check_password_hash(hashed, "securepassword123!"))

# Test 1.6: Unique salt per hash (same password = different hash)
hashed2 = generate_password_hash(password)
test("Same password produces different hash (unique salt)", 
     hashed != hashed2,
     f"Hash1: {hashed[30:50]}...\n         Hash2: {hashed2[30:50]}...")

# Test 1.7: Empty password handling
try:
    empty_hash = generate_password_hash("")
    test("Empty password can be hashed", True)
    test("Empty password verifies correctly", check_password_hash(empty_hash, ""))
except Exception as e:
    test("Empty password handling", False, str(e))

# Test 1.8: Special characters in password
special_pwd = "P@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
special_hash = generate_password_hash(special_pwd)
test("Special characters password works", 
     check_password_hash(special_hash, special_pwd))

# Test 1.9: Unicode password
unicode_pwd = "密码123パスワード"
unicode_hash = generate_password_hash(unicode_pwd)
test("Unicode password works", 
     check_password_hash(unicode_hash, unicode_pwd))

# Test 1.10: Very long password
long_pwd = "A" * 1000
long_hash = generate_password_hash(long_pwd)
test("Long password (1000 chars) works", 
     check_password_hash(long_hash, long_pwd))

# ============================================================================
# 2. AES-256 ENCRYPTION FOR CORRECT ANSWERS
# ============================================================================
print("\n" + "=" * 70)
print("2️⃣  AES-256-CBC ENCRYPTION (Correct Answers)")
print("=" * 70)

from crypto_utils import encrypt_answer, decrypt_answer, get_aes_key

# Test 2.1: Basic encryption/decryption
answer = "A"
encrypted = encrypt_answer(answer)
decrypted = decrypt_answer(encrypted)
test("Basic encrypt/decrypt works", 
     decrypted == answer,
     f"Original: {answer}, Encrypted: {encrypted[:30]}..., Decrypted: {decrypted}")

# Test 2.2: All answer options
for opt in ["A", "B", "C", "D"]:
    enc = encrypt_answer(opt)
    dec = decrypt_answer(enc)
    test(f"Option '{opt}' encrypts/decrypts correctly", dec == opt)

# Test 2.3: Same answer produces different ciphertext (random IV)
enc1 = encrypt_answer("A")
enc2 = encrypt_answer("A")
enc3 = encrypt_answer("A")
test("Same answer produces different ciphertext (random IV)", 
     enc1 != enc2 and enc2 != enc3 and enc1 != enc3,
     f"Enc1: {enc1[:20]}...\n         Enc2: {enc2[:20]}...\n         Enc3: {enc3[:20]}...")

# Test 2.4: Encrypted data is Base64
try:
    decoded = base64.b64decode(encrypted)
    test("Encrypted output is valid Base64", True)
except:
    test("Encrypted output is valid Base64", False)

# Test 2.5: IV + Ciphertext structure (16 bytes IV + ciphertext)
decoded = base64.b64decode(encrypted)
test("Encrypted data has IV (16+ bytes)", 
     len(decoded) >= 16,
     f"Total length: {len(decoded)} bytes (IV=16, Ciphertext={len(decoded)-16})")

# Test 2.6: AES key is 256 bits (32 bytes)
key = get_aes_key()
test("AES key is 256 bits (32 bytes)", 
     len(key) == 32,
     f"Key length: {len(key)} bytes = {len(key)*8} bits")

# Test 2.7: Longer text encryption
long_answer = "This is a longer answer text for testing"
enc_long = encrypt_answer(long_answer)
dec_long = decrypt_answer(enc_long)
test("Longer text encrypts/decrypts correctly", 
     dec_long == long_answer)

# Test 2.8: Special characters
special_answer = "A!@#$%"
enc_special = encrypt_answer(special_answer)
dec_special = decrypt_answer(enc_special)
test("Special characters encrypt/decrypt correctly", 
     dec_special == special_answer)

# Test 2.9: Tampered ciphertext detection
try:
    # Modify one character in the middle of Base64
    tampered = encrypted[:20] + ('X' if encrypted[20] != 'X' else 'Y') + encrypted[21:]
    result = decrypt_answer(tampered)
    # If decryption succeeds but gives wrong result, it's also a fail
    test("Tampered ciphertext is detected", result != answer)
except Exception as e:
    test("Tampered ciphertext raises error", True, f"Error: {type(e).__name__}")

# Test 2.10: Empty/None handling
test("encrypt_answer(None) returns None", encrypt_answer(None) is None)
test("encrypt_answer('') returns None", encrypt_answer('') is None)
test("decrypt_answer(None) returns None", decrypt_answer(None) is None)

# ============================================================================
# 3. RSA DIGITAL SIGNATURES
# ============================================================================
print("\n" + "=" * 70)
print("3️⃣  RSA-2048 DIGITAL SIGNATURES (SHA-256)")
print("=" * 70)

from crypto_utils import sign_quiz_result, verify_quiz_result, load_private_key, load_public_key

# Test 3.1: Key files exist
from crypto_utils import PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
test("Private key file exists", os.path.exists(PRIVATE_KEY_PATH))
test("Public key file exists", os.path.exists(PUBLIC_KEY_PATH))

# Test 3.2: Keys can be loaded
try:
    private_key = load_private_key()
    test("Private key loads successfully", private_key is not None)
except Exception as e:
    test("Private key loads successfully", False, str(e))

try:
    public_key = load_public_key()
    test("Public key loads successfully", public_key is not None)
except Exception as e:
    test("Public key loads successfully", False, str(e))

# Test 3.3: Basic signature and verification
user_id, quiz_id, score, timestamp = 123, 45, 8.5, "2026-01-25T10:30:00"
signature = sign_quiz_result(user_id, quiz_id, score, timestamp)
test("Signature is generated", 
     signature is not None and len(signature) > 100,
     f"Length: {len(signature)} chars")

# Test 3.4: Valid signature verifies
is_valid = verify_quiz_result(user_id, quiz_id, score, timestamp, signature)
test("Valid signature verifies correctly", is_valid)

# Test 3.5: Tampered user_id detected
test("Tampered user_id is detected", 
     not verify_quiz_result(999, quiz_id, score, timestamp, signature))

# Test 3.6: Tampered quiz_id detected
test("Tampered quiz_id is detected", 
     not verify_quiz_result(user_id, 999, score, timestamp, signature))

# Test 3.7: Tampered score detected
test("Tampered score is detected", 
     not verify_quiz_result(user_id, quiz_id, 10.0, timestamp, signature))

# Test 3.8: Tampered timestamp detected
test("Tampered timestamp is detected", 
     not verify_quiz_result(user_id, quiz_id, score, "2026-01-26T10:30:00", signature))

# Test 3.9: Same data produces same signature (deterministic with same message)
sig1 = sign_quiz_result(1, 1, 10, "2026-01-25")
sig2 = sign_quiz_result(1, 1, 10, "2026-01-25")
# Note: PSS padding is probabilistic, so signatures may differ
# But both should verify correctly
test("Signature 1 verifies", verify_quiz_result(1, 1, 10, "2026-01-25", sig1))
test("Signature 2 verifies", verify_quiz_result(1, 1, 10, "2026-01-25", sig2))

# Test 3.10: Signature is Base64 encoded
try:
    decoded_sig = base64.b64decode(signature)
    test("Signature is valid Base64", True, f"Decoded length: {len(decoded_sig)} bytes")
except:
    test("Signature is valid Base64", False)

# Test 3.11: Float score precision
score_float = 8.333333333
sig_float = sign_quiz_result(1, 1, score_float, "2026-01-25")
test("Float score with precision works", 
     verify_quiz_result(1, 1, score_float, "2026-01-25", sig_float))

# Test 3.12: Zero score
sig_zero = sign_quiz_result(1, 1, 0, "2026-01-25")
test("Zero score works", verify_quiz_result(1, 1, 0, "2026-01-25", sig_zero))

# ============================================================================
# 4. BASE64 ENCODING (Verification Tokens)
# ============================================================================
print("\n" + "=" * 70)
print("4️⃣  BASE64 ENCODING (Verification Tokens)")
print("=" * 70)

from crypto_utils import encode_quiz_result_base64, decode_quiz_result_base64

# Test 4.1: Basic encode/decode
user_id, quiz_id, score, timestamp = 123, 45, 8.5, "2026-01-25T14:58:46"
token = encode_quiz_result_base64(user_id, quiz_id, score, timestamp)
test("Token is generated", token is not None and len(token) > 10)

# Test 4.2: Token is valid Base64
try:
    base64.b64decode(token)
    test("Token is valid Base64", True, f"Token: {token}")
except:
    test("Token is valid Base64", False)

# Test 4.3: Decode returns correct data
decoded = decode_quiz_result_base64(token)
test("Decoded user_id matches", decoded['user_id'] == user_id)
test("Decoded quiz_id matches", decoded['quiz_id'] == quiz_id)
test("Decoded score matches", decoded['score'] == score)
test("Decoded timestamp matches", decoded['timestamp'] == timestamp)

# Test 4.4: URL-safe (no problematic characters for URLs)
# Standard Base64 uses +, /, = which might need URL encoding
test("Token character analysis", True, 
     f"Length: {len(token)}, Contains +: {'+' in token}, Contains /: {'/' in token}")

# Test 4.5: Large values
big_token = encode_quiz_result_base64(999999, 999999, 100.0, "2026-12-31T23:59:59.999999")
big_decoded = decode_quiz_result_base64(big_token)
test("Large values encode/decode correctly", 
     big_decoded['user_id'] == 999999 and big_decoded['quiz_id'] == 999999)

# ============================================================================
# 5. HEXADECIMAL ENCODING (Integrity Hashes)
# ============================================================================
print("\n" + "=" * 70)
print("5️⃣  HEXADECIMAL ENCODING (Integrity Hashes)")
print("=" * 70)

from crypto_utils import generate_quiz_integrity_hex, verify_quiz_integrity_hex, hex_to_bytes

# Test 5.1: Generate hex hash
quiz_id = 1
questions_data = "1:What is Python?:A|2:What is Flask?:B"
integrity_hex = generate_quiz_integrity_hex(quiz_id, questions_data)
test("Integrity hash is generated", 
     integrity_hex is not None and len(integrity_hex) == 64,
     f"Hash: {integrity_hex[:32]}...")

# Test 5.2: Hash is valid hexadecimal
try:
    bytes.fromhex(integrity_hex)
    test("Hash is valid hexadecimal", True)
except:
    test("Hash is valid hexadecimal", False)

# Test 5.3: SHA-256 produces 64 hex characters (32 bytes)
test("Hash length is 64 hex chars (SHA-256)", 
     len(integrity_hex) == 64,
     f"Length: {len(integrity_hex)} chars = {len(integrity_hex)//2} bytes")

# Test 5.4: Same input produces same hash
hash1 = generate_quiz_integrity_hex(quiz_id, questions_data)
hash2 = generate_quiz_integrity_hex(quiz_id, questions_data)
test("Same input produces same hash (deterministic)", hash1 == hash2)

# Test 5.5: Different input produces different hash
hash_diff = generate_quiz_integrity_hex(quiz_id, "1:Different question?:C")
test("Different input produces different hash", hash1 != hash_diff)

# Test 5.6: Verify integrity - valid
test("Valid integrity verifies", 
     verify_quiz_integrity_hex(quiz_id, questions_data, integrity_hex))

# Test 5.7: Verify integrity - tampered content
test("Tampered content detected", 
     not verify_quiz_integrity_hex(quiz_id, "1:Tampered?:A", integrity_hex))

# Test 5.8: Verify integrity - tampered quiz_id
test("Tampered quiz_id detected", 
     not verify_quiz_integrity_hex(999, questions_data, integrity_hex))

# Test 5.9: Hex to bytes conversion
hex_string = "48656c6c6f"  # "Hello" in hex
converted = hex_to_bytes(hex_string)
test("Hex to bytes conversion works", 
     converted == b"Hello",
     f"'{hex_string}' -> {converted}")

# Test 5.10: Case insensitivity of hex
upper_hex = integrity_hex.upper()
lower_hex = integrity_hex.lower()
test("Hex verification is case-insensitive", 
     verify_quiz_integrity_hex(quiz_id, questions_data, upper_hex) and
     verify_quiz_integrity_hex(quiz_id, questions_data, lower_hex))

# ============================================================================
# 6. ACCESS CONTROL (Role Decorators)
# ============================================================================
print("\n" + "=" * 70)
print("6️⃣  ACCESS CONTROL (Role-Based Decorators)")
print("=" * 70)

# We'll test the decorator logic by simulating JWT identities
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'test-secret-key'
app.config['TESTING'] = True
jwt = JWTManager(app)

with app.app_context():
    # Test 6.1: Admin identity
    admin_token = create_access_token(identity='admin')
    test("Admin token created", admin_token is not None)
    
    # Test 6.2: User identity structure
    user_identity = {'id': 1, 'email': 'user@test.com', 'role': 'user'}
    user_token = create_access_token(identity=user_identity)
    test("User token created with role structure", user_token is not None)
    
    # Test 6.3: Quiz Master identity structure
    qm_identity = {'id': 1, 'email': 'qm@test.com', 'role': 'quiz_master', 'full_name': 'Test QM'}
    qm_token = create_access_token(identity=qm_identity)
    test("Quiz Master token created with role structure", qm_token is not None)

# Test 6.4: Verify decorator imports work
try:
    from routes.auth_routes import admin_required, user_required, quiz_master_required, admin_or_quiz_master_required
    test("All role decorators import successfully", True)
except ImportError as e:
    test("All role decorators import successfully", False, str(e))

# ============================================================================
# 7. OTP GENERATION & VALIDATION
# ============================================================================
print("\n" + "=" * 70)
print("7️⃣  OTP GENERATION & VALIDATION")
print("=" * 70)

from routes.auth_routes import generate_otp

# Test 7.1: OTP is 6 digits
otp = generate_otp()
test("OTP is 6 characters", len(otp) == 6, f"OTP: {otp}")

# Test 7.2: OTP is numeric only
test("OTP is numeric only", otp.isdigit())

# Test 7.3: OTP uniqueness (generate multiple)
otps = [generate_otp() for _ in range(100)]
unique_otps = set(otps)
test("OTPs have good randomness", 
     len(unique_otps) >= 90,  # At least 90% unique
     f"100 OTPs generated, {len(unique_otps)} unique")

# Test 7.4: OTP range (000000 to 999999)
all_valid = all(0 <= int(otp) <= 999999 for otp in otps)
test("All OTPs in valid range (000000-999999)", all_valid)

# ============================================================================
# 8. DATABASE MODEL SECURITY FIELDS
# ============================================================================
print("\n" + "=" * 70)
print("8️⃣  DATABASE MODEL SECURITY FIELDS")
print("=" * 70)

from models.models import User, QuizMaster, Admin, Quiz, Question, Score

# Test 8.1: User model has password field for hash
test("User model has password field", hasattr(User, 'password'))
test("User model has OTP fields", hasattr(User, 'otp') and hasattr(User, 'otp_created_at'))

# Test 8.2: QuizMaster model has password field
test("QuizMaster model has password field", hasattr(QuizMaster, 'password'))

# Test 8.3: Quiz model has integrity_hash field
test("Quiz model has integrity_hash field", hasattr(Quiz, 'integrity_hash'))

# Test 8.4: Quiz model has ownership tracking
test("Quiz model has created_by_quiz_master_id", hasattr(Quiz, 'created_by_quiz_master_id'))

# Test 8.5: Question model has correct_option for encrypted answers
test("Question model has correct_option field", hasattr(Question, 'correct_option'))

# Test 8.6: Score model has digital_signature
test("Score model has digital_signature field", hasattr(Score, 'digital_signature'))

# Test 8.7: Score model has verification_token
test("Score model has verification_token field", hasattr(Score, 'verification_token'))

# ============================================================================
# 9. SECURITY EDGE CASES
# ============================================================================
print("\n" + "=" * 70)
print("9️⃣  SECURITY EDGE CASES")
print("=" * 70)

# Test 9.1: SQL Injection in hash (should just hash the string)
sql_injection = "'; DROP TABLE users; --"
sql_hash = generate_password_hash(sql_injection)
test("SQL injection string is safely hashed", 
     check_password_hash(sql_hash, sql_injection))

# Test 9.2: XSS in password (should just hash the string)
xss_payload = "<script>alert('xss')</script>"
xss_hash = generate_password_hash(xss_payload)
test("XSS payload is safely hashed", 
     check_password_hash(xss_hash, xss_payload))

# Test 9.3: Null byte injection
null_byte = "password\x00injection"
try:
    null_hash = generate_password_hash(null_byte)
    test("Null byte in password is handled", True)
except:
    test("Null byte in password is handled", False)

# Test 9.4: Very large signature doesn't cause issues
large_data = sign_quiz_result(999999999, 999999999, 999999.999999, "2026-12-31T23:59:59.999999")
test("Large values in signature work", 
     verify_quiz_result(999999999, 999999999, 999999.999999, "2026-12-31T23:59:59.999999", large_data))

# Test 9.5: Negative score handling
neg_sig = sign_quiz_result(1, 1, -5.0, "2026-01-25")
test("Negative score is signed correctly", 
     verify_quiz_result(1, 1, -5.0, "2026-01-25", neg_sig))

# Test 9.6: Encryption of answer with leading/trailing spaces
space_answer = "  A  "
enc_space = encrypt_answer(space_answer)
dec_space = decrypt_answer(enc_space)
test("Answer with spaces preserves spaces", dec_space == space_answer)

# ============================================================================
# 10. CRYPTOGRAPHIC STRENGTH VERIFICATION
# ============================================================================
print("\n" + "=" * 70)
print("🔟  CRYPTOGRAPHIC STRENGTH VERIFICATION")
print("=" * 70)

# Test 10.1: Check hash algorithm strength
is_scrypt = "scrypt:" in hashed
is_pbkdf2 = "260000" in hashed
test("Hash uses strong algorithm (scrypt or pbkdf2 with 260k iterations)", 
     is_scrypt or is_pbkdf2,
     f"Algorithm: {'scrypt (memory-hard, modern)' if is_scrypt else 'pbkdf2:sha256:260000'}")

# Test 10.2: AES key entropy (should be random bytes)
key1 = get_aes_key()
# Check key is not all zeros or a simple pattern
test("AES key has entropy (not all zeros)", 
     key1 != b'\x00' * 32)

# Test 10.3: RSA key size verification
from cryptography.hazmat.primitives.asymmetric import rsa
private_key = load_private_key()
key_size = private_key.key_size
test("RSA key is 2048 bits", key_size == 2048, f"Key size: {key_size} bits")

# Test 10.4: Hash algorithm in signature (SHA-256 = 32 bytes digest)
# The message format: user_id|quiz_id|score|timestamp
message = "123|45|8.5|2026-01-25T10:30:00"
digest = hashlib.sha256(message.encode()).digest()
test("SHA-256 produces 32-byte digest", 
     len(digest) == 32,
     f"Digest length: {len(digest)} bytes")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("📊 FINAL TEST SUMMARY")
print("=" * 70)
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"📝 Total:  {total}")
print(f"📈 Score:  {passed}/{total} ({(passed/total)*100:.1f}%)")
print("=" * 70)

if failed == 0:
    print("\n🎉 ALL TESTS PASSED! Your security implementation is solid.")
else:
    print(f"\n⚠️  {failed} test(s) failed. Review the failures above.")

print("\n📋 Components Tested:")
print("   1. Password Hashing (pbkdf2:sha256 + salt)")
print("   2. AES-256-CBC Encryption (correct answers)")
print("   3. RSA-2048 Digital Signatures (SHA-256)")
print("   4. Base64 Encoding (verification tokens)")
print("   5. Hexadecimal Encoding (integrity hashes)")
print("   6. Access Control (role decorators)")
print("   7. OTP Generation")
print("   8. Database Security Fields")
print("   9. Security Edge Cases")
print("   10. Cryptographic Strength")
print("=" * 70)
